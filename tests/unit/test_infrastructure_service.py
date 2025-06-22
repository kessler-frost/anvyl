"""
Unit tests for Anvyl Infrastructure Service
"""

import pytest
import tempfile
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from anvyl.infra.service import InfrastructureService
from anvyl.database.models import Host, Container


class TestInfrastructureServiceInitialization:
    """Test InfrastructureService initialization."""

    @patch('anvyl.infra.service.DatabaseManager')
    @patch('docker.from_env')
    @patch('socket.gethostname')
    def test_service_initialization_success(self, mock_hostname, mock_docker, mock_db):
        """Test successful service initialization."""
        mock_hostname.return_value = "test-host"
        mock_docker_client = Mock()
        mock_docker.return_value = mock_docker_client
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance

        # Mock database operations
        mock_db_instance.get_host_by_ip.return_value = None

        with patch.object(InfrastructureService, '_sync_containers_with_docker'):
            service = InfrastructureService()

        assert service.db == mock_db_instance
        assert service.docker_client == mock_docker_client
        assert service.host_id is not None
        mock_db_instance.add_host.assert_called_once()

    @patch('anvyl.infra.service.DatabaseManager')
    @patch('docker.from_env')
    @patch('socket.gethostname')
    def test_service_initialization_existing_host(self, mock_hostname, mock_docker, mock_db):
        """Test initialization with existing host."""
        mock_hostname.return_value = "test-host"
        mock_docker_client = Mock()
        mock_docker.return_value = mock_docker_client
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance

        # Mock existing host
        existing_host = Host(id="existing-id", name="test-host", ip="127.0.0.1")
        mock_db_instance.get_host_by_ip.return_value = existing_host

        with patch.object(InfrastructureService, '_sync_containers_with_docker'):
            service = InfrastructureService()

        assert service.host_id == "existing-id"
        mock_db_instance.update_host.assert_called_once()

    @patch('anvyl.infra.service.DatabaseManager')
    @patch('docker.from_env')
    def test_service_initialization_docker_unavailable(self, mock_docker, mock_db):
        """Test initialization when Docker is unavailable."""
        mock_docker.side_effect = Exception("Docker daemon not running")
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.get_host_by_ip.return_value = None

        with patch.object(InfrastructureService, '_sync_containers_with_docker'):
            service = InfrastructureService()

        assert service.docker_client is None


class TestInfrastructureServiceHostManagement:
    """Test host management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch('anvyl.infra.service.DatabaseManager'), \
             patch('docker.from_env'), \
             patch.object(InfrastructureService, '_register_local_host'), \
             patch.object(InfrastructureService, '_sync_containers_with_docker'):
            self.service = InfrastructureService()
            self.service.db = Mock()
            self.service.docker_client = Mock()
            self.service.host_id = "test-host-id"

    def test_list_hosts_success(self):
        """Test listing hosts successfully."""
        mock_hosts = [
            Host(id="host1", name="Host 1", ip="192.168.1.100", os="Linux", status="online"),
            Host(id="host2", name="Host 2", ip="192.168.1.101", os="Linux", status="offline")
        ]
        self.service.db.list_hosts.return_value = mock_hosts

        with patch.object(self.service, '_get_host_resources', return_value={"cpu_count": 8}):
            result = self.service.list_hosts()

        assert len(result) == 2
        assert result[0]["id"] == "host1"
        assert result[0]["name"] == "Host 1"
        assert result[0]["ip"] == "192.168.1.100"
        assert result[0]["status"] == "online"

    def test_add_host_success(self):
        """Test adding a host successfully."""
        self.service.db.add_host.return_value = Host(
            id="new-host-id", name="New Host", ip="192.168.1.200", os="Linux"
        )
        self.service.db.refresh_system_status.return_value = None

        result = self.service.add_host("New Host", "192.168.1.200", "Linux", ["production"])

        assert result is not None
        assert result["name"] == "New Host"
        assert result["ip"] == "192.168.1.200"
        assert result["os"] == "Linux"
        self.service.db.add_host.assert_called_once()
        self.service.db.refresh_system_status.assert_called_once()

    def test_add_host_error(self):
        """Test adding a host with error."""
        self.service.db.add_host.side_effect = Exception("Database error")

        result = self.service.add_host("New Host", "192.168.1.200")

        assert result is None

    def test_update_host_success(self):
        """Test updating a host successfully."""
        mock_host = Host(id="host1", name="Host 1", ip="192.168.1.100")
        self.service.db.get_host.return_value = mock_host
        self.service.db.update_host.return_value = mock_host
        self.service.db.refresh_system_status.return_value = None

        result = self.service.update_host(
            "host1",
            resources={"cpu_count": 8},
            status="online",
            tags=["web-server"]
        )

        assert result is not None
        assert result["id"] == "host1"
        self.service.db.update_host.assert_called_once()

    def test_update_host_not_found(self):
        """Test updating a non-existent host."""
        self.service.db.get_host.return_value = None

        result = self.service.update_host("nonexistent-host")

        assert result is None

    def test_get_host_metrics_success(self):
        """Test getting host metrics successfully."""
        mock_host = Host(id="host1", name="Host 1", ip="192.168.1.100")
        self.service.db.get_host.return_value = mock_host

        with patch.object(self.service, '_get_host_resources', return_value={"cpu_count": 8}):
            result = self.service.get_host_metrics("host1")

        assert result is not None
        assert result["cpu_count"] == 8

    def test_host_heartbeat_success(self):
        """Test host heartbeat update."""
        mock_host = Host(id="host1", name="Host 1", ip="192.168.1.100")
        self.service.db.get_host.return_value = mock_host
        self.service.db.update_host_heartbeat.return_value = None

        result = self.service.host_heartbeat("host1")

        assert result is True
        self.service.db.update_host_heartbeat.assert_called_once_with("host1")


class TestInfrastructureServiceContainerManagement:
    """Test container management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch('anvyl.infra.service.DatabaseManager'), \
             patch('docker.from_env'), \
             patch.object(InfrastructureService, '_register_local_host'), \
             patch.object(InfrastructureService, '_sync_containers_with_docker'):
            self.service = InfrastructureService()
            self.service.db = Mock()
            self.service.docker_client = Mock()
            self.service.host_id = "test-host-id"

    def test_list_containers_success(self):
        """Test listing containers successfully."""
        mock_containers = [
            Container(
                id="container1", name="nginx", image="nginx:latest",
                host_id="host1", status="running",
                labels='{"anvyl.type": "web"}'
            ),
            Container(
                id="container2", name="postgres", image="postgres:13",
                host_id="host1", status="running",
                labels='{"anvyl.type": "database"}'
            )
        ]
        self.service.db.list_containers.return_value = mock_containers

        result = self.service.list_containers()

        assert len(result) == 2
        assert result[0]["name"] == "nginx"
        assert result[1]["name"] == "postgres"

    def test_list_containers_all_flag(self):
        """Test listing all containers including non-Anvyl ones."""
        mock_containers = [
            Container(
                id="container1", name="nginx", image="nginx:latest",
                host_id="host1", status="running", labels='{}'
            ),
            Container(
                id="container2", name="system", image="system:latest",
                host_id="host1", status="running", labels='{}'
            )
        ]
        self.service.db.list_containers.return_value = mock_containers

        result = self.service.list_containers(all=True)

        assert len(result) == 2

    def test_list_containers_by_host(self):
        """Test listing containers filtered by host."""
        mock_containers = [
            Container(
                id="container1", name="nginx", image="nginx:latest",
                host_id="host1", status="running",
                labels='{"anvyl.type": "web"}'
            )
        ]
        self.service.db.list_containers.return_value = mock_containers

        result = self.service.list_containers(host_id="host1")

        assert len(result) == 1
        assert result[0]["host_id"] == "host1"

    def test_add_container_success(self):
        """Test adding a container successfully."""
        mock_docker_container = Mock()
        mock_docker_container.id = "docker-container-id"
        mock_docker_container.status = "running"
        self.service.docker_client.containers.run.return_value = mock_docker_container
        self.service.db.add_container.return_value = Mock()
        self.service.db.refresh_system_status.return_value = None

        result = self.service.add_container(
            name="test-container",
            image="nginx:latest",
            ports=["8080:80"],
            environment=["ENV=production"],
            labels={"app": "test"}
        )

        assert result is not None
        self.service.docker_client.containers.run.assert_called_once()
        self.service.db.add_container.assert_called_once()

    def test_add_container_docker_unavailable(self):
        """Test adding a container when Docker is unavailable."""
        self.service.docker_client = None

        result = self.service.add_container("test-container", "nginx:latest")

        assert result is None

    def test_add_container_docker_error(self):
        """Test adding a container with Docker error."""
        self.service.docker_client.containers.run.side_effect = Exception("Docker error")

        result = self.service.add_container("test-container", "nginx:latest")

        assert result is None

    def test_remove_container_success(self):
        """Test removing a container successfully."""
        # Mock Docker container
        mock_container = Mock()
        mock_container.stop.return_value = None
        mock_container.remove.return_value = None

        # Mock Docker client
        self.service.docker_client = Mock()
        self.service.docker_client.containers.get.return_value = mock_container

        # Mock database
        self.service.db = Mock()
        self.service.db.refresh_system_status.return_value = None

        result = self.service.remove_container("container-id", timeout=5)

        self.assertTrue(result)
        mock_container.stop.assert_called_once_with(timeout=5)
        mock_container.remove.assert_called_once()

    def test_remove_container_docker_unavailable(self):
        """Test removing a container when Docker is unavailable."""
        self.service.docker_client = None

        result = self.service.remove_container("container-id")

        self.assertFalse(result)

    def test_get_logs_success(self):
        """Test getting container logs successfully."""
        mock_docker_container = Mock()
        mock_docker_container.logs.return_value = b"Container log output"
        self.service.docker_client.containers.get.return_value = mock_docker_container

        result = self.service.get_logs("container-id", tail=50)

        assert result == "Container log output"
        mock_docker_container.logs.assert_called_once_with(tail=50, follow=False)

    def test_exec_command_success(self):
        """Test executing command in container successfully."""
        mock_docker_container = Mock()
        mock_exec_result = Mock()
        mock_exec_result.output = b"Command output"
        mock_exec_result.exit_code = 0
        mock_docker_container.exec_run.return_value = mock_exec_result
        self.service.docker_client.containers.get.return_value = mock_docker_container

        result = self.service.exec_command("container-id", ["ls", "-la"])

        assert result is not None
        assert result["output"] == "Command output"
        assert result["exit_code"] == 0
        assert result["success"] is True

    def test_exec_command_on_host_local(self):
        """Test executing command on local host."""
        with patch('subprocess.run') as mock_subprocess:
            mock_result = Mock()
            mock_result.stdout = "Command output"
            mock_result.stderr = ""
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result

            result = self.service.exec_command_on_host(
                self.service.host_id,
                ["echo", "hello"]
            )

        assert result is not None
        assert result["output"] == "Command output"
        assert result["exit_code"] == 0
        assert result["success"] is True

    def test_exec_command_on_host_remote(self):
        """Test executing command on remote host (should fail)."""
        result = self.service.exec_command_on_host("remote-host-id", ["ls"])

        assert result is not None
        assert result["success"] is False
        assert "Can only execute commands on local host" in result["error_message"]


class TestInfrastructureServiceDockerSync:
    """Test Docker container synchronization."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch('anvyl.infra.service.DatabaseManager'), \
             patch('docker.from_env'), \
             patch.object(InfrastructureService, '_register_local_host'):
            self.service = InfrastructureService()
            self.service.db = Mock()
            self.service.docker_client = Mock()
            self.service.host_id = "test-host-id"

    def test_sync_containers_with_docker_success(self):
        """Test successful container synchronization."""
        # Mock Docker containers
        mock_docker_container = Mock()
        mock_docker_container.id = "docker-id-1"
        mock_docker_container.attrs = {
            'Name': '/test-container',
            'Config': {
                'Image': 'nginx:latest',
                'Labels': {'app': 'test'},
                'Env': ['ENV=production']
            },
            'State': {'Status': 'running'},
            'HostConfig': {'PortBindings': {'80/tcp': [{'HostPort': '8080', 'HostIp': '0.0.0.0'}]}}
        }
        self.service.docker_client.containers.list.return_value = [mock_docker_container]

        # Mock database containers
        self.service.db.list_containers.return_value = []

        self.service._sync_containers_with_docker()

        self.service.db.add_container.assert_called_once()
        self.service.db.refresh_system_status.assert_called_once()

    def test_sync_containers_docker_unavailable(self):
        """Test synchronization when Docker is unavailable."""
        self.service.docker_client = None

        self.service._sync_containers_with_docker()

        # Should not crash and should log warning

    def test_sync_containers_remove_deleted(self):
        """Test removing containers that no longer exist in Docker."""
        # Mock empty Docker containers list
        self.service.docker_client.containers.list.return_value = []

        # Mock existing database container
        mock_db_container = Container(
            id="old-container", name="old", image="old:latest",
            host_id="host1", status="running"
        )
        self.service.db.list_containers.return_value = [mock_db_container]

        self.service._sync_containers_with_docker()

        self.service.db.delete_container.assert_called_once_with("old-container")


class TestInfrastructureServiceResourceMonitoring:
    """Test resource monitoring functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch('anvyl.infra.service.DatabaseManager'), \
             patch('docker.from_env'), \
             patch.object(InfrastructureService, '_register_local_host'), \
             patch.object(InfrastructureService, '_sync_containers_with_docker'):
            self.service = InfrastructureService()

    @patch('psutil.cpu_count')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_get_host_resources_success(self, mock_disk, mock_memory, mock_cpu):
        """Test getting host resources successfully."""
        mock_cpu.return_value = 8
        mock_memory.return_value = Mock(total=16 * 1024**3, available=8 * 1024**3)
        mock_disk.return_value = Mock(total=500 * 1024**3, free=250 * 1024**3)

        result = self.service._get_host_resources()

        assert result["cpu_count"] == 8
        assert result["memory_total"] == 16 * 1024  # MB
        assert result["memory_available"] == 8 * 1024  # MB
        assert result["disk_total"] == 500  # GB
        assert result["disk_available"] == 250  # GB

    @patch('psutil.cpu_count')
    def test_get_host_resources_error(self, mock_cpu):
        """Test getting host resources with error."""
        mock_cpu.side_effect = Exception("psutil error")

        result = self.service._get_host_resources()

        assert result["cpu_count"] == 0
        assert result["memory_total"] == 0


class TestInfrastructureServiceErrorHandling:
    """Test error handling scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch('anvyl.infra.service.DatabaseManager'), \
             patch('docker.from_env'), \
             patch.object(InfrastructureService, '_register_local_host'), \
             patch.object(InfrastructureService, '_sync_containers_with_docker'):
            self.service = InfrastructureService()
            self.service.db = Mock()
            self.service.docker_client = Mock()

    def test_add_host_database_error(self):
        """Test adding host with database error."""
        self.service.db.add_host.side_effect = Exception("Database connection failed")

        result = self.service.add_host("Test Host", "192.168.1.100")

        assert result is None

    def test_remove_container_docker_error(self):
        """Test removing container with Docker error."""
        self.service.docker_client.containers.get.side_effect = Exception("Container not found")

        result = self.service.remove_container("nonexistent-container")

        assert result is False

    def test_get_logs_docker_error(self):
        """Test getting logs with Docker error."""
        self.service.docker_client.containers.get.side_effect = Exception("Container not found")

        result = self.service.get_logs("nonexistent-container")

        assert result is None

    def test_exec_command_docker_error(self):
        """Test executing command with Docker error."""
        self.service.docker_client.containers.get.side_effect = Exception("Container not found")

        result = self.service.exec_command("nonexistent-container", ["ls"])

        assert result is None


class TestInfrastructureServiceSingleton:
    """Test singleton pattern implementation."""

    @patch('anvyl.infra.service.DatabaseManager')
    @patch('docker.from_env')
    @patch.object(InfrastructureService, '_register_local_host')
    @patch.object(InfrastructureService, '_sync_containers_with_docker')
    def test_get_infrastructure_service_singleton(self, mock_sync, mock_register, mock_docker, mock_db):
        """Test that get_infrastructure_service returns the same instance."""
        from anvyl.infra.service import get_infrastructure_service

        service1 = get_infrastructure_service()
        service2 = get_infrastructure_service()

        assert service1 is service2