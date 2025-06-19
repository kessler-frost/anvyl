"""
Unit tests for Anvyl gRPC Server
"""

import unittest
from unittest.mock import Mock, patch
import pytest

# Import the server module
from anvyl_grpc_server import serve


class TestAnvylServerBasics(unittest.TestCase):
    """Basic test cases for Anvyl Server functionality."""

    def test_server_module_imports(self):
        """Test that server module imports correctly."""
        import anvyl_grpc_server
        self.assertTrue(hasattr(anvyl_grpc_server, 'AnvylService'))
        self.assertTrue(hasattr(anvyl_grpc_server, 'serve'))

    @patch('anvyl_grpc_server.anvyl_pb2_grpc')
    @patch('anvyl_grpc_server.grpc')
    @patch('anvyl_grpc_server.futures')
    @patch('anvyl_grpc_server.AnvylService')
    def test_serve_function_basic(self, mock_service, mock_futures, mock_grpc, mock_pb2_grpc):
        """Test basic serve function setup."""
        # Mock the server and its methods
        mock_server = Mock()
        mock_grpc.server.return_value = mock_server
        mock_server.wait_for_termination.side_effect = KeyboardInterrupt()
        
        # Mock the service instance
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance
        
        # Test that serve function handles KeyboardInterrupt gracefully
        try:
            serve()
        except SystemExit:
            pass  # Expected behavior
        
        # Verify server setup calls
        mock_grpc.server.assert_called_once()
        mock_server.add_insecure_port.assert_called_once_with('[::]:50051')
        mock_server.start.assert_called_once()


if __name__ == '__main__':
    unittest.main()