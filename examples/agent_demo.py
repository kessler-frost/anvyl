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
from anvyl.infrastructure_service import InfrastructureService


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


def demo_remote_queries():
    """Demo remote agent queries."""
    print("\n🌐 Remote Agent Queries Demo")
    print("=" * 50)

    # This would typically be done through the CLI or API
    print("\nTo use the CLI instead:")
    print("1. Start the agent:")
    print("  anvyl agent start --lmstudio-url http://localhost:1234/v1 --model llama-3.2-3b-instruct --port 4200")
    print()
    print("2. Add a remote host:")
    print("  anvyl agent add-host <host_b_id> <host_b_ip> --port 4200")
    print()
    print("3. Query the agent:")
    print("  anvyl agent query 'How many containers are running?' --host-id <host_b_id> --port 4200")
    print()
    print("4. List containers:")
    print("  anvyl agent query 'List all containers' --host-id <host_b_id> --port 4200")


def demo_infrastructure_tools():
    """Demo the infrastructure tools directly."""
    print("\n🔧 Infrastructure Tools Demo")
    print("=" * 50)

    # Get infrastructure service
    infrastructure_service = InfrastructureService()

    # Demo tools
    print("Available infrastructure operations:")
    print()

    # List hosts
    hosts = infrastructure_service.list_hosts()
    print(f"📊 Hosts in network: {len(hosts)}")
    for host in hosts:
        status_emoji = "🟢" if host['status'] == 'online' else "🔴"
        print(f"  {status_emoji} {host['name']} ({host['ip']}) - {host['status']}")

    print()

    # List containers
    containers = infrastructure_service.list_containers()
    print(f"🐳 Containers running: {len(containers)}")
    for container in containers:
        status_emoji = "🟢" if container['status'] == 'running' else "🔴"
        print(f"  {status_emoji} {container['name']} - {container['status']}")

    print()


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