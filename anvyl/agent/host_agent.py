"""
Host Agent

This module provides the main AI agent that runs on each host and manages
local infrastructure using LangChain and tool-use capabilities.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.agents import initialize_agent
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama
from langchain_openai import OpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import BaseTool
import json
from langchain_core.language_models.base import BaseLanguageModel
from pydantic import Field

from .tools import InfrastructureTools
from .communication import AgentCommunication, AgentMessage
from ..infrastructure_service import InfrastructureService

logger = logging.getLogger(__name__)


class HostAgent:
    """AI Agent that manages infrastructure on a single host."""

    def __init__(self,
                 infrastructure_service: InfrastructureService,
                 host_id: str,
                 host_ip: str,
                 lmstudio_url: Optional[str] = None,
                 lmstudio_model: str = "default",
                 port: int = 4200):
        """Initialize the host agent."""
        self.infrastructure_service = infrastructure_service
        self.host_id = host_id
        self.host_ip = host_ip
        self.port = port
        self.lmstudio_url = lmstudio_url or "http://localhost:1234/v1"
        self.lmstudio_model = lmstudio_model

        # Initialize communication
        self.communication = AgentCommunication(host_id, host_ip, port)

        # Initialize tools
        self.infrastructure_tools = InfrastructureTools(infrastructure_service)
        self.tools = self.infrastructure_tools.get_tools()

        # Initialize LLM and get actual model info
        self.llm, self.actual_model_name = self._initialize_llm()

        # Initialize agent
        self.agent_executor = self._create_agent()

        # Register message handlers
        self._register_message_handlers()

        logger.info(f"Host agent initialized for host {host_id}")

    def _get_actual_model_name(self, lmstudio_url: str) -> str:
        """Get the actual model name from LMStudio."""
        try:
            import requests
            response = requests.get(f"{lmstudio_url}/models", timeout=5)
            if response.status_code == 200:
                models = response.json()
                if models and "data" in models and models["data"]:
                    # Get the first available model
                    model = models["data"][0]
                    return model.get("id", "unknown")
                else:
                    return "no models available"
            else:
                return f"error: HTTP {response.status_code}"
        except Exception as e:
            logger.warning(f"Could not fetch model info from LMStudio: {e}")
            return "unknown"

    def _initialize_llm(self):
        """Initialize the LLM and return both the LLM instance and actual model name."""
        if self.lmstudio_url:
            try:
                llm = OpenAI(
                    openai_api_base=self.lmstudio_url,
                    model_name=self.lmstudio_model,
                    openai_api_key="dummy-key",
                    temperature=0,
                    max_tokens=1000
                )
                # Test the connection and get actual model name
                actual_model = self._get_actual_model_name(self.lmstudio_url)
                return llm, actual_model
            except Exception as e:
                logger.warning(f"LMStudio not available: {e}, falling back to mock LLM")
                return self._create_mock_llm(), "mock"
        else:
            # Try to use default LMStudio URL
            try:
                llm = OpenAI(
                    openai_api_base="http://localhost:1234/v1",
                    model_name="default",
                    openai_api_key="dummy-key",
                    temperature=0,
                    max_tokens=1000
                )
                # Test the connection
                test_response = llm("Hello")
                if "Error" in test_response:
                    logger.warning("LMStudio not available, falling back to mock LLM")
                    return self._create_mock_llm(), "mock"
                else:
                    actual_model = self._get_actual_model_name("http://localhost:1234/v1")
                    return llm, actual_model
            except Exception as e:
                logger.warning(f"LMStudio not available: {e}, falling back to mock LLM")
                return self._create_mock_llm(), "mock"

    def _create_mock_llm(self):
        """Create a mock LLM for testing when LMStudio is not available."""
        from langchain_core.language_models.base import BaseLanguageModel

        class MockLLM(BaseLanguageModel):
            def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
                return "I'm a mock LLM. Please start LMStudio for full functionality."

            @property
            def _llm_type(self) -> str:
                return "mock"

            # Required abstract methods for BaseLanguageModel
            def predict(self, text: str, *args, **kwargs) -> str:
                return self._call(text)

            async def apredict(self, text: str, *args, **kwargs) -> str:
                return self._call(text)  # Mock async call

            def predict_messages(self, messages, *args, **kwargs):
                raise NotImplementedError("predict_messages is not implemented in MockLLM")

            async def apredict_messages(self, messages, *args, **kwargs):
                raise NotImplementedError("apredict_messages is not implemented in MockLLM")

            def generate_prompt(self, *args, **kwargs):
                raise NotImplementedError("generate_prompt is not implemented in MockLLM")

            async def agenerate_prompt(self, *args, **kwargs):
                raise NotImplementedError("agenerate_prompt is not implemented in MockLLM")

            def invoke(self, *args, **kwargs):
                raise NotImplementedError("invoke is not implemented in MockLLM")

        return MockLLM()

    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent with tools."""
        try:
            logger.info("Creating agent with LLM type: %s", self.llm._llm_type)
            logger.info("Number of tools: %d", len(self.tools))

            system_prompt = """You are an AI agent responsible for managing infrastructure on this host.

Your capabilities include:
- Managing Docker containers (list, start, stop, create)
- Monitoring host resources (CPU, memory, disk)
- Executing commands on the host
- Communicating with agents on other hosts

When asked about other hosts, use the appropriate tools to query them.
Always provide clear, actionable responses and explain what you're doing.

Current host: {host_id} ({host_ip})"""

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt.format(host_id=self.host_id, host_ip=self.host_ip)),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            logger.info("Creating OpenAI tools agent...")
            # Use create_openai_tools_agent for better compatibility with newer LangChain
            agent = create_openai_tools_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            logger.info("Creating agent executor...")
            return AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True
            )
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
            result = await self.agent_executor.ainvoke({"input": query})

            return {
                "host_id": self.host_id,
                "host_ip": self.host_ip,
                "query": query,
                "response": result.get("output", "No response generated"),
                "timestamp": message.timestamp.isoformat()
            }
        except Exception as e:
            logger.error(f"Error handling query: {e}")
            return {
                "host_id": self.host_id,
                "error": str(e),
                "query": message.content.get("query", "")
            }

    async def _handle_broadcast(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle a broadcast message from another agent."""
        try:
            content = message.content
            logger.info(f"Handling broadcast from {message.sender_host}: {content}")

            # For now, just acknowledge the broadcast
            # In the future, this could trigger specific actions
            return {
                "host_id": self.host_id,
                "host_ip": self.host_ip,
                "broadcast_received": True,
                "content": content,
                "timestamp": message.timestamp.isoformat()
            }
        except Exception as e:
            logger.error(f"Error handling broadcast: {e}")
            return {
                "host_id": self.host_id,
                "error": str(e)
            }

    async def process_query(self, query: str) -> str:
        """Process a query using the agent."""
        try:
            result = await self.agent_executor.ainvoke({"input": query})
            return result.get("output", "No response generated")
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"Error processing query: {str(e)}"

    async def query_remote_host(self, host_id: str, query: str) -> str:
        """Query a remote host's agent."""
        result = await self.communication.send_query(host_id, query)
        if "error" in result:
            return f"Error querying remote host: {result['error']}"
        else:
            return result.get("response", "No response from remote host")

    async def get_remote_containers(self, host_id: str) -> str:
        """Get containers from a remote host."""
        return await self.query_remote_host(host_id, "List all containers on this host")

    async def get_remote_host_info(self, host_id: str) -> str:
        """Get host information from a remote host."""
        return await self.query_remote_host(host_id, "Get host information and resources")

    def add_known_host(self, host_id: str, host_ip: str):
        """Add a host to the known hosts list."""
        self.communication.add_known_host(host_id, host_ip)

    def remove_known_host(self, host_id: str):
        """Remove a host from the known hosts list."""
        self.communication.remove_known_host(host_id)

    def get_known_hosts(self) -> Dict[str, str]:
        """Get all known hosts."""
        return self.communication.get_known_hosts()

    async def broadcast_to_all_hosts(self, message: str) -> List[Dict[str, Any]]:
        """Broadcast a message to all known hosts."""
        return await self.communication.broadcast_message("info", {"message": message})

    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent."""
        return {
            "host_id": self.host_id,
            "host_ip": self.host_ip,
            "port": self.port,
            "known_hosts": self.get_known_hosts(),
            "tools_available": [tool.name for tool in self.tools],
            "llm_model": self.llm._llm_type if hasattr(self.llm, '_llm_type') else "unknown",
            "actual_model_name": self.actual_model_name
        }