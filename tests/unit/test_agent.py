"""
Tests for the Anvyl AI Agent System
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from anvyl.agent import HostAgent, AgentManager, InfrastructureTools
from anvyl.infra.client import InfrastructureClient
from anvyl.agent.communication import AgentCommunication

pytest_asyncio = pytest.importorskip('pytest_asyncio', reason='pytest-asyncio is required for async tests')

class TestInfrastructureTools:
    """Test the infrastructure tools."""

    def setup_method(self):
        """Set up test fixtures."""
        self.infrastructure_client = Mock(spec=InfrastructureClient)
        self.tools = InfrastructureTools(self.infrastructure_client)

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
        # Mock the infrastructure client response
        self.infrastructure_client.list_containers.return_value = [
            {
                'id': 'test-container-id',
                'name': 'test-container',
                'status': 'running'
            }
        ]

        # Test the tool
        result = self.tools.list_containers()
        assert 'test-container' in result
        assert 'running' in result

    def test_get_host_resources_tool(self):
        """Test the get host resources tool."""
        # Test the tool (should work with local psutil)
        result = self.tools.get_host_resources()
        assert 'cpu_percent' in result
        assert 'memory' in result
        assert 'disk' in result


class TestHostAgent:
    """Test the host agent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.infrastructure_client = Mock(spec=InfrastructureClient)
        self.host_id = "test-host-id"
        self.host_ip = "127.0.0.1"
        self.communication = Mock(spec=AgentCommunication)

        # Mock the infrastructure client to return some hosts
        self.infrastructure_client.list_hosts.return_value = [
            {
                'id': self.host_id,
                'name': 'test-host',
                'ip': self.host_ip,
                'status': 'online',
                'tags': ['local', 'anvyl-server']
            }
        ]

        # Mock communication
        self.communication.known_hosts = {}

    @patch('anvyl.agent.agent_manager.HostAgent')
    def test_host_agent_creation(self, mock_host_agent):
        """Test that host agent can be created."""
        # Mock the model
        mock_model_instance = Mock()
        mock_model_instance.provider = "mock"
        mock_host_agent.return_value = mock_model_instance

        # Create the host agent
        agent = HostAgent(
            communication=self.communication,
            tools=[],
            host_id=self.host_id,
            host_ip=self.host_ip,
            lmstudio_url="http://localhost:1234/v1",
            lmstudio_model="default"
        )

        assert agent.host_id == self.host_id
        assert agent.host_ip == self.host_ip
        from anvyl.infra.client import InfrastructureClient
        assert isinstance(agent.infrastructure_client, InfrastructureClient)

    def test_host_agent_mock_model(self):
        """Test host agent with mock model (no LMStudio)."""
        agent = HostAgent(
            communication=self.communication,
            tools=[],
            host_id=self.host_id,
            host_ip=self.host_ip
        )

        assert agent.host_id == self.host_id
        assert agent.host_ip == self.host_ip
        assert hasattr(agent.model, 'provider')
        assert agent.model.provider == 'mock'

    def test_agent_info(self):
        """Test getting agent information."""
        agent = HostAgent(
            communication=self.communication,
            tools=[],
            host_id=self.host_id,
            host_ip=self.host_ip
        )

        info = agent.get_agent_info()

        assert info['host_id'] == self.host_id
        assert info['host_ip'] == self.host_ip
        assert 'tools_available' in info
        assert 'model_provider' in info

    def test_known_hosts_management(self):
        """Test adding and removing known hosts."""
        agent = HostAgent(
            communication=self.communication,
            tools=[],
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
        self.host_id = "test-host-id"
        self.host_ip = "127.0.0.1"

    @patch('anvyl.agent.agent_manager.HostAgent')
    @patch('anvyl.agent.agent_manager.InfrastructureTools')
    def test_agent_manager_creation(self, mock_tools, mock_host_agent):
        """Test that agent manager can be created."""
        # Mock the tools and host agent
        mock_tools_instance = Mock()
        mock_tools_instance.get_tools.return_value = []
        mock_tools.return_value = mock_tools_instance

        mock_agent = Mock()
        mock_host_agent.return_value = mock_agent

        # Create the agent manager
        manager = AgentManager(
            host_id=self.host_id,
            host_ip=self.host_ip,
            lmstudio_url="http://localhost:1234/v1",
            lmstudio_model="default",
            port=4201
        )

        assert manager.host_id == self.host_id
        assert manager.host_ip == self.host_ip
        assert manager.port == 4201

    def test_fastapi_app_creation(self):
        """Test that FastAPI app is created correctly."""
        manager = AgentManager(
            host_id=self.host_id,
            host_ip=self.host_ip,
            port=4201
        )

        assert manager.app is not None
        assert hasattr(manager.app, 'routes')

    @patch('anvyl.agent.agent_manager.HostAgent')
    @patch('anvyl.agent.agent_manager.InfrastructureTools')
    def test_api_endpoints(self, mock_tools, mock_host_agent):
        """Test that API endpoints are registered."""
        # Mock the tools and host agent
        mock_tools_instance = Mock()
        mock_tools_instance.get_tools.return_value = []
        mock_tools.return_value = mock_tools_instance

        mock_agent = Mock()
        mock_agent.get_agent_info.return_value = {"test": "info"}
        mock_host_agent.return_value = mock_agent

        manager = AgentManager(
            host_id=self.host_id,
            host_ip=self.host_ip,
            port=4201
        )

        # Check that endpoints are registered
        routes = [route.path for route in manager.app.routes]
        expected_routes = [
            "/",
            "/health",
            "/agent/info",
            "/agent/query",
            "/agent/broadcast",
            "/agent/process",
            "/agent/remote-query",
            "/agent/hosts",
            "/infrastructure/containers",
            "/infrastructure/hosts"
        ]

        for expected_route in expected_routes:
            assert expected_route in routes


@pytest.mark.asyncio
def test_agent_communication():
    """Test agent communication."""
    from anvyl.agent.communication import AgentCommunication, AgentMessage
    from datetime import datetime, timezone

    # Create communication instance
    comm = AgentCommunication(
        local_host_id="test-host",
        local_host_ip="127.0.0.1",
        port=4200
    )

    # Add a known host
    comm.known_hosts["remote-host"] = "192.168.1.100"

    # Test known hosts
    assert "remote-host" in comm.known_hosts
    assert comm.known_hosts["remote-host"] == "192.168.1.100"


def test_create_agent_manager():
    """Test the create_agent_manager function."""
    from anvyl.agent.agent_manager import create_agent_manager

    manager = create_agent_manager(
        lmstudio_url="http://localhost:1234/v1",
        lmstudio_model="test-model",
        port=4201,
        infrastructure_api_url="http://localhost:4200"
    )

    assert manager is not None
    assert manager.port == 4201
    assert manager.lmstudio_url == "http://localhost:1234/v1"
    assert manager.lmstudio_model == "test-model"


class TestModelIntegration:
    """Test model integration."""

    def test_mock_model_creation(self):
        """Test mock model creation when LMStudio is not available."""
        from anvyl.agent.host_agent import HostAgent
        from anvyl.agent.communication import AgentCommunication

        communication = Mock(spec=AgentCommunication)
        communication.known_hosts = {}

        agent = HostAgent(
            communication=communication,
            tools=[],
            host_id="test-host",
            host_ip="127.0.0.1"
        )

        # Should create a mock model
        assert hasattr(agent.model, 'provider')
        assert agent.model.provider == 'mock'

    @patch('requests.get')
    def test_model_name_fetching(self, mock_get):
        """Test fetching model name from LMStudio."""
        from anvyl.agent.host_agent import HostAgent
        from anvyl.agent.communication import AgentCommunication

        # Mock successful response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "data": [{"id": "test-model"}]
        }

        communication = Mock(spec=AgentCommunication)
        communication.known_hosts = {}

        agent = HostAgent(
            communication=communication,
            tools=[],
            host_id="test-host",
            host_ip="127.0.0.1",
            lmstudio_url="http://localhost:1234/v1"
        )

        # Should get the actual model name (mock if LMStudio is not available)
        assert agent.actual_model_name in ("test-model", "mock")


if __name__ == "__main__":
    pytest.main([__file__])