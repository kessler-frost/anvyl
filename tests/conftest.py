"""
Pytest configuration and fixtures
"""

import pytest
import sys
from unittest.mock import Mock

# Mock the generated protobuf modules globally for all tests
sys.modules['generated.anvyl_pb2'] = Mock()
sys.modules['generated.anvyl_pb2_grpc'] = Mock()

@pytest.fixture
def mock_docker_client():
    """Fixture for mocked Docker client."""
    client = Mock()
    client.ping.return_value = True
    client.containers.list.return_value = []
    return client

@pytest.fixture
def mock_grpc_channel():
    """Fixture for mocked gRPC channel."""
    return Mock()

@pytest.fixture
def mock_grpc_stub():
    """Fixture for mocked gRPC stub."""
    return Mock()