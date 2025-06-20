#!/usr/bin/env python3
"""
Anvyl CLI - Command line interface for Anvyl infrastructure orchestrator
"""

import typer
import os
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.tree import Tree
from rich import print as rprint
import json
import sys
import logging

from .grpc_client import AnvylClient

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
        import subprocess
        project_root = get_project_root()
        ui_dir = os.path.join(project_root, "ui")

        if service and service in ["grpc-server", "grpc"]:
            # Handle gRPC server logs (Python process)
            console.print(f"📋 [bold]Logs for gRPC server (Python process):[/bold]")
            console.print("[yellow]Note: gRPC server logs are displayed in the terminal where it was started[/yellow]")
            console.print("[yellow]To see gRPC server logs, start it manually with: python -m anvyl.grpc_server[/yellow]")
            return

        if service:
            service_map = {
                "frontend": "anvyl-ui-frontend",
                "backend": "anvyl-ui-backend"
            }

            container_name = service_map.get(service, service)
            cmd = ["docker-compose", "-f", "docker-compose.yml", "logs"]

            if follow:
                cmd.append("-f")
            if tail:
                cmd.extend(["--tail", str(tail)])

            cmd.append(container_name)

            console.print(f"📋 [bold]Logs for {service}:[/bold]")
            subprocess.run(cmd, cwd=ui_dir)
        else:
            # Show logs for all Docker services
            cmd = ["docker-compose", "-f", "docker-compose.yml", "logs"]

            if follow:
                cmd.append("-f")
            if tail:
                cmd.extend(["--tail", str(tail)])

            console.print("📋 [bold]Logs for all Docker services:[/bold]")
            subprocess.run(cmd, cwd=ui_dir)

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

@agent_app.command("list")
def list_agents(
    host_id: Optional[str] = typer.Option(None, "--host-id", help="Filter by host ID"),
    host: str = typer.Option("localhost", "--host", "-h", help="Anvyl server host"),
    port: int = typer.Option(50051, "--port", "-p", help="Anvyl server port"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json")
):
    """List agents."""
    client = get_client(host, port)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Fetching agents...", total=None)
        agents = client.list_agents(host_id)

    if not agents:
        console.print("[yellow]No agents found[/yellow]")
        return

    if output == "json":
        agents_data = []
        for agent in agents:
            agent_dict = {
                "id": getattr(agent, 'id', ''),
                "name": getattr(agent, 'name', ''),
                "status": getattr(agent, 'status', ''),
                "host_id": getattr(agent, 'host_id', ''),
                "entrypoint": getattr(agent, 'entrypoint', ''),
                "persistent": getattr(agent, 'persistent', False)
            }
            agents_data.append(agent_dict)
        console.print(json.dumps(agents_data, indent=2))
    else:
        table = Table(title="Anvyl Agents")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="magenta")
        table.add_column("Host", style="yellow")
        table.add_column("Entrypoint", style="blue")
        table.add_column("Persistent", style="dim")

        for agent in agents:
            table.add_row(
                getattr(agent, 'id', '')[:12],  # Short ID
                getattr(agent, 'name', ''),
                getattr(agent, 'status', ''),
                getattr(agent, 'host_id', ''),
                getattr(agent, 'entrypoint', ''),
                "Yes" if getattr(agent, 'persistent', False) else "No"
            )

        console.print(table)

@agent_app.command("launch")
def launch_agent(
    name: str = typer.Argument(..., help="Agent name"),
    host_id: str = typer.Argument(..., help="Target host ID"),
    entrypoint: str = typer.Argument(..., help="Agent entrypoint script"),
    env: List[str] = typer.Option([], "--env", "-e", help="Environment variables"),
    use_container: bool = typer.Option(False, "--container", help="Run in container"),
    working_dir: str = typer.Option("", "--workdir", "-w", help="Working directory"),
    arguments: List[str] = typer.Option([], "--arg", "-a", help="Command arguments"),
    persistent: bool = typer.Option(False, "--persistent", help="Make agent persistent"),
    host: str = typer.Option("localhost", "--host", "-h", help="Anvyl server host"),
    port: int = typer.Option(50051, "--port", "-p", help="Anvyl server port")
):
    """Launch a new agent."""
    client = get_client(host, port)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task(f"Launching agent {name}...", total=None)
        result = client.launch_agent(
            name=name,
            host_id=host_id,
            entrypoint=entrypoint,
            env=env,
            use_container=use_container,
            working_directory=working_dir,
            arguments=arguments,
            persistent=persistent
        )

    if result:
        console.print(f"[green]✓[/green] Successfully launched agent: {name}")
        console.print(f"Agent ID: {getattr(result, 'id', 'N/A')}")
    else:
        console.print(f"[red]✗[/red] Failed to launch agent: {name}")
        raise typer.Exit(1)

@agent_app.command("stop")
def stop_agent(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    host: str = typer.Option("localhost", "--host", "-h", help="Anvyl server host"),
    port: int = typer.Option(50051, "--port", "-p", help="Anvyl server port")
):
    """Stop an agent."""
    client = get_client(host, port)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task(f"Stopping agent {agent_id}...", total=None)
        success = client.stop_agent(agent_id)

    if success:
        console.print(f"[green]✓[/green] Successfully stopped agent: {agent_id}")
    else:
        console.print(f"[red]✗[/red] Failed to stop agent: {agent_id}")
        raise typer.Exit(1)

# MCP (Model Context Protocol) commands
mcp_app = typer.Typer(help="MCP (Model Context Protocol) agent management commands.")
app.add_typer(mcp_app, name="mcp")

# LMStudio model management commands
model_app = typer.Typer(help="LMStudio model management commands.")
app.add_typer(model_app, name="model")

@model_app.command("list")
def list_models(
    host: str = typer.Option("localhost", "--host", "-h", help="Anvyl server host"),
    port: int = typer.Option(50051, "--port", "-p", help="Anvyl server port"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json")
):
    """List available and loaded MLX models."""
    try:
        import lmstudio as lms
        
        console.print("📊 [bold blue]MLX Models Status[/bold blue]")
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Fetching model information...", total=None)
            
            # Get models from LMStudio
            try:
                client = lms.get_default_client()
                downloaded_models = client.system.list_downloaded_models()
                loaded_models = client.llm.list_loaded()
            except Exception as e:
                console.print(f"[yellow]Warning: Could not connect to LMStudio: {e}[/yellow]")
                console.print("[yellow]Make sure LMStudio is running and accessible.[/yellow]")
                return

        if output == "json":
            models_data = {
                "downloaded": [getattr(model, 'id', '') for model in downloaded_models],
                "loaded": [getattr(model, 'identifier', '') for model in loaded_models]
            }
            console.print(json.dumps(models_data, indent=2))
        else:
            # Show downloaded models
            if downloaded_models:
                downloaded_table = Table(title="Downloaded MLX Models")
                downloaded_table.add_column("Model ID", style="cyan")
                downloaded_table.add_column("Architecture", style="green")
                downloaded_table.add_column("Size", style="blue")
                
                for model in downloaded_models:
                    # Filter for MLX models only
                    if hasattr(model, 'path') and 'mlx' in str(model.path).lower():
                        size = getattr(model, 'size_bytes', 0)
                        size_mb = f"{size / (1024*1024):.1f} MB" if size > 0 else "Unknown"
                        downloaded_table.add_row(
                            getattr(model, 'id', ''),
                            getattr(model, 'architecture', 'Unknown'),
                            size_mb
                        )
                
                console.print(downloaded_table)
            else:
                console.print("[yellow]No MLX models found. Use 'lms get <model>' to download models.[/yellow]")
            
            # Show loaded models
            if loaded_models:
                loaded_table = Table(title="Loaded MLX Models")
                loaded_table.add_column("Identifier", style="cyan")
                loaded_table.add_column("Model", style="green")
                loaded_table.add_column("Status", style="blue")
                
                for model in loaded_models:
                    loaded_table.add_row(
                        model.identifier,
                        getattr(model, 'model', 'Unknown'),
                        "Loaded"
                    )
                
                console.print(loaded_table)
            else:
                console.print("[yellow]No models currently loaded.[/yellow]")

    except ImportError:
        console.print("[red]LMStudio SDK not available. Install with: pip install lmstudio[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error listing models: {e}[/red]")
        raise typer.Exit(1)

@model_app.command("start")
def start_model_container(
    model_id: str = typer.Argument(..., help="Model ID to start (MLX format only)"),
    container_name: Optional[str] = typer.Option(None, "--name", "-n", help="Container name (default: model-<model_id>)"),
    port: int = typer.Option(1234, "--port", "-p", help="Port to expose LMStudio server on"),
    host_id: Optional[str] = typer.Option(None, "--host-id", help="Target host ID"),
    memory_limit: Optional[str] = typer.Option(None, "--memory", "-m", help="Memory limit (e.g., 8g)"),
    anvyl_host: str = typer.Option("localhost", "--anvyl-host", help="Anvyl server host"),
    anvyl_port: int = typer.Option(50051, "--anvyl-port", help="Anvyl server port")
):
    """Start a user-specified MLX model in a container using LMStudio."""
    try:
        import lmstudio as lms
        
        # Validate model is MLX format
        if not model_id or 'mlx' not in model_id.lower():
            console.print("[red]Error: Only MLX models are supported. Model ID should contain 'mlx'.[/red]")
            console.print("[yellow]Available MLX models can be found with 'anvyl model list'[/yellow]")
            raise typer.Exit(1)
        
        # Generate container name if not provided
        if not container_name:
            safe_model_id = model_id.replace('/', '-').replace(':', '-').lower()
            container_name = f"model-{safe_model_id}"
        
        console.print(f"🚀 [bold blue]Starting MLX Model Container[/bold blue]")
        console.print(f"Model: [cyan]{model_id}[/cyan]")
        console.print(f"Container: [green]{container_name}[/green]")
        console.print(f"Port: [blue]{port}[/blue]")
        
        # Connect to Anvyl server
        anvyl_client = get_client(anvyl_host, anvyl_port)
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Creating model container...", total=None)
            
            # Prepare container configuration
            container_config = {
                'name': container_name,
                'image': 'python:3.12-slim',  # Base Python image
                'host_id': host_id or '',
                'ports': [f"{port}:1234"],  # Map host port to LMStudio default port
                'environment': [
                    f'MODEL_ID={model_id}',
                    'PYTHONUNBUFFERED=1'
                ],
                'labels': {
                    'anvyl.service': 'lmstudio-model',
                    'anvyl.model.id': model_id,
                    'anvyl.model.type': 'mlx'
                }
            }
            
            # Add memory limit if specified
            if memory_limit:
                # Docker memory limit will be handled in the gRPC server
                container_config['environment'].append(f'MEMORY_LIMIT={memory_limit}')
            
            # Create startup script for the container
            startup_script = f'''#!/bin/bash
set -e

echo "Installing LMStudio SDK..."
pip install lmstudio

echo "Starting MLX model: {model_id}"
python3 -c "
import lmstudio as lms
import time
import sys

try:
    print('Loading model: {model_id}')
    model = lms.llm('{model_id}')
    print(f'Model loaded successfully: {model_id}')
    
    # Keep the container running and serve the model
    print('Model server is running on port 1234')
    print('Container will remain active to serve the model...')
    
    # Keep alive loop
    while True:
        time.sleep(60)
        print(f'Model {model_id} is still running...')
        
except Exception as e:
    print(f'Error loading model: {{e}}')
    sys.exit(1)
"
'''
            
            # Add the startup script as a volume mount
            container_config['volumes'] = ['/tmp/startup.sh:/startup.sh:ro']
            container_config['environment'].append('STARTUP_SCRIPT=/startup.sh')
            
            # Use custom command to run the startup script
            # This will be handled in the gRPC server implementation
            
            # Create container via Anvyl
            result = anvyl_client.add_container(**container_config)
        
        if result:
            console.print(f"[green]✓[/green] Successfully created model container: {container_name}")
            console.print(f"[green]✓[/green] Model {model_id} is starting...")
            console.print(f"\n🌐 [bold]Access Information:[/bold]")
            console.print(f"  • Model Server: http://localhost:{port}")
            console.print(f"  • Container ID: {getattr(result, 'id', 'N/A')}")
            console.print(f"\n💡 [bold]Usage Tips:[/bold]")
            console.print(f"  • Check logs: anvyl container logs {getattr(result, 'id', container_name)[:12]}")
            console.print(f"  • Stop model: anvyl container stop {getattr(result, 'id', container_name)[:12]}")
        else:
            console.print(f"[red]✗[/red] Failed to create model container")
            raise typer.Exit(1)
            
    except ImportError:
        console.print("[red]LMStudio SDK not available. Install with: pip install lmstudio[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error starting model container: {e}[/red]")
        raise typer.Exit(1)

@model_app.command("stop")
def stop_model_container(
    model_id: str = typer.Argument(..., help="Model ID or container name to stop"),
    anvyl_host: str = typer.Option("localhost", "--anvyl-host", help="Anvyl server host"),
    anvyl_port: int = typer.Option(50051, "--anvyl-port", help="Anvyl server port")
):
    """Stop a running MLX model container."""
    try:
        console.print(f"🛑 [bold red]Stopping MLX Model Container[/bold red]")
        console.print(f"Model/Container: [cyan]{model_id}[/cyan]")
        
        # Connect to Anvyl server
        anvyl_client = get_client(anvyl_host, anvyl_port)
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Finding and stopping container...", total=None)
            
            # First, try to find container by model ID or name
            containers = anvyl_client.list_containers()
            target_container = None
            
            for container in containers:
                # Check if it's a model container with matching model ID
                labels = getattr(container, 'labels', {})
                container_name = getattr(container, 'name', '')
                container_id = getattr(container, 'id', '')
                
                if (labels.get('anvyl.model.id') == model_id or 
                    container_name == model_id or 
                    container_id.startswith(model_id) or
                    container_name == f"model-{model_id.replace('/', '-').replace(':', '-').lower()}"):
                    target_container = container
                    break
            
            if not target_container:
                console.print(f"[red]No model container found for: {model_id}[/red]")
                console.print("[yellow]Use 'anvyl container list' to see available containers[/yellow]")
                raise typer.Exit(1)
            
            # Stop the container
            container_id = getattr(target_container, 'id', '')
            success = anvyl_client.stop_container(container_id)
        
        if success:
            console.print(f"[green]✓[/green] Successfully stopped model container")
            console.print(f"Model: [cyan]{model_id}[/cyan]")
        else:
            console.print(f"[red]✗[/red] Failed to stop model container")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error stopping model container: {e}[/red]")
        raise typer.Exit(1)

@model_app.command("ps")
def list_model_containers(
    anvyl_host: str = typer.Option("localhost", "--anvyl-host", help="Anvyl server host"),
    anvyl_port: int = typer.Option(50051, "--anvyl-port", help="Anvyl server port"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json")
):
    """List running MLX model containers."""
    try:
        console.print("📋 [bold blue]MLX Model Containers[/bold blue]")
        
        # Connect to Anvyl server
        anvyl_client = get_client(anvyl_host, anvyl_port)
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Fetching model containers...", total=None)
            
            # Get all containers and filter for model containers
            containers = anvyl_client.list_containers()
            model_containers = []
            
            for container in containers:
                labels = getattr(container, 'labels', {})
                if labels.get('anvyl.service') == 'lmstudio-model':
                    model_containers.append(container)
        
        if not model_containers:
            console.print("[yellow]No MLX model containers found[/yellow]")
            console.print("💡 Use 'anvyl model start <model-id>' to start a model container")
            return
        
        if output == "json":
            containers_data = []
            for container in model_containers:
                labels = getattr(container, 'labels', {})
                container_data = {
                    "id": getattr(container, 'id', ''),
                    "name": getattr(container, 'name', ''),
                    "model_id": labels.get('anvyl.model.id', 'Unknown'),
                    "status": getattr(container, 'status', 'unknown'),
                    "host_id": getattr(container, 'host_id', '')
                }
                containers_data.append(container_data)
            console.print(json.dumps(containers_data, indent=2))
        else:
            table = Table(title="MLX Model Containers")
            table.add_column("Container ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Model ID", style="blue")
            table.add_column("Status", style="magenta")
            table.add_column("Host", style="yellow")
            
            for container in model_containers:
                labels = getattr(container, 'labels', {})
                table.add_row(
                    getattr(container, 'id', '')[:12],
                    getattr(container, 'name', ''),
                    labels.get('anvyl.model.id', 'Unknown'),
                    getattr(container, 'status', 'unknown'),
                    getattr(container, 'host_id', '')
                )
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error listing model containers: {e}[/red]")
        raise typer.Exit(1)

# MCP commands (existing functionality)
from .mcp_cli import mcp_app

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