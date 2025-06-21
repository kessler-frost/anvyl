#!/usr/bin/env python3
"""
Manual test script to verify async agent functionality

This is a manual test script that can be run to verify the async agent works correctly.
It requires actual services to be running (LMStudio, infrastructure API, etc.).

Usage:
    python tests/manual/test_async_agent.py
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

async def test_async_agent():
    """Test the async agent functionality."""
    print("🧪 Testing Async Agent Functionality")
    print("=" * 50)

    try:
        # Test infrastructure client
        print("1. Testing infrastructure client...")
        from anvyl.infra.client import get_infrastructure_client
        client = await get_infrastructure_client()
        print("   ✅ Infrastructure client created successfully")

        # Test agent tools
        print("2. Testing agent tools...")
        from anvyl.agent.tools import InfrastructureTools
        tools = InfrastructureTools(client)
        tool_list = tools.get_tools()
        print(f"   ✅ Agent tools created successfully ({len(tool_list)} tools)")

        # Test agent manager creation
        print("3. Testing agent manager creation...")
        from anvyl.agent import create_agent_manager
        agent_manager = await create_agent_manager(
            lmstudio_url="http://localhost:1234/v1",
            lmstudio_model="llama-3.2-3b-instruct",
            port=4201
        )
        print("   ✅ Agent manager created successfully")

        # Test agent info
        print("4. Testing agent info...")
        agent_info = agent_manager.host_agent.get_agent_info()
        print(f"   ✅ Agent info retrieved: {agent_info['host_id']}")

        # Clean up
        await client.close()
        await agent_manager.stop()

        print("\n🎉 All async tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(test_async_agent())
    sys.exit(0 if success else 1)