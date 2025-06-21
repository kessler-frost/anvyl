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
import requests
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from anvyl.agent.server import start_agent_server
from anvyl.infra.client import get_infrastructure_client


def check_infrastructure_api(infrastructure_api_url: str) -> bool:
    """Check if the infrastructure API is available."""
    try:
        response = requests.get(f"{infrastructure_api_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ [green]Infrastructure API is running and accessible[/green]")
            return True
        else:
            print("⚠️  Warning: Infrastructure API not accessible")
            return False
    except Exception as e:
        print("⚠️  Warning: Infrastructure API not accessible")
        print("   Start the infrastructure API with 'anvyl infra up'")
        return False


def check_model_provider(model_provider_url: str) -> bool:
    """Check if the model provider is available."""
    try:
        response = requests.get(f"{model_provider_url}/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            if models and "data" in models and models["data"]:
                print("✅ [green]Model provider is running and accessible[/green]")
                return True
            else:
                print("⚠️  Warning: Model provider is running but may not be serving models")
                return False
        else:
            print("⚠️  Warning: Model provider not accessible")
            return False
    except Exception as e:
        print("⚠️  Warning: Model provider not accessible")
        print("   Start a model provider and load a model for full AI capabilities")
        return False


def create_agent(infrastructure_api_url: str, model_provider_url: str):
    """Create an agent instance for demo purposes."""
    # This is a placeholder - in a real demo, you might want to create an agent instance
    # For now, we'll just return a dict with the configuration
    return {
        "infrastructure_api_url": infrastructure_api_url,
        "model_provider_url": model_provider_url
    }


def run_demo(agent):
    """Run the demo with the created agent."""
    print("🤖 Anvyl AI Agent Demo")
    print("=" * 50)

    print(f"🏗️  Infrastructure API: {agent['infrastructure_api_url']}")
    print(f"🧠 Model Provider: {agent['model_provider_url']}")
    print()

    print("📋 Demo Queries:")
    demo_queries = [
        "List all containers on this host",
        "Get current host resources",
        "Show information about this host",
        "List all hosts in the network"
    ]

    for i, query in enumerate(demo_queries, 1):
        print(f"  {i}. {query}")

    print("\n🚀 Starting agent server...")
    print("   (Press Ctrl+C to stop)")
    print()

    # Start the agent server
    try:
        start_agent_server(
            port=4201,
            infrastructure_api_url=agent['infrastructure_api_url'],
            model_provider_url=agent['model_provider_url']
        )
    except KeyboardInterrupt:
        print("\n🛑 Agent stopped by user")


async def demo_local_agent():
    """Demo the local agent capabilities."""
    print("🤖 Anvyl AI Agent Demo - Local Agent")
    print("=" * 50)

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
        start_agent_server(
            port=4201,
            model_provider_url="http://localhost:11434/v1",
            infrastructure_api_url="http://localhost:4200"
        )
    except KeyboardInterrupt:
        print("\n🛑 Agent stopped by user")


async def demo_infrastructure_tools():
    """Demo the infrastructure tools directly."""
    print("🔧 Infrastructure Tools Demo")
    print("=" * 40)

    try:
        # Get infrastructure client
        client = await get_infrastructure_client()

        # Demo container listing
        print("\n📦 Container Management:")
        containers = await client.list_containers()
        if containers:
            for container in containers[:3]:  # Show first 3
                print(f"  - {container['name']} ({container['status']})")
        else:
            print("  No containers found")

        # Demo host listing
        print("\n🖥️  Host Management:")
        hosts = await client.list_hosts()
        if hosts:
            for host in hosts:
                print(f"  - {host['name']} ({host['ip']}) - {host['status']}")
        else:
            print("  No hosts found")

        await client.close()

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
    print("  anvyl agent up --port 4201")
    print("  anvyl agent add-host host-b 192.168.1.101")
    print("")
    print("  # On Host B")
    print("  anvyl agent up --port 4202")
    print("  anvyl agent add-host host-a 192.168.1.100")
    print("")
    print("  # Query from Host A to Host B")
    print("  anvyl agent query host-b 'List all containers'")


def main():
    """Main demo function."""
    print("🚀 [bold blue]Anvyl AI Agent Demo[/bold blue]")
    print()

    # Configuration
    infrastructure_api_url = "http://localhost:4200"
    model_provider_url = "http://localhost:11434/v1"

    print(f"🏗️  Infrastructure API: {infrastructure_api_url}")
    print(f"🧠 Model Provider: {model_provider_url}")
    print()

    # Check if infrastructure API is available
    if not check_infrastructure_api(infrastructure_api_url):
        print("❌ Infrastructure API not available. Please start it with 'anvyl infra up'")
        return

    # Check if model provider is available
    if not check_model_provider(model_provider_url):
        print("⚠️  Model provider not available. Agent will use mock responses.")
        print("   Start a model provider for full AI capabilities")

    # Create and start the agent
    try:
        agent = create_agent(
            infrastructure_api_url=infrastructure_api_url,
            model_provider_url=model_provider_url
        )

        # Run the demo
        run_demo(agent)

    except Exception as e:
        print(f"❌ Error: {e}")
        return


if __name__ == "__main__":
    main()