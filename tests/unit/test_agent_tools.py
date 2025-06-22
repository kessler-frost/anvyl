"""
Unit tests for Anvyl Agent Tools and Communication
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from anvyl.agent.communication import AgentCommunication, AgentMessage, RemoteQueryTool
from anvyl.agent.tools import InfrastructureTools
from anvyl.infra.client import InfrastructureClient


class TestAgentMessage:
    """Test AgentMessage dataclass functionality."""

    def test_agent_message_creation(self):
        """Test creating an AgentMessage with all fields."""
        message = AgentMessage(
            sender_id="sender-123",
            sender_host="192.168.1.100",
            message_type="query",
            content={"query": "test query"},
            recipient_id="recipient-456",
            recipient_host="192.168.1.101"
        )
        
        assert message.sender_id == "sender-123"
        assert message.sender_host == "192.168.1.100"
        assert message.message_type == "query"
        assert message.content == {"query": "test query"}
        assert message.recipient_id == "recipient-456"
        assert message.recipient_host == "192.168.1.101"
        assert message.timestamp is not None

    def test_agent_message_auto_timestamp(self):
        """Test automatic timestamp generation."""
        before_time = datetime.now(timezone.utc)
        
        message = AgentMessage(
            sender_id="sender-123",
            sender_host="192.168.1.100",
            message_type="query",
            content={"query": "test"}
        )
        
        after_time = datetime.now(timezone.utc)
        
        assert before_time <= message.timestamp <= after_time

    def test_agent_message_custom_timestamp(self):
        """Test setting custom timestamp."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        message = AgentMessage(
            sender_id="sender-123",
            sender_host="192.168.1.100",
            message_type="query",
            content={"query": "test"},
            timestamp=custom_time
        )
        
        assert message.timestamp == custom_time


class TestAgentCommunication:
    """Test AgentCommunication functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.communication = AgentCommunication("local-host", "127.0.0.1", 4200)

    def test_communication_initialization(self):
        """Test AgentCommunication initialization."""
        assert self.communication.local_host_id == "local-host"
        assert self.communication.local_host_ip == "127.0.0.1"
        assert self.communication.port == 4200
        assert isinstance(self.communication.known_hosts, dict)
        assert isinstance(self.communication.message_handlers, dict)

    def test_register_message_handler(self):
        """Test registering message handlers."""
        mock_handler = Mock()
        
        self.communication.register_message_handler("query", mock_handler)
        
        assert "query" in self.communication.message_handlers
        assert self.communication.message_handlers["query"] == mock_handler

    def test_add_known_host(self):
        """Test adding known hosts."""
        self.communication.add_known_host("remote-host", "192.168.1.100")
        
        assert "remote-host" in self.communication.known_hosts
        assert self.communication.known_hosts["remote-host"] == "192.168.1.100"

    def test_remove_known_host(self):
        """Test removing known hosts."""
        self.communication.add_known_host("temp-host", "192.168.1.100")
        self.communication.remove_known_host("temp-host")
        
        assert "temp-host" not in self.communication.known_hosts

    def test_remove_nonexistent_host(self):
        """Test removing non-existent host."""
        # Should not raise an error
        self.communication.remove_known_host("nonexistent-host")

    def test_get_known_hosts(self):
        """Test getting known hosts."""
        self.communication.add_known_host("host1", "192.168.1.100")
        self.communication.add_known_host("host2", "192.168.1.101")
        
        hosts = self.communication.get_known_hosts()
        
        assert hosts == {"host1": "192.168.1.100", "host2": "192.168.1.101"}
        # Verify it returns a copy, not the original dict
        hosts["host3"] = "192.168.1.102"
        assert "host3" not in self.communication.known_hosts

    @patch('aiohttp.ClientSession.post')
    async def test_send_query_success(self, mock_post):
        """Test successful query sending."""
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"response": "success"}
        mock_post.return_value.__aenter__.return_value = mock_response
        
        self.communication.add_known_host("target-host", "192.168.1.100")
        
        result = await self.communication.send_query("target-host", "test query")
        
        assert result == {"response": "success"}
        mock_post.assert_called_once()

    async def test_send_query_unknown_host(self):
        """Test sending query to unknown host."""
        result = await self.communication.send_query("unknown-host", "test query")
        
        assert "error" in result
        assert "Unknown host" in result["error"]

    @patch('aiohttp.ClientSession.post')
    async def test_send_query_http_error(self, mock_post):
        """Test sending query with HTTP error."""
        # Setup mock response with error
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Internal server error"
        mock_post.return_value.__aenter__.return_value = mock_response
        
        self.communication.add_known_host("target-host", "192.168.1.100")
        
        result = await self.communication.send_query("target-host", "test query")
        
        assert "error" in result
        assert "HTTP 500" in result["error"]

    @patch('aiohttp.ClientSession.post')
    async def test_send_query_network_error(self, mock_post):
        """Test sending query with network error."""
        # Setup mock to raise exception
        mock_post.side_effect = Exception("Connection refused")
        
        self.communication.add_known_host("target-host", "192.168.1.100")
        
        result = await self.communication.send_query("target-host", "test query")
        
        assert "error" in result
        assert "Communication error" in result["error"]

    @patch('aiohttp.ClientSession.post')
    async def test_broadcast_message_success(self, mock_post):
        """Test successful message broadcasting."""
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"host_id": "host1", "response": "received"}
        mock_post.return_value.__aenter__.return_value = mock_response
        
        self.communication.add_known_host("host1", "192.168.1.100")
        self.communication.add_known_host("host2", "192.168.1.101")
        
        result = await self.communication.broadcast_message("test", {"message": "hello"})
        
        assert len(result) == 2  # Sent to both hosts
        assert all("host_id" in r for r in result)

    @patch('aiohttp.ClientSession.post')
    async def test_broadcast_message_skip_self(self, mock_post):
        """Test broadcast skips local host."""
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"response": "received"}
        mock_post.return_value.__aenter__.return_value = mock_response
        
        self.communication.add_known_host("local-host", "127.0.0.1")  # Same as local
        self.communication.add_known_host("remote-host", "192.168.1.100")
        
        result = await self.communication.broadcast_message("test", {"message": "hello"})
        
        assert len(result) == 1  # Only sent to remote host
        mock_post.assert_called_once()

    async def test_handle_incoming_message_success(self):
        """Test successful incoming message handling."""
        mock_handler = AsyncMock(return_value={"response": "handled"})
        self.communication.register_message_handler("query", mock_handler)
        
        message_data = {
            "sender_id": "remote-agent",
            "sender_host": "192.168.1.100",
            "message_type": "query",
            "content": {"query": "test"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        result = await self.communication.handle_incoming_message(message_data)
        
        assert result == {"response": "handled"}
        mock_handler.assert_called_once()

    async def test_handle_incoming_message_unknown_type(self):
        """Test handling message with unknown type."""
        message_data = {
            "sender_id": "remote-agent",
            "sender_host": "192.168.1.100",
            "message_type": "unknown",
            "content": {"data": "test"}
        }
        
        result = await self.communication.handle_incoming_message(message_data)
        
        assert "error" in result
        assert "Unknown message type" in result["error"]

    async def test_handle_incoming_message_error(self):
        """Test handling message with invalid data."""
        # Missing required fields
        message_data = {
            "sender_host": "192.168.1.100",
            "content": {"data": "test"}
        }
        
        result = await self.communication.handle_incoming_message(message_data)
        
        assert "error" in result
        assert "Message handling error" in result["error"]


class TestRemoteQueryTool:
    """Test RemoteQueryTool functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_communication = Mock(spec=AgentCommunication)
        self.tool = RemoteQueryTool(self.mock_communication)

    async def test_query_remote_agent_success(self):
        """Test successful remote agent query."""
        self.mock_communication.send_query.return_value = {
            "host_id": "remote-host",
            "response": "Remote response",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        result = await self.tool.query_remote_agent("remote-host", "test query")
        
        assert "Remote response" in result
        assert "remote-host" in result
        self.mock_communication.send_query.assert_called_once_with("remote-host", "test query")

    async def test_query_remote_agent_error(self):
        """Test remote agent query with error."""
        self.mock_communication.send_query.return_value = {
            "error": "Host not reachable"
        }
        
        result = await self.tool.query_remote_agent("remote-host", "test query")
        
        assert "Error querying remote agent" in result
        assert "Host not reachable" in result

    async def test_get_remote_containers(self):
        """Test getting containers from remote host."""
        self.mock_communication.send_query.return_value = {
            "host_id": "remote-host",
            "containers": [{"name": "nginx", "status": "running"}]
        }
        
        result = await self.tool.get_remote_containers("remote-host")
        
        assert "nginx" in result
        assert "running" in result
        self.mock_communication.send_query.assert_called_once_with(
            "remote-host", "List all containers on this host"
        )

    async def test_get_remote_host_info(self):
        """Test getting host info from remote host."""
        self.mock_communication.send_query.return_value = {
            "host_id": "remote-host",
            "info": {"cpu_count": 8, "memory": "16GB"}
        }
        
        result = await self.tool.get_remote_host_info("remote-host")
        
        assert "cpu_count" in result
        assert "16GB" in result
        self.mock_communication.send_query.assert_called_once_with(
            "remote-host", "Get host information and resources"
        )

    async def test_get_remote_host_resources(self):
        """Test getting resource usage from remote host."""
        self.mock_communication.send_query.return_value = {
            "host_id": "remote-host",
            "resources": {"cpu_usage": "45%", "memory_usage": "60%"}
        }
        
        result = await self.tool.get_remote_host_resources("remote-host")
        
        assert "cpu_usage" in result
        assert "45%" in result
        self.mock_communication.send_query.assert_called_once_with(
            "remote-host", "Get current resource usage"
        )


class TestAgentCommunicationIntegration:
    """Integration tests for agent communication."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent1 = AgentCommunication("agent1", "192.168.1.100", 4201)
        self.agent2 = AgentCommunication("agent2", "192.168.1.101", 4202)

    def test_bidirectional_host_management(self):
        """Test bidirectional host management."""
        # Agent1 knows about Agent2
        self.agent1.add_known_host("agent2", "192.168.1.101")
        
        # Agent2 knows about Agent1
        self.agent2.add_known_host("agent1", "192.168.1.100")
        
        assert self.agent1.get_known_hosts()["agent2"] == "192.168.1.101"
        assert self.agent2.get_known_hosts()["agent1"] == "192.168.1.100"

    def test_message_handler_registration(self):
        """Test message handler registration and retrieval."""
        query_handler = Mock()
        broadcast_handler = Mock()
        
        self.agent1.register_message_handler("query", query_handler)
        self.agent1.register_message_handler("broadcast", broadcast_handler)
        
        assert self.agent1.message_handlers["query"] == query_handler
        assert self.agent1.message_handlers["broadcast"] == broadcast_handler

    async def test_self_communication_prevention(self):
        """Test that agents don't send messages to themselves."""
        self.agent1.add_known_host("agent1", "192.168.1.100")  # Add self
        self.agent1.add_known_host("agent2", "192.168.1.101")  # Add remote
        
        # Mock the HTTP call
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"response": "ok"}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await self.agent1.broadcast_message("test", {"msg": "hello"})
            
            # Should only call once (to agent2, not to self)
            assert mock_post.call_count == 1


class TestAgentToolsErrorHandling:
    """Test error handling in agent tools."""

    def setup_method(self):
        """Set up test fixtures."""
        self.communication = AgentCommunication("test-agent", "127.0.0.1", 4200)
        self.tool = RemoteQueryTool(self.communication)

    async def test_communication_timeout_handling(self):
        """Test handling of communication timeouts."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError("Request timed out")
            
            self.communication.add_known_host("slow-host", "192.168.1.200")
            result = await self.communication.send_query("slow-host", "test")
            
            assert "error" in result
            assert "Communication error" in result["error"]

    async def test_malformed_response_handling(self):
        """Test handling of malformed responses."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.side_effect = Exception("Invalid JSON")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            self.communication.add_known_host("bad-host", "192.168.1.200")
            result = await self.communication.send_query("bad-host", "test")
            
            assert "error" in result

    async def test_handler_exception_handling(self):
        """Test handling of exceptions in message handlers."""
        def failing_handler(message):
            raise Exception("Handler failed")
        
        self.communication.register_message_handler("test", failing_handler)
        
        message_data = {
            "sender_id": "test-sender",
            "sender_host": "192.168.1.100",
            "message_type": "test",
            "content": {"data": "test"}
        }
        
        result = await self.communication.handle_incoming_message(message_data)
        
        assert "error" in result
        assert "Message handling error" in result["error"]


class TestAgentMessageSerialization:
    """Test message serialization and deserialization."""

    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        timestamp = datetime.now(timezone.utc)
        message = AgentMessage(
            sender_id="sender-123",
            sender_host="192.168.1.100",
            message_type="query",
            content={"query": "test"},
            timestamp=timestamp
        )
        
        message_dict = message.__dict__
        
        assert message_dict["sender_id"] == "sender-123"
        assert message_dict["sender_host"] == "192.168.1.100"
        assert message_dict["message_type"] == "query"
        assert message_dict["content"] == {"query": "test"}
        assert message_dict["timestamp"] == timestamp

    def test_message_from_dict(self):
        """Test creating message from dictionary."""
        timestamp = datetime.now(timezone.utc)
        message_dict = {
            "sender_id": "sender-123",
            "sender_host": "192.168.1.100",
            "message_type": "query",
            "content": {"query": "test"},
            "timestamp": timestamp
        }
        
        message = AgentMessage(**message_dict)
        
        assert message.sender_id == "sender-123"
        assert message.sender_host == "192.168.1.100"
        assert message.message_type == "query"
        assert message.content == {"query": "test"}
        assert message.timestamp == timestamp

    def test_message_json_serialization(self):
        """Test JSON serialization of message content."""
        complex_content = {
            "query": "complex query",
            "parameters": {"limit": 10, "filters": ["active", "running"]},
            "metadata": {"priority": "high", "timeout": 30}
        }
        
        message = AgentMessage(
            sender_id="sender-123",
            sender_host="192.168.1.100",
            message_type="query",
            content=complex_content
        )
        
        # Verify content can be serialized to JSON
        json_str = json.dumps(message.content)
        deserialized = json.loads(json_str)
        
        assert deserialized == complex_content

class TestInfrastructureTools:
    """Test InfrastructureTools functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=InfrastructureClient)
        self.tools = InfrastructureTools(self.mock_client)

    @pytest.mark.asyncio
    async def test_get_container_logs_success(self):
        """Test getting container logs successfully."""
        # Mock the infrastructure client response
        self.mock_client.get_logs.return_value = "Container log output\nMore log lines"
        
        result = await self.tools.get_container_logs("test-container-id", tail=50)
        
        assert "Container test-container-id logs:" in result
        assert "Container log output" in result
        self.mock_client.get_logs.assert_called_once_with("test-container-id", follow=False, tail=50)

    @pytest.mark.asyncio
    async def test_get_container_logs_not_found(self):
        """Test getting container logs when container not found."""
        # Mock the infrastructure client response
        self.mock_client.get_logs.return_value = None
        
        result = await self.tools.get_container_logs("nonexistent-container")
        
        assert "Container nonexistent-container not found or no logs available" in result
        self.mock_client.get_logs.assert_called_once_with("nonexistent-container", follow=False, tail=100)

    @pytest.mark.asyncio
    async def test_get_container_logs_error(self):
        """Test getting container logs with error."""
        # Mock the infrastructure client to raise an exception
        self.mock_client.get_logs.side_effect = Exception("Connection failed")
        
        result = await self.tools.get_container_logs("test-container-id")
        
        assert "Error getting container logs: Connection failed" in result
        self.mock_client.get_logs.assert_called_once_with("test-container-id", follow=False, tail=100)

    @pytest.mark.asyncio
    async def test_get_container_logs_with_follow(self):
        """Test getting container logs with follow=True."""
        # Mock the infrastructure client response
        self.mock_client.get_logs.return_value = "Real-time log output"
        
        result = await self.tools.get_container_logs("test-container-id", follow=True, tail=200)
        
        assert "Container test-container-id logs:" in result
        assert "Real-time log output" in result
        self.mock_client.get_logs.assert_called_once_with("test-container-id", follow=True, tail=200)

    def test_get_tools_includes_container_logs(self):
        """Test that get_tools includes the container logs tool."""
        tools = self.tools.get_tools()
        
        # Find the container logs tool
        container_logs_tool = None
        tool_names = []
        for tool in tools:
            name = getattr(tool, 'name', None)
            if name:
                tool_names.append(name)
                if name == 'get_container_logs':
                    container_logs_tool = tool
                    break
        if container_logs_tool is None:
            print(f"Registered tool names: {tool_names}")
            print(f"Tools list: {tools}")
        assert container_logs_tool is not None, "Container logs tool should be included in available tools"

    def test_get_tools_includes_add_container(self):
        """Test that get_tools includes the add container tool."""
        tools = self.tools.get_tools()
        
        # Find the add container tool
        add_container_tool = None
        for tool in tools:
            name = getattr(tool, 'name', None)
            if name == 'add_container':
                add_container_tool = tool
                break
        
        assert add_container_tool is not None, "Add container tool should be included in available tools"

    def test_get_tools_includes_remove_container(self):
        """Test that get_tools includes the remove container tool."""
        tools = self.tools.get_tools()
        
        # Find the remove container tool
        remove_container_tool = None
        for tool in tools:
            name = getattr(tool, 'name', None)
            if name == 'remove_container':
                remove_container_tool = tool
                break
        assert remove_container_tool is not None, "Remove container tool should be included in available tools"