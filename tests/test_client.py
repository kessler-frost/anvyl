"""
Unit tests for Anvyl gRPC Client
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest
import grpc

# Import the client module
from anvyl.grpc_client import AnvylClient, create_client

# Mock the generated protobuf modules
import sys
sys.modules['generated.anvyl_pb2'] = Mock()
sys.modules['generated.anvyl_pb2_grpc'] = Mock()
import generated.anvyl_pb2 as anvyl_pb2
import generated.anvyl_pb2_grpc as anvyl_pb2_grpc


class TestAnvylClient(unittest.TestCase):
    """Test cases for AnvylClient class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock gRPC objects
        self.mock_channel = Mock()
        self.mock_stub = Mock()
        
        # Mock protobuf objects
        anvyl_pb2.ListHostsRequest = Mock()
        anvyl_pb2.AddHostRequest = Mock()
        anvyl_pb2.ListContainersRequest = Mock()
        anvyl_pb2.AddContainerRequest = Mock()
        anvyl_pb2.StopContainerRequest = Mock()
        anvyl_pb2.GetLogsRequest = Mock()
        anvyl_pb2.ExecCommandRequest = Mock()
        
        # Mock response objects
        self.mock_host = Mock()
        self.mock_host.id = "host-id"
        self.mock_host.name = "test-host"
        self.mock_host.ip = "192.168.1.100"
        
        self.mock_container = Mock()
        self.mock_container.id = "container-id"
        self.mock_container.name = "test-container"
        self.mock_container.image = "test:latest"

    def test_init_default_values(self):
        """Test client initialization with default values."""
        client = AnvylClient()
        
        self.assertEqual(client.host, "localhost")
        self.assertEqual(client.port, 50051)
        self.assertEqual(client.address, "localhost:50051")
        self.assertIsNone(client.channel)
        self.assertIsNone(client.stub)

    def test_init_custom_values(self):
        """Test client initialization with custom values."""
        client = AnvylClient(host="custom-host", port=9999)
        
        self.assertEqual(client.host, "custom-host")
        self.assertEqual(client.port, 9999)
        self.assertEqual(client.address, "custom-host:9999")

    @patch('anvyl.grpc_client.grpc.insecure_channel')
    @patch('anvyl.grpc_client.anvyl_pb2_grpc.AnvylServiceStub')
    def test_connect_success(self, mock_stub_class, mock_channel):
        """Test successful connection."""
        mock_channel.return_value = self.mock_channel
        mock_stub_class.return_value = self.mock_stub
        
        # Mock successful ListHosts call for connection test
        self.mock_stub.ListHosts.return_value = Mock()
        
        client = AnvylClient()
        result = client.connect()
        
        self.assertTrue(result)
        self.assertEqual(client.channel, self.mock_channel)
        self.assertEqual(client.stub, self.mock_stub)
        mock_channel.assert_called_once_with("localhost:50051")
        mock_stub_class.assert_called_once_with(self.mock_channel)
        self.mock_stub.ListHosts.assert_called_once()

    @patch('anvyl.grpc_client.grpc.insecure_channel')
    def test_connect_failure(self, mock_channel):
        """Test connection failure."""
        mock_channel.side_effect = Exception("Connection failed")
        
        client = AnvylClient()
        result = client.connect()
        
        self.assertFalse(result)
        self.assertIsNone(client.channel)
        self.assertIsNone(client.stub)

    def test_disconnect(self):
        """Test disconnection."""
        client = AnvylClient()
        client.channel = self.mock_channel
        
        client.disconnect()
        
        self.mock_channel.close.assert_called_once()

    def test_disconnect_no_channel(self):
        """Test disconnection when no channel exists."""
        client = AnvylClient()
        
        # Should not raise an exception
        client.disconnect()

    @patch('anvyl.grpc_client.anvyl_pb2.ListHostsRequest')
    def test_list_hosts_success(self, mock_request_class):
        """Test successful list_hosts call."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        mock_request = Mock()
        mock_request_class.return_value = mock_request
        
        mock_response = Mock()
        mock_response.hosts = [self.mock_host]
        self.mock_stub.ListHosts.return_value = mock_response
        
        result = client.list_hosts()
        
        self.assertEqual(len(result), 1)
        self.mock_stub.ListHosts.assert_called_once_with(mock_request)
        mock_request_class.assert_called_once()

    def test_list_hosts_error(self):
        """Test list_hosts with error."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        self.mock_stub.ListHosts.side_effect = Exception("gRPC error")
        
        result = client.list_hosts()
        
        self.assertEqual(result, [])

    @patch('anvyl.grpc_client.anvyl_pb2.AddHostRequest')
    def test_add_host_success(self, mock_request_class):
        """Test successful add_host call."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        mock_request = Mock()
        mock_request_class.return_value = mock_request
        
        mock_response = Mock()
        mock_response.success = True
        mock_response.host = self.mock_host
        self.mock_stub.AddHost.return_value = mock_response
        
        result = client.add_host("test-host", "192.168.1.100")
        
        self.assertEqual(result, self.mock_host)
        self.mock_stub.AddHost.assert_called_once_with(mock_request)
        mock_request_class.assert_called_once_with(name="test-host", ip="192.168.1.100")

    def test_add_host_failure(self):
        """Test add_host with failure response."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        mock_response = Mock()
        mock_response.success = False
        mock_response.error_message = "Host already exists"
        self.mock_stub.AddHost.return_value = mock_response
        
        result = client.add_host("test-host", "192.168.1.100")
        
        self.assertIsNone(result)

    def test_add_host_error(self):
        """Test add_host with exception."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        self.mock_stub.AddHost.side_effect = Exception("gRPC error")
        
        result = client.add_host("test-host", "192.168.1.100")
        
        self.assertIsNone(result)

    def test_list_containers_no_host_filter(self):
        """Test list_containers without host filter."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        mock_response = Mock()
        mock_response.containers = [self.mock_container]
        self.mock_stub.ListContainers.return_value = mock_response
        
        result = client.list_containers()
        
        self.assertEqual(len(result), 1)
        self.mock_stub.ListContainers.assert_called_once()

    def test_list_containers_with_host_filter(self):
        """Test list_containers with host filter."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        mock_response = Mock()
        mock_response.containers = [self.mock_container]
        self.mock_stub.ListContainers.return_value = mock_response
        
        result = client.list_containers(host_id="test-host-id")
        
        self.assertEqual(len(result), 1)
        # Verify that host_id was set on the request
        call_args = self.mock_stub.ListContainers.call_args[0][0]
        self.assertEqual(call_args.host_id, "test-host-id")

    def test_list_containers_error(self):
        """Test list_containers with error."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        self.mock_stub.ListContainers.side_effect = Exception("gRPC error")
        
        result = client.list_containers()
        
        self.assertEqual(result, [])

    def test_add_container_minimal_params(self):
        """Test add_container with minimal parameters."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        mock_response = Mock()
        mock_response.success = True
        mock_response.container = self.mock_container
        self.mock_stub.AddContainer.return_value = mock_response
        
        result = client.add_container("test-container", "test:latest")
        
        self.assertEqual(result, self.mock_container)
        self.mock_stub.AddContainer.assert_called_once()

    @patch('anvyl.grpc_client.anvyl_pb2.AddContainerRequest')
    def test_add_container_full_params(self, mock_request_class):
        """Test add_container with all parameters."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        mock_request = Mock()
        mock_request.name = "test-container"
        mock_request.image = "test:latest"
        mock_request.host_id = "test-host-id"
        mock_request_class.return_value = mock_request
        
        mock_response = Mock()
        mock_response.success = True
        mock_response.container = self.mock_container
        self.mock_stub.AddContainer.return_value = mock_response
        
        result = client.add_container(
            name="test-container",
            image="test:latest",
            host_id="test-host-id",
            labels={"env": "test"},
            ports=["8080:80"],
            volumes=["/host:/container"],
            environment=["ENV=test"]
        )
        
        self.assertEqual(result, self.mock_container)
        
        # Verify request parameters
        self.mock_stub.AddContainer.assert_called_once_with(mock_request)
        self.assertEqual(mock_request.name, "test-container")
        self.assertEqual(mock_request.image, "test:latest")
        self.assertEqual(mock_request.host_id, "test-host-id")

    def test_add_container_failure(self):
        """Test add_container with failure response."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        mock_response = Mock()
        mock_response.success = False
        mock_response.error_message = "Image not found"
        self.mock_stub.AddContainer.return_value = mock_response
        
        result = client.add_container("test-container", "test:latest")
        
        self.assertIsNone(result)

    def test_add_container_error(self):
        """Test add_container with exception."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        self.mock_stub.AddContainer.side_effect = Exception("gRPC error")
        
        result = client.add_container("test-container", "test:latest")
        
        self.assertIsNone(result)

    def test_stop_container_success(self):
        """Test successful stop_container call."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        mock_response = Mock()
        mock_response.success = True
        self.mock_stub.StopContainer.return_value = mock_response
        
        result = client.stop_container("container-id")
        
        self.assertTrue(result)
        self.mock_stub.StopContainer.assert_called_once()

    @patch('anvyl.grpc_client.anvyl_pb2.StopContainerRequest')
    def test_stop_container_with_timeout(self, mock_request_class):
        """Test stop_container with custom timeout."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        mock_request = Mock()
        mock_request.timeout = 30
        mock_request_class.return_value = mock_request
        
        mock_response = Mock()
        mock_response.success = True
        self.mock_stub.StopContainer.return_value = mock_response
        
        result = client.stop_container("container-id", timeout=30)
        
        self.assertTrue(result)
        
        # Verify timeout parameter
        self.mock_stub.StopContainer.assert_called_once_with(mock_request)
        self.assertEqual(mock_request.timeout, 30)

    def test_stop_container_error(self):
        """Test stop_container with error."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        self.mock_stub.StopContainer.side_effect = Exception("gRPC error")
        
        result = client.stop_container("container-id")
        
        self.assertFalse(result)

    def test_get_logs_success(self):
        """Test successful get_logs call."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        mock_response = Mock()
        mock_response.success = True
        mock_response.logs = "Container logs here"
        self.mock_stub.GetLogs.return_value = mock_response
        
        result = client.get_logs("container-id")
        
        self.assertEqual(result, "Container logs here")
        self.mock_stub.GetLogs.assert_called_once()

    @patch('anvyl.grpc_client.anvyl_pb2.GetLogsRequest')
    def test_get_logs_with_params(self, mock_request_class):
        """Test get_logs with follow and tail parameters."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        mock_request = Mock()
        mock_request.container_id = "container-id"
        mock_request.follow = True
        mock_request.tail = 50
        mock_request_class.return_value = mock_request
        
        mock_response = Mock()
        mock_response.success = True
        mock_response.logs = "Container logs here"
        self.mock_stub.GetLogs.return_value = mock_response
        
        result = client.get_logs("container-id", follow=True, tail=50)
        
        self.assertEqual(result, "Container logs here")
        
        # Verify parameters
        self.mock_stub.GetLogs.assert_called_once_with(mock_request)
        self.assertEqual(mock_request.container_id, "container-id")
        self.assertTrue(mock_request.follow)
        self.assertEqual(mock_request.tail, 50)

    def test_get_logs_failure(self):
        """Test get_logs with failure response."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        mock_response = Mock()
        mock_response.success = False
        mock_response.error_message = "Container not found"
        self.mock_stub.GetLogs.return_value = mock_response
        
        result = client.get_logs("container-id")
        
        self.assertIsNone(result)

    def test_get_logs_error(self):
        """Test get_logs with exception."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        self.mock_stub.GetLogs.side_effect = Exception("gRPC error")
        
        result = client.get_logs("container-id")
        
        self.assertIsNone(result)

    def test_exec_command_success(self):
        """Test successful exec_command call."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        mock_response = Mock()
        mock_response.output = "Command output"
        mock_response.exit_code = 0
        self.mock_stub.ExecCommand.return_value = mock_response
        
        result = client.exec_command("container-id", ["ls", "-la"])
        
        self.assertEqual(result, mock_response)
        self.mock_stub.ExecCommand.assert_called_once()

    @patch('anvyl.grpc_client.anvyl_pb2.ExecCommandRequest')
    def test_exec_command_with_tty(self, mock_request_class):
        """Test exec_command with TTY parameter."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        mock_request = Mock()
        mock_request.container_id = "container-id"
        mock_request.command = ["bash"]
        mock_request.tty = True
        mock_request_class.return_value = mock_request
        
        mock_response = Mock()
        self.mock_stub.ExecCommand.return_value = mock_response
        
        result = client.exec_command("container-id", ["bash"], tty=True)
        
        self.assertEqual(result, mock_response)
        
        # Verify parameters
        self.mock_stub.ExecCommand.assert_called_once_with(mock_request)
        self.assertEqual(mock_request.container_id, "container-id")
        self.assertEqual(mock_request.command, ["bash"])
        self.assertTrue(mock_request.tty)

    def test_exec_command_error(self):
        """Test exec_command with exception."""
        client = AnvylClient()
        client.stub = self.mock_stub
        
        self.mock_stub.ExecCommand.side_effect = Exception("gRPC error")
        
        result = client.exec_command("container-id", ["ls"])
        
        self.assertIsNone(result)


class TestCreateClientFunction(unittest.TestCase):
    """Test cases for the create_client convenience function."""

    @patch('anvyl.grpc_client.AnvylClient')
    def test_create_client_success(self, mock_client_class):
        """Test successful create_client call."""
        mock_client = Mock()
        mock_client.connect.return_value = True
        mock_client_class.return_value = mock_client
        
        result = create_client("test-host", 9999)
        
        self.assertEqual(result, mock_client)
        mock_client_class.assert_called_once_with("test-host", 9999)
        mock_client.connect.assert_called_once()

    @patch('anvyl.grpc_client.AnvylClient')
    def test_create_client_connection_failure(self, mock_client_class):
        """Test create_client with connection failure."""
        mock_client = Mock()
        mock_client.connect.return_value = False
        mock_client_class.return_value = mock_client
        
        with pytest.raises(ConnectionError) as exc_info:
            create_client("test-host", 9999)
        
        self.assertIn("Failed to connect to Anvyl server", str(exc_info.value))

    @patch('anvyl.grpc_client.AnvylClient')
    def test_create_client_default_params(self, mock_client_class):
        """Test create_client with default parameters."""
        mock_client = Mock()
        mock_client.connect.return_value = True
        mock_client_class.return_value = mock_client
        
        result = create_client()
        
        self.assertEqual(result, mock_client)
        mock_client_class.assert_called_once_with("localhost", 50051)


if __name__ == '__main__':
    unittest.main()