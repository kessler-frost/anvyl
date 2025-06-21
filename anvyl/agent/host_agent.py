"""
Host Agent

This module provides the main AI agent that runs on each host and manages
local infrastructure using Pydantic AI and tool-use capabilities.
"""

import logging
import asyncio
import uuid
import socket
from typing import Dict, List, Any, Optional
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import json

from anvyl.agent.communication import AgentCommunication, AgentMessage
from anvyl.infra.client import get_infrastructure_client

logger = logging.getLogger(__name__)


class HostAgent:
    """AI Agent that manages infrastructure on a single host."""

    def __init__(
        self,
        communication: AgentCommunication,
        tools: List,
        infrastructure_api_url: str = "http://localhost:4200",
        host_id: str = None,
        host_ip: str = None,
        model_provider_url: Optional[str] = None,
        port: int = 4201):
        """Initialize the host agent."""
        self.infrastructure_api_url = infrastructure_api_url
        self.infrastructure_client = None  # Will be initialized async

        # Use provided communication and tools
        self.communication = communication
        self.tools = tools

        # Generate host_id and host_ip if not provided
        if host_id is None:
            host_id = str(uuid.uuid4())
        if host_ip is None:
            try:
                host_ip = socket.gethostbyname(socket.gethostname())
            except:
                host_ip = "127.0.0.1"

        self.host_id = host_id
        self.host_ip = host_ip
        self.port = port
        self.model_provider_url = model_provider_url or "http://localhost:11434/v1"

        # Initialize model and get actual model info
        self.model, self.actual_model_name = self._initialize_model()

        # Define system prompt
        self.system_prompt = f"""You are an AI agent running on host {self.host_id} (IP: {self.host_ip}) in the Anvyl infrastructure orchestration system.

Your primary role is to help manage and monitor infrastructure on this host and communicate with other hosts in the network.

AVAILABLE TOOLS:
- list_containers: List Docker containers (use all=True to include stopped/non-Anvyl containers)  
- get_container_info: Get detailed information about a specific container
- stop_container: Stop a running container
- create_container: Create and start a new container with specified image, ports, volumes, environment
- get_host_info: Get information about a specific host in the network
- get_host_resources: Get current CPU, memory, and disk usage for the local host
- list_hosts: List all hosts in the Anvyl network with their status, IP addresses, and tags
- execute_command: Run shell commands on the local host
- duckduckgo_search: Search the web using DuckDuckGo (if available) - useful for finding current information, documentation, troubleshooting guides, and latest updates about technologies you're working with

LIMITATIONS:
- Container start functionality is not yet implemented via the API
- Remote host resource querying is not yet implemented
- Container operations are limited to Anvyl-managed containers by default
- Command execution on hosts is not available for security reasons

COMMUNICATION:
- You can communicate with other agents in the network
- You can query remote hosts for container and host information
- You can broadcast messages to all known hosts

When responding to queries:
1. Use the appropriate tools to gather information
2. Provide clear, actionable responses
3. Include relevant details like container IDs, status, and resource usage
4. Be helpful and explain what you're doing
5. If a tool fails, explain the error and suggest alternatives

Always be accurate about your capabilities and limitations."""

        # Initialize agent
        self.agent = self._create_agent()

        # Register message handlers
        self._register_message_handlers()

        logger.info(f"Host agent initialized for host {host_id}")
        logger.info(f"Model provider: {self.model_provider_url}")

    async def _initialize_infrastructure_client(self):
        """Initialize the infrastructure client asynchronously."""
        if self.infrastructure_client is None:
            self.infrastructure_client = await get_infrastructure_client(self.infrastructure_api_url)

    def _get_actual_model_name(self, model_provider_url: str) -> str:
        """Get the actual model name from the model provider."""
        try:
            import requests
            response = requests.get(f"{model_provider_url}/models", timeout=5)
            if response.status_code == 200:
                models = response.json()
                if models and "data" in models:
                    return models["data"][0]["id"]
            return self.actual_model_name
        except Exception as e:
            logger.warning(f"Could not fetch model info from model provider: {e}")
            return self.actual_model_name

    def _initialize_model(self):
        """Initialize the model and return both the model instance and actual model name."""
        # NOTE: The model_name here is arbitrary and only required by the OpenAIModel constructor.
        # It is not exposed to the user and can be changed to any valid model name supported by the provider.
        # 'llama3.2:latest' is used as a default, but you can change it if needed.
        if self.model_provider_url:
            try:
                # Create model provider using OpenAIProvider with custom base URL
                model_provider = OpenAIProvider(base_url=self.model_provider_url)
                model = OpenAIModel(
                    model_name="llama3.2:latest",  # Arbitrary model name, required by OpenAIModel
                    provider=model_provider
                )
                # Test the connection and get actual model name
                actual_model = self._get_actual_model_name(self.model_provider_url)
                return model, actual_model
            except Exception as e:
                logger.warning(f"Model provider not available: {e}, falling back to mock model")
                return self._create_mock_model(), "mock"
        else:
            # Try to use default model provider URL
            try:
                model_provider = OpenAIProvider(base_url="http://localhost:11434/v1")
                model = OpenAIModel(
                    model_name="llama3.2:latest",  # Arbitrary model name, required by OpenAIModel
                    provider=model_provider
                )
                # Test the connection
                actual_model = self._get_actual_model_name("http://localhost:11434/v1")
                return model, actual_model
            except Exception as e:
                logger.warning(f"Model provider not available: {e}, falling back to mock model")
                return self._create_mock_model(), "mock"

    def _create_mock_model(self):
        """Create a mock model for testing when the model provider is not available."""
        from pydantic_ai.models import Model

        class MockModel(Model):
            @property
            def system(self):
                return "mock"

            @property
            def model_name(self):
                return "mock"

            @property
            def provider(self):
                return "mock"

            async def request(self, messages, model_settings=None, model_request_parameters=None):
                from pydantic_ai.models import ModelResponse, ModelResponsePart
                return ModelResponse(
                    parts=[ModelResponsePart(
                        type="text",
                        text="I'm a mock model. Please start a model provider for full functionality."
                    )]
                )

        return MockModel()

    def _create_agent(self) -> Agent:
        """Create the Pydantic AI agent with tools."""
        try:
            logger.info("Creating agent with model provider: %s", self.model.system)
            logger.info("Number of tools: %d", len(self.tools))

            # Create the agent with the model and tools
            agent = Agent(
                model=self.model,
                tools=self.tools,
                system_prompt=self.system_prompt
            )

            logger.info("Agent created successfully")
            return agent
        except Exception as e:
            logger.error("Error creating agent: %s", str(e))
            raise

    def _register_message_handlers(self):
        """Register handlers for incoming messages from other agents."""
        self.communication.register_message_handler("query", self._handle_query)
        self.communication.register_message_handler("broadcast", self._handle_broadcast)

    async def _handle_query(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle a query from another agent."""
        try:
            query = message.content.get("query", "")
            logger.info(f"Handling query from {message.sender_host}: {query}")

            # Execute the query using the agent
            result = await self.agent.run(query)

            return {
                "host_id": self.host_id,
                "host_ip": self.host_ip,
                "query": query,
                "response": result.content if hasattr(result, 'content') else str(result),
                "timestamp": message.timestamp.isoformat()
            }
        except Exception as e:
            logger.error(f"Error handling query: {e}")
            return {
                "host_id": self.host_id,
                "host_ip": self.host_ip,
                "query": query,
                "error": str(e),
                "timestamp": message.timestamp.isoformat()
            }

    async def _handle_broadcast(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle a broadcast message from another agent."""
        try:
            query = message.content.get("message", "")
            logger.info(f"Handling broadcast from {message.sender_host}: {query}")

            # Execute the query using the agent
            result = await self.agent.run(query)

            return {
                "host_id": self.host_id,
                "host_ip": self.host_ip,
                "broadcast": query,
                "response": result.content if hasattr(result, 'content') else str(result),
                "timestamp": message.timestamp.isoformat()
            }
        except Exception as e:
            logger.error(f"Error handling broadcast: {e}")
            return {
                "host_id": self.host_id,
                "host_ip": self.host_ip,
                "broadcast": query,
                "error": str(e),
                "timestamp": message.timestamp.isoformat()
            }

    async def process_query(self, query: str) -> str:
        """Process a query using the AI agent."""
        try:
            result = await self.agent.run(query)
            return result.content if hasattr(result, 'content') else str(result)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"Error processing query: {str(e)}"

    async def query_remote_host(self, host_id: str, query: str) -> str:
        """Query a remote host's agent."""
        try:
            result = await self.communication.send_query(host_id, query)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error querying remote host: {e}")
            return f"Error querying remote host: {str(e)}"

    async def get_remote_containers(self, host_id: str) -> str:
        """Get containers from a remote host."""
        return await self.query_remote_host(host_id, "List all containers on this host")

    async def get_remote_host_info(self, host_id: str) -> str:
        """Get host information from a remote host."""
        return await self.query_remote_host(host_id, "Get host information and resources")

    def add_known_host(self, host_id: str, host_ip: str):
        """Add a known host."""
        self.communication.add_known_host(host_id, host_ip)

    def remove_known_host(self, host_id: str):
        """Remove a known host."""
        self.communication.remove_known_host(host_id)

    def get_known_hosts(self) -> Dict[str, str]:
        """Get all known hosts."""
        return self.communication.get_known_hosts()

    async def broadcast_to_all_hosts(self, message: str) -> List[Dict[str, Any]]:
        """Broadcast a message to all known hosts."""
        try:
            return await self.communication.broadcast_message("broadcast", {"message": message})
        except Exception as e:
            logger.error(f"Error broadcasting to all hosts: {e}")
            return [{"error": str(e)}]

    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent."""
        # Extract tool names properly from Pydantic AI Tool objects
        tool_names = []
        if self.tools:
            for tool in self.tools:
                if hasattr(tool, 'name'):
                    tool_names.append(tool.name)
                elif hasattr(tool, '__name__'):
                    tool_names.append(tool.__name__)
                else:
                    tool_names.append(str(type(tool).__name__))

        return {
            "host_id": self.host_id,
            "host_ip": self.host_ip,
            "llm_model": self.actual_model_name,
            "actual_model_name": self.actual_model_name,
            "tools_available": tool_names,
            "known_hosts": self.get_known_hosts(),
            "port": self.port
        }

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent."""
        return {
            "host_id": self.host_id,
            "is_running": self.is_running,
            "last_heartbeat": self.last_heartbeat,
            "model_provider_url": self.model_provider_url,
            "actual_model_name": self.actual_model_name,
            "agent_config": self.agent_config
        }