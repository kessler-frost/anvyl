"""
Integration tests for Anvyl CLI
"""

import pytest
import tempfile
import os
import json
import subprocess
import time
import asyncio
from pathlib import Path
from unittest.mock import patch

from anvyl.database.models import DatabaseManager, Host, Container


@pytest.fixture
def temp_database():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        db_path = temp_file.name
    
    try:
        db_manager = DatabaseManager(f"sqlite:///{db_path}")
        yield db_manager
    finally:
        try:
            os.unlink(db_path)
        except:
            pass


@pytest.fixture
def mock_project_root():
    """Create a mock project root directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create required directories and files
        for subdir in ["anvyl", "ui"]:
            os.makedirs(os.path.join(temp_dir, subdir))
        
        # Create pyproject.toml
        with open(os.path.join(temp_dir, "pyproject.toml"), "w") as f:
            f.write("[project]\nname = 'anvyl'\n")
        
        # Create docker-compose.yml in ui directory
        docker_compose_content = """
version: '3.8'
services:
  frontend:
    image: anvyl/frontend:latest
    ports:
      - "3000:3000"
  backend:
    image: anvyl/backend:latest
    ports:
      - "8000:8000"
"""
        ui_dir = os.path.join(temp_dir, "ui")
        with open(os.path.join(ui_dir, "docker-compose.yml"), "w") as f:
            f.write(docker_compose_content)
        
        yield temp_dir


class TestCLIInfrastructureIntegration:
    """Integration tests for CLI infrastructure commands."""

    @patch('anvyl.cli.subprocess.run')
    @patch('anvyl.cli.get_project_root')
    def test_up_down_workflow(self, mock_get_root, mock_subprocess, mock_project_root):
        """Test complete up/down workflow."""
        mock_get_root.return_value = mock_project_root
        
        # Mock successful subprocess calls
        mock_subprocess.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        
        from anvyl.cli import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        # Test up command
        result = runner.invoke(app, ["up", "--no-build"])
        assert result.exit_code == 0
        assert "infrastructure started successfully" in result.stdout
        
        # Test down command  
        result = runner.invoke(app, ["down"])
        assert result.exit_code == 0
        assert "Infrastructure stack stopped successfully" in result.stdout


class TestCLIHostIntegration:
    """Integration tests for CLI host management."""

    def test_host_lifecycle(self, temp_database):
        """Test complete host lifecycle: add, list, update, metrics."""
        from anvyl.cli import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        with patch('anvyl.cli.get_infrastructure') as mock_get_infra:
            # Setup mock infrastructure service
            mock_service = MockInfrastructureService(temp_database)
            mock_get_infra.return_value = mock_service
            
            # Test adding a host
            result = runner.invoke(app, [
                "host", "add", "test-host", "192.168.1.100",
                "--os", "Linux", "--tag", "production"
            ])
            assert result.exit_code == 0
            assert "Host added successfully" in result.stdout
            
            # Test listing hosts
            result = runner.invoke(app, ["host", "list"])
            assert result.exit_code == 0
            assert "test-host" in result.stdout
            assert "192.168.1.100" in result.stdout
            
            # Test JSON output
            result = runner.invoke(app, ["host", "list", "--output", "json"])
            assert result.exit_code == 0
            hosts_data = json.loads(result.stdout.strip())
            assert len(hosts_data) >= 1
            assert any(h["name"] == "test-host" for h in hosts_data)


class TestCLIContainerIntegration:
    """Integration tests for CLI container management."""

    def test_container_lifecycle(self, temp_database):
        """Test complete container lifecycle: create, list, stop, logs."""
        from anvyl.cli import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        with patch('anvyl.cli.get_infrastructure') as mock_get_infra:
            # Setup mock infrastructure service
            mock_service = MockInfrastructureService(temp_database)
            mock_get_infra.return_value = mock_service
            
            # Test creating a container
            result = runner.invoke(app, [
                "container", "create", "test-nginx", "nginx:latest",
                "--port", "8080:80", "--env", "ENV=test"
            ])
            assert result.exit_code == 0
            assert "Container created successfully" in result.stdout
            
            # Test listing containers
            result = runner.invoke(app, ["container", "list"])
            assert result.exit_code == 0
            assert "test-nginx" in result.stdout
            
            # Test stopping container
            result = runner.invoke(app, ["container", "stop", "test-container-id"])
            assert result.exit_code == 0
            assert "Container stopped successfully" in result.stdout
            
            # Test getting logs
            result = runner.invoke(app, ["container", "logs", "test-container-id"])
            assert result.exit_code == 0
            assert "Mock log output" in result.stdout


class TestCLIAgentIntegration:
    """Integration tests for CLI agent management."""

    @patch('anvyl.cli.get_service_manager')
    def test_agent_lifecycle(self, mock_get_service_manager):
        """Test complete agent lifecycle: up, query, status, down."""
        from anvyl.cli import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        # Setup mock service manager
        mock_service_manager = MockServiceManager()
        mock_get_service_manager.return_value = mock_service_manager
        
        # Test starting agent
        result = runner.invoke(app, [
            "agent", "up",
            "--model-provider-url", "http://localhost:11434/v1",
            "--port", "4201"
        ])
        assert result.exit_code == 0
        assert "Agent started successfully" in result.stdout
        
        # Test querying agent
        with patch('anvyl.cli.requests.get') as mock_requests:
            mock_response = type('MockResponse', (), {
                'status_code': 200,
                'json': lambda: {"response": "I found 2 containers running."}
            })()
            mock_requests.return_value = mock_response
            
            result = runner.invoke(app, [
                "agent", "query", "List all containers",
                "--port", "4201"
            ])
            assert result.exit_code == 0
            assert "I found 2 containers running" in result.stdout
        
        # Test stopping agent
        result = runner.invoke(app, ["agent", "down"])
        assert result.exit_code == 0
        assert "Agent stopped successfully" in result.stdout


class TestCLISystemIntegration:
    """Integration tests for CLI system commands."""

    def test_status_command_integration(self, temp_database):
        """Test system status command with real data."""
        from anvyl.cli import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        with patch('anvyl.cli.get_infrastructure') as mock_get_infra, \
             patch('anvyl.cli.requests.get') as mock_requests:
            
            # Setup mock infrastructure service with data
            mock_service = MockInfrastructureService(temp_database)
            mock_service.add_test_data()
            mock_get_infra.return_value = mock_service
            
            # Mock API health check
            mock_response = type('MockResponse', (), {
                'status_code': 200,
                'json': lambda: {"status": "healthy"}
            })()
            mock_requests.return_value = mock_response
            
            result = runner.invoke(app, ["status"])
            assert result.exit_code == 0
            assert "System Status" in result.stdout

    def test_purge_command_integration(self, temp_database):
        """Test data purge command with real database."""
        from anvyl.cli import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        # Add some test data
        host = Host(id="test-host", name="Test Host", ip="192.168.1.100")
        temp_database.add_host(host)
        
        container = Container(
            id="test-container", name="test", image="nginx:latest",
            host_id="test-host", status="running"
        )
        temp_database.add_container(container)
        
        with patch('anvyl.cli.DatabaseManager', return_value=temp_database):
            # Test force purge
            result = runner.invoke(app, ["purge", "--force"])
            assert result.exit_code == 0
            assert "Data purged successfully" in result.stdout
            
            # Verify data is purged
            assert len(temp_database.list_hosts()) == 0
            assert len(temp_database.list_containers()) == 0


class TestCLIErrorScenarios:
    """Integration tests for error scenarios."""

    def test_service_unavailable_scenarios(self):
        """Test CLI behavior when services are unavailable."""
        from anvyl.cli import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        with patch('anvyl.cli.get_infrastructure') as mock_get_infra:
            # Test infrastructure service error
            mock_get_infra.side_effect = Exception("Service unavailable")
            
            result = runner.invoke(app, ["host", "list"])
            assert result.exit_code == 1
            assert "Error initializing infrastructure service" in result.stdout

    def test_agent_connection_errors(self):
        """Test CLI behavior when agent is unreachable."""
        from anvyl.cli import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        with patch('anvyl.cli.requests.get') as mock_requests:
            # Test connection error
            mock_requests.side_effect = Exception("Connection refused")
            
            result = runner.invoke(app, ["agent", "query", "test query"])
            assert result.exit_code == 1
            assert "Error querying agent" in result.stdout


# Helper Classes for Integration Testing

class MockInfrastructureService:
    """Mock infrastructure service for integration testing."""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.containers = []
        self.next_container_id = 1
    
    def list_hosts(self):
        hosts = self.db.list_hosts()
        return [
            {
                "id": h.id,
                "name": h.name,
                "ip": h.ip,
                "os": h.os or "",
                "status": h.status,
                "tags": h.get_tags()
            }
            for h in hosts
        ]
    
    def add_host(self, name, ip, os="", tags=None):
        host = Host(
            id=f"host-{len(self.list_hosts()) + 1}",
            name=name,
            ip=ip,
            os=os
        )
        if tags:
            host.set_tags(tags)
        
        self.db.add_host(host)
        return {
            "id": host.id,
            "name": host.name,
            "ip": host.ip,
            "os": host.os,
            "status": host.status,
            "tags": host.get_tags()
        }
    
    def list_containers(self, host_id=None):
        containers = self.db.list_containers(host_id)
        return [
            {
                "id": c.id,
                "name": c.name,
                "image": c.image,
                "status": c.status,
                "host_id": c.host_id,
                "labels": c.get_labels(),
                "ports": c.get_ports(),
                "volumes": c.get_volumes(),
                "environment": c.get_environment()
            }
            for c in containers
        ]
    
    def add_container(self, name, image, **kwargs):
        container = Container(
            id=f"test-container-id",
            name=name,
            image=image,
            host_id="test-host-id",
            status="running"
        )
        
        self.db.add_container(container)
        return {
            "id": container.id,
            "name": container.name,
            "image": container.image,
            "status": container.status,
            "host_id": container.host_id
        }
    
    def stop_container(self, container_id, timeout=10):
        return True
    
    def get_logs(self, container_id, follow=False, tail=100):
        return "Mock log output\nAnother log line"
    
    def exec_command(self, container_id, command, tty=False):
        return {
            "output": f"Mock command output for: {' '.join(command)}",
            "exit_code": 0,
            "success": True
        }
    
    def get_host_metrics(self, host_id):
        return {
            "cpu_count": 8,
            "memory_total": 16384,
            "memory_available": 8192,
            "disk_total": 500,
            "disk_available": 250
        }
    
    def add_test_data(self):
        """Add test data for integration tests."""
        host = Host(id="test-host", name="Test Host", ip="192.168.1.100")
        self.db.add_host(host)
        
        container = Container(
            id="test-container", name="test-nginx", image="nginx:latest",
            host_id="test-host", status="running"
        )
        self.db.add_container(container)


class MockServiceManager:
    """Mock service manager for agent testing."""
    
    def __init__(self):
        self.agent_running = False
    
    def start_agent(self, **kwargs):
        self.agent_running = True
        return True
    
    def stop_agent(self):
        self.agent_running = False
        return True
    
    def get_agent_status(self):
        return {
            "running": self.agent_running,
            "port": 4201,
            "host": "127.0.0.1"
        }


class TestCLIRealWorldScenarios:
    """Integration tests for real-world usage scenarios."""

    def test_complete_infrastructure_setup(self, temp_database, mock_project_root):
        """Test setting up complete infrastructure from scratch."""
        from anvyl.cli import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        with patch('anvyl.cli.get_infrastructure') as mock_get_infra, \
             patch('anvyl.cli.subprocess.run') as mock_subprocess, \
             patch('anvyl.cli.get_project_root') as mock_get_root:
            
            mock_get_root.return_value = mock_project_root
            mock_subprocess.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )
            
            mock_service = MockInfrastructureService(temp_database)
            mock_get_infra.return_value = mock_service
            
            # 1. Start infrastructure
            result = runner.invoke(app, ["up", "--no-build"])
            assert result.exit_code == 0
            
            # 2. Add hosts
            result = runner.invoke(app, [
                "host", "add", "web-server", "192.168.1.100",
                "--os", "Linux", "--tag", "web"
            ])
            assert result.exit_code == 0
            
            result = runner.invoke(app, [
                "host", "add", "db-server", "192.168.1.101",
                "--os", "Linux", "--tag", "database"
            ])
            assert result.exit_code == 0
            
            # 3. Create containers
            result = runner.invoke(app, [
                "container", "create", "nginx", "nginx:latest",
                "--port", "80:80"
            ])
            assert result.exit_code == 0
            
            result = runner.invoke(app, [
                "container", "create", "postgres", "postgres:13",
                "--env", "POSTGRES_PASSWORD=secret"
            ])
            assert result.exit_code == 0
            
            # 4. Check status
            with patch('anvyl.cli.requests.get') as mock_requests:
                mock_response = type('MockResponse', (), {
                    'status_code': 200,
                    'json': lambda: {"status": "healthy"}
                })()
                mock_requests.return_value = mock_response
                
                result = runner.invoke(app, ["status"])
                assert result.exit_code == 0
            
            # 5. List everything
            result = runner.invoke(app, ["host", "list"])
            assert result.exit_code == 0
            assert "web-server" in result.stdout
            assert "db-server" in result.stdout
            
            result = runner.invoke(app, ["container", "list"])
            assert result.exit_code == 0
            assert "nginx" in result.stdout
            assert "postgres" in result.stdout

    def test_troubleshooting_workflow(self, temp_database):
        """Test troubleshooting workflow: logs, exec, metrics."""
        from anvyl.cli import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        with patch('anvyl.cli.get_infrastructure') as mock_get_infra:
            mock_service = MockInfrastructureService(temp_database)
            mock_service.add_test_data()
            mock_get_infra.return_value = mock_service
            
            # 1. Check container logs
            result = runner.invoke(app, ["container", "logs", "test-container"])
            assert result.exit_code == 0
            assert "Mock log output" in result.stdout
            
            # 2. Execute commands in container
            result = runner.invoke(app, [
                "container", "exec", "test-container", "ps", "aux"
            ])
            assert result.exit_code == 0
            assert "Mock command output" in result.stdout
            
            # 3. Check host metrics
            result = runner.invoke(app, ["host", "metrics", "test-host"])
            assert result.exit_code == 0
            assert "Host Metrics" in result.stdout