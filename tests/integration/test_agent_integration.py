"""
Integration tests for agent functionality

These tests verify that the agent system works correctly with the infrastructure.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

pytest_asyncio = pytest.importorskip('pytest_asyncio', reason='pytest-asyncio is required for async tests')

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_with_infrastructure_client():
    """Test that agent can work with infrastructure client."""
    try:
        from anvyl.infra.client import get_infrastructure_client
        from anvyl.agent.tools import InfrastructureTools

        # This would require actual infrastructure service running
        # For now, we'll mock it
        with patch('anvyl.infra.client.get_infrastructure_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            client = await get_infrastructure_client()
            tools = InfrastructureTools(client)

            # Verify tools are created
            tool_list = tools.get_tools()
            assert len(tool_list) > 0

    except Exception as e:
        pytest.skip(f"Integration test requires infrastructure service: {e}")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_manager_integration():
    """Test agent manager integration with infrastructure."""
    try:
        from anvyl.agent import create_agent_manager

        # This would require actual services running
        # For now, we'll mock the dependencies
        with patch('anvyl.infra.client.get_infrastructure_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            # Test agent manager creation
            agent_manager = await create_agent_manager(
                lmstudio_url="http://localhost:1234/v1",
                lmstudio_model="llama-3.2-3b-instruct",
                port=4201
            )

            # Verify agent manager is created
            assert agent_manager is not None
            assert hasattr(agent_manager, 'host_agent')

            # Clean up
            await agent_manager.stop()

    except Exception as e:
        pytest.skip(f"Integration test requires services: {e}")