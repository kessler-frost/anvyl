"""
Unit tests for Anvyl gRPC Server
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import uuid
import pytest
import grpc
from datetime import datetime
from concurrent import futures

# Import the server module
import anvyl_grpc_server
from anvyl_grpc_server import AnvylService, serve

# Mock the generated protobuf modules
import sys
sys.modules['generated.anvyl_pb2'] = Mock()
sys.modules['generated.anvyl_pb2_grpc'] = Mock()
import generated.anvyl_pb2 as anvyl_pb2
import generated.anvyl_pb2_grpc as anvyl_pb2_grpc


class TestAnvylService(unittest.TestCase):
    """Test cases for AnvylService class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock docker client
        self.mock_docker_client = Mock()
        self.mock_docker_client.ping.return_value = True
        
        # Mock container objects
        self.mock_container = Mock()
        self.mock_container.id = "test_container_id"
        self.mock_container.name = "test_container"
        self.mock_container.status = "running"
        self.mock_container.labels = {"test": "label"}
        self.mock_container.image.tags = ["test:latest"]
        self.mock_container.attrs = {'Created': datetime.now().timestamp()}
        
        # Mock protobuf objects
        anvyl_pb2.Host = Mock()
        anvyl_pb2.Container = Mock()
        anvyl_pb2.ListHostsResponse = Mock()
        anvyl_pb2.AddHostResponse = Mock()
        anvyl_pb2.ListContainersResponse = Mock()
        anvyl_pb2.AddContainerResponse = Mock()
        anvyl_pb2.StopContainerResponse = Mock()
        anvyl_pb2.GetLogsResponse = Mock()
        anvyl_pb2.ExecCommandResponse = Mock()

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_init_successful_docker_connection(self, mock_uuid, mock_socket, mock_docker_from_env):
        """Test successful Docker client initialization."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.return_value = "test-host"
        mock_socket.gethostbyname.return_value = "192.168.1.100"
        mock_docker_from_env.return_value = self.mock_docker_client
        
        service = AnvylService()
        
        self.assertIsNotNone(service.docker_client)
        self.mock_docker_client.ping.assert_called_once()
        self.assertEqual(len(service.hosts), 1)

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.docker.DockerClient')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_init_fallback_docker_connection(self, mock_uuid, mock_socket, mock_docker_client_class, mock_docker_from_env):
        """Test Docker client fallback connection methods."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.return_value = "test-host"
        mock_socket.gethostbyname.return_value = "192.168.1.100"
        
        # First connection fails
        mock_docker_from_env.side_effect = Exception("Connection failed")
        
        # Second connection succeeds
        mock_docker_client_class.return_value = self.mock_docker_client
        
        service = AnvylService()
        
        self.assertIsNotNone(service.docker_client)
        mock_docker_client_class.assert_called_with(base_url='unix:///var/run/docker.sock')

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.docker.DockerClient')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_init_no_docker_connection(self, mock_uuid, mock_socket, mock_docker_client_class, mock_docker_from_env):
        """Test when all Docker connections fail."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.return_value = "test-host"
        mock_socket.gethostbyname.return_value = "192.168.1.100"
        
        # All connections fail
        mock_docker_from_env.side_effect = Exception("Connection failed")
        mock_docker_client_class.side_effect = Exception("Connection failed")
        
        service = AnvylService()
        
        self.assertIsNone(service.docker_client)

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_register_local_host(self, mock_uuid, mock_socket, mock_docker_from_env):
        """Test local host registration."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.return_value = "test-host"
        mock_socket.gethostbyname.return_value = "192.168.1.100"
        mock_docker_from_env.return_value = self.mock_docker_client
        
        service = AnvylService()
        
        self.assertEqual(len(service.hosts), 1)
        mock_socket.gethostname.assert_called_once()
        mock_socket.gethostbyname.assert_called_once()

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_register_local_host_socket_error(self, mock_uuid, mock_socket, mock_docker_from_env):
        """Test local host registration with socket errors."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.side_effect = Exception("Socket error")
        mock_docker_from_env.return_value = self.mock_docker_client
        
        service = AnvylService()
        
        # Should fallback to localhost
        self.assertEqual(len(service.hosts), 1)

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_list_hosts(self, mock_uuid, mock_socket, mock_docker_from_env):
        """Test ListHosts method."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.return_value = "test-host"
        mock_socket.gethostbyname.return_value = "192.168.1.100"
        mock_docker_from_env.return_value = self.mock_docker_client
        
        service = AnvylService()
        context = Mock()
        request = Mock()
        
        response = service.ListHosts(request, context)
        
        anvyl_pb2.ListHostsResponse.assert_called_once()

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_add_host(self, mock_uuid, mock_socket, mock_docker_from_env):
        """Test AddHost method."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.return_value = "test-host"
        mock_socket.gethostbyname.return_value = "192.168.1.100"
        mock_docker_from_env.return_value = self.mock_docker_client
        
        service = AnvylService()
        context = Mock()
        request = Mock()
        request.name = "new-host"
        request.ip = "192.168.1.200"
        
        response = service.AddHost(request, context)
        
        self.assertEqual(len(service.hosts), 2)  # Original + new host
        anvyl_pb2.AddHostResponse.assert_called_once()

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_list_containers_no_docker(self, mock_uuid, mock_socket, mock_docker_from_env):
        """Test ListContainers with no Docker client."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.return_value = "test-host"
        mock_socket.gethostbyname.return_value = "192.168.1.100"
        mock_docker_from_env.side_effect = Exception("No Docker")
        
        service = AnvylService()
        context = Mock()
        request = Mock()
        
        response = service.ListContainers(request, context)
        
        anvyl_pb2.ListContainersResponse.assert_called_with(containers=[])

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_list_containers_with_docker(self, mock_uuid, mock_socket, mock_docker_from_env):
        """Test ListContainers with Docker client."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.return_value = "test-host"
        mock_socket.gethostbyname.return_value = "192.168.1.100"
        mock_docker_from_env.return_value = self.mock_docker_client
        
        self.mock_docker_client.containers.list.return_value = [self.mock_container]
        
        service = AnvylService()
        context = Mock()
        request = Mock()
        
        response = service.ListContainers(request, context)
        
        self.mock_docker_client.containers.list.assert_called_once_with(all=True)
        anvyl_pb2.Container.assert_called()

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_list_containers_docker_error(self, mock_uuid, mock_socket, mock_docker_from_env):
        """Test ListContainers with Docker error."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.return_value = "test-host"
        mock_socket.gethostbyname.return_value = "192.168.1.100"
        mock_docker_from_env.return_value = self.mock_docker_client
        
        self.mock_docker_client.containers.list.side_effect = Exception("Docker error")
        
        service = AnvylService()
        context = Mock()
        request = Mock()
        
        response = service.ListContainers(request, context)
        
        anvyl_pb2.ListContainersResponse.assert_called_with(containers=[])

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_add_container_no_docker(self, mock_uuid, mock_socket, mock_docker_from_env):
        """Test AddContainer with no Docker client."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.return_value = "test-host"
        mock_socket.gethostbyname.return_value = "192.168.1.100"
        mock_docker_from_env.side_effect = Exception("No Docker")
        
        service = AnvylService()
        context = Mock()
        request = Mock()
        request.name = "test-container"
        request.image = "test:latest"
        
        response = service.AddContainer(request, context)
        
        anvyl_pb2.AddContainerResponse.assert_called_with(
            container=None,
            success=False,
            error_message="Docker client not available"
        )

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_add_container_success(self, mock_uuid, mock_socket, mock_docker_from_env):
        """Test successful AddContainer."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.return_value = "test-host"
        mock_socket.gethostbyname.return_value = "192.168.1.100"
        mock_docker_from_env.return_value = self.mock_docker_client
        
        self.mock_docker_client.containers.run.return_value = self.mock_container
        
        service = AnvylService()
        context = Mock()
        request = Mock()
        request.name = "test-container"
        request.image = "test:latest"
        request.labels = {"test": "label"}
        request.ports = ["8080:80"]
        request.volumes = ["/host:/container"]
        request.environment = ["ENV=test"]
        
        response = service.AddContainer(request, context)
        
        self.mock_docker_client.containers.run.assert_called_once()
        anvyl_pb2.Container.assert_called()

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_add_container_docker_error(self, mock_uuid, mock_socket, mock_docker_from_env):
        """Test AddContainer with Docker error."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.return_value = "test-host"
        mock_socket.gethostbyname.return_value = "192.168.1.100"
        mock_docker_from_env.return_value = self.mock_docker_client
        
        self.mock_docker_client.containers.run.side_effect = Exception("Docker error")
        
        service = AnvylService()
        context = Mock()
        request = Mock()
        request.name = "test-container"
        request.image = "test:latest"
        request.labels = {}
        request.ports = []
        request.volumes = []
        request.environment = []
        
        response = service.AddContainer(request, context)
        
        anvyl_pb2.AddContainerResponse.assert_called_with(
            container=None,
            success=False,
            error_message="Docker error"
        )

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_stop_container(self, mock_uuid, mock_socket, mock_docker_from_env):
        """Test StopContainer stub method."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.return_value = "test-host"
        mock_socket.gethostbyname.return_value = "192.168.1.100"
        mock_docker_from_env.return_value = self.mock_docker_client
        
        service = AnvylService()
        context = Mock()
        request = Mock()
        request.container_id = "test-container-id"
        
        response = service.StopContainer(request, context)
        
        anvyl_pb2.StopContainerResponse.assert_called_with(
            success=False,
            error_message="Not implemented yet"
        )

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_get_logs(self, mock_uuid, mock_socket, mock_docker_from_env):
        """Test GetLogs stub method."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.return_value = "test-host"
        mock_socket.gethostbyname.return_value = "192.168.1.100"
        mock_docker_from_env.return_value = self.mock_docker_client
        
        service = AnvylService()
        context = Mock()
        request = Mock()
        request.container_id = "test-container-id"
        
        response = service.GetLogs(request, context)
        
        anvyl_pb2.GetLogsResponse.assert_called_with(
            logs="",
            success=False,
            error_message="Not implemented yet"
        )

    @patch('anvyl_grpc_server.docker.from_env')
    @patch('anvyl_grpc_server.socket')
    @patch('anvyl_grpc_server.uuid.uuid4')
    def test_exec_command(self, mock_uuid, mock_socket, mock_docker_from_env):
        """Test ExecCommand stub method."""
        mock_uuid.return_value = Mock(hex="test-uuid")
        mock_socket.gethostname.return_value = "test-host"
        mock_socket.gethostbyname.return_value = "192.168.1.100"
        mock_docker_from_env.return_value = self.mock_docker_client
        
        service = AnvylService()
        context = Mock()
        request = Mock()
        request.container_id = "test-container-id"
        
        response = service.ExecCommand(request, context)
        
        anvyl_pb2.ExecCommandResponse.assert_called_with(
            output="",
            exit_code=1,
            success=False,
            error_message="Not implemented yet"
        )


class TestServeFunction(unittest.TestCase):
    """Test cases for the serve function."""

    @patch('anvyl_grpc_server.grpc.server')
    @patch('anvyl_grpc_server.futures.ThreadPoolExecutor')
    @patch('anvyl_grpc_server.anvyl_pb2_grpc.add_AnvylServiceServicer_to_server')
    def test_serve_function(self, mock_add_servicer, mock_executor, mock_grpc_server):
        """Test the serve function setup."""
        mock_server = Mock()
        mock_grpc_server.return_value = mock_server
        
        # Mock server.wait_for_termination to avoid blocking
        mock_server.wait_for_termination.side_effect = KeyboardInterrupt()
        
        with pytest.raises(SystemExit):
            serve()
        
        mock_grpc_server.assert_called_once_with(mock_executor.return_value)
        mock_server.add_insecure_port.assert_called_once_with('[::]:50051')
        mock_server.start.assert_called_once()
        mock_server.stop.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main()