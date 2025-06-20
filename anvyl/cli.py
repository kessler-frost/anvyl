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

from .grpc_client import AnvylClient
from .database.models import DatabaseManager

# Ensure protobuf files are generated automatically
from .proto_utils import ensure_protos_generated
ensure_protos_generated()

# Initialize rich console
console = Console()
app = typer.Typer(help="Anvyl Infrastructure Orchestrator CLI")

# Global client variable
_client: Optional[AnvylClient] = None

def get_client(host: str = "localhost", port: int = 50051) -> AnvylClient:
    """Get or create the global client instance."""
    global _client
    if _client is None:
        try:
            _client = AnvylClient(host, port)
            if not _client.connect():
                raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Error connecting to Anvyl server at {host}:{port}[/red]")
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)
    return _client

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
    """Start the Anvyl infrastructure stack (gRPC server + UI)."""
    project_root = get_project_root()

    try:
        # Create a client for Docker operations (no gRPC connection needed yet)
        client = AnvylClient()

        console.print("🚀 [bold blue]Starting Anvyl Infrastructure Stack[/bold blue]")

        if build and not ui_only:
            console.print("\n📦 Building Docker images...")
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Building images...", total=None)
                build_results = client.build_ui_images(project_root)

            # Show build results
            build_table = Table(title="Build Results")
            build_table.add_column("Image", style="cyan")
            build_table.add_column("Status", style="bold")

            for image, success in build_results.items():
                status = "[green]✓ Success[/green]" if success else "[red]✗ Failed[/red]"
                build_table.add_row(image, status)

            console.print(build_table)

            # Check if all builds succeeded
            if not all(build_results.values()):
                console.print("[red]Some images failed to build. Check Docker logs for details.[/red]")
                raise typer.Exit(1)

        console.print("\n🏗️ Deploying infrastructure stack...")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Starting services...", total=None)
            success = client.deploy_ui_stack(project_root)

        if success:
            console.print("\n✅ [bold green]Anvyl infrastructure started successfully![/bold green]")
            console.print("\n🌐 [bold]Access Points:[/bold]")
            console.print("  • Web UI:      http://localhost:3000")
            console.print("  • API Server:  http://localhost:8000")
            console.print("  • gRPC Server: localhost:50051")

            if logs:
                console.print("\n📋 Use 'anvyl logs' to view container logs")
                console.print("💡 Use 'anvyl down' to stop the stack")
        else:
            console.print("[red]✗ Failed to start infrastructure stack[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error starting infrastructure: {e}[/red]")
        raise typer.Exit(1)

@app.command("down")
def stop_infrastructure():
    """Stop the Anvyl infrastructure stack."""
    project_root = get_project_root()

    try:
        client = AnvylClient()

        console.print("🛑 [bold red]Stopping Anvyl Infrastructure Stack[/bold red]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Stopping services...", total=None)
            success = client.stop_ui_stack(project_root)

        if success:
            console.print("✅ [bold green]Infrastructure stack stopped successfully![/bold green]")
        else:
            console.print("[red]✗ Failed to stop infrastructure stack[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error stopping infrastructure: {e}[/red]")
        raise typer.Exit(1)

@app.command("ps")
def list_infrastructure():
    """Show status of Anvyl infrastructure containers."""
    try:
        client = AnvylClient()

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Getting container status...", total=None)
            status = client.get_ui_stack_status()

        if "error" in status:
            console.print(f"[red]Error getting status: {status['error']}[/red]")
            raise typer.Exit(1)

        # Show services status
        services_table = Table(title="Anvyl Services")
        services_table.add_column("Service", style="cyan")
        services_table.add_column("Status", style="bold")
        services_table.add_column("Details", style="dim")

        for service_name, service_info in status["services"].items():
            status_style = "green" if service_info["status"] == "running" else "red"
            status_text = f"[{status_style}]{service_info['status']}[/{status_style}]"

            # Handle different service types
            if service_name == "grpc-server":
                if service_info["process"]:
                    details = f"PID: {service_info['process']['pid']} (Python)"
                else:
                    details = "Not running"
            elif service_info["container"]:
                details = service_info["container"]["name"]
            else:
                details = "Not running"

            services_table.add_row(service_name, status_text, details)

        console.print(services_table)

        # Show containers details if any are running
        if status["containers"]:
            containers_table = Table(title="Container Details")
            containers_table.add_column("ID", style="cyan")
            containers_table.add_column("Name", style="green")
            containers_table.add_column("Status", style="bold")
            containers_table.add_column("Ports", style="blue")

            for container in status["containers"]:
                ports = []
                for port_config in container.get("ports", {}).values():
                    if port_config:
                        for port_info in port_config:
                            host_port = port_info.get("HostPort", "")
                            if host_port:
                                ports.append(f"{host_port}:{port_info.get('HostIp', '0.0.0.0')}")

                status_style = "green" if container["status"] == "running" else "red"
                status_text = f"[{status_style}]{container['status']}[/{status_style}]"

                containers_table.add_row(
                    container["id"],
                    container["name"],
                    status_text,
                    ", ".join(ports) if ports else "None"
                )

            console.print(containers_table)
        else:
            console.print("\n[yellow]No Anvyl containers running[/yellow]")
            console.print("💡 Use 'anvyl up' to start the infrastructure")

    except Exception as e:
        console.print(f"[red]Error getting infrastructure status: {e}[/red]")
        raise typer.Exit(1)

@app.command("logs")
def show_logs(
    service: Optional[str] = typer.Argument(None, help="Service name (frontend, backend, grpc-server)"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow logs"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines to show")
):
    """Show logs from Anvyl infrastructure containers and processes."""
    try:
        project_root = get_project_root()
        ui_dir = os.path.join(project_root, "ui")

        if service and service in ["grpc-server", "grpc"]:
            # Handle gRPC server logs (Python process)
            console.print(f"📋 [bold]Logs for gRPC server (Python process):[/bold]")
            console.print("[yellow]Note: gRPC server logs are displayed in the terminal where it was started[/yellow]")
            console.print("[yellow]To see gRPC server logs, start it manually with: python -m anvyl.grpc_server[/yellow]")
            return

        # Use Docker SDK to get container logs
        client = docker.from_env()

        if service:
            service_map = {
                "frontend": "anvyl-ui-frontend",
                "backend": "anvyl-ui-backend"
            }

            container_name = service_map.get(service, service)

            try:
                # Find container by name
                containers = client.containers.list(filters={"name": container_name})
                if not containers:
                    console.print(f"[red]Container '{container_name}' not found[/red]")
                    return

                container = containers[0]
                console.print(f"📋 [bold]Logs for {service}:[/bold]")

                if follow:
                    for log in container.logs(stream=True, tail=tail):
                        console.print(log.decode('utf-8'), end='')
                else:
                    logs = container.logs(tail=tail).decode('utf-8')
                    console.print(logs)

            except Exception as e:
                console.print(f"[red]Error getting logs for {service}: {e}[/red]")
                return
        else:
            # Show logs for all Docker services
            try:
                # Find all anvyl containers
                containers = client.containers.list(filters={"label": "anvyl.component"})

                if not containers:
                    console.print("[yellow]No Anvyl containers found[/yellow]")
                    return

                console.print("📋 [bold]Logs for all Docker services:[/bold]")

                for container in containers:
                    service_name = container.labels.get("anvyl.service", "unknown")
                    console.print(f"\n[bold cyan]=== {service_name} ===[/bold cyan]")

                    if follow:
                        for log in container.logs(stream=True, tail=tail):
                            console.print(log.decode('utf-8'), end='')
                    else:
                        logs = container.logs(tail=tail).decode('utf-8')
                        console.print(logs)

            except Exception as e:
                console.print(f"[red]Error getting container logs: {e}[/red]")
                return

            # Add note about gRPC server
            console.print("\n[yellow]Note: gRPC server runs as a Python process, not a Docker container[/yellow]")
            console.print("[yellow]To see gRPC server logs, start it manually with: python -m anvyl.grpc_server[/yellow]")

    except Exception as e:
        console.print(f"[red]Error showing logs: {e}[/red]")
        raise typer.Exit(1)

# Host management commands
host_app = typer.Typer(help="Host management commands.")
app.add_typer(host_app, name="host")

@host_app.command("list")
def list_hosts(
    host: str = typer.Option("localhost", "--host", "-h", help="Anvyl server host"),
    port: int = typer.Option(50051, "--port", "-p", help="Anvyl server port"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json")
):
    """List all registered hosts."""
    client = get_client(host, port)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Fetching hosts...", total=None)
        hosts = client.list_hosts()

    if not hosts:
        console.print("[yellow]No hosts found[/yellow]")
        return

    if output == "json":
        # Convert to serializable format
        hosts_data = []
        for host in hosts:
            host_dict = {
                "id": getattr(host, 'id', ''),
                "name": getattr(host, 'name', ''),
                "ip": getattr(host, 'ip', ''),
                "os": getattr(host, 'os', ''),
                "status": getattr(host, 'status', ''),
                "tags": list(getattr(host, 'tags', []))
            }
            hosts_data.append(host_dict)
        console.print(json.dumps(hosts_data, indent=2))
    else:
        table = Table(title="Anvyl Hosts")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("IP Address", style="blue")
        table.add_column("OS", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Tags", style="dim")

        for host in hosts:
            tags = ", ".join(getattr(host, 'tags', []))
            table.add_row(
                getattr(host, 'id', ''),
                getattr(host, 'name', ''),
                getattr(host, 'ip', ''),
                getattr(host, 'os', ''),
                getattr(host, 'status', ''),
                tags
            )

        console.print(table)

@host_app.command("add")
def add_host(
    name: str = typer.Argument(..., help="Host name"),
    ip: str = typer.Argument(..., help="Host IP address"),
    os: str = typer.Option("", "--os", help="Operating system"),
    tags: List[str] = typer.Option([], "--tag", "-t", help="Host tags (can be used multiple times)"),
    host: str = typer.Option("localhost", "--host", "-h", help="Anvyl server host"),
    port: int = typer.Option(50051, "--port", "-p", help="Anvyl server port")
):
    """Add a new host to the system."""
    client = get_client(host, port)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task(f"Adding host {name}...", total=None)
        result = client.add_host(name, ip, os, tags)

    if result:
        console.print(f"[green]✓[/green] Successfully added host: {name} ({ip})")
    else:
        console.print(f"[red]✗[/red] Failed to add host: {name}")
        raise typer.Exit(1)

@host_app.command("metrics")
def get_host_metrics(
    host_id: str = typer.Argument(..., help="Host ID"),
    host: str = typer.Option("localhost", "--host", "-h", help="Anvyl server host"),
    port: int = typer.Option(50051, "--port", "-p", help="Anvyl server port"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json")
):
    """Get host metrics."""
    client = get_client(host, port)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task(f"Fetching metrics for {host_id}...", total=None)
        metrics = client.get_host_metrics(host_id)

    if not metrics:
        console.print(f"[red]No metrics found for host: {host_id}[/red]")
        raise typer.Exit(1)

    if output == "json":
        metrics_dict = {
            "cpu_count": getattr(metrics, 'cpu_count', 0),
            "memory_total": getattr(metrics, 'memory_total', 0),
            "memory_available": getattr(metrics, 'memory_available', 0),
            "disk_total": getattr(metrics, 'disk_total', 0),
            "disk_available": getattr(metrics, 'disk_available', 0)
        }
        console.print(json.dumps(metrics_dict, indent=2))
    else:
        panel = Panel.fit(
            f"[bold]Host Metrics: {host_id}[/bold]\n\n"
            f"CPU Cores: {getattr(metrics, 'cpu_count', 'N/A')}\n"
            f"Memory Total: {getattr(metrics, 'memory_total', 'N/A')} MB\n"
            f"Memory Available: {getattr(metrics, 'memory_available', 'N/A')} MB\n"
            f"Disk Total: {getattr(metrics, 'disk_total', 'N/A')} GB\n"
            f"Disk Available: {getattr(metrics, 'disk_available', 'N/A')} GB",
            title="Host Metrics"
        )
        console.print(panel)

# Container management commands
container_app = typer.Typer(help="Container management commands.")
app.add_typer(container_app, name="container")

@container_app.command("list")
def list_containers(
    host_id: Optional[str] = typer.Option(None, "--host-id", help="Filter by host ID"),
    host: str = typer.Option("localhost", "--host", "-h", help="Anvyl server host"),
    port: int = typer.Option(50051, "--port", "-p", help="Anvyl server port"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json")
):
    """List containers."""
    client = get_client(host, port)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Fetching containers...", total=None)
        containers = client.list_containers(host_id)

    if not containers:
        console.print("[yellow]No containers found[/yellow]")
        return

    if output == "json":
        containers_data = []
        for container in containers:
            container_dict = {
                "id": getattr(container, 'id', ''),
                "name": getattr(container, 'name', ''),
                "image": getattr(container, 'image', ''),
                "status": getattr(container, 'status', ''),
                "host_id": getattr(container, 'host_id', ''),
                "ports": list(getattr(container, 'ports', [])),
                "labels": dict(getattr(container, 'labels', {}))
            }
            containers_data.append(container_dict)
        console.print(json.dumps(containers_data, indent=2))
    else:
        table = Table(title="Anvyl Containers")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Image", style="blue")
        table.add_column("Status", style="magenta")
        table.add_column("Host", style="yellow")
        table.add_column("Ports", style="dim")

        for container in containers:
            ports = ", ".join(getattr(container, 'ports', []))
            table.add_row(
                getattr(container, 'id', '')[:12],  # Short ID
                getattr(container, 'name', ''),
                getattr(container, 'image', ''),
                getattr(container, 'status', ''),
                getattr(container, 'host_id', ''),
                ports
            )

        console.print(table)

@container_app.command("create")
def create_container(
    name: str = typer.Argument(..., help="Container name"),
    image: str = typer.Argument(..., help="Container image"),
    host_id: Optional[str] = typer.Option(None, "--host-id", help="Target host ID"),
    ports: List[str] = typer.Option([], "--port", "-p", help="Port mappings (e.g., 8080:80)"),
    volumes: List[str] = typer.Option([], "--volume", "-v", help="Volume mounts (e.g., /host:/container)"),
    env: List[str] = typer.Option([], "--env", "-e", help="Environment variables (e.g., KEY=value)"),
    labels: List[str] = typer.Option([], "--label", "-l", help="Labels (e.g., key=value)"),
    host: str = typer.Option("localhost", "--host", "-h", help="Anvyl server host"),
    port: int = typer.Option(50051, "--port", help="Anvyl server port")
):
    """Create a new container."""
    client = get_client(host, port)

    # Parse labels
    labels_dict = {}
    for label in labels:
        if "=" in label:
            key, value = label.split("=", 1)
            labels_dict[key] = value

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task(f"Creating container {name}...", total=None)
        result = client.add_container(
            name=name,
            image=image,
            host_id=host_id,
            labels=labels_dict,
            ports=ports,
            volumes=volumes,
            environment=env
        )

    if result:
        console.print(f"[green]✓[/green] Successfully created container: {name}")
        console.print(f"Container ID: {getattr(result, 'id', 'N/A')}")
    else:
        console.print(f"[red]✗[/red] Failed to create container: {name}")
        raise typer.Exit(1)

@container_app.command("stop")
def stop_container(
    container_id: str = typer.Argument(..., help="Container ID"),
    timeout: int = typer.Option(10, "--timeout", "-t", help="Stop timeout in seconds"),
    host: str = typer.Option("localhost", "--host", "-h", help="Anvyl server host"),
    port: int = typer.Option(50051, "--port", "-p", help="Anvyl server port")
):
    """Stop a container."""
    client = get_client(host, port)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task(f"Stopping container {container_id}...", total=None)
        success = client.stop_container(container_id, timeout)

    if success:
        console.print(f"[green]✓[/green] Successfully stopped container: {container_id}")
    else:
        console.print(f"[red]✗[/red] Failed to stop container: {container_id}")
        raise typer.Exit(1)

@container_app.command("logs")
def get_container_logs(
    container_id: str = typer.Argument(..., help="Container ID"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines to show"),
    host: str = typer.Option("localhost", "--host", "-h", help="Anvyl server host"),
    port: int = typer.Option(50051, "--port", "-p", help="Anvyl server port")
):
    """Get container logs."""
    client = get_client(host, port)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task(f"Fetching logs for {container_id}...", total=None)
        logs = client.get_container_logs(container_id, follow, tail)

    if logs:
        console.print(f"[bold]Logs for container {container_id}:[/bold]")
        console.print(logs)
    else:
        console.print(f"[yellow]No logs found for container: {container_id}[/yellow]")

@container_app.command("exec")
def exec_command(
    container_id: str = typer.Argument(..., help="Container ID"),
    command: List[str] = typer.Argument(..., help="Command to execute"),
    tty: bool = typer.Option(False, "--tty", "-t", help="Allocate a pseudo-TTY"),
    host: str = typer.Option("localhost", "--host", "-h", help="Anvyl server host"),
    port: int = typer.Option(50051, "--port", "-p", help="Anvyl server port")
):
    """Execute a command in a container."""
    client = get_client(host, port)

    cmd_str = " ".join(command)
    console.print(f"[bold]Executing command in {container_id}:[/bold] {cmd_str}")

    result = client.exec_container_command(container_id, command, tty)

    if result:
        console.print(result)
    else:
        console.print(f"[red]Failed to execute command in container: {container_id}[/red]")
        raise typer.Exit(1)

# Agent management commands
agent_app = typer.Typer(help="Agent management commands.")
app.add_typer(agent_app, name="agent")

@agent_app.command("create")
def agent_create(
    name: str = typer.Argument(..., help="Unique name for the AI agent"),
    provider: str = typer.Option("lmstudio", "--provider", "-pr", help="Model provider (lmstudio, ollama, openai, anthropic)"),
    model_id: str = typer.Option("deepseek/deepseek-r1-0528-qwen3-8b", "--model", "-m", help="Model identifier to use"),
    anvyl_host: str = typer.Option("localhost", "--anvyl-host", help="Anvyl gRPC server host"),
    anvyl_port: int = typer.Option(50051, "--anvyl-port", help="Anvyl gRPC server port"),
    provider_host: str = typer.Option("localhost", "--provider-host", help="Model provider host (e.g., Ollama server host)"),
    provider_port: int = typer.Option(None, "--provider-port", help="Model provider port (e.g., Ollama server port)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for cloud providers"),
    auto_start: bool = typer.Option(False, "--start", "-s", help="Automatically start the agent after creation")
):
    """Create a new AI agent with specified configuration."""
    try:
        from .agent_manager import get_agent_manager

        console.print(f"🤖 [bold blue]Creating AI Agent '{name}' with {provider}...[/bold blue]")

        # Prepare provider-specific kwargs
        provider_kwargs = {}

        # Set provider host/port based on provider type
        if provider == "ollama":
            provider_kwargs.update({
                "ollama_host": provider_host,
                "ollama_port": provider_port or 11434  # Default Ollama port
            })
        elif provider in ["openai", "anthropic"]:
            if api_key:
                provider_kwargs["api_key"] = api_key
            else:
                # Check environment variables
                env_key = f"{provider.upper()}_API_KEY"
                api_key = os.getenv(env_key)
                if api_key:
                    provider_kwargs["api_key"] = api_key
                else:
                    console.print(f"[yellow]Warning: No API key provided for {provider}. Set --api-key or {env_key} env var[/yellow]")
        elif provider == "lmstudio":
            # LM Studio typically runs locally, no additional host/port needed
            pass

        # Create agent configuration
        manager = get_agent_manager()
        config = manager.create_agent(
            name=name,
            provider=provider,
            model_id=model_id,
            host=anvyl_host,
            port=anvyl_port,
            verbose=verbose,
            **provider_kwargs
        )

        console.print(f"✅ [bold green]Agent '{name}' created successfully![/bold green]")
        console.print(f"   Provider: {config.provider}")
        console.print(f"   Model: {config.model_id}")
        console.print(f"   Anvyl Server: {config.host}:{config.port}")

        # Show provider-specific info
        if provider == "ollama":
            provider_info = f"Ollama: {provider_host}:{provider_port or 11434}"
        elif provider in ["openai", "anthropic"]:
            provider_info = f"{provider.title()}: Cloud API"
        else:
            provider_info = f"{provider.title()}: Local"
        console.print(f"   Provider Config: {provider_info}")

        # Auto-start if requested
        if auto_start:
            console.print(f"\n🚀 [bold yellow]Starting agent '{name}'...[/bold yellow]")
            manager.start_agent(name)
            console.print(f"✅ [bold green]Agent '{name}' is now running![/bold green]")
            console.print(f"\n💡 [bold]Usage:[/bold] anvyl agent act {name} \"<your instruction>\"")
        else:
            console.print(f"\n💡 [bold]Next steps:[/bold]")
            console.print(f"   Start agent: anvyl agent start {name}")
            console.print(f"   Execute actions: anvyl agent act {name} \"<your instruction>\"")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("start")
def agent_start(
    name: str = typer.Argument(..., help="Name of the AI agent to start")
):
    """Start an AI agent in a Docker container."""
    try:
        from .agent_manager import get_agent_manager

        console.print(f"🚀 [bold blue]Starting AI Agent '{name}' in container...[/bold blue]")

        manager = get_agent_manager()

        # Check if agent exists first
        config = manager.get_agent_config(name)
        if not config:
            console.print(f"[red]Error: Agent '{name}' not found.[/red]")
            console.print(f"[yellow]Create the agent first: anvyl agent create {name}[/yellow]")
            raise typer.Exit(1)

        # Start the agent
        if manager.start_agent(name):
            console.print(f"✅ [bold green]Agent '{name}' is now running in container![/bold green]")
            console.print(f"   Provider: {config.provider}")
            console.print(f"   Model: {config.model_id}")
            console.print(f"   gRPC Server: {config.host}:{config.port}")

            console.print(f"\n💡 [bold]Usage:[/bold] anvyl agent act {name} \"<your instruction>\"")
            console.print(f"📋 [bold]View logs:[/bold] anvyl agent logs {name}")
        else:
            console.print(f"[red]Failed to start agent '{name}'[/red]")
            raise typer.Exit(1)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        if "not found" in str(e):
            console.print(f"[yellow]Create the agent first: anvyl agent create {name}[/yellow]")
        raise typer.Exit(1)
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        if "Docker is not available" in str(e):
            console.print(f"[yellow]Please install and start Docker, then try again[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("stop")
def agent_stop(
    name: str = typer.Argument(..., help="Name of the AI agent to stop")
):
    """Stop a running AI agent container."""
    try:
        from .agent_manager import get_agent_manager

        manager = get_agent_manager()
        if manager.stop_agent(name):
            console.print(f"✅ [bold green]Agent '{name}' stopped successfully![/bold green]")
        else:
            console.print(f"[yellow]Agent '{name}' is not running[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("logs")
def agent_logs(
    name: str = typer.Argument(..., help="Name of the AI agent to show logs for"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output")
):
    """Show logs from an AI agent container."""
    try:
        from .agent_manager import get_agent_manager

        manager = get_agent_manager()
        logs = manager.get_agent_logs(name, tail=tail, follow=follow)

        if logs:
            if follow:
                # For follow mode, we need to stream the logs
                import subprocess
                config = manager.get_agent_config(name)
                if config and config.container_id:
                    cmd = ['docker', 'logs', '-f', '--tail', str(tail), config.container_id]
                    try:
                        subprocess.run(cmd)
                    except KeyboardInterrupt:
                        console.print("\n[yellow]Stopped following logs[/yellow]")
            else:
                console.print(logs)
        else:
            console.print(f"[red]No logs available for agent '{name}'[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("act")
def agent_act(
    agent_name: str = typer.Argument(..., help="Name of the AI agent to use"),
    instruction: str = typer.Argument(..., help="Natural language instruction for the AI agent to execute")
):
    """Execute an instruction using a configured AI agent."""
    try:
        from .agent_manager import get_agent_manager

        manager = get_agent_manager()

        # Check if agent exists
        config = manager.get_agent_config(agent_name)
        if not config:
            console.print(f"[red]Error: Agent '{agent_name}' not found.[/red]")
            console.print(f"[yellow]Create the agent first: anvyl agent create {agent_name}[/yellow]")
            raise typer.Exit(1)

        # Check if agent is running
        status_info = manager.get_agent_status(agent_name)
        if not status_info or not status_info.get("running", False):
            console.print(f"🚀 [bold yellow]Agent '{agent_name}' not running. Starting...[/bold yellow]")
            try:
                if manager.start_agent(agent_name):
                    console.print(f"✅ [bold green]Agent '{agent_name}' started![/bold green]")
                else:
                    console.print(f"[red]Failed to start agent '{agent_name}'[/red]")
                    raise typer.Exit(1)
            except Exception as e:
                console.print(f"[red]Error starting agent: {e}[/red]")
                raise typer.Exit(1)

        # Execute the instruction by calling the agent via gRPC
        console.print(f"\n🔄 [bold cyan]Executing:[/bold cyan] {instruction}")
        console.print("⏳ [bold blue]Processing...[/bold blue]")

        # Execute the instruction via gRPC
        try:
            from .grpc_client import AnvylClient

            # Connect to gRPC server
            client = AnvylClient(config.host, config.port)
            if not client.connect():
                console.print(f"[red]Failed to connect to gRPC server at {config.host}:{config.port}[/red]")
                raise typer.Exit(1)

            # Execute instruction
            result = client.execute_agent_instruction(agent_name, instruction)

            if result and result.get("success"):
                console.print(f"\n✅ [bold green]Result:[/bold green] {result['result']}")
            else:
                error_msg = result.get("error_message", "Unknown error") if result else "No response from server"
                console.print(f"\n❌ [bold red]Error:[/bold red] {error_msg}")
                raise typer.Exit(1)

        except Exception as e:
            console.print(f"\n❌ [bold red]Error executing instruction:[/bold red] {e}")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("execute")
def agent_execute(
    agent_name: str = typer.Argument(..., help="Name of the AI agent to use"),
    instruction: str = typer.Argument(..., help="Natural language instruction for the AI agent to execute")
):
    """Execute an instruction using a configured AI agent (alias for 'act' command)."""
    return agent_act(agent_name, instruction)

@agent_app.command("session")
def agent_session(
    agent_name: str = typer.Argument(..., help="Name of the AI agent to use")
):
    """Start an interactive action execution session with a configured AI agent."""
    try:
        from .agent_manager import get_agent_manager

        manager = get_agent_manager()

        # Check if agent exists
        config = manager.get_agent_config(agent_name)
        if not config:
            console.print(f"[red]Error: Agent '{agent_name}' not found.[/red]")
            console.print(f"[yellow]Create the agent first: anvyl agent create {agent_name}[/yellow]")
            raise typer.Exit(1)

        # Check if agent is running
        status_info = manager.get_agent_status(agent_name)
        if not status_info or not status_info.get("running", False):
            console.print(f"🚀 [bold yellow]Agent '{agent_name}' not running. Starting...[/bold yellow]")
            try:
                if manager.start_agent(agent_name):
                    console.print(f"✅ [bold green]Agent '{agent_name}' started![/bold green]")
                else:
                    console.print(f"[red]Failed to start agent '{agent_name}'[/red]")
                    raise typer.Exit(1)
            except Exception as e:
                console.print(f"[red]Error starting agent: {e}[/red]")
                raise typer.Exit(1)

        # For containerized agents, interactive sessions need to be implemented differently
        console.print(f"\n⚠️  [bold yellow]Note:[/bold yellow] Interactive sessions with containerized agents are not yet implemented.")
        console.print(f"   The agent '{agent_name}' is running in a container.")
        console.print(f"   Use 'anvyl agent logs {agent_name} --follow' to see real-time agent activity.")
        console.print(f"   Use 'anvyl agent act {agent_name} \"<instruction>\"' to execute individual instructions.")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("actions")
def agent_actions(
    agent_name: str = typer.Argument(..., help="Name of the AI agent to query")
):
    """Show available actions for a configured AI agent."""
    try:
        from .agent_manager import get_agent_manager

        manager = get_agent_manager()

        # Get agent config to show basic info
        config = manager.get_agent_config(agent_name)
        if not config:
            console.print(f"[red]Agent '{agent_name}' not found.[/red]")
            console.print(f"[yellow]Create the agent first: anvyl agent create {agent_name}[/yellow]")
            console.print(f"[yellow]List available agents: anvyl agent list[/yellow]")
            raise typer.Exit(1)

        # Show agent configuration and status
        status_info = manager.get_agent_status(agent_name)

        console.print(f"[bold cyan]Agent Configuration:[/bold cyan]")
        console.print(f"   Name: {config.name}")
        console.print(f"   Provider: {config.provider}")
        console.print(f"   Model: {config.model_id}")
        console.print(f"   gRPC Server: {config.host}:{config.port}")
        console.print(f"   Status: {status_info.get('status', 'unknown') if status_info else 'unknown'}")

        if status_info and status_info.get("container_id"):
            console.print(f"   Container: {status_info['container_id']}")

        console.print(f"\n[bold cyan]Available Actions:[/bold cyan]")
        console.print(f"   • Host Management: List, add, and monitor hosts")
        console.print(f"   • Container Management: Create, stop, view logs, execute commands")
        console.print(f"   • Agent Management: Launch and manage infrastructure agents")
        console.print(f"   • System Monitoring: Get real-time status and metrics")
        console.print(f"   • UI Stack Management: Monitor and manage the Anvyl UI components")

        console.print(f"\n💡 [bold]Usage:[/bold] anvyl agent act {agent_name} \"<your instruction>\"")
        console.print(f"📋 [bold]View logs:[/bold] anvyl agent logs {agent_name}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("list")
def agent_list(
    running_only: bool = typer.Option(False, "--running", "-r", help="Show only running agents"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json")
):
    """List all configured AI agents."""
    try:
        from .agent_manager import get_agent_manager

        manager = get_agent_manager()
        agents = manager.list_agents()

        if running_only:
            agents = [a for a in agents if a.get("running", False)]

        if output == "json":
            console.print(json.dumps(agents, indent=2))
        else:
            if not agents:
                status_msg = "running agents" if running_only else "configured agents"
                console.print(f"[yellow]No {status_msg} found.[/yellow]")
                if not running_only:
                    console.print(f"[yellow]Create an agent: anvyl agent create <name>[/yellow]")
                return

            table = Table(title="Anvyl AI Agents")
            table.add_column("Name", style="cyan")
            table.add_column("Provider", style="green")
            table.add_column("Model", style="blue")
            table.add_column("Status", style="yellow")
            table.add_column("Container ID", style="magenta")

            for agent in agents:
                status_style = "green" if agent.get("running", False) else "red"
                container_id = agent.get("container_id", "")
                if container_id:
                    container_id = container_id[:12] + "..." if len(container_id) > 12 else container_id

                table.add_row(
                    agent["name"],
                    agent["provider"],
                    agent["model_id"],
                    agent.get("status", "unknown"),
                    container_id
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

@agent_app.command("remove")
def agent_remove(
    name: str = typer.Argument(..., help="Name of the AI agent to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Force removal without confirmation"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-accept all prompts")
):
    """Remove an AI agent configuration."""
    try:
        from .agent_manager import get_agent_manager

        manager = get_agent_manager()
        config = manager.get_agent_config(name)

        if not config:
            console.print(f"[red]Agent '{name}' not found.[/red]")
            raise typer.Exit(1)

        # Confirm removal unless forced or auto-accept is enabled
        if not force and not yes:
            console.print(f"[yellow]Are you sure you want to remove agent '{name}'?[/yellow]")
            console.print(f"  Provider: {config.provider}")
            console.print(f"  Model: {config.model_id}")
            console.print(f"  Created: {config.created_at}")

            confirm = typer.confirm("Remove this agent?", default=True)
            if not confirm:
                console.print("[yellow]Removal cancelled.[/yellow]")
                return

        # Remove the agent
        manager.remove_agent(name)
        console.print(f"✅ [bold green]Agent '{name}' removed successfully![/bold green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
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
            console.print(f"[red]Agent '{name}' not found.[/red]")
            console.print(f"[yellow]List available agents: anvyl agent list[/yellow]")
            raise typer.Exit(1)

        # Check if agent is running using the new container-based method
        status_info = manager.get_agent_status(name)
        is_running = status_info and status_info.get("running", False)

        # Create info panel
        info_text = f"""[bold cyan]Name:[/bold cyan] {config.name}
[bold cyan]Status:[/bold cyan] {'🟢 Running' if is_running else '🔴 Stopped'}
[bold cyan]Provider:[/bold cyan] {config.provider}
[bold cyan]Model:[/bold cyan] {config.model_id}
[bold cyan]Anvyl Server:[/bold cyan] {config.host}:{config.port}
[bold cyan]Verbose:[/bold cyan] {config.verbose}
[bold cyan]Created:[/bold cyan] {config.created_at}"""

        if config.provider_kwargs:
            info_text += f"\n[bold cyan]Provider Config:[/bold cyan] {config.provider_kwargs}"

        if status_info and status_info.get("container_id"):
            info_text += f"\n[bold cyan]Container:[/bold cyan] {status_info['container_id']}"

        console.print(Panel(info_text, title=f"🤖 Agent: {name}", border_style="blue"))

        # Show usage examples
        console.print(f"\n💡 [bold]Usage Examples:[/bold]")
        if not is_running:
            console.print(f"  Start agent: anvyl agent start {name}")
        console.print(f"  Execute action: anvyl agent act {name} \"show all hosts\"")
        console.print(f"  View logs: anvyl agent logs {name}")
        console.print(f"  Show actions: anvyl agent actions {name}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

# Backward compatibility commands (deprecated)
@agent_app.command("chat")
def agent_chat_deprecated(
    agent_name: str = typer.Argument(..., help="Name of the AI agent to use"),
    message: str = typer.Argument(..., help="Natural language message for the AI agent")
):
    """[DEPRECATED] Send a message to the AI agent. Use 'act' command instead."""
    console.print("[yellow]⚠️  The 'chat' command is deprecated. Use 'anvyl agent act' instead.[/yellow]")
    console.print(f"[yellow]💡 Try: anvyl agent act {agent_name} \"{message}\"[/yellow]\n")

    # Redirect to the act command
    return agent_act(agent_name, message)

@agent_app.command("interactive")
def agent_interactive_deprecated(
    agent_name: str = typer.Argument(..., help="Name of the AI agent to use")
):
    """[DEPRECATED] Start an interactive session. Use 'session' command instead."""
    console.print("[yellow]⚠️  The 'interactive' command is deprecated. Use 'anvyl agent session' instead.[/yellow]")
    console.print(f"[yellow]💡 Try: anvyl agent session {agent_name}[/yellow]\n")

    # Redirect to the session command
    return agent_session(agent_name)

@agent_app.command("demo")
def agent_demo(
    agent_name: str = typer.Argument(..., help="Name of the AI agent to use")
):
    """Run a demonstration of AI agent action capabilities."""
    try:
        from .agent_manager import get_agent_manager

        manager = get_agent_manager()

        # Get the agent (start it if not running)
        agent = manager.get_agent(agent_name)
        if not agent:
            console.print(f"🚀 [bold yellow]Agent '{agent_name}' not running. Starting...[/bold yellow]")
            try:
                agent = manager.start_agent(agent_name)
                console.print(f"✅ [bold green]Agent '{agent_name}' started![/bold green]")
            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")
                if "not found" in str(e):
                    console.print(f"[yellow]Create the agent first: anvyl agent create {agent_name}[/yellow]")
                    console.print(f"[yellow]List available agents: anvyl agent list[/yellow]")
                raise typer.Exit(1)

        model_info = agent.get_model_info()
        console.print(f"🎬 [bold blue]Anvyl AI Agent Action Demo for '{agent_name}'[/bold blue]")
        console.print(f"Using {model_info['provider']} with {model_info['model_id']}")
        console.print("This demo will show various AI agent action capabilities.\n")

        # Demo instructions
        demo_instructions = [
            "What's the current system status?",
            "Show me all hosts",
            "List all containers",
            "What agents are running?"
        ]

        for i, instruction in enumerate(demo_instructions, 1):
            console.print(f"\n[bold yellow]Demo {i}/{len(demo_instructions)}:[/bold yellow] {instruction}")
            console.print("⏳ [bold blue]Executing...[/bold blue]")

            try:
                result = agent.act(instruction)
                console.print(f"✅ [bold green]Result:[/bold green] {result}")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

            if i < len(demo_instructions):
                console.print("\n" + "─" * 50)

        console.print("\n✅ [bold green]Demo completed![/bold green]")
        console.print("💡 Try 'anvyl agent session <agent_name>' for a full interactive session.")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

# Status and overview commands
@app.command("status")
def status(
    host: str = typer.Option("localhost", "--host", "-h", help="Anvyl server host"),
    port: int = typer.Option(50051, "--port", "-p", help="Anvyl server port")
):
    """Show overall system status."""
    client = get_client(host, port)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Fetching system status...", total=None)
        hosts = client.list_hosts()
        containers = client.list_containers()
        agents = client.list_agents()

    # Create status tree
    tree = Tree("🔨 Anvyl System Status")

    hosts_branch = tree.add(f"📡 Hosts ({len(hosts)})")
    for host in hosts:
        host_name = getattr(host, 'name', 'Unknown')
        host_ip = getattr(host, 'ip', 'Unknown')
        host_status = getattr(host, 'status', 'Unknown')
        status_color = "green" if host_status == "online" else "red"
        hosts_branch.add(f"[{status_color}]{host_name}[/{status_color}] ({host_ip}) - {host_status}")

    containers_branch = tree.add(f"📦 Containers ({len(containers)})")
    running_containers = [c for c in containers if getattr(c, 'status', '') == 'running']
    containers_branch.add(f"[green]Running: {len(running_containers)}[/green]")
    containers_branch.add(f"[yellow]Total: {len(containers)}[/yellow]")

    agents_branch = tree.add(f"🤖 Agents ({len(agents)})")
    running_agents = [a for a in agents if getattr(a, 'status', '') == 'running']
    agents_branch.add(f"[green]Running: {len(running_agents)}[/green]")
    agents_branch.add(f"[yellow]Total: {len(agents)}[/yellow]")

    console.print(tree)

@app.command("version")
def version():
    """Show Anvyl CLI version."""
    from anvyl import __version__
    console.print(f"Anvyl CLI v{__version__}")

if __name__ == "__main__":
    app()