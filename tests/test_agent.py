"""
Tests for the Anvyl AI Agent System
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from anvyl.agent import HostAgent, AgentManager, InfrastructureTools
from anvyl.infrastructure_service import InfrastructureService
from anvyl.database.models import DatabaseManager


class TestInfrastructureTools:
    """Test the infrastructure tools."""

    def setup_method(self):
        """Set up test fixtures."""
        self.infrastructure_service = Mock(spec=InfrastructureService)
        self.tools = InfrastructureTools(self.infrastructure_service)

    def test_tools_creation(self):
        """Test that tools are created correctly."""
        tools = self.tools.get_tools()
        assert len(tools) > 0

        # Check that we have the expected tools
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            'list_containers',
            'get_container_info',
            'start_container',
            'stop_container',
            'create_container',
            'get_host_info',
            'get_host_resources',
            'list_hosts',
            'execute_command'
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    def test_list_containers_tool(self):
        """Test the list containers tool."""
        # Mock the infrastructure service response
        self.infrastructure_service.list_containers.return_value = [
            {
                'id': 'test-container-id',
                'name': 'test-container',
                'status': 'running'
            }
        ]

        # Get the list containers tool
        list_tool = None
        for tool in self.tools.get_tools():
            if tool.name == 'list_containers':
                list_tool = tool
                break

        assert list_tool is not None

        # Test the tool
        result = list_tool._run()
        assert 'test-container' in result
        assert 'running' in result


class TestHostAgent:
    """Test the host agent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.infrastructure_service = Mock(spec=InfrastructureService)
        self.host_id = "test-host-id"
        self.host_ip = "127.0.0.1"

        # Mock the infrastructure service to return some hosts
        self.infrastructure_service.list_hosts.return_value = [
            {
                'id': self.host_id,
                'name': 'test-host',
                'ip': self.host_ip,
                'status': 'online',
                'tags': ['local', 'anvyl-server']
            }
        ]

    @patch('anvyl.agent.host_agent.LMStudioLLM')
    def test_host_agent_creation(self, mock_lmstudio):
        """Test that host agent can be created."""
        # Mock the LMStudio client
        mock_llm = Mock()
        mock_lmstudio.return_value = mock_llm

        # Create the host agent
        agent = HostAgent(
            infrastructure_service=self.infrastructure_service,
            host_id=self.host_id,
            host_ip=self.host_ip,
            lmstudio_url="http://localhost:1234/v1",
            lmstudio_model="default"
        )

        assert agent.host_id == self.host_id
        assert agent.host_ip == self.host_ip
        assert agent.infrastructure_service == self.infrastructure_service
        assert len(agent.tools) > 0

    def test_host_agent_mock_llm(self):
        """Test host agent with mock LLM (no LMStudio)."""
        agent = HostAgent(
            infrastructure_service=self.infrastructure_service,
            host_id=self.host_id,
            host_ip=self.host_ip
        )

        assert agent.host_id == self.host_id
        assert agent.host_ip == self.host_ip
        assert hasattr(agent.llm, '_llm_type')
        assert agent.llm._llm_type == 'mock'

    def test_agent_info(self):
        """Test getting agent information."""
        agent = HostAgent(
            infrastructure_service=self.infrastructure_service,
            host_id=self.host_id,
            host_ip=self.host_ip
        )

        info = agent.get_agent_info()

        assert info['host_id'] == self.host_id
        assert info['host_ip'] == self.host_ip
        assert 'tools_available' in info
        assert 'llm_model' in info

    def test_known_hosts_management(self):
        """Test adding and removing known hosts."""
        agent = HostAgent(
            infrastructure_service=self.infrastructure_service,
            host_id=self.host_id,
            host_ip=self.host_ip
        )

        # Initially no known hosts
        assert len(agent.get_known_hosts()) == 0

        # Add a host
        agent.add_known_host("remote-host-id", "192.168.1.100")
        known_hosts = agent.get_known_hosts()
        assert "remote-host-id" in known_hosts
        assert known_hosts["remote-host-id"] == "192.168.1.100"

        # Remove the host
        agent.remove_known_host("remote-host-id")
        assert len(agent.get_known_hosts()) == 0


class TestAgentManager:
    """Test the agent manager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.infrastructure_service = Mock(spec=InfrastructureService)
        self.host_id = "test-host-id"
        self.host_ip = "127.0.0.1"

        # Mock the infrastructure service to return some hosts
        self.infrastructure_service.list_hosts.return_value = [
            {
                'id': self.host_id,
                'name': 'test-host',
                'ip': self.host_ip,
                'status': 'online',
                'tags': ['local', 'anvyl-server']
            }
        ]

    @patch('anvyl.agent.agent_manager.HostAgent')
    def test_agent_manager_creation(self, mock_host_agent):
        """Test that agent manager can be created."""
        # Mock the host agent
        mock_agent = Mock()
        mock_host_agent.return_value = mock_agent

        # Create the agent manager
        manager = AgentManager(
            infrastructure_service=self.infrastructure_service,
            host_id=self.host_id,
            host_ip=self.host_ip,
            lmstudio_url="http://localhost:1234/v1",
            lmstudio_model="default",
            port=8080
        )

        assert manager.host_id == self.host_id
        assert manager.host_ip == self.host_ip
        assert manager.port == 8080
        assert manager.infrastructure_service == self.infrastructure_service

    def test_fastapi_app_creation(self):
        """Test that FastAPI app is created correctly."""
        with patch('anvyl.agent.agent_manager.HostAgent'):
            manager = AgentManager(
                infrastructure_service=self.infrastructure_service,
                host_id=self.host_id,
                host_ip=self.host_ip,
                port=8080
            )

            assert manager.app is not None
            assert hasattr(manager.app, 'routes')

    @patch('anvyl.agent.agent_manager.HostAgent')
    def test_api_endpoints(self, mock_host_agent):
        """Test that API endpoints are registered."""
        # Mock the host agent
        mock_agent = Mock()
        mock_host_agent.return_value = mock_agent

        manager = AgentManager(
            infrastructure_service=self.infrastructure_service,
            host_id=self.host_id,
            host_ip=self.host_ip,
            port=8080
        )

        # Check that we have the expected routes
        route_paths = [route.path for route in manager.app.routes]

        expected_paths = [
            '/',
            '/agent/info',
            '/agent/query',
            '/agent/broadcast',
            '/agent/process',
            '/agent/remote-query',
            '/agent/hosts',
            '/infrastructure/containers',
            '/infrastructure/hosts'
        ]

        for expected_path in expected_paths:
            assert expected_path in route_paths


@pytest.mark.asyncio
async def test_agent_communication():
    """Test agent communication functionality."""
    from anvyl.agent.communication import AgentCommunication, AgentMessage

    # Create communication instance
    comm = AgentCommunication("host-a", "192.168.1.100", 8080)

    # Test adding known hosts
    comm.add_known_host("host-b", "192.168.1.101")
    known_hosts = comm.get_known_hosts()
    assert "host-b" in known_hosts
    assert known_hosts["host-b"] == "192.168.1.101"

    # Test message creation
    message = AgentMessage(
        sender_id="host-a",
        sender_host="192.168.1.100",
        message_type="query",
        content={"query": "test query"}
    )

    assert message.sender_id == "host-a"
    assert message.message_type == "query"
    assert message.content["query"] == "test query"
    assert message.timestamp is not None


def test_create_agent_manager():
    """Test the create_agent_manager helper function."""
    with patch('anvyl.agent.agent_manager.InfrastructureService') as mock_service:
        # Mock the infrastructure service
        mock_infrastructure = Mock()
        mock_service.return_value = mock_infrastructure

        # Mock the list_hosts method
        mock_infrastructure.list_hosts.return_value = [
            {
                'id': 'test-host-id',
                'name': 'test-host',
                'ip': '127.0.0.1',
                'status': 'online',
                'tags': ['local', 'anvyl-server']
            }
        ]

        with patch('anvyl.agent.agent_manager.AgentManager') as mock_manager:
            # Mock the agent manager
            mock_agent_manager = Mock()
            mock_manager.return_value = mock_agent_manager

            # Test the function
            from anvyl.agent.agent_manager import create_agent_manager
            result = create_agent_manager(lmstudio_url="http://localhost:1234/v1", lmstudio_model="default", port=8080)

            assert result == mock_agent_manager
            mock_manager.assert_called_once()


class TestLMStudioLLM:
    """Test the LMStudio LLM class."""

    @patch('requests.post')
    def test_lmstudio_llm_call(self, mock_post):
        """Test LMStudio LLM API call."""
        from anvyl.agent.host_agent import LMStudioLLM

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello from LMStudio"}}]
        }
        mock_post.return_value = mock_response

        # Create LLM instance
        llm = LMStudioLLM(base_url="http://localhost:1234/v1", model="default")

        # Test the call
        result = llm._call("Hello")
        assert result == "Hello from LMStudio"

        # Verify the API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:1234/v1/chat/completions"

        # Verify the request payload
        payload = call_args[1]['json']
        assert payload['model'] == 'default'
        assert payload['messages'][0]['content'] == 'Hello'

    @patch('requests.post')
    def test_lmstudio_llm_error(self, mock_post):
        """Test LMStudio LLM error handling."""
        from anvyl.agent.host_agent import LMStudioLLM

        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        # Create LLM instance
        llm = LMStudioLLM(base_url="http://localhost:1234/v1", model="default")

        # Test the call
        result = llm._call("Hello")
        assert "trouble connecting" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__])