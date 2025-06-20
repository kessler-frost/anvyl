#!/usr/bin/env python3
"""
Containerized AI Agent Example

This example demonstrates how to create, start, and use AI agents
that run in Docker containers for better isolation and persistence.
"""

import time
import subprocess
from rich.console import Console
from rich.panel import Panel

console = Console()

def check_docker():
    """Check if Docker is available."""
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False

def check_infrastructure_service():
    """Check if Anvyl infrastructure service is available."""
    try:
        from anvyl.infrastructure_service import get_infrastructure_service
        service = get_infrastructure_service()
        return True
    except Exception:
        return False

def main():
    """Main example function."""
    console.print(Panel.fit(
        "🐳 Containerized AI Agent Example",
        style="bold blue"
    ))

    # Check prerequisites
    console.print("\n🔍 [bold]Checking prerequisites...[/bold]")

    if not check_docker():
        console.print("❌ [red]Docker is not available. Please install and start Docker.[/red]")
        return

    console.print("✅ [green]Docker is available[/green]")

    if not check_infrastructure_service():
        console.print("❌ [red]Anvyl infrastructure service is not available. Please start it with 'anvyl up'[/red]")
        return

    console.print("✅ [green]Anvyl infrastructure service is available[/green]")

    # Example workflow
    console.print("\n🚀 [bold]Containerized Agent Workflow[/bold]")
    console.print("=" * 50)

    # Step 1: Create an agent
    console.print("\n1️⃣ [bold cyan]Creating AI Agent...[/bold cyan]")
    console.print("   Command: anvyl agent create my-container-agent --provider lmstudio --model llama-3.2-1b-instruct-mlx")

    # Step 2: Start the agent in a container
    console.print("\n2️⃣ [bold cyan]Starting Agent in Container...[/bold cyan]")
    console.print("   Command: anvyl agent start my-container-agent")
    console.print("   This will:")
    console.print("   • Create a Docker image with the agent")
    console.print("   • Start a container running the agent")
    console.print("   • Connect to the infrastructure service")
    console.print("   • Keep the agent running persistently")

    # Step 3: Execute instructions
    console.print("\n3️⃣ [bold cyan]Executing Instructions...[/bold cyan]")
    console.print("   Command: anvyl agent act my-container-agent \"List all hosts\"")
    console.print("   This will:")
    console.print("   • Send the instruction to the containerized agent")
    console.print("   • Execute the instruction using the AI model")
    console.print("   • Return the result via infrastructure service")

    # Step 4: View logs
    console.print("\n4️⃣ [bold cyan]Viewing Agent Logs...[/bold cyan]")
    console.print("   Command: anvyl agent logs my-container-agent --follow")
    console.print("   This will show real-time logs from the agent container")

    # Step 5: Stop the agent
    console.print("\n5️⃣ [bold cyan]Stopping the Agent...[/bold cyan]")
    console.print("   Command: anvyl agent stop my-container-agent")
    console.print("   This will stop and remove the container")

    # Benefits
    console.print("\n🎯 [bold]Benefits of Containerized Agents[/bold]")
    console.print("=" * 50)
    console.print("✅ [green]Isolation:[/green] Each agent runs in its own container")
    console.print("✅ [green]Persistence:[/green] Agents continue running even if CLI is closed")
    console.print("✅ [green]Scalability:[/green] Multiple agents can run simultaneously")
    console.print("✅ [green]Resource Management:[/green] Easy to monitor and control resources")
    console.print("✅ [green]Portability:[/green] Agents can run on any system with Docker")
    console.print("✅ [green]Reliability:[/green] Container restart on failures")

    # Available commands
    console.print("\n📋 [bold]Available Commands[/bold]")
    console.print("=" * 50)
    console.print("anvyl agent create <name>     - Create a new agent configuration")
    console.print("anvyl agent start <name>      - Start agent in container")
    console.print("anvyl agent stop <name>       - Stop agent container")
    console.print("anvyl agent act <name> <cmd>  - Execute instruction")
    console.print("anvyl agent logs <name>       - View agent logs")
    console.print("anvyl agent list              - List all agents")
    console.print("anvyl agent info <name>       - Show agent details")
    console.print("anvyl agent remove <name>     - Remove agent and container")

    # Example usage
    console.print("\n💡 [bold]Example Usage[/bold]")
    console.print("=" * 50)
    console.print("# Create and start an agent")
    console.print("anvyl agent create my-agent --provider lmstudio --auto-start")
    console.print("")
    console.print("# Create agent with custom provider settings")
    console.print("anvyl agent create my-agent --provider ollama --model llama3.2:1b --provider-host localhost --provider-port 11434")
    console.print("")
    console.print("# Execute some instructions")
    console.print("anvyl agent act my-agent \"Show me all hosts\"")
    console.print("anvyl agent act my-agent \"Create a nginx container\"")
    console.print("anvyl agent act my-agent \"What's the system status?\"")
    console.print("")
    console.print("# Monitor the agent")
    console.print("anvyl agent logs my-agent --follow")
    console.print("")
    console.print("# Clean up")
    console.print("anvyl agent stop my-agent")
    console.print("anvyl agent remove my-agent")

if __name__ == "__main__":
    main()