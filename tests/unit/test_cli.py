"""
Unit tests for Anvyl CLI module
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, call
from click.testing import CliRunner
import typer
from typer.testing import CliRunner as TyperCliRunner
from anvyl.config import get_settings

from anvyl.cli import app, get_infrastructure, get_project_root

# Get settings for testing
settings = get_settings()

runner = TyperCliRunner()


class TestCLIInfrastructure:
    """Test CLI infrastructure management commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = TyperCliRunner()

    @patch('anvyl.cli.subprocess.run')
    @patch('anvyl.cli.get_project_root')
    def test_start_infrastructure_success(self, mock_get_root, mock_subprocess):
        """Test successful infrastructure startup."""
        mock_get_root.return_value = "/fake/project"
        mock_subprocess.return_value = Mock(returncode=0, stderr="", stdout="")

        result = self.runner.invoke(app, ["up", "--no-build"])

        assert result.exit_code == 0
        assert "Starting Anvyl Infrastructure Stack" in result.stdout
        assert "infrastructure started successfully" in result.stdout

        # Verify docker-compose was called
        mock_subprocess.assert_called()

    @patch('anvyl.cli.subprocess.run')
    @patch('anvyl.cli.get_project_root')
    def test_start_infrastructure_build_failure(self, mock_get_root, mock_subprocess):
        """Test infrastructure startup with build failure."""
        mock_get_root.return_value = "/fake/project"
        mock_subprocess.return_value = Mock(returncode=1, stderr="Build failed", stdout="")

        result = self.runner.invoke(app, ["up", "--build"])

        assert result.exit_code == 1
        assert "Failed to build images" in result.stdout

    @patch('anvyl.cli.subprocess.run')
    @patch('anvyl.cli.get_project_root')
    def test_stop_infrastructure_success(self, mock_get_root, mock_subprocess):
        """Test successful infrastructure shutdown."""
        mock_get_root.return_value = "/fake/project"
        mock_subprocess.return_value = Mock(returncode=0, stderr="", stdout="")

        result = self.runner.invoke(app, ["down"])

        assert result.exit_code == 0
        assert "Stopping Anvyl Infrastructure Stack" in result.stdout
        assert "Infrastructure stack stopped successfully" in result.stdout

    @patch('anvyl.cli.get_infrastructure')
    def test_list_infrastructure_with_containers(self, mock_get_infra):
        """Test listing infrastructure with running containers."""
        mock_service = Mock()
        mock_service.list_containers.return_value = [
            {
                "id": "container123",
                "name": "nginx-server",
                "status": "running",
                "image": "nginx:latest"
            },
            {
                "id": "container456",
                "name": "postgres-db",
                "status": "running",
                "image": "postgres:13"
            }
        ]
        mock_get_infra.return_value = mock_service

        result = self.runner.invoke(app, ["ps"])

        assert result.exit_code == 0
        assert "Anvyl Services" in result.stdout
        assert "nginx-server" in result.stdout
        assert "postgres-db" in result.stdout


class TestCLIHostManagement:
    """Test CLI host management commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = TyperCliRunner()

    @patch('anvyl.cli.get_infrastructure')
    def test_list_hosts_table_format(self, mock_get_infra):
        """Test listing hosts in table format."""
        mock_service = Mock()
        mock_service.list_hosts.return_value = [
            {
                "id": "host123",
                "name": "test-host",
                "ip": "192.168.1.100",
                "os": "Linux",
                "status": "online",
                "tags": ["web-server", "local"]
            }
        ]
        mock_get_infra.return_value = mock_service

        result = self.runner.invoke(app, ["host", "list"])

        assert result.exit_code == 0
        assert "Registered Hosts" in result.stdout
        assert "test-host" in result.stdout
        assert "192.168.1.100" in result.stdout
        assert "online" in result.stdout

    @patch('anvyl.cli.get_infrastructure')
    def test_list_hosts_json_format(self, mock_get_infra):
        """Test listing hosts in JSON format."""
        mock_service = Mock()
        hosts_data = [
            {
                "id": "host123",
                "name": "test-host",
                "ip": "192.168.1.100",
                "os": "Linux",
                "status": "online",
                "tags": ["web-server"]
            }
        ]
        mock_service.list_hosts.return_value = hosts_data
        mock_get_infra.return_value = mock_service

        result = self.runner.invoke(app, ["host", "list", "--output", "json"])

        assert result.exit_code == 0
        # Parse JSON output
        output_data = json.loads(result.stdout.strip())
        assert output_data == hosts_data

    @patch('anvyl.cli.get_infrastructure')
    def test_list_hosts_empty(self, mock_get_infra):
        """Test listing hosts when none exist."""
        mock_service = Mock()
        mock_service.list_hosts.return_value = []
        mock_get_infra.return_value = mock_service

        result = self.runner.invoke(app, ["host", "list"])

        assert result.exit_code == 0
        assert "No hosts found" in result.stdout

    @patch('anvyl.cli.get_infrastructure')
    def test_add_host_success(self, mock_get_infra):
        """Test successfully adding a host."""
        mock_service = Mock()
        mock_service.add_host.return_value = {
            "id": "host123",
            "name": "new-host",
            "ip": "192.168.1.200",
            "os": "Linux",
            "status": "online"
        }
        mock_get_infra.return_value = mock_service

        result = self.runner.invoke(app, [
            "host", "add", "new-host", "192.168.1.200",
            "--os", "Linux", "--tag", "production"
        ])

        assert result.exit_code == 0
        assert "Host added successfully" in result.stdout
        mock_service.add_host.assert_called_once()

    @patch('anvyl.cli.get_infrastructure')
    def test_get_host_metrics_success(self, mock_get_infra):
        """Test getting host metrics."""
        mock_service = Mock()
        mock_service.get_host_metrics.return_value = {
            "cpu_count": 8,
            "memory_total": 16384,
            "memory_available": 8192,
            "disk_total": 500,
            "disk_available": 250
        }
        mock_get_infra.return_value = mock_service

        result = self.runner.invoke(app, ["host", "metrics", "host123"])

        assert result.exit_code == 0
        assert "Host Metrics" in result.stdout
        assert "8" in result.stdout  # CPU count
        assert "16384" in result.stdout  # Memory total


class TestCLIContainerManagement:
    """Test CLI container management commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = TyperCliRunner()

    @patch('anvyl.cli.get_infrastructure')
    def test_list_containers_success(self, mock_get_infra):
        """Test listing containers successfully."""
        mock_service = Mock()
        mock_service.list_containers.return_value = [
            {
                "id": "container123",
                "name": "test-container",
                "image": "nginx:latest",
                "status": "running",
                "host_id": "host123",
                "ports": ["8080:80"],
                "volumes": ["/data:/app/data"],
                "environment": ["ENV=production"]
            }
        ]
        mock_get_infra.return_value = mock_service

        result = self.runner.invoke(app, ["container", "list"])

        assert result.exit_code == 0
        assert "Containers" in result.stdout
        assert "test-container" in result.stdout
        assert "nginx:latest" in result.stdout
        assert "running" in result.stdout

    @patch('anvyl.cli.get_infrastructure')
    def test_add_container_success(self, mock_get_infra):
        """Test adding a container successfully."""
        mock_service = Mock()
        mock_service.add_container.return_value = {
            "id": "new-container-id",
            "name": "new-container",
            "image": "nginx:latest",
            "status": "running"
        }
        mock_get_infra.return_value = mock_service

        result = self.runner.invoke(app, [
            "container", "add", "new-container", "nginx:latest",
            "--port", "8080:80"
        ])

        self.assertEqual(result.exit_code, 0)
        mock_service.add_container.assert_called_once()

    @patch('anvyl.cli.get_infrastructure')
    def test_remove_container_success(self, mock_get_infra):
        """Test removing a container successfully."""
        mock_service = Mock()
        mock_service.remove_container.return_value = True
        mock_get_infra.return_value = mock_service

        result = self.runner.invoke(app, ["container", "remove", "container123"])

        self.assertEqual(result.exit_code, 0)
        mock_service.remove_container.assert_called_once_with("container123", 10)

    @patch('anvyl.cli.get_infrastructure')
    def test_container_logs_success(self, mock_get_infra):
        """Test getting container logs successfully."""
        mock_service = Mock()
        mock_service.get_logs.return_value = "Container log output\nMore log lines"
        mock_get_infra.return_value = mock_service

        result = self.runner.invoke(app, ["container", "logs", "container123"])

        assert result.exit_code == 0
        assert "Container log output" in result.stdout
        mock_service.get_logs.assert_called_once()

    @patch('anvyl.cli.get_infrastructure')
    def test_container_exec_success(self, mock_get_infra):
        """Test executing command in container successfully."""
        mock_service = Mock()
        mock_service.exec_command.return_value = {
            "output": "Command output",
            "exit_code": 0,
            "success": True
        }
        mock_get_infra.return_value = mock_service

        result = self.runner.invoke(app, ["container", "exec", "container123", "ls", "-la"])

        assert result.exit_code == 0
        assert "Command output" in result.stdout
        mock_service.exec_command.assert_called_once()


class TestCLIAgentManagement:
    """Test CLI AI agent management commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = TyperCliRunner()

    @patch('anvyl.cli.get_service_manager')
    def test_agent_up_success(self, mock_get_service_manager):
        """Test starting agent successfully."""
        mock_service_manager = Mock()
        mock_service_manager.start_agent.return_value = True
        mock_get_service_manager.return_value = mock_service_manager

        result = self.runner.invoke(app, [
            "agent", "up",
            "--model-provider-url", "http://localhost:11434/v1",
            "--port", "4201"
        ])

        assert result.exit_code == 0
        assert "Agent started successfully" in result.stdout

    @patch('anvyl.cli.get_service_manager')
    def test_agent_down_success(self, mock_get_service_manager):
        """Test stopping agent successfully."""
        mock_service_manager = Mock()
        mock_service_manager.stop_agent.return_value = True
        mock_get_service_manager.return_value = mock_service_manager

        result = self.runner.invoke(app, ["agent", "down"])

        assert result.exit_code == 0
        assert "Agent stopped successfully" in result.stdout

    @patch('anvyl.cli.requests.get')
    def test_agent_query_success(self, mock_requests_get):
        """Test querying agent successfully."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "I found 3 containers running on this host."
        }
        mock_requests_get.return_value = mock_response

        result = self.runner.invoke(app, [
            "agent", "query", "List all containers",
            "--port", "4201"
        ])

        assert result.exit_code == 0
        assert "I found 3 containers" in result.stdout

    @patch('anvyl.cli.requests.get')
    def test_agent_info_success(self, mock_requests_get):
        """Test getting agent info successfully."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "host_id": "host123",
            "host_ip": "127.0.0.1",
            "llm_model": "llama3.2:latest",
            "tools_available": ["list_containers", "get_host_info"],
            "known_hosts": {"host456": "192.168.1.100"}
        }
        mock_requests_get.return_value = mock_response

        result = self.runner.invoke(app, ["agent", "info"])

        assert result.exit_code == 0
        assert "Agent Information" in result.stdout
        assert "host123" in result.stdout
        assert "llama3.2:latest" in result.stdout


class TestCLIUtilityCommands:
    """Test CLI utility commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = TyperCliRunner()

    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "Anvyl Infrastructure Orchestrator" in result.stdout
        assert "Version:" in result.stdout

    @patch('anvyl.cli.get_infrastructure')
    @patch('anvyl.cli.requests.get')
    def test_status_command_success(self, mock_requests, mock_get_infra):
        """Test status command with all services healthy."""
        # Mock infrastructure service
        mock_service = Mock()
        mock_service.list_hosts.return_value = [{"id": "host1", "status": "online"}]
        mock_service.list_containers.return_value = [{"id": "cont1", "status": "running"}]
        mock_get_infra.return_value = mock_service

        # Mock API health check
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_requests.return_value = mock_response

        result = self.runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "System Status" in result.stdout
        assert "healthy" in result.stdout.lower()

    @patch('anvyl.cli.Confirm.ask')
    def test_purge_data_with_confirmation(self, mock_confirm):
        """Test purge data command with user confirmation."""
        mock_confirm.return_value = True

        with patch('anvyl.cli.DatabaseManager') as mock_db_manager:
            mock_db = Mock()
            mock_db_manager.return_value = mock_db

            result = self.runner.invoke(app, ["purge"])

            assert result.exit_code == 0
            assert "Data purged successfully" in result.stdout

    def test_purge_data_force_flag(self):
        """Test purge data command with force flag."""
        with patch('anvyl.cli.DatabaseManager') as mock_db_manager:
            mock_db = Mock()
            mock_db_manager.return_value = mock_db

            result = self.runner.invoke(app, ["purge", "--force"])

            assert result.exit_code == 0
            assert "Data purged successfully" in result.stdout


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = TyperCliRunner()

    @patch('anvyl.cli.get_infrastructure')
    def test_infrastructure_service_error(self, mock_get_infra):
        """Test handling of infrastructure service errors."""
        mock_get_infra.side_effect = Exception("Service unavailable")

        result = self.runner.invoke(app, ["host", "list"])

        assert result.exit_code == 1
        assert "Error initializing infrastructure service" in result.stdout

    @patch('anvyl.cli.get_infrastructure')
    def test_container_operation_error(self, mock_get_infra):
        """Test handling of container operation errors."""
        mock_service = Mock()
        mock_service.list_containers.side_effect = Exception("Docker unavailable")
        mock_get_infra.return_value = mock_service

        result = self.runner.invoke(app, ["container", "list"])

        assert result.exit_code == 1
        assert "Error listing containers" in result.stdout

    @patch('anvyl.cli.requests.get')
    def test_agent_connection_error(self, mock_requests):
        """Test handling of agent connection errors."""
        mock_requests.side_effect = Exception("Connection refused")

        result = self.runner.invoke(app, ["agent", "query", "test query"])

        assert result.exit_code == 1
        assert "Error querying agent" in result.stdout


class TestCLIProjectRoot:
    """Test project root detection."""

    def test_get_project_root_found(self):
        """Test project root detection when files are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the required files
            os.makedirs(os.path.join(temp_dir, "anvyl"))

            with open(os.path.join(temp_dir, "pyproject.toml"), "w") as f:
                f.write("[project]\nname = 'anvyl'")

            # Change to a subdirectory
            subdir = os.path.join(temp_dir, "subdir")
            os.makedirs(subdir)

            with patch('os.getcwd', return_value=subdir):
                root = get_project_root()
                assert root == temp_dir

    def test_get_project_root_not_found(self):
        """Test project root detection when files are not found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('os.getcwd', return_value=temp_dir):
                root = get_project_root()
                assert root == temp_dir  # Should return current directory


class TestCLI:
    """Test cases for the CLI commands."""

    def test_start_all_services(self):
        """Test starting all services."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.start_all_services.return_value = True
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["start"])

            assert result.exit_code == 0
            mock_manager.start_all_services.assert_called_once()

    def test_stop_infrastructure(self):
        """Test stopping infrastructure."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.stop_all_services.return_value = True
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["down"])

            assert result.exit_code == 0
            mock_manager.stop_all_services.assert_called_once()

    def test_show_status(self):
        """Test showing status."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["status"])

            assert result.exit_code == 0

    def test_purge_data(self):
        """Test purging data."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["purge", "--force"])

            assert result.exit_code == 0

    def test_restart_all_services(self):
        """Test restarting all services."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.restart_all_services.return_value = True
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["restart"])

            assert result.exit_code == 0
            mock_manager.restart_all_services.assert_called_once()

    def test_infrastructure_up(self):
        """Test starting infrastructure API."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.start_infrastructure_api.return_value = True
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["infra", "up"])

            assert result.exit_code == 0
            mock_manager.start_infrastructure_api.assert_called_once()

    def test_infrastructure_down(self):
        """Test stopping infrastructure API."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.stop_infrastructure_api.return_value = True
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["infra", "down"])

            assert result.exit_code == 0
            mock_manager.stop_infrastructure_api.assert_called_once()

    def test_infrastructure_status(self):
        """Test infrastructure status."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["infra", "status"])

            assert result.exit_code == 0

    def test_infrastructure_logs(self):
        """Test infrastructure logs."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_service_logs.return_value = "Test logs"
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["infra", "logs"])

            assert result.exit_code == 0

    def test_infrastructure_restart(self):
        """Test restarting infrastructure API."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.restart_service.return_value = True
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["infra", "restart"])

            assert result.exit_code == 0
            mock_manager.restart_service.assert_called_once()

    def test_agent_up(self):
        """Test starting agent."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.start_agent_service.return_value = True
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["agent", "up"])

            assert result.exit_code == 0
            mock_manager.start_agent_service.assert_called_once()

    def test_agent_down(self):
        """Test stopping agent."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.stop_agent_service.return_value = True
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["agent", "down"])

            assert result.exit_code == 0
            mock_manager.stop_agent_service.assert_called_once()

    def test_agent_logs(self):
        """Test agent logs."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_service_logs.return_value = "Test logs"
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["agent", "logs"])

            assert result.exit_code == 0

    def test_agent_restart(self):
        """Test restarting agent."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.restart_service.return_value = True
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["agent", "restart"])

            assert result.exit_code == 0
            mock_manager.restart_service.assert_called_once()

    def test_agent_info(self):
        """Test agent info."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"host_id": "test-host"}
            mock_get.return_value = mock_response

            result = runner.invoke(app, ["agent", "info"])

            assert result.exit_code == 0

    def test_agent_query(self):
        """Test agent query."""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Test response"}
            mock_post.return_value = mock_response

            result = runner.invoke(app, ["agent", "query", "test query"])

            assert result.exit_code == 0

    def test_agent_hosts(self):
        """Test agent hosts."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"hosts": {"test-host": "127.0.0.1"}}
            mock_get.return_value = mock_response

            result = runner.invoke(app, ["agent", "hosts"])

            assert result.exit_code == 0

    def test_agent_add_host(self):
        """Test adding agent host."""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"message": "Host added"}
            mock_post.return_value = mock_response

            result = runner.invoke(app, ["agent", "add-host", "test-host", "127.0.0.1"])

            assert result.exit_code == 0

    def test_mcp_up(self):
        """Test starting MCP server."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.start_mcp_server.return_value = True
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["mcp", "up"])

            assert result.exit_code == 0
            mock_manager.start_mcp_server.assert_called_once()

    def test_mcp_down(self):
        """Test stopping MCP server."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.stop_mcp_server.return_value = True
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["mcp", "down"])

            assert result.exit_code == 0
            mock_manager.stop_mcp_server.assert_called_once()

    def test_mcp_logs(self):
        """Test MCP logs."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_service_logs.return_value = "Test logs"
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["mcp", "logs"])

            assert result.exit_code == 0

    def test_mcp_restart(self):
        """Test restarting MCP server."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.restart_service.return_value = True
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["mcp", "restart"])

            assert result.exit_code == 0
            mock_manager.restart_service.assert_called_once()

    def test_mcp_status(self):
        """Test MCP status."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, ["mcp", "status"])

            assert result.exit_code == 0

    def test_agent_query_with_custom_port(self):
        """Test agent query with custom port."""
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Test response"}
            mock_post.return_value = mock_response

            result = runner.invoke(app, [
                "agent", "query", "test query",
                "--port", str(settings.agent_port)
            ])

            assert result.exit_code == 0

    def test_agent_up_with_custom_settings(self):
        """Test agent up with custom settings."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.start_agent_service.return_value = True
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, [
                "agent", "up",
                "--model-provider-url", settings.model_provider_url,
                "--port", str(settings.agent_port)
            ])

            assert result.exit_code == 0
            mock_manager.start_agent_service.assert_called_once()

    def test_infrastructure_up_with_custom_settings(self):
        """Test infrastructure up with custom settings."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.start_infrastructure_api.return_value = True
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, [
                "infra", "up",
                "--host", settings.infra_host,
                "--port", str(settings.infra_port)
            ])

            assert result.exit_code == 0
            mock_manager.start_infrastructure_api.assert_called_once()

    def test_mcp_up_with_custom_settings(self):
        """Test MCP up with custom settings."""
        with patch('anvyl.cli.get_service_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.start_mcp_server.return_value = True
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(app, [
                "mcp", "up",
                "--host", settings.infra_host,
                "--port", str(settings.mcp_port)
            ])

            assert result.exit_code == 0
            mock_manager.start_mcp_server.assert_called_once()