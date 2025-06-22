"""
Test script for Anvyl MCP Server

This script tests the basic functionality of the MCP server
by connecting to it and calling some tools.
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from mcp.client.stdio import stdio_client
    from mcp.client import ClientSession
except ImportError:
    print("❌ MCP client not available. Install with: pip install mcp>=1.0.0")
    sys.exit(1)


async def test_mcp_server():
    """Test the MCP server functionality."""
    print("🧪 Testing Anvyl MCP Server")
    print("=" * 50)
    
    try:
        # Connect to the MCP server
        print("🔌 Connecting to MCP server...")
        async with stdio_client(["python", "-m", "anvyl.mcp.server"]) as (read, write):
            client = ClientSession(read, write)
            
            # Initialize the client
            await client.initialize(
                protocol_version="2024-11-05",
                capabilities={},
                client_info={
                    "name": "anvyl-mcp-test",
                    "version": "0.1.0"
                }
            )
            
            print("✅ Connected to MCP server")
            
            # Test 1: List tools
            print("\n📋 Testing tool listing...")
            tools_result = await client.list_tools()
            print(f"✅ Found {len(tools_result.tools)} tools:")
            for tool in tools_result.tools:
                print(f"  • {tool.name}: {tool.description}")
            
            # Test 2: System status
            print("\n🏥 Testing system status...")
            status_result = await client.call_tool("system_status", {})
            if status_result.content:
                print("✅ System status retrieved:")
                print(status_result.content[0].text)
            else:
                print("❌ No system status content")
            
            # Test 3: List hosts
            print("\n🏠 Testing host listing...")
            hosts_result = await client.call_tool("list_hosts", {})
            if hosts_result.content:
                print("✅ Hosts retrieved:")
                print(hosts_result.content[0].text)
            else:
                print("❌ No hosts content")
            
            # Test 4: List containers
            print("\n🐳 Testing container listing...")
            containers_result = await client.call_tool("list_containers", {"all": True})
            if containers_result.content:
                print("✅ Containers retrieved:")
                print(containers_result.content[0].text)
            else:
                print("❌ No containers content")
            
            print("\n🎉 All tests completed successfully!")
            
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False
    
    return True


def main():
    """Main test function."""
    print("🚀 Starting Anvyl MCP Server Tests")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("anvyl/mcp/server.py"):
        print("❌ MCP server not found. Make sure you're in the project root directory.")
        sys.exit(1)
    
    # Run the tests
    success = asyncio.run(test_mcp_server())
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 