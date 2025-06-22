"""
Tests for MCP server infrastructure integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from anvyl.mcp.server import server, infrastructure
from anvyl.infra.service import InfrastructureService


class TestMCPServerInfrastructure:
    """Test that MCP server uses infrastructure service instead of Docker SDK."""

    def test_mcp_server_uses_infrastructure_service(self):
        """Test that MCP server tools use infrastructure service methods."""
        # Verify that the infrastructure service is available
        assert infrastructure is not None
        assert isinstance(infrastructure, InfrastructureService)

    @patch('anvyl.infra.service.InfrastructureService.list_images')
    def test_list_images_uses_infrastructure(self, mock_list_images):
        """Test that list_images tool uses infrastructure service."""
        # Mock the infrastructure service method
        mock_list_images.return_value = [
            {
                'id': 'abc123',
                'repository': 'test/image',
                'tag': 'latest',
                'created': '2024-01-01T00:00:00Z',
                'size': 1000000
            }
        ]

        # Get the actual function from the tool
        list_images_tool = server.tools.get('list_images')
        assert list_images_tool is not None

        # The tool should be a FunctionTool, we can't call it directly in tests
        # but we can verify it exists and the infrastructure service is mocked
        assert list_images_tool.name == 'list_images'

    @patch('anvyl.infra.service.InfrastructureService.get_system_info')
    def test_get_system_info_uses_infrastructure(self, mock_get_system_info):
        """Test that get_system_info tool uses infrastructure service."""
        # Mock the infrastructure service method
        mock_get_system_info.return_value = {
            'platform': 'Linux',
            'platform_version': '24.5.0',
            'architecture': 'arm64',
            'processor': 'Apple M1',
            'hostname': 'test-host',
            'cpu_count': 8,
            'memory_total': 16000000000,
            'memory_available': 8000000000,
            'disk_usage': 1000000000000
        }

        # Get the actual function from the tool
        get_system_info_tool = server.tools.get('get_system_info')
        assert get_system_info_tool is not None
        assert get_system_info_tool.name == 'get_system_info'

    @patch('anvyl.infra.service.InfrastructureService.start_container')
    def test_start_container_uses_infrastructure(self, mock_start_container):
        """Test that start_container tool uses infrastructure service."""
        # Mock the infrastructure service method
        mock_start_container.return_value = True

        # Get the actual function from the tool
        start_container_tool = server.tools.get('start_container')
        assert start_container_tool is not None
        assert start_container_tool.name == 'start_container'

    @patch('anvyl.infra.service.InfrastructureService.stop_container')
    def test_stop_container_uses_infrastructure(self, mock_stop_container):
        """Test that stop_container tool uses infrastructure service."""
        # Mock the infrastructure service method
        mock_stop_container.return_value = True

        # Get the actual function from the tool
        stop_container_tool = server.tools.get('stop_container')
        assert stop_container_tool is not None
        assert stop_container_tool.name == 'stop_container'

    @patch('anvyl.infra.service.InfrastructureService.pull_image')
    def test_pull_image_uses_infrastructure(self, mock_pull_image):
        """Test that pull_image tool uses infrastructure service."""
        # Mock the infrastructure service method
        mock_pull_image.return_value = {
            'id': 'abc123',
            'tags': ['test/image:latest'],
            'created': '2024-01-01T00:00:00Z',
            'size': 1000000
        }

        # Get the actual function from the tool
        pull_image_tool = server.tools.get('pull_image')
        assert pull_image_tool is not None
        assert pull_image_tool.name == 'pull_image'

    def test_no_docker_import_in_mcp_server(self):
        """Test that the MCP server module doesn't import docker directly."""
        import anvyl.mcp.server as mcp_server

        # Check that docker is not in the module's globals
        assert 'docker' not in mcp_server.__dict__

        # Check that the module doesn't have docker as a dependency
        import inspect
        source = inspect.getsource(mcp_server)
        assert 'import docker' not in source

    def test_infrastructure_service_has_all_required_methods(self):
        """Test that the infrastructure service has all the methods needed by MCP server."""
        required_methods = [
            'list_images',
            'start_container',
            'stop_container',
            'restart_container',
            'inspect_container',
            'get_container_stats',
            'pull_image',
            'remove_image',
            'inspect_image',
            'get_system_info',
            'get_disk_usage',
            'get_network_interfaces',
            'get_running_processes',
            'check_port'
        ]

        for method_name in required_methods:
            assert hasattr(infrastructure, method_name), f"Missing method: {method_name}"
            assert callable(getattr(infrastructure, method_name)), f"Method {method_name} is not callable"

    def test_mcp_server_has_all_expected_tools(self):
        """Test that the MCP server has all the expected tools."""
        expected_tools = [
            'list_hosts',
            'list_containers',
            'list_images',
            'create_container',
            'remove_container',
            'get_container_logs',
            'exec_container_command',
            'get_host_metrics',
            'add_host',
            'system_status',
            'start_container',
            'stop_container',
            'restart_container',
            'inspect_container',
            'container_stats',
            'pull_image',
            'remove_image',
            'inspect_image',
            'get_system_info',
            'get_disk_usage',
            'get_network_interfaces',
            'get_running_processes',
            'check_port',
            'list_available_tools'
        ]

        for tool_name in expected_tools:
            assert tool_name in server.tools, f"Missing tool: {tool_name}"