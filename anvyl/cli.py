#!/usr/bin/env python3
"""
Anvyl CLI - Command Line Interface for Anvyl Infrastructure Orchestrator

This module provides a comprehensive CLI for managing Anvyl infrastructure,
including hosts, containers, agents, and monitoring capabilities.
"""

import typer
import json
import os
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.tree import Tree
import sys
import logging
import docker

from .infrastructure_service import get_infrastructure_service
from .database.models import DatabaseManager

# Initialize rich console
console = Console()
app = typer.Typer(help="Anvyl Infrastructure Orchestrator CLI")

def get_infrastructure():
    """Get the infrastructure service instance."""
    try:
        return get_infrastructure_service()
    except Exception as e:
        console.print(f"[red]Error initializing infrastructure service: {e}[/red]")
        raise typer.Exit(1)

def get_project_root() -> str:
    """Get the project root directory."""
    # Look for key files that indicate this is the project root
    current_dir = os.getcwd()
    while current_dir != "/":
        if all(os.path.exists(os.path.join(current_dir, f)) for f in ["anvyl", "ui", "pyproject.toml"]):
            return current_dir
        current_dir = os.path.dirname(current_dir)

    # If not found, assume current directory
    return os.getcwd()

# UI and Infrastructure Management Commands
@app.command("up")
def start_infrastructure(
    build: bool = typer.Option(True, "--build/--no-build", help="Build Docker images before starting"),
    ui_only: bool = typer.Option(False, "--ui-only", help="Start only UI components"),
    logs: bool = typer.Option(False, "--logs", "-l", help="Show logs after starting")
):
    """Start the Anvyl infrastructure stack (UI)."""
    project_root = get_project_root()

    try:
        console.print("🚀 [bold blue]Starting Anvyl Infrastructure Stack[/bold blue]")

        if build and not ui_only:
            console.print("\n📦 Building Docker images...")
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Building images...", total=None)

                # Build UI images using docker-compose
                import subprocess
                result = subprocess.run(
                    ["docker-compose", "-f", os.path.join(project_root, "ui", "docker-compose.yml"), "build"],
                    cwd=os.path.join(project_root, "ui"),
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    console.print(f"[red]Failed to build images: {result.stderr}[/red]")
                    raise typer.Exit(1)

            console.print("✅ [green]Images built successfully[/green]")

        console.print("\n🏗️ Deploying infrastructure stack...")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Starting services...", total=None)

            # Start UI stack using docker-compose
            import subprocess
            result = subprocess.run(
                ["docker-compose", "-f", os.path.join(project_root, "ui", "docker-compose.yml"), "up", "-d"],
                cwd=os.path.join(project_root, "ui"),
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                console.print(f"[red]Failed to start services: {result.stderr}[/red]")
                raise typer.Exit(1)

        console.print("\n✅ [bold green]Anvyl infrastructure started successfully![/bold green]")
        console.print("\n🌐 [bold]Access Points:[/bold]")
        console.print("  • Web UI:      http://localhost:3000")
        console.print("  • API Server:  http://localhost:8000")

        if logs:
            console.print("\n📋 Use 'anvyl logs' to view container logs")
            console.print("💡 Use 'anvyl down' to stop the stack")

    except Exception as e:
        console.print(f"[red]Error starting infrastructure: {e}[/red]")
        raise typer.Exit(1)

@app.command("down")
def stop_infrastructure():
    """Stop the Anvyl infrastructure stack."""
    project_root = get_project_root()

    try:
        console.print("🛑 [bold red]Stopping Anvyl Infrastructure Stack[/bold red]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Stopping services...", total=None)

            # Stop UI stack using docker-compose
            import subprocess
            result = subprocess.run(
                ["docker-compose", "-f", os.path.join(project_root, "ui", "docker-compose.yml"), "down"],
                cwd=os.path.join(project_root, "ui"),
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                console.print(f"[red]Failed to stop services: {result.stderr}[/red]")
                raise typer.Exit(1)

        console.print("✅ [bold green]Infrastructure stack stopped successfully![/bold green]")

    except Exception as e:
        console.print(f"[red]Error stopping infrastructure: {e}[/red]")
        raise typer.Exit(1)

@app.command("ps")
def list_infrastructure():
    """Show status of Anvyl infrastructure containers."""
    try:
        infrastructure = get_infrastructure()

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Getting container status...", total=None)
            containers = infrastructure.list_containers()

        # Filter UI-related containers
        ui_containers = [c for c in containers if "ui" in c.get("name", "").lower() or "frontend" in c.get("name", "").lower() or "backend" in c.get("name", "").lower()]

        # Show services status
        services_table = Table(title="Anvyl Services")
        services_table.add_column("Service", style="cyan")
        services_table.add_column("Status", style="bold")
        services_table.add_column("Details", style="dim")

        # Add UI services
        for container in ui_containers:
            service_name = container.get("name", "unknown")
            status = container.get("status", "unknown")
            status_style = "green" if status == "running" else "red"
            status_text = f"[{status_style}]{status}[/{status_style}]"
            details = f"Container: {container.get('id', 'unknown')[:12]}"

            services_table.add_row(service_name, status_text, details)

        console.print(services_table)

        # Show containers details if any are running
        if ui_containers:
            containers_table = Table(title="Container Details")
            containers_table.add_column("ID", style="cyan")
            containers_table.add_column("Name", style="green")
            containers_table.add_column("Status", style="bold")
            containers_table.add_column("Image", style="blue")

            for container in ui_containers:
                status_style = "green" if container.get("status") == "running" else "red"
                status_text = f"[{status_style}]{container.get('status', 'unknown')}[/{status_style}]"

                containers_table.add_row(
                    container.get("id", "")[:12],
                    container.get("name", "unknown"),
                    status_text,
                    container.get("image", "unknown")
                )

            console.print(containers_table)

    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")
        raise typer.Exit(1)

@app.command("logs")
def show_logs(
    service: Optional[str] = typer.Argument(None, help="Service name (frontend, backend)"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow logs"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines to show")
):
    """Show logs from Anvyl infrastructure containers."""
    try:
        infrastructure = get_infrastructure()
        containers = infrastructure.list_containers()

        # Filter UI-related containers
        ui_containers = [c for c in containers if "ui" in c.get("name", "").lower() or "frontend" in c.get("name", "").lower() or "backend" in c.get("name", "").lower()]

        if service:
            # Show logs for specific service
            target_container = None
            for container in ui_containers:
                if service.lower() in container.get("name", "").lower():
                    target_container = container
                    break

            if not target_container:
                console.print(f"[red]Service '{service}' not found[/red]")
                raise typer.Exit(1)

            console.print(f"📋 [bold]Logs for {target_container['name']}:[/bold]")
            logs = infrastructure.get_logs(target_container["id"], tail=tail, follow=follow)
            if logs:
                console.print(logs)
            else:
                console.print("[yellow]No logs available[/yellow]")

        else:
            # Show logs for all services
            for container in ui_containers:
                console.print(f"\n📋 [bold]Logs for {container['name']}:[/bold]")
                logs = infrastructure.get_logs(container["id"], tail=tail, follow=follow)
                if logs:
                    console.print(logs)
                else:
                    console.print("[yellow]No logs available[/yellow]")

    except Exception as e:
        console.print(f"[red]Error showing logs: {e}[/red]")
        raise typer.Exit(1)

# Host Management Commands
host_app = typer.Typer(help="Host management commands")
app.add_typer(host_app, name="host")

@host_app.command("list")
def list_hosts(
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json")
):
    """List all registered hosts."""
    try:
        infrastructure = get_infrastructure()
        hosts = infrastructure.list_hosts()

        if output == "json":
            console.print(json.dumps(hosts, indent=2))
            return

        if not hosts:
            console.print("[yellow]No hosts found[/yellow]")
            return

        table = Table(title="Registered Hosts")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("IP", style="blue")
        table.add_column("OS", style="yellow")
        table.add_column("Status", style="bold")
        table.add_column("Tags", style="dim")

        for host in hosts:
            status_style = "green" if host.get("status") == "online" else "red"
            status_text = f"[{status_style}]{host.get('status', 'unknown')}[/{status_style}]"
            tags = ", ".join(host.get("tags", []))

            table.add_row(
                host.get("id", "")[:8],
                host.get("name", "unknown"),
                host.get("ip", "unknown"),
                host.get("os", "unknown"),
                status_text,
                tags
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing hosts: {e}[/red]")
        raise typer.Exit(1)

@host_app.command("add")
def add_host(
    name: str = typer.Argument(..., help="Host name"),
    ip: str = typer.Argument(..., help="Host IP address"),
    os: str = typer.Option("", "--os", help="Operating system"),
    tags: List[str] = typer.Option([], "--tag", "-t", help="Host tags (can be used multiple times)")
):
    """Add a new host to the system."""
    try:
        infrastructure = get_infrastructure()
        host = infrastructure.add_host(name, ip, os, tags)

        if host:
            console.print(f"✅ [green]Host '{name}' added successfully[/green]")
            console.print(f"   ID: {host.get('id', 'unknown')}")
            console.print(f"   IP: {host.get('ip', 'unknown')}")
            console.print(f"   Status: {host.get('status', 'unknown')}")
        else:
            console.print("[red]Failed to add host[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error adding host: {e}[/red]")
        raise typer.Exit(1)

@host_app.command("metrics")
def get_host_metrics(
    host_id: str = typer.Argument(..., help="Host ID"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json")
):
    """Get metrics for a specific host."""
    try:
        infrastructure = get_infrastructure()
        metrics = infrastructure.get_host_metrics(host_id)

        if not metrics:
            console.print("[red]Failed to get host metrics[/red]")
            raise typer.Exit(1)

        if output == "json":
            console.print(json.dumps(metrics, indent=2))
            return

        table = Table(title=f"Host Metrics - {host_id[:8]}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                if "memory" in key.lower():
                    value_str = f"{value} MB"
                elif "disk" in key.lower():
                    value_str = f"{value} GB"
                else:
                    value_str = str(value)
            else:
                value_str = str(value)

            table.add_row(key.replace("_", " ").title(), value_str)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error getting host metrics: {e}[/red]")
        raise typer.Exit(1)

# Container Management Commands
container_app = typer.Typer(help="Container management commands")
app.add_typer(container_app, name="container")

@container_app.command("list")
def list_containers(
    host_id: Optional[str] = typer.Option(None, "--host-id", help="Filter by host ID"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json")
):
    """List containers."""
    try:
        infrastructure = get_infrastructure()
        containers = infrastructure.list_containers(host_id)

        if output == "json":
            console.print(json.dumps(containers, indent=2))
            return

        if not containers:
            console.print("[yellow]No containers found[/yellow]")
            return

        table = Table(title="Containers")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Image", style="blue")
        table.add_column("Status", style="bold")
        table.add_column("Host ID", style="yellow")

        for container in containers:
            status_style = "green" if container.get("status") == "running" else "red"
            status_text = f"[{status_style}]{container.get('status', 'unknown')}[/{status_style}]"

            table.add_row(
                container.get("id", "")[:12],
                container.get("name", "unknown"),
                container.get("image", "unknown"),
                status_text,
                container.get("host_id", "")[:8] if container.get("host_id") else "unknown"
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing containers: {e}[/red]")
        raise typer.Exit(1)

@container_app.command("create")
def create_container(
    name: str = typer.Argument(..., help="Container name"),
    image: str = typer.Argument(..., help="Container image"),
    host_id: Optional[str] = typer.Option(None, "--host-id", help="Target host ID"),
    ports: List[str] = typer.Option([], "--port", "-p", help="Port mappings (e.g., 8080:80)"),
    volumes: List[str] = typer.Option([], "--volume", "-v", help="Volume mounts (e.g., /host:/container)"),
    env: List[str] = typer.Option([], "--env", "-e", help="Environment variables (e.g., KEY=value)"),
    labels: List[str] = typer.Option([], "--label", "-l", help="Labels (e.g., key=value)")
):
    """Create a new container."""
    try:
        infrastructure = get_infrastructure()

        # Convert labels list to dict
        labels_dict = {}
        for label in labels:
            if "=" in label:
                key, value = label.split("=", 1)
                labels_dict[key] = value

        container = infrastructure.add_container(
            name=name,
            image=image,
            host_id=host_id,
            ports=ports,
            volumes=volumes,
            environment=env
        )

        if container:
            console.print(f"✅ [green]Container '{name}' created successfully[/green]")
            console.print(f"   ID: {container.get('id', 'unknown')}")
            console.print(f"   Image: {container.get('image', 'unknown')}")
            console.print(f"   Status: {container.get('status', 'unknown')}")
        else:
            console.print("[red]Failed to create container[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error creating container: {e}[/red]")
        raise typer.Exit(1)

@container_app.command("stop")
def stop_container(
    container_id: str = typer.Argument(..., help="Container ID"),
    timeout: int = typer.Option(10, "--timeout", "-t", help="Stop timeout in seconds")
):
    """Stop a container."""
    try:
        infrastructure = get_infrastructure()
        success = infrastructure.stop_container(container_id, timeout)

        if success:
            console.print(f"✅ [green]Container {container_id[:12]} stopped successfully[/green]")
        else:
            console.print(f"[red]Failed to stop container {container_id[:12]}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error stopping container: {e}[/red]")
        raise typer.Exit(1)

@container_app.command("logs")
def get_container_logs(
    container_id: str = typer.Argument(..., help="Container ID"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines to show")
):
    """Get container logs."""
    try:
        infrastructure = get_infrastructure()
        logs = infrastructure.get_logs(container_id, tail=tail, follow=follow)

        if logs:
            console.print(logs)
        else:
            console.print("[yellow]No logs available[/yellow]")

    except Exception as e:
        console.print(f"[red]Error getting container logs: {e}[/red]")
        raise typer.Exit(1)

@container_app.command("exec")
def exec_command(
    container_id: str = typer.Argument(..., help="Container ID"),
    command: List[str] = typer.Argument(..., help="Command to execute"),
    tty: bool = typer.Option(False, "--tty", "-t", help="Allocate a pseudo-TTY")
):
    """Execute a command in a container."""
    try:
        infrastructure = get_infrastructure()
        result = infrastructure.exec_command(container_id, command, tty)

        if result:
            if result["success"]:
                console.print(f"✅ [green]Command executed successfully (exit code: {result['exit_code']})[/green]")
                if result["output"]:
                    console.print(f"\n[bold]Output:[/bold]\n{result['output']}")
            else:
                console.print(f"[red]Command failed (exit code: {result['exit_code']})[/red]")
                if result["output"]:
                    console.print(f"\n[bold]Output:[/bold]\n{result['output']}")
        else:
            console.print("[red]Failed to execute command[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error executing command: {e}[/red]")
        raise typer.Exit(1)

# Agent Management Commands
agent_app = typer.Typer(help="AI Agent management commands")
app.add_typer(agent_app, name="agent")

@agent_app.command("create")
def agent_create(
    name: str = typer.Argument(..., help="Unique name for the AI agent"),
    provider: str = typer.Option("lmstudio", "--provider", "-pr", help="Model provider (lmstudio, ollama, openai, anthropic)"),
    model_id: str = typer.Option("deepseek/deepseek-r1-0528-qwen3-8b", "--model", "-m", help="Model identifier to use"),
    anvyl_host: str = typer.Option("localhost", "--anvyl-host", help="Anvyl infrastructure service host"),
    anvyl_port: int = typer.Option(50051, "--anvyl-port", help="Anvyl infrastructure service port"),
    provider_host: str = typer.Option("localhost", "--provider-host", help="Model provider host (e.g., Ollama server host)"),
    provider_port: int = typer.Option(None, "--provider-port", help="Model provider port (e.g., Ollama server port)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for cloud providers"),
    auto_start: bool = typer.Option(False, "--start", "-s", help="Automatically start the agent after creation")
):
    """Create a new AI agent configuration."""
    try:
        from .agent_manager import get_agent_manager

        manager = get_agent_manager()

        # Prepare provider kwargs
        provider_kwargs = {}
        if provider == "lmstudio":
            provider_kwargs["lmstudio_host"] = provider_host
            if provider_port:
                provider_kwargs["lmstudio_port"] = provider_port
        elif provider == "ollama":
            provider_kwargs["ollama_host"] = provider_host
            if provider_port:
                provider_kwargs["ollama_port"] = provider_port
        elif provider in ["openai", "anthropic"]:
            if api_key:
                provider_kwargs["api_key"] = api_key
            else:
                console.print("[red]API key required for cloud providers[/red]")
                raise typer.Exit(1)

        # Create agent configuration
        config = manager.create_agent(
            name=name,
            provider=provider,
            model_id=model_id,
            host=anvyl_host,
            port=anvyl_port,
            verbose=verbose,
            **provider_kwargs
        )

        console.print(f"✅ [green]Agent '{name}' created successfully[/green]")
        console.print(f"   Provider: {config.provider}")
        console.print(f"   Model: {config.model_id}")
        console.print(f"   Host: {config.host}:{config.port}")
        console.print(f"   Verbose: {config.verbose}")

        if auto_start:
            console.print("\n🚀 Starting agent...")
            if manager.start_agent(name):
                console.print(f"✅ [green]Agent '{name}' started successfully[/green]")
            else:
                console.print(f"[red]Failed to start agent '{name}'[/red]")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error creating agent: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("start")
def agent_start(
    name: str = typer.Argument(..., help="Name of the AI agent to start")
):
    """Start an AI agent."""
    try:
        from .agent_manager import get_agent_manager

        manager = get_agent_manager()

        console.print(f"🚀 [bold blue]Starting agent '{name}'...[/bold blue]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Starting agent...", total=None)
            success = manager.start_agent(name)

        if success:
            console.print(f"✅ [green]Agent '{name}' started successfully[/green]")

            # Show agent status
            status = manager.get_agent_status(name)
            if status:
                console.print(f"   Status: {status.get('status', 'unknown')}")
                if status.get('container_id'):
                    console.print(f"   Container: {status['container_id'][:12]}")
        else:
            console.print(f"[red]Failed to start agent '{name}'[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error starting agent: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("stop")
def agent_stop(
    name: str = typer.Argument(..., help="Name of the AI agent to stop")
):
    """Stop an AI agent."""
    try:
        from .agent_manager import get_agent_manager

        manager = get_agent_manager()

        console.print(f"🛑 [bold red]Stopping agent '{name}'...[/bold red]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Stopping agent...", total=None)
            success = manager.stop_agent(name)

        if success:
            console.print(f"✅ [green]Agent '{name}' stopped successfully[/green]")
        else:
            console.print(f"[red]Failed to stop agent '{name}'[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error stopping agent: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("logs")
def agent_logs(
    name: str = typer.Argument(..., help="Name of the AI agent to show logs for"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output")
):
    """Show logs for an AI agent."""
    try:
        from .agent_manager import get_agent_manager

        manager = get_agent_manager()

        console.print(f"📋 [bold]Logs for agent '{name}':[/bold]")
        logs = manager.get_agent_logs(name, tail=tail, follow=follow)

        if logs:
            console.print(logs)
        else:
            console.print("[yellow]No logs available[/yellow]")

    except Exception as e:
        console.print(f"[red]Error getting agent logs: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("act")
def agent_act(
    agent_name: str = typer.Argument(..., help="Name of the AI agent to use"),
    instruction: str = typer.Argument(..., help="Natural language instruction for the AI agent to execute")
):
    """Execute an action using an AI agent."""
    try:
        from .agent_manager import get_agent_manager
        from .ai_agent import create_ai_agent

        manager = get_agent_manager()
        config = manager.get_agent_config(agent_name)

        if not config:
            console.print(f"[red]Agent '{agent_name}' not found[/red]")
            raise typer.Exit(1)

        # Check if agent is running
        status = manager.get_agent_status(agent_name)
        if not status or not status.get("running", False):
            console.print(f"[yellow]Agent '{agent_name}' is not running. Starting it...[/yellow]")
            if not manager.start_agent(agent_name):
                console.print(f"[red]Failed to start agent '{agent_name}'[/red]")
                raise typer.Exit(1)

        console.print(f"🤖 [bold blue]Executing instruction with agent '{agent_name}':[/bold blue]")
        console.print(f"   Instruction: {instruction}")

        # Create agent instance and execute instruction
        agent = create_ai_agent(
            model_provider=config.provider,
            model_id=config.model_id,
            host=config.host,
            port=config.port,
            verbose=config.verbose,
            agent_name=agent_name,
            **config.provider_kwargs
        )

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Executing instruction...", total=None)
            result = agent.act(instruction)

        console.print(f"\n✅ [bold green]Result:[/bold green]")
        console.print(result)

    except Exception as e:
        console.print(f"[red]Error executing instruction: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("execute")
def agent_execute(
    agent_name: str = typer.Argument(..., help="Name of the AI agent to use"),
    instruction: str = typer.Argument(..., help="Natural language instruction for the AI agent to execute")
):
    """Execute an instruction using an AI agent (alias for act)."""
    agent_act(agent_name, instruction)

@agent_app.command("session")
def agent_session(
    agent_name: str = typer.Argument(..., help="Name of the AI agent to use")
):
    """Start an interactive session with an AI agent."""
    try:
        from .agent_manager import get_agent_manager
        from .ai_agent import create_ai_agent

        manager = get_agent_manager()
        config = manager.get_agent_config(agent_name)

        if not config:
            console.print(f"[red]Agent '{agent_name}' not found[/red]")
            raise typer.Exit(1)

        # Check if agent is running
        status = manager.get_agent_status(agent_name)
        if not status or not status.get("running", False):
            console.print(f"[yellow]Agent '{agent_name}' is not running. Starting it...[/yellow]")
            if not manager.start_agent(agent_name):
                console.print(f"[red]Failed to start agent '{agent_name}'[/red]")
                raise typer.Exit(1)

        # Create agent instance and start interactive session
        agent = create_ai_agent(
            model_provider=config.provider,
            model_id=config.model_id,
            host=config.host,
            port=config.port,
            verbose=config.verbose,
            agent_name=agent_name,
            **config.provider_kwargs
        )

        console.print(f"🤖 [bold blue]Starting interactive session with agent '{agent_name}':[/bold blue]")
        agent.interactive_action_session()

    except Exception as e:
        console.print(f"[red]Error starting interactive session: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("actions")
def agent_actions(
    agent_name: str = typer.Argument(..., help="Name of the AI agent to query")
):
    """Show available actions for an AI agent."""
    try:
        from .agent_manager import get_agent_manager
        from .ai_agent import create_ai_agent

        manager = get_agent_manager()
        config = manager.get_agent_config(agent_name)

        if not config:
            console.print(f"[red]Agent '{agent_name}' not found[/red]")
            raise typer.Exit(1)

        # Create agent instance and show actions
        agent = create_ai_agent(
            model_provider=config.provider,
            model_id=config.model_id,
            host=config.host,
            port=config.port,
            verbose=config.verbose,
            agent_name=agent_name,
            **config.provider_kwargs
        )

        console.print(f"🤖 [bold blue]Available actions for agent '{agent_name}':[/bold blue]")
        agent._show_available_actions()

    except Exception as e:
        console.print(f"[red]Error getting agent actions: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("list")
def agent_list(
    running_only: bool = typer.Option(False, "--running", "-r", help="Show only running agents"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json")
):
    """List all AI agents."""
    try:
        from .agent_manager import get_agent_manager

        manager = get_agent_manager()
        agents = manager.list_agents()

        if running_only:
            agents = [agent for agent in agents if agent.get("running", False)]

        if output == "json":
            console.print(json.dumps(agents, indent=2))
            return

        if not agents:
            console.print("[yellow]No agents found[/yellow]")
            return

        table = Table(title="AI Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Provider", style="green")
        table.add_column("Model", style="blue")
        table.add_column("Status", style="bold")
        table.add_column("Created", style="dim")

        for agent in agents:
            status_style = "green" if agent.get("running", False) else "red"
            status_text = f"[{status_style}]{agent.get('status', 'unknown')}[/{status_style}]"

            table.add_row(
                agent.get("name", "unknown"),
                agent.get("provider", "unknown"),
                agent.get("model_id", "unknown"),
                status_text,
                agent.get("created_at", "unknown")
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing agents: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("remove")
def agent_remove(
    name: str = typer.Argument(..., help="Name of the AI agent to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Force removal without confirmation"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-accept all prompts")
):
    """Remove an AI agent and its Docker image."""
    try:
        from .agent_manager import get_agent_manager

        manager = get_agent_manager()

        if not force and not yes:
            # Check if agent is running
            status = manager.get_agent_status(name)
            if status and status.get("running", False):
                console.print(f"[yellow bold]⚠️  Warning:[/yellow bold] Agent '[bold]{name}[/bold]' is currently running!")

            console.print(f"[bold red]This will permanently remove agent '[bold]{name}[/bold]' and its Docker image.[/bold red]")
            confirm = typer.confirm(f"[bold]Are you sure you want to proceed?[/bold]", default=True)
            if not confirm:
                console.print("[yellow]Operation cancelled.[/yellow]")
                return

        console.print(f"🗑️ [bold red]Removing agent '[bold]{name}[/bold]'...[/bold red]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Removing agent...", total=None)
            success = manager.remove_agent(name)

        if success:
            console.print(f"✅ [green]Agent '[bold]{name}[/bold]' removed successfully[/green]")
        else:
            console.print(f"[red]Failed to remove agent '[bold]{name}[/bold]'[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error removing agent: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("info")
def agent_info(
    name: str = typer.Argument(..., help="Name of the AI agent to show info for")
):
    """Show detailed information about an AI agent."""
    try:
        from .agent_manager import get_agent_manager

        manager = get_agent_manager()
        config = manager.get_agent_config(name)

        if not config:
            console.print(f"[red]Agent '{name}' not found[/red]")
            raise typer.Exit(1)

        status = manager.get_agent_status(name)

        console.print(f"🤖 [bold blue]Agent Information: {name}[/bold blue]")
        console.print(f"   Provider: {config.provider}")
        console.print(f"   Model: {config.model_id}")
        console.print(f"   Host: {config.host}:{config.port}")
        console.print(f"   Verbose: {config.verbose}")
        console.print(f"   Created: {config.created_at}")

        if status:
            console.print(f"   Status: {status.get('status', 'unknown')}")
            console.print(f"   Running: {status.get('running', False)}")
            if status.get('container_id'):
                console.print(f"   Container: {status['container_id'][:12]}")
            if status.get('started_at'):
                console.print(f"   Started: {status['started_at']}")
            if status.get('stopped_at'):
                console.print(f"   Stopped: {status['stopped_at']}")
            if status.get('exit_code') is not None:
                console.print(f"   Exit Code: {status['exit_code']}")

        if config.provider_kwargs:
            console.print(f"   Provider Config: {config.provider_kwargs}")

    except Exception as e:
        console.print(f"[red]Error getting agent info: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("chat")
def agent_chat_deprecated(
    agent_name: str = typer.Argument(..., help="Name of the AI agent to use"),
    message: str = typer.Argument(..., help="Natural language message for the AI agent")
):
    """Chat with an AI agent (deprecated - use 'act' instead)."""
    console.print("[yellow]Warning: 'chat' is deprecated. Use 'act' instead.[/yellow]")
    agent_act(agent_name, message)

@agent_app.command("interactive")
def agent_interactive_deprecated(
    agent_name: str = typer.Argument(..., help="Name of the AI agent to use")
):
    """Start an interactive chat session with an AI agent (deprecated - use 'session' instead)."""
    console.print("[yellow]Warning: 'interactive' is deprecated. Use 'session' instead.[/yellow]")
    agent_session(agent_name)

@agent_app.command("demo")
def agent_demo(
    agent_name: str = typer.Argument(..., help="Name of the AI agent to use")
):
    """Run a demo with an AI agent."""
    try:
        from .agent_manager import get_agent_manager
        from .ai_agent import create_ai_agent

        manager = get_agent_manager()
        config = manager.get_agent_config(agent_name)

        if not config:
            console.print(f"[red]Agent '{agent_name}' not found[/red]")
            raise typer.Exit(1)

        # Check if agent is running
        status = manager.get_agent_status(agent_name)
        if not status or not status.get("running", False):
            console.print(f"[yellow]Agent '{agent_name}' is not running. Starting it...[/yellow]")
            if not manager.start_agent(agent_name):
                console.print(f"[red]Failed to start agent '{agent_name}'[/red]")
                raise typer.Exit(1)

        # Create agent instance
        agent = create_ai_agent(
            model_provider=config.provider,
            model_id=config.model_id,
            host=config.host,
            port=config.port,
            verbose=config.verbose,
            agent_name=agent_name,
            **config.provider_kwargs
        )

        console.print(f"🎬 [bold blue]Running demo with agent '{agent_name}':[/bold blue]")

        # Demo instructions
        demo_instructions = [
            "Show me all hosts",
            "List running containers",
            "Get system status"
        ]

        for instruction in demo_instructions:
            console.print(f"\n🤖 [bold]Demo: {instruction}[/bold]")
            result = agent.act(instruction)
            console.print(f"✅ [green]Result:[/green]\n{result}")

        console.print(f"\n🎉 [bold green]Demo completed![/bold green]")

    except Exception as e:
        console.print(f"[red]Error running demo: {e}[/red]")
        raise typer.Exit(1)

# Main status command
@app.command("status")
def status():
    """Show overall system status."""
    try:
        infrastructure = get_infrastructure()

        console.print("📊 [bold blue]Anvyl System Status[/bold blue]")

        # Get system status
        hosts = infrastructure.list_hosts()
        containers = infrastructure.list_containers()
        agents = infrastructure.list_agents()

        # Hosts status
        console.print(f"\n🖥️  [bold]Hosts:[/bold] {len(hosts)} total")
        online_hosts = [h for h in hosts if h.get("status") == "online"]
        console.print(f"   • Online: {len(online_hosts)}")
        console.print(f"   • Offline: {len(hosts) - len(online_hosts)}")

        # Containers status
        console.print(f"\n📦 [bold]Containers:[/bold] {len(containers)} total")
        running_containers = [c for c in containers if c.get("status") == "running"]
        console.print(f"   • Running: {len(running_containers)}")
        console.print(f"   • Stopped: {len(containers) - len(running_containers)}")

        # Agents status
        console.print(f"\n🤖 [bold]Agents:[/bold] {len(agents)} total")
        running_agents = [a for a in agents if a.get("status") == "running"]
        console.print(f"   • Running: {len(running_agents)}")
        console.print(f"   • Stopped: {len(agents) - len(running_agents)}")

        # Show running containers
        if running_containers:
            console.print(f"\n📋 [bold]Running Containers:[/bold]")
            for container in running_containers:
                console.print(f"   • {container.get('name', 'unknown')} ({container.get('image', 'unknown')})")

        # Show running agents
        if running_agents:
            console.print(f"\n🤖 [bold]Running Agents:[/bold]")
            for agent in running_agents:
                console.print(f"   • {agent.get('name', 'unknown')}")

    except Exception as e:
        console.print(f"[red]Error getting system status: {e}[/red]")
        raise typer.Exit(1)

@app.command("version")
def version():
    """Show Anvyl version information."""
    console.print("Anvyl Infrastructure Orchestrator")
    console.print("Version: 0.1.0")
    console.print("Python: 3.12+")

if __name__ == "__main__":
    app()