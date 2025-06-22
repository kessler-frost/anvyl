"""
Unit tests for Anvyl Host Agent
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

from anvyl.agent.core import AnvylAgent, HostAgent
from anvyl.agent.communication import AgentMessage, AgentCommunication
from anvyl.config import get_settings

# Get settings for testing
settings = get_settings()


class TestHostAgentInitialization:
    """Test HostAgent initialization and configuration."""

    @patch('anvyl.agent.core.get_infrastructure_client')
    def test_host_agent_init_with_defaults(self, mock_get_client):
        """Test HostAgent initialization with default parameters."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_tools = [Mock(), Mock()]

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            agent = AnvylAgent(
                communication=mock_communication,
                tools=mock_tools
            )

        assert agent.host_id is not None
        assert agent.host_ip is not None
        assert agent.infrastructure_api_url == settings.infra_url
        assert agent.port == settings.agent_port
        assert agent.model_provider_url == settings.model_provider_url
        assert agent.communication == mock_communication
        assert agent.tools == mock_tools

    @patch('anvyl.agent.core.get_infrastructure_client')
    def test_host_agent_init_with_custom_params(self, mock_get_client):
        """Test HostAgent initialization with custom parameters."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_tools = [Mock()]

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "custom-model")):
            agent = AnvylAgent(
                communication=mock_communication,
                tools=mock_tools,
                infrastructure_api_url="http://custom:8080",
                host_id="custom-host-id",
                host_ip="192.168.1.100",
                model_provider_url="http://custom-model:1234/v1",
                port=5555
            )

        assert agent.host_id == "custom-host-id"
        assert agent.host_ip == "192.168.1.100"
        assert agent.infrastructure_api_url == "http://custom:8080"
        assert agent.port == 5555
        assert agent.model_provider_url == "http://custom-model:1234/v1"

    @patch('anvyl.agent.core.get_infrastructure_client')
    @patch('socket.gethostbyname')
    @patch('socket.gethostname')
    def test_host_agent_auto_detect_ip(self, mock_hostname, mock_ip, mock_get_client):
        """Test automatic IP detection when not provided."""
        mock_hostname.return_value = "test-host"
        mock_ip.return_value = "192.168.1.50"
        mock_communication = Mock(spec=AgentCommunication)

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            agent = AnvylAgent(
                communication=mock_communication,
                tools=[]
            )

        assert agent.host_ip == "192.168.1.50"

    @patch('anvyl.agent.core.get_infrastructure_client')
    @patch('socket.gethostbyname')
    def test_host_agent_ip_fallback(self, mock_ip, mock_get_client):
        """Test IP fallback to localhost when detection fails."""
        mock_ip.side_effect = Exception("Network error")
        mock_communication = Mock(spec=AgentCommunication)

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            agent = AnvylAgent(
                communication=mock_communication,
                tools=[]
            )

        assert agent.host_ip == "127.0.0.1"


class TestHostAgentModelInitialization:
    """Test model initialization and configuration."""

    @patch('anvyl.agent.core.get_infrastructure_client')
    @patch('requests.get')
    def test_initialize_model_with_provider(self, mock_requests, mock_get_client):
        """Test model initialization with working provider."""
        # Mock successful response from model provider
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "llama-3.2-3b-instruct"}]
        }
        mock_requests.return_value = mock_response

        mock_communication = Mock(spec=AgentCommunication)

        agent = AnvylAgent(
            communication=mock_communication,
            tools=[],
            model_provider_url="http://localhost:11434/v1"
        )

        assert agent.actual_model_name == "llama-3.2-3b-instruct"
        assert agent.model is not None

    @patch('anvyl.agent.core.get_infrastructure_client')
    @patch('requests.get')
    def test_initialize_model_provider_unavailable(self, mock_requests, mock_get_client):
        """Test model initialization when provider is unavailable."""
        mock_requests.side_effect = Exception("Connection refused")
        mock_communication = Mock(spec=AgentCommunication)

        agent = AnvylAgent(
            communication=mock_communication,
            tools=[],
            model_provider_url="http://localhost:11434/v1"
        )

        assert agent.actual_model_name == "mock"
        assert agent.model is not None

    @patch('anvyl.agent.core.get_infrastructure_client')
    def test_create_mock_model(self, mock_get_client):
        """Test mock model creation."""
        mock_communication = Mock(spec=AgentCommunication)

        with patch.object(AnvylAgent, '_initialize_model') as mock_init:
            # Call the actual _create_mock_model method
            agent = AnvylAgent(communication=mock_communication, tools=[])
            mock_model = agent._create_mock_model()

            assert mock_model.system == "mock"
            assert mock_model.model_name == "mock"
            assert mock_model.provider == "mock"


class TestHostAgentQueryProcessing:
    """Test query processing and AI agent interaction."""

    @patch('anvyl.agent.core.get_infrastructure_client')
    async def test_process_query_success(self, mock_get_client):
        """Test successful query processing."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_agent = AsyncMock()
        mock_result = Mock()
        mock_result.content = "Query processed successfully"
        mock_agent.run.return_value = mock_result

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            host_agent = AnvylAgent(communication=mock_communication, tools=[])
            host_agent.agent = mock_agent

            result = await host_agent.process_query("List containers")

            assert result == "Query processed successfully"
            mock_agent.run.assert_called_once_with("List containers")

    @patch('anvyl.agent.core.get_infrastructure_client')
    async def test_process_query_error(self, mock_get_client):
        """Test query processing with error."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("AI model error")

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            host_agent = AnvylAgent(communication=mock_communication, tools=[])
            host_agent.agent = mock_agent

            result = await host_agent.process_query("List containers")

            assert "Error processing query: AI model error" in result

    @patch('anvyl.agent.core.get_infrastructure_client')
    async def test_query_remote_host_success(self, mock_get_client):
        """Test querying remote host successfully."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_communication.send_query.return_value = {
            "host_id": "remote-host",
            "response": "Remote query response"
        }

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            host_agent = AnvylAgent(communication=mock_communication, tools=[])

            result = await host_agent.query_remote_host("remote-host", "Get status")

            result_data = json.loads(result)
            assert result_data["host_id"] == "remote-host"
            assert result_data["response"] == "Remote query response"

    @patch('anvyl.agent.core.get_infrastructure_client')
    async def test_query_remote_host_error(self, mock_get_client):
        """Test querying remote host with error."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_communication.send_query.side_effect = Exception("Network error")

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            host_agent = AnvylAgent(communication=mock_communication, tools=[])

            result = await host_agent.query_remote_host("remote-host", "Get status")

            assert "Error querying remote host: Network error" in result


class TestHostAgentMessageHandling:
    """Test message handling from other agents."""

    @patch('anvyl.agent.core.get_infrastructure_client')
    async def test_handle_query_message_success(self, mock_get_client):
        """Test handling query message successfully."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_agent = AsyncMock()
        mock_result = Mock()
        mock_result.content = "Query handled successfully"
        mock_agent.run.return_value = mock_result

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            host_agent = AnvylAgent(communication=mock_communication, tools=[])
            host_agent.agent = mock_agent

            message = AgentMessage(
                sender_id="remote-agent-id",
                sender_host="remote-host",
                message_type="query",
                content={"query": "List containers"},
                timestamp=datetime.now()
            )

            result = await host_agent._handle_query(message)

            assert result["host_id"] == host_agent.host_id
            assert result["query"] == "List containers"
            assert result["response"] == "Query handled successfully"

    @patch('anvyl.agent.core.get_infrastructure_client')
    async def test_handle_query_message_error(self, mock_get_client):
        """Test handling query message with error."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("Processing error")

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            host_agent = AnvylAgent(communication=mock_communication, tools=[])
            host_agent.agent = mock_agent

            message = AgentMessage(
                sender_id="remote-agent-id",
                sender_host="remote-host",
                message_type="query",
                content={"query": "List containers"},
                timestamp=datetime.now()
            )

            result = await host_agent._handle_query(message)

            assert result["host_id"] == host_agent.host_id
            assert result["query"] == "List containers"
            assert "error" in result
            assert "Processing error" in result["error"]

    @patch('anvyl.agent.core.get_infrastructure_client')
    async def test_handle_broadcast_message(self, mock_get_client):
        """Test handling broadcast message."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_agent = AsyncMock()
        mock_result = Mock()
        mock_result.content = "Broadcast handled"
        mock_agent.run.return_value = mock_result

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            host_agent = AnvylAgent(communication=mock_communication, tools=[])
            host_agent.agent = mock_agent

            message = AgentMessage(
                sender_id="remote-agent-id",
                sender_host="remote-host",
                message_type="broadcast",
                content={"message": "System update"},
                timestamp=datetime.now()
            )

            result = await host_agent._handle_broadcast(message)

            assert result["host_id"] == host_agent.host_id
            assert result["broadcast"] == "System update"
            assert result["response"] == "Broadcast handled"


class TestHostAgentHostManagement:
    """Test host management functionality."""

    @patch('anvyl.agent.core.get_infrastructure_client')
    def test_add_known_host(self, mock_get_client):
        """Test adding a known host."""
        mock_communication = Mock(spec=AgentCommunication)

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            host_agent = AnvylAgent(communication=mock_communication, tools=[])

            host_agent.add_known_host("host123", "192.168.1.100")

            mock_communication.add_known_host.assert_called_once_with("host123", "192.168.1.100")

    @patch('anvyl.agent.core.get_infrastructure_client')
    def test_remove_known_host(self, mock_get_client):
        """Test removing a known host."""
        mock_communication = Mock(spec=AgentCommunication)

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            host_agent = AnvylAgent(communication=mock_communication, tools=[])

            host_agent.remove_known_host("host123")

            mock_communication.remove_known_host.assert_called_once_with("host123")

    @patch('anvyl.agent.core.get_infrastructure_client')
    def test_get_known_hosts(self, mock_get_client):
        """Test getting known hosts."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_communication.get_known_hosts.return_value = {
            "host123": "192.168.1.100",
            "host456": "192.168.1.101"
        }

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            host_agent = AnvylAgent(communication=mock_communication, tools=[])

            result = host_agent.get_known_hosts()

            assert result == {"host123": "192.168.1.100", "host456": "192.168.1.101"}

    @patch('anvyl.agent.core.get_infrastructure_client')
    async def test_broadcast_to_all_hosts_success(self, mock_get_client):
        """Test broadcasting to all hosts successfully."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_communication.broadcast_message.return_value = [
            {"host_id": "host1", "response": "Received"},
            {"host_id": "host2", "response": "Received"}
        ]

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            host_agent = AnvylAgent(communication=mock_communication, tools=[])

            result = await host_agent.broadcast_to_all_hosts("System update")

            assert len(result) == 2
            assert result[0]["host_id"] == "host1"
            assert result[1]["host_id"] == "host2"

    @patch('anvyl.agent.core.get_infrastructure_client')
    async def test_broadcast_to_all_hosts_error(self, mock_get_client):
        """Test broadcasting to all hosts with error."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_communication.broadcast_message.side_effect = Exception("Broadcast failed")

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            host_agent = AnvylAgent(communication=mock_communication, tools=[])

            result = await host_agent.broadcast_to_all_hosts("System update")

            assert len(result) == 1
            assert "error" in result[0]
            assert "Broadcast failed" in result[0]["error"]


class TestHostAgentInfo:
    """Test agent information and status methods."""

    @patch('anvyl.agent.core.get_infrastructure_client')
    def test_get_agent_info(self, mock_get_client):
        """Test getting agent information."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_communication.get_known_hosts.return_value = {"host1": "192.168.1.100"}

        # Create mock tools with names
        mock_tool1 = Mock()
        mock_tool1.name = "list_containers"
        mock_tool2 = Mock()
        mock_tool2.__name__ = "get_host_info"
        mock_tools = [mock_tool1, mock_tool2]

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "llama-3.2")):
            host_agent = AnvylAgent(
                communication=mock_communication,
                tools=mock_tools,
                host_id="test-host",
                host_ip="127.0.0.1",
                port=4201
            )

            info = host_agent.get_agent_info()

            assert info["host_id"] == "test-host"
            assert info["host_ip"] == "127.0.0.1"
            assert info["llm_model"] == "llama-3.2"
            assert "list_containers" in info["tools_available"]
            assert "get_host_info" in info["tools_available"]
            assert info["known_hosts"] == {"host1": "192.168.1.100"}
            assert info["port"] == 4201

    @patch('anvyl.agent.core.get_infrastructure_client')
    def test_get_agent_info_with_unnamed_tools(self, mock_get_client):
        """Test getting agent info with tools that don't have names."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_communication.get_known_hosts.return_value = {}

        # Create mock tool without name
        mock_tool = Mock(spec=[])  # No name or __name__ attribute
        mock_tool.__class__.__name__ = "UnnamedTool"
        mock_tools = [mock_tool]

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            host_agent = AnvylAgent(
                communication=mock_communication,
                tools=mock_tools
            )

            info = host_agent.get_agent_info()

            assert "UnnamedTool" in info["tools_available"]


class TestHostAgentIntegration:
    """Test integration scenarios."""

    @patch('anvyl.agent.core.get_infrastructure_client')
    async def test_full_workflow_local_query(self, mock_get_client):
        """Test complete workflow of processing a local query."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_agent = AsyncMock()
        mock_result = Mock()
        mock_result.content = "Found 3 containers: nginx, postgres, redis"
        mock_agent.run.return_value = mock_result

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            host_agent = AnvylAgent(communication=mock_communication, tools=[])
            host_agent.agent = mock_agent

            # Process a query
            result = await host_agent.process_query("List all containers")

            assert "Found 3 containers" in result
            mock_agent.run.assert_called_once_with("List all containers")

    @patch('anvyl.agent.core.get_infrastructure_client')
    async def test_full_workflow_remote_query(self, mock_get_client):
        """Test complete workflow of handling a remote query."""
        mock_communication = Mock(spec=AgentCommunication)
        mock_communication.send_query.return_value = {
            "host_id": "remote-host",
            "response": "Remote host has 2 containers",
            "timestamp": "2023-01-01T00:00:00"
        }

        with patch.object(AnvylAgent, '_initialize_model', return_value=(Mock(), "test-model")):
            host_agent = AnvylAgent(communication=mock_communication, tools=[])

            # Query remote host
            result = await host_agent.query_remote_host("remote-host", "Get container count")

            result_data = json.loads(result)
            assert result_data["host_id"] == "remote-host"
            assert "2 containers" in result_data["response"]


class TestHostAgent:
    """Test cases for the HostAgent class."""

    def test_host_agent_initialization(self):
        """Test HostAgent initialization with default values."""
        communication = AgentCommunication("test-host", "127.0.0.1", 4201)

        agent = HostAgent(communication)

        assert agent.communication == communication
        assert agent.infrastructure_api_url == settings.infra_url
        assert agent.port == settings.agent_port
        assert agent.model_provider_url == settings.model_provider_url

    def test_host_agent_with_custom_values(self):
        """Test HostAgent initialization with custom values."""
        communication = AgentCommunication("test-host", "127.0.0.1", 4201)

        agent = HostAgent(
            communication=communication,
            infrastructure_api_url="http://custom-infra:8080",
            port=8080,
            model_provider_url="http://custom-model:1234/v1",
            mcp_server_url="http://custom-mcp:8081/mcp/"
        )

        assert agent.infrastructure_api_url == "http://custom-infra:8080"
        assert agent.port == 8080
        assert agent.model_provider_url == "http://custom-model:1234/v1"
        assert agent.mcp_server_url == "http://custom-mcp:8081/mcp/"

    def test_host_agent_host_ip_property(self):
        """Test the host_ip property."""
        communication = AgentCommunication("test-host", "127.0.0.1", 4201)
        agent = HostAgent(communication)

        assert agent.host_ip == "127.0.0.1"

    @pytest.mark.asyncio
    async def test_process_query_success(self):
        """Test successful query processing."""
        communication = AgentCommunication("test-host", "127.0.0.1", 4201)
        agent = HostAgent(communication)

        # Mock the tools and model
        mock_tools = MagicMock()
        mock_tools.list_containers.return_value = [{"id": "test-container"}]

        with patch.object(agent, '_get_tools', return_value=mock_tools):
            with patch.object(agent, '_get_model', return_value=AsyncMock()):
                result = await agent.process_query("List containers")

                assert result is not None
                assert hasattr(result, 'output')

    @pytest.mark.asyncio
    async def test_process_query_with_model_provider_url(self):
        """Test query processing with custom model provider URL."""
        communication = AgentCommunication("test-host", "127.0.0.1", 4201)
        agent = HostAgent(
            communication,
            model_provider_url=settings.model_provider_url
        )

        # Mock the tools and model
        mock_tools = MagicMock()
        mock_tools.list_containers.return_value = [{"id": "test-container"}]

        with patch.object(agent, '_get_tools', return_value=mock_tools):
            with patch.object(agent, '_get_model', return_value=AsyncMock()):
                result = await agent.process_query("List containers")

                assert result is not None

    @pytest.mark.asyncio
    async def test_process_query_with_mcp_server_url(self):
        """Test query processing with custom MCP server URL."""
        communication = AgentCommunication("test-host", "127.0.0.1", 4201)
        agent = HostAgent(
            communication,
            mcp_server_url=settings.mcp_server_url
        )

        # Mock the tools and model
        mock_tools = MagicMock()
        mock_tools.list_containers.return_value = [{"id": "test-container"}]

        with patch.object(agent, '_get_tools', return_value=mock_tools):
            with patch.object(agent, '_get_model', return_value=AsyncMock()):
                result = await agent.process_query("List containers")

                assert result is not None

    @pytest.mark.asyncio
    async def test_process_query_failure(self):
        """Test query processing failure."""
        communication = AgentCommunication("test-host", "127.0.0.1", 4201)
        agent = HostAgent(communication)

        # Mock the tools to raise an exception
        mock_tools = MagicMock()
        mock_tools.list_containers.side_effect = Exception("Test error")

        with patch.object(agent, '_get_tools', return_value=mock_tools):
            with patch.object(agent, '_get_model', return_value=AsyncMock()):
                result = await agent.process_query("List containers")

                assert result is not None
                assert "error" in result.output.lower()

    def test_get_agent_info(self):
        """Test getting agent information."""
        communication = AgentCommunication("test-host", "127.0.0.1", 4201)
        agent = HostAgent(communication)

        info = agent.get_agent_info()

        assert isinstance(info, dict)
        assert info["host_id"] == "test-host"
        assert info["host_ip"] == "127.0.0.1"
        assert info["port"] == 4201
        assert "infrastructure_api_url" in info
        assert "model_provider_url" in info
        assert "mcp_server_url" in info

    def test_get_agent_info_with_custom_values(self):
        """Test getting agent information with custom values."""
        communication = AgentCommunication("test-host", "127.0.0.1", 4201)
        agent = HostAgent(
            communication,
            infrastructure_api_url="http://custom-infra:8080",
            model_provider_url="http://custom-model:1234/v1",
            mcp_server_url="http://custom-mcp:8081/mcp/"
        )

        info = agent.get_agent_info()

        assert info["infrastructure_api_url"] == "http://custom-infra:8080"
        assert info["model_provider_url"] == "http://custom-model:1234/v1"
        assert info["mcp_server_url"] == "http://custom-mcp:8081/mcp/"

    @pytest.mark.asyncio
    async def test_get_tools_initialization(self):
        """Test tools initialization."""
        communication = AgentCommunication("test-host", "127.0.0.1", 4201)
        agent = HostAgent(communication)

        tools = agent._get_tools()

        assert tools is not None
        assert hasattr(tools, 'list_containers')

    @pytest.mark.asyncio
    async def test_get_model_initialization(self):
        """Test model initialization."""
        communication = AgentCommunication("test-host", "127.0.0.1", 4201)
        agent = HostAgent(communication)

        # Mock the model creation
        with patch('anvyl.agent.core.ChatOpenAI') as mock_chat_openai:
            mock_model = AsyncMock()
            mock_chat_openai.return_value = mock_model

            model = agent._get_model()

            assert model is not None
            mock_chat_openai.assert_called_once()

    def test_agent_communication_integration(self):
        """Test integration with AgentCommunication."""
        communication = AgentCommunication("test-host", "127.0.0.1", 4201)
        agent = HostAgent(communication)

        # Test that the agent uses the communication's host information
        assert agent.host_ip == communication.local_host_ip
        assert agent.port == communication.port

        # Test agent info reflects communication settings
        info = agent.get_agent_info()
        assert info["host_id"] == communication.host_id
        assert info["host_ip"] == communication.local_host_ip
        assert info["port"] == communication.port