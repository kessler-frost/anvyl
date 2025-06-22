#!/usr/bin/env python3
"""
MCP Agent Demo

This script demonstrates how to use the Anvyl MCP agent to interact with
infrastructure tools and execute commands.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from anvyl.agent.communication import AgentCommunication
from anvyl.agent.core import HostAgent
from anvyl.infra.client import InfrastructureTools
from anvyl.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


async def main():
    """Main demo function."""
    print("🚀 [bold blue]Anvyl MCP Agent Demo[/bold blue]")
    print("=" * 40)

    try:
        # Create agent communication
        communication = AgentCommunication(
            host_id="demo-host",
            local_host_ip=settings.agent_host,
            port=settings.agent_port
        )

        # Create infrastructure tools
        tools = InfrastructureTools(settings.mcp_server_url)

        # Create host agent
        agent = HostAgent(
            communication=communication,
            host_ip=settings.agent_host,
            port=settings.agent_port,
            model_provider_url=settings.model_provider_url,
            mcp_server_url=settings.mcp_server_url
        )

        print(f"✅ Created MCP server instance with URL: {settings.mcp_server_url}")
        print(f"🤖 Created agent with model provider: {settings.model_provider_url}")

        # Example queries to test the agent
        test_queries = [
            "List all containers",
            "Show system information",
            "What's the current disk usage?",
            "Start a basic nginx container and show me the logs"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n[bold cyan]Query {i}:[/bold cyan] {query}")
            print("-" * 50)

            try:
                # Execute the query
                result = await agent.process_query(query)

                if result:
                    print(f"✅ [green]Response:[/green]")
                    print(result.output if hasattr(result, 'output') else result)
                else:
                    print("❌ [red]No response received[/red]")

            except Exception as e:
                print(f"❌ [red]Error processing query: {e}[/red]")

            # Small delay between queries
            await asyncio.sleep(1)

        print("\n🎉 [bold green]Demo completed![/bold green]")

    except Exception as e:
        print(f"❌ [red]Demo failed: {e}[/red]")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)