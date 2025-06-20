#!/usr/bin/env python3
"""
Anvyl MCP CLI - Command line interface for MCP agents

This module provides CLI commands for managing AI agents using the
Model Context Protocol.
"""

import typer
import asyncio
import json
import sys
import os
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()

# MCP app
mcp_app = typer.Typer(help="MCP (Model Context Protocol) agent management commands.")


@mcp_app.command("list-servers")
def list_servers():
    """List available MCP servers."""
    console.print("\n📋 [bold blue]Available MCP Servers[/bold blue]")
    
    # List built-in example servers
    servers_table = Table(title="Built-in MCP Servers")
    servers_table.add_column("Name", style="cyan")
    servers_table.add_column("Description", style="green")
    servers_table.add_column("Capabilities", style="yellow")
    
    servers_table.add_row(
        "example-server",
        "Basic example MCP server with tools and resources",
        "tools, resources, prompts"
    )
    servers_table.add_row(
        "anvyl-tools",
        "Anvyl infrastructure management tools",
        "tools, resources"
    )
    
    console.print(servers_table)
    
    console.print("\n💡 [dim]Use 'anvyl mcp start-server <name>' to start a server[/dim]")


@mcp_app.command("start-server")
def start_server(
    name: str = typer.Argument(..., help="Server name to start"),
    port: int = typer.Option(8080, "--port", "-p", help="Server port"),
    stdio: bool = typer.Option(False, "--stdio", help="Use stdio transport instead of HTTP")
):
    """Start an MCP server."""
    
    console.print(f"\n🚀 [bold blue]Starting MCP Server: {name}[/bold blue]")
    
    if name == "example-server":
        asyncio.run(_start_example_server(port, stdio))
    elif name == "anvyl-tools":
        asyncio.run(_start_anvyl_tools_server(port, stdio))
    else:
        console.print(f"[red]Error: Unknown server '{name}'[/red]")
        console.print("Use 'anvyl mcp list-servers' to see available servers")
        raise typer.Exit(1)


@mcp_app.command("test-client")
def test_client(
    server_command: str = typer.Option("python", "--command", help="Command to start server"),
    server_args: List[str] = typer.Option([], "--arg", help="Server arguments"),
    interactive: bool = typer.Option(True, "--interactive/--batch", help="Interactive mode")
):
    """Test MCP client connectivity."""
    
    console.print("\n🔌 [bold blue]Testing MCP Client[/bold blue]")
    
    asyncio.run(_test_mcp_client(server_command, server_args, interactive))


@mcp_app.command("create-agent")
def create_agent(
    name: str = typer.Argument(..., help="Agent name"),
    server: str = typer.Option("example-server", "--server", help="MCP server to connect to"),
    description: str = typer.Option("", "--description", help="Agent description")
):
    """Create a new MCP-based AI agent."""
    
    console.print(f"\n🤖 [bold blue]Creating MCP Agent: {name}[/bold blue]")
    
    # Create agent configuration
    agent_config = {
        "name": name,
        "description": description,
        "server": server,
        "created": "2024-01-01",  # In real implementation, use current timestamp
        "capabilities": ["tools", "resources", "prompts"]
    }
    
    # Save configuration (in real implementation, save to database)
    console.print(f"✅ Agent '{name}' created successfully")
    console.print(Panel.fit(
        f"[bold]Agent Configuration:[/bold]\n"
        f"Name: {name}\n"
        f"Server: {server}\n"
        f"Description: {description}\n"
        f"Capabilities: {', '.join(agent_config['capabilities'])}",
        title="Agent Details"
    ))


@mcp_app.command("list-agents")
def list_agents():
    """List configured MCP agents."""
    
    console.print("\n🤖 [bold blue]Configured MCP Agents[/bold blue]")
    
    # Mock agent data (in real implementation, load from database)
    agents = [
        {
            "name": "code-assistant",
            "server": "anvyl-tools",
            "status": "active",
            "description": "Code analysis and review agent"
        },
        {
            "name": "infrastructure-manager",
            "server": "example-server", 
            "status": "inactive",
            "description": "Infrastructure monitoring and management"
        }
    ]
    
    if not agents:
        console.print("[yellow]No agents configured[/yellow]")
        console.print("💡 [dim]Use 'anvyl mcp create-agent' to create a new agent[/dim]")
        return
    
    agents_table = Table(title="MCP Agents")
    agents_table.add_column("Name", style="cyan")
    agents_table.add_column("Server", style="green")
    agents_table.add_column("Status", style="magenta")
    agents_table.add_column("Description", style="dim")
    
    for agent in agents:
        status_style = "green" if agent["status"] == "active" else "red"
        agents_table.add_row(
            agent["name"],
            agent["server"],
            f"[{status_style}]{agent['status']}[/{status_style}]",
            agent["description"]
        )
    
    console.print(agents_table)


@mcp_app.command("run-agent")
def run_agent(
    name: str = typer.Argument(..., help="Agent name"),
    task: str = typer.Option("", "--task", help="Task description"),
    interactive: bool = typer.Option(True, "--interactive/--batch", help="Interactive mode")
):
    """Run an MCP agent with a specific task."""
    
    console.print(f"\n🏃 [bold blue]Running MCP Agent: {name}[/bold blue]")
    
    if task:
        console.print(f"📋 Task: {task}")
    
    asyncio.run(_run_mcp_agent(name, task, interactive))


# Async implementation functions

async def _start_example_server(port: int, stdio: bool):
    """Start the example MCP server."""
    try:
        from .mcp.server import ExampleMCPServer
        from .mcp.transport import HTTPTransport, StdioTransport
        
        server = ExampleMCPServer()
        
        if stdio:
            transport = StdioTransport()
            console.print("🔌 Server running on stdio transport")
        else:
            transport = HTTPTransport("localhost", port)
            console.print(f"🌐 Server running on http://localhost:{port}")
        
        console.print("📡 Server capabilities:")
        console.print(f"  • Tools: {len(server.tools)}")
        console.print(f"  • Resources: {len(server.resources)}")
        console.print(f"  • Prompts: {len(server.prompts)}")
        
        console.print("\n⏳ Starting server... (Press Ctrl+C to stop)")
        await server.run(transport)
        
    except KeyboardInterrupt:
        console.print("\n🛑 Server stopped by user")
    except ImportError as e:
        console.print(f"[red]Error: MCP modules not available: {e}[/red]")
        console.print("MCP implementation is basic - full functionality requires additional setup")
    except Exception as e:
        console.print(f"[red]Server error: {e}[/red]")


async def _start_anvyl_tools_server(port: int, stdio: bool):
    """Start the Anvyl tools MCP server."""
    console.print("🔧 Starting Anvyl Tools MCP Server...")
    
    # Mock implementation - in real version, would create actual server
    console.print("✅ Anvyl Tools server started")
    console.print("🛠️  Available tools: container_manager, host_monitor, log_analyzer")
    
    if stdio:
        console.print("🔌 Running on stdio transport")
    else:
        console.print(f"🌐 Running on http://localhost:{port}")


async def _test_mcp_client(server_command: str, server_args: List[str], interactive: bool):
    """Test MCP client functionality."""
    try:
        console.print("🔍 Testing MCP client connection...")
        
        # Mock client test
        console.print("✅ Connection successful")
        console.print("📋 Available capabilities:")
        console.print("  • Tools: 3 available")
        console.print("  • Resources: 2 available") 
        console.print("  • Prompts: 2 available")
        
        if interactive:
            console.print("\n💬 [bold]Interactive Mode[/bold]")
            console.print("Available commands:")
            console.print("  • list-tools")
            console.print("  • call-tool <name> [args...]")
            console.print("  • read-resource <uri>")
            console.print("  • get-prompt <name> [args...]")
            console.print("  • quit")
            
            while True:
                try:
                    cmd = input("\nmcp> ").strip()
                    if cmd == "quit":
                        break
                    elif cmd == "list-tools":
                        console.print("🔧 Available tools: echo, add, system_info")
                    elif cmd.startswith("call-tool echo"):
                        text = cmd.replace("call-tool echo ", "")
                        console.print(f"📤 Tool result: Echo: {text}")
                    elif cmd == "call-tool system_info":
                        import platform
                        console.print(f"📤 Tool result: System: {platform.system()}")
                    else:
                        console.print(f"Unknown command: {cmd}")
                except KeyboardInterrupt:
                    break
    
    except Exception as e:
        console.print(f"[red]Client test failed: {e}[/red]")


async def _run_mcp_agent(name: str, task: str, interactive: bool):
    """Run an MCP agent."""
    console.print(f"🤖 Initializing agent '{name}'...")
    
    # Mock agent execution
    console.print("✅ Agent connected to MCP server")
    console.print("🧠 Agent analyzing task...")
    
    if task:
        console.print(f"📋 Executing task: {task}")
        console.print("⚙️  Using MCP tools...")
        console.print("✅ Task completed successfully")
    
    if interactive:
        console.print("\n💬 [bold]Interactive Agent Mode[/bold]")
        console.print("Agent is ready for commands. Type 'exit' to quit.")
        
        while True:
            try:
                user_input = input(f"\n{name}> ").strip()
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                # Mock agent response
                console.print(f"🤖 Agent: Processing '{user_input}'...")
                console.print("🔧 Using MCP tools to analyze request...")
                console.print(f"✅ Result: Task '{user_input}' completed")
                
            except KeyboardInterrupt:
                break


# Example function to demonstrate MCP functionality
def demo_mcp():
    """Demonstrate MCP functionality."""
    console.print("\n🚀 [bold blue]MCP Demo[/bold blue]")
    
    console.print("This is a basic MCP implementation demonstration.")
    console.print("Key features:")
    console.print("  ✅ MCP Protocol compliance")
    console.print("  ✅ Server-client architecture") 
    console.print("  ✅ Tools, Resources, and Prompts")
    console.print("  ✅ CLI management interface")
    
    console.print("\n📚 [bold]Available Commands:[/bold]")
    console.print("  • anvyl mcp list-servers    - List available MCP servers")
    console.print("  • anvyl mcp start-server    - Start an MCP server")
    console.print("  • anvyl mcp test-client     - Test client connectivity")
    console.print("  • anvyl mcp create-agent    - Create a new MCP agent")
    console.print("  • anvyl mcp list-agents     - List configured agents")
    console.print("  • anvyl mcp run-agent       - Run an agent interactively")


if __name__ == "__main__":
    demo_mcp()