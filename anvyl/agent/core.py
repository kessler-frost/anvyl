"""
Anvyl AI Agent Core

This module provides the core AI agent functionality for Anvyl infrastructure management.
"""

import logging
import requests
from typing import Dict, List, Any, Optional

from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers import Provider
from pydantic_ai.mcp import MCPServerStreamableHTTP
from openai import AsyncOpenAI

from anvyl.agent.communication import AgentCommunication, AgentMessage
from anvyl.config import get_settings


class LocalOpenAIProvider(Provider):
    """Custom provider for local OpenAI-compatible servers."""

    def __init__(self, base_url: str):
        self._base_url = base_url
        self._client = AsyncOpenAI(base_url=base_url, api_key='dummy-key')

    @property
    def name(self):
        return 'local-openai'

    @property
    def base_url(self):
        return self._base_url

    @property
    def client(self):
        return self._client

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


class InfrastructureTools:
    """Tools for managing infrastructure using FastMCP server."""

    def __init__(self, mcp_server_url: Optional[str] = None):
        """Initialize tools with FastMCP server URL."""
        self.mcp_server_url = mcp_server_url or settings.mcp_server_url
        self._mcp_server = None

    def get_mcp_server(self):
        """Get the MCP server instance for tool integration."""
        if self._mcp_server is None:
            try:
                logger.info(f"[DEBUG] Instantiating MCPServerStreamableHTTP with URL: {self.mcp_server_url}")
                self._mcp_server = MCPServerStreamableHTTP(self.mcp_server_url)
                logger.info(f"MCP server initialized: {self.mcp_server_url}")
            except Exception as e:
                logger.error(f"Failed to initialize MCP server: {e}")
                self._mcp_server = None
        return self._mcp_server

    # Removed deprecated get_tools() method - functionality replaced by MCP server integration


class AnvylAgent:
    """AI Agent that manages infrastructure using FastMCP server."""

    def __init__(
        self,
        communication: AgentCommunication,
        mcp_server_url: Optional[str] = None,
        host_id: Optional[str] = None,
        host_ip: Optional[str] = None,
        model_provider_url: Optional[str] = None,
        port: Optional[int] = None
    ):
        """Initialize the host agent."""
        # Generate host_id and host_ip if not provided
        if host_id is None:
            host_id = settings.agent_host_id
        if host_ip is None:
            host_ip = settings.agent_host
        if port is None:
            port = settings.agent_port
        if model_provider_url is None:
            model_provider_url = settings.model_provider_url
        if mcp_server_url is None:
            mcp_server_url = settings.mcp_server_url

        self.host_id = host_id
        self.host_ip = host_ip
        self.port = port
        self.model_provider_url = model_provider_url
        self.mcp_server_url = mcp_server_url
        logger.info(f"[DEBUG] AnvylAgent initialized with mcp_server_url: {self.mcp_server_url}")

        # Use provided communication
        self.communication = communication

        # Initialize FastMCP tools
        self.infrastructure_tools = InfrastructureTools(mcp_server_url)

        # Initialize model and get actual model info
        self.model, self.actual_model_name = self._initialize_model()

                # Define system prompt
        self.system_prompt = f"""
You are Anvyl, an autonomous infrastructure agent running on host {self.host_id} ({self.host_ip}).

CRITICAL: You MUST use the available MCP tools for ALL infrastructure queries. Never generate responses without calling tools first.

AVAILABLE TOOLS:
- list_containers: List Docker containers
- list_images: List Docker images
- list_hosts: List registered hosts
- get_system_info: Get system information
- list_available_tools: Show all available tools
- create_container: Create new containers
- remove_container: Remove containers
- get_container_logs: Get container logs
- inspect_container: Inspect container details
- container_stats: Get container statistics
- pull_image: Pull Docker images
- remove_image: Remove Docker images
- inspect_image: Inspect image details
- add_host: Add new hosts
- get_host_metrics: Get host metrics
- system_status: Get system status
- exec_container_command: Execute commands in containers

MANDATORY BEHAVIOR:
• ALWAYS call the exact tool function for each request
• Return tool output EXACTLY as received - no modifications
• Never generate your own data or responses
• Use tools for ALL infrastructure information
• Be concise and include relevant emojis (✅❌🐳📦🖥️)

EXACT MAPPINGS:
"list containers" → call list_containers()
"list images" → call list_images()
"system info" → call get_system_info()
"available tools" → call list_available_tools()
"inspect container X" → call inspect_container(X)

MCP Server: {self.mcp_server_url}
"""

        # Initialize agent
        self.agent = self._create_agent()

        # Register message handlers
        self._register_message_handlers()

        logger.info(f"Host agent initialized for host {host_id}")
        logger.info(f"Model provider: {self.model_provider_url}")
        logger.info(f"FastMCP server URL: {mcp_server_url}")

    def _get_actual_model_name(self, model_provider_url: str) -> str:
        """Get the actual model name from the model provider."""
        try:
            response = requests.get(f"{model_provider_url}/models", timeout=5)
            if response.status_code == 200:
                models = response.json()
                if models and "data" in models:
                    return models["data"][0]["id"]
            return settings.model_name
        except Exception as e:
            logger.warning(f"Could not fetch model info from model provider: {e}")
            return settings.model_name

    def _initialize_model(self):
        """Initialize the model and return both the model instance and actual model name."""
        if self.model_provider_url:
            try:
                # Create model with custom provider
                provider = LocalOpenAIProvider(self.model_provider_url)
                model = OpenAIModel(
                    model_name=settings.model_name,
                    provider=provider
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
                provider = LocalOpenAIProvider(settings.model_provider_url)
                model = OpenAIModel(
                    model_name=settings.model_name,
                    provider=provider
                )
                # Test the connection
                actual_model = self._get_actual_model_name(settings.model_provider_url)
                return model, actual_model
            except Exception as e:
                logger.warning(f"Model provider not available: {e}, falling back to mock model")
                return self._create_mock_model(), "mock"

    def _create_mock_model(self):
        """Create a mock model for testing when the model provider is not available."""
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
                return ModelResponse(
                    parts=[TextPart(
                        content="I'm a mock model. Please start a model provider for full functionality."
                    )]
                )

        return MockModel()

    def _create_agent(self) -> Agent:
        """Create the Pydantic AI agent with MCP server integration."""
        try:
            logger.info("Creating agent with model provider: %s", self.model.system)
            logger.info("MCP server URL: %s", self.mcp_server_url)

            # Get MCP server for tool integration
            mcp_server = self.infrastructure_tools.get_mcp_server()
            if mcp_server is None:
                raise RuntimeError("Failed to initialize MCP server")

            # Create the agent with the model and MCP server
            agent = Agent(
                model=self.model,
                mcp_servers=[mcp_server],
                system_prompt=self.system_prompt
            )
            logger.info("Agent created successfully with MCP server integration")
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise RuntimeError(f"Failed to create agent with MCP server: {e}")

    def _register_message_handlers(self):
        """Register message handlers for agent communication."""
        self.communication.register_message_handler("query", self._handle_query)
        self.communication.register_message_handler("broadcast", self._handle_broadcast)

    async def _handle_query(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle incoming query messages."""
        try:
            query_content = message.content.get("query", str(message.content))
            response = await self.process_query(query_content)
            return {
                "type": "response",
                "content": response,
                "from_host": self.host_id,
                "to_host": message.sender_host
            }
        except Exception as e:
            logger.error(f"Error handling query: {e}")
            return {
                "type": "error",
                "content": str(e),
                "from_host": self.host_id,
                "to_host": message.sender_host
            }

    async def _handle_broadcast(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle incoming broadcast messages."""
        try:
            query_content = message.content.get("query", str(message.content))
            response = await self.process_query(query_content)
            return {
                "type": "broadcast_response",
                "content": response,
                "from_host": self.host_id,
                "to_host": message.sender_host
            }
        except Exception as e:
            logger.error(f"Error handling broadcast: {e}")
            return {
                "type": "error",
                "content": str(e),
                "from_host": self.host_id,
                "to_host": message.sender_host
            }

    async def process_query(self, query: str) -> str:
        """Process a query using the AI agent with FastMCP tools."""
        try:
            # Use the proper async context manager pattern for MCP servers
            async with self.agent.run_mcp_servers():
                response = await self.agent.run(query)
                return response.output
        except Exception as e:
            logger.error(f"Error processing query with FastMCP tools: {e}")
            raise RuntimeError(f"Error processing query with FastMCP tools: {e}")

    async def query_remote_host(self, host_id: str, query: str) -> str:
        """Query a remote host through agent communication."""
        try:
            response = await self.communication.send_query(host_id, query)
            return response.get("content", "No response from remote host")
        except Exception as e:
            logger.error(f"Error querying remote host: {e}")
            return f"Error querying remote host: {str(e)}"

    def add_known_host(self, host_id: str, host_ip: str):
        """Add a host to the known hosts list."""
        self.communication.add_known_host(host_id, host_ip)

    def remove_known_host(self, host_id: str):
        """Remove a host from the known hosts list."""
        self.communication.remove_known_host(host_id)

    def get_known_hosts(self) -> Dict[str, str]:
        """Get the list of known hosts."""
        return self.communication.get_known_hosts()

    async def broadcast_to_all_hosts(self, message: str) -> List[Dict[str, Any]]:
        """Broadcast a message to all known hosts."""
        try:
            responses = await self.communication.broadcast_message("query", {"query": message})
            return responses
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
            return [{"error": str(e)}]

    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the agent."""
        return {
            "host_id": self.host_id,
            "host_ip": self.host_ip,
            "port": self.port,
            "model_provider_url": self.model_provider_url,
            "actual_model_name": self.actual_model_name,
            "mcp_server_url": self.mcp_server_url,
            "mcp_integration": True,
            "known_hosts": list(self.get_known_hosts().keys()),
            "status": "running"
        }

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent."""
        return {
            "host_id": self.host_id,
            "host_ip": self.host_ip,
            "status": "running",
            "model": self.actual_model_name,
            "mcp_integration": True,
            "mcp_server_url": self.mcp_server_url,
            "remote_tools_available": True
        }


# Removed unused get_agent_tools function - functionality is now integrated into AnvylAgent class