#!/usr/bin/env python3
"""
Anvyl AI Agent Demo

This script demonstrates how to use the Anvyl AI agent system
for distributed infrastructure management.
"""

import asyncio
import os
import sys
import time
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from anvyl.agent import create_agent_manager
from anvyl.infra.infrastructure_client import get_infrastructure_client


async def demo_local_agent():
    """Demo the local agent capabilities."""
    print("🤖 Anvyl AI Agent Demo - Local Agent")
    print("=" * 50)

    # Start the agent
    print("Starting agent...")
    agent_manager = create_agent_manager(
        lmstudio_url="http://localhost:1234/v1",
        lmstudio_model="llama-3.2-3b-instruct",
        port=4200
    )

    # Demo queries
    demo_queries = [
        "List all containers on this host",
        "Get current host resources",
        "Show information about this host",
        "List all hosts in the network"
    ]

    print("📋 Demo Queries:")
    for i, query in enumerate(demo_queries, 1):
        print(f"  {i}. {query}")

    print("\n🚀 Starting agent server...")
    print("   (Press Ctrl+C to stop)")
    print()

    # Start the agent server
    try:
        await agent_manager.start()
    except KeyboardInterrupt:
        print("\n🛑 Agent stopped by user")


def demo_infrastructure_tools():
    """Demo the infrastructure tools directly."""
    print("🔧 Infrastructure Tools Demo")
    print("=" * 40)

    try:
        # Get infrastructure client
        client = get_infrastructure_client()

        # Demo container listing
        print("\n📦 Container Management:")
        containers = client.list_containers()
        if containers:
            for container in containers[:3]:  # Show first 3
                print(f"  - {container['name']} ({container['status']})")
        else:
            print("  No containers found")

        # Demo host listing
        print("\n🖥️  Host Management:")
        hosts = client.list_hosts()
        if hosts:
            for host in hosts:
                print(f"  - {host['name']} ({host['ip']}) - {host['status']}")
        else:
            print("  No hosts found")

    except Exception as e:
        print(f"  Error: {e}")


def demo_remote_queries():
    """Demo remote agent queries."""
    print("\n🌐 Remote Agent Queries Demo")
    print("=" * 40)

    print("To test remote queries, you need:")
    print("1. Multiple hosts running Anvyl agents")
    print("2. Network connectivity between hosts")
    print("3. Known host configurations")

    print("\nExample setup:")
    print("  # On Host A")
    print("  anvyl agent start --port 4200")
    print("  anvyl agent add-host host-b 192.168.1.101")
    print("")
    print("  # On Host B")
    print("  anvyl agent start --port 4201")
    print("  anvyl agent add-host host-a 192.168.1.100")
    print("")
    print("  # Query from Host A to Host B")
    print("  anvyl agent query-remote host-b 'List all containers'")


def main():
    """Main demo function."""
    print("🚀 Anvyl AI Agent System Demo")
    print("=" * 60)
    print()

    # Check if LMStudio is available
    lmstudio_url = "http://localhost:1234/v1"
    try:
        import requests
        response = requests.get(f"{lmstudio_url}/models", timeout=5)
        if response.status_code == 200:
            print("✅ [green]LMStudio is running and accessible[/green]")
        else:
            print("⚠️  Warning: LMStudio is running but may not be serving models")
    except Exception as e:
        print("⚠️  Warning: LMStudio not accessible")
        print(f"   Error: {e}")
        print("   The agent will run in mock mode with limited functionality")
        print("   Start LMStudio and load a model for full AI capabilities")
        print()

    # Demo infrastructure tools
    demo_infrastructure_tools()

    # Demo remote queries
    demo_remote_queries()

    # Ask user if they want to start the agent
    print("🤖 Would you like to start the AI agent server? (y/n): ", end="")
    response = input().lower().strip()

    if response in ['y', 'yes']:
        print()
        asyncio.run(demo_local_agent())
    else:
        print("\n✅ Demo completed. Use 'anvyl agent start' to start the agent manually.")


if __name__ == "__main__":
    main()