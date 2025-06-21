#!/usr/bin/env python3
"""
Anvyl CLI - Command Line Interface for Anvyl Infrastructure Orchestrator

This module provides a comprehensive CLI for managing Anvyl infrastructure,
including hosts, containers, and monitoring capabilities.
"""

import typer
import json
import os
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
import sys
import logging
import requests
import subprocess
from pathlib import Path

from anvyl.infra.infrastructure_service import get_infrastructure_service
from anvyl.database.models import DatabaseManager
from anvyl.agent import AgentManager, create_agent_manager
from anvyl.utils.background_service import get_service_manager

# Initialize rich console
console = Console()
app = typer.Typer(
    help="Anvyl Infrastructure Orchestrator CLI",
    no_args_is_help=True,
    add_completion=False
)

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
    project_root = get_project_root()

    try:
        if service:
            # Show logs for specific service
            console.print(f"📋 [bold blue]Logs for {service}[/bold blue]")

            # Use docker-compose logs
            cmd = ["docker-compose", "-f", os.path.join(project_root, "ui", "docker-compose.yml"), "logs"]

            if follow:
                cmd.append("-f")
            if tail:
                cmd.extend(["--tail", str(tail)])

            cmd.append(service)

            # Run the command and stream output
            process = subprocess.Popen(
                cmd,
                cwd=os.path.join(project_root, "ui"),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            try:
                for line in process.stdout:
                    console.print(line.rstrip())
            except KeyboardInterrupt:
                process.terminate()
                console.print("\n[yellow]Log following stopped[/yellow]")

        else:
            # Show logs for all services
            console.print("📋 [bold blue]Anvyl Infrastructure Logs[/bold blue]")

            cmd = ["docker-compose", "-f", os.path.join(project_root, "ui", "docker-compose.yml"), "logs"]

            if follow:
                cmd.append("-f")
            if tail:
                cmd.extend(["--tail", str(tail)])

            # Run the command and stream output
            process = subprocess.Popen(
                cmd,
                cwd=os.path.join(project_root, "ui"),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            try:
                for line in process.stdout:
                    console.print(line.rstrip())
            except KeyboardInterrupt:
                process.terminate()
                console.print("\n[yellow]Log following stopped[/yellow]")

    except Exception as e:
        console.print(f"[red]Error showing logs: {e}[/red]")
        raise typer.Exit(1)

# Infrastructure API Management Commands
infra_group = typer.Typer(
    help="Manage the Anvyl Infrastructure API service.",
    no_args_is_help=True,
    add_completion=False
)
app.add_typer(infra_group, name="infra")

@infra_group.command("up")
def start_infrastructure_api(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(4200, "--port", "-p", help="Port to bind to"),
    background: bool = typer.Option(True, "--background/--foreground", help="Run in background")
):
    """Start the Anvyl Infrastructure API service."""
    try:
        service_manager = get_service_manager()

        if background:
            console.print("🏗️ [bold blue]Starting Anvyl Infrastructure API in background[/bold blue]")

            if service_manager.start_infrastructure_api(host=host, port=port):
                console.print(f"✅ [green]Infrastructure API started successfully in background[/green]")
                console.print(f"🌐 API URL: http://{host}:{port}")
                console.print(f"📋 API Docs: http://{host}:{port}/docs")
                console.print(f"📁 Service logs: ~/.anvyl/services/infrastructure_api.log")
                console.print()
                console.print("Use 'anvyl infra status' to check service status")
                console.print("Use 'anvyl infra logs' to view service logs")
                console.print("Use 'anvyl infra down' to stop the service")
            else:
                console.print("[red]❌ Failed to start Infrastructure API[/red]")
                raise typer.Exit(1)
        else:
            console.print("🏗️ [bold blue]Starting Anvyl Infrastructure API in foreground[/bold blue]")
            console.print(f"🌐 API URL: http://{host}:{port}")
            console.print(f"📋 API Docs: http://{host}:{port}/docs")
            console.print("Press Ctrl+C to stop")

            from anvyl.infra.infrastructure_api import run_infrastructure_api
            run_infrastructure_api(host=host, port=port)

    except Exception as e:
        console.print(f"[red]Error starting infrastructure API: {e}[/red]")
        raise typer.Exit(1)

@infra_group.command("down")
def stop_infrastructure_api():
    """Stop the Anvyl Infrastructure API service."""
    try:
        service_manager = get_service_manager()

        console.print("🛑 [bold red]Stopping Anvyl Infrastructure API[/bold red]")

        if service_manager.stop_infrastructure_api():
            console.print("✅ [green]Infrastructure API stopped successfully[/green]")
        else:
            console.print("[red]❌ Failed to stop Infrastructure API[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error stopping infrastructure API: {e}[/red]")
        raise typer.Exit(1)

@infra_group.command("status")
def status_infrastructure_api():
    """Show status of the Anvyl Infrastructure API service."""
    try:
        service_manager = get_service_manager()

        console.print("📊 [bold blue]Anvyl Infrastructure API Status[/bold blue]")

        status = service_manager.get_service_status("infrastructure_api")

        if status:
            from rich.table import Table
            table = Table(show_header=False, box=None)
            table.add_column("Property", style="cyan", width=15)
            table.add_column("Value", style="green")

            table.add_row("Status", status.get("status", "unknown"))
            table.add_row("Running", "✅ Yes" if status.get("running", False) else "❌ No")
            table.add_row("PID", str(status.get("pid", "N/A")))
            table.add_row("Host", status.get("host", "N/A"))
            table.add_row("Port", str(status.get("port", "N/A")))
            table.add_row("Started", status.get("started_at", "N/A"))
            table.add_row("Log File", status.get("log_file", "N/A"))

            console.print(table)

            if status.get("running", False):
                console.print(f"\n🌐 API URL: http://{status.get('host')}:{status.get('port')}")
                console.print(f"📋 API Docs: http://{status.get('host')}:{status.get('port')}/docs")
        else:
            console.print("[yellow]Infrastructure API service is not running[/yellow]")
            console.print("Use 'anvyl infra up' to start the service")

    except Exception as e:
        console.print(f"[red]Error getting infrastructure API status: {e}[/red]")
        raise typer.Exit(1)

@infra_group.command("logs")
def logs_infrastructure_api(
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines to show")
):
    """Show logs from the Anvyl Infrastructure API service."""
    try:
        service_manager = get_service_manager()

        console.print("📋 [bold blue]Anvyl Infrastructure API Logs[/bold blue]")

        logs = service_manager.get_service_logs("infrastructure_api", lines=tail)

        if logs:
            console.print(logs)

            if follow:
                console.print("\n[yellow]Note: Following logs is not supported for background services[/yellow]")
                console.print("Use 'anvyl infra logs --tail 100' to see recent logs")
        else:
            console.print("[yellow]No logs available[/yellow]")
            console.print("The service may not be running or no logs have been generated yet")

    except Exception as e:
        console.print(f"[red]Error viewing infrastructure API logs: {e}[/red]")
        raise typer.Exit(1)

@infra_group.command("restart")
def restart_infrastructure_api(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(4200, "--port", "-p", help="Port to bind to")
):
    """Restart the Anvyl Infrastructure API service."""
    try:
        service_manager = get_service_manager()

        console.print("🔄 [bold blue]Restarting Anvyl Infrastructure API[/bold blue]")

        # Stop the service
        if service_manager.stop_infrastructure_api():
            console.print("✅ Stopped existing service")
        else:
            console.print("[yellow]No existing service to stop[/yellow]")

        # Start the service
        if service_manager.start_infrastructure_api(host=host, port=port):
            console.print("✅ [green]Infrastructure API restarted successfully[/green]")
            console.print(f"🌐 API URL: http://{host}:{port}")
            console.print(f"📋 API Docs: http://{host}:{port}/docs")
        else:
            console.print("[red]❌ Failed to restart Infrastructure API[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error restarting infrastructure API: {e}[/red]")
        raise typer.Exit(1)

# Host Management Commands
host_app = typer.Typer(
    help="Host management commands",
    no_args_is_help=True,
    add_completion=False
)
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
container_app = typer.Typer(
    help="Container management commands",
    no_args_is_help=True,
    add_completion=False
)
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

# Main status command
@app.command("status")
def status():
    """Show overall system status."""
    try:
        import requests
        infrastructure = get_infrastructure()

        # Check infra API health
        infra_url = "http://localhost:4200/health"
        try:
            resp = requests.get(infra_url, timeout=2)
            if resp.status_code == 200 and resp.json().get("status") == "healthy":
                infra_status = ("1", "1", "🟢 Healthy")
            else:
                infra_status = ("1", "0", "🔴 Unhealthy")
        except Exception:
            infra_status = ("1", "0", "🔴 Unreachable")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Getting system status...", total=None)
            hosts = infrastructure.list_hosts()
            containers = infrastructure.list_containers()

        # Calculate status
        total_hosts = len(hosts)
        online_hosts = len([h for h in hosts if h.get("status") == "online"])
        total_containers = len(containers)
        running_containers = len([c for c in containers if c.get("status") == "running"])

        # Display status
        status_table = Table(title="Anvyl System Status")
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Total", style="bold")
        status_table.add_column("Active", style="green")
        status_table.add_column("Status", style="bold")

        # Infra API status
        status_table.add_row("Infra API", *infra_status)

        # Hosts status
        host_status = "🟢 Healthy" if online_hosts == total_hosts else "🟡 Partial" if online_hosts > 0 else "🔴 Offline"
        status_table.add_row("Hosts", str(total_hosts), str(online_hosts), host_status)

        # Containers status
        container_status = "🟢 Running" if running_containers > 0 else "🔴 Stopped"
        status_table.add_row("Containers", str(total_containers), str(running_containers), container_status)

        # Agent status (container and API)
        try:
            from anvyl.infra.infrastructure_client import get_infrastructure_client
            agent_port = 4201
            infrastructure_client = get_infrastructure_client("http://localhost:4200")
            agent_container = infrastructure_client.get_agent_container_status()
            # Check agent API health
            try:
                resp = requests.get(f"http://localhost:{agent_port}/health", timeout=2)
                if resp.status_code == 200 and resp.json().get("status") == "healthy":
                    agent_api_status = "🟢 API Healthy"
                else:
                    agent_api_status = f"🔴 API Unhealthy (HTTP {resp.status_code})"
            except Exception:
                agent_api_status = "🔴 API Unreachable"
            if agent_container:
                agent_container_status = "🟢 Running" if agent_container.get("status") == "running" else "🟡 Not Running"
                agent_details = f"ID: {agent_container.get('id', 'N/A')[:12]}, Image: {agent_container.get('image', 'N/A')} | {agent_api_status}"
            else:
                agent_container_status = "🔴 Not Found"
                agent_details = f"No agent container running | {agent_api_status}"
            status_table.add_row("Agent", "1", "1" if agent_container_status == "🟢 Running" else "0", agent_container_status + " | " + agent_api_status)
        except Exception:
            status_table.add_row("Agent", "1", "0", "🔴 Error getting status")

        console.print(status_table)

        # Show recent activity
        if hosts or containers:
            console.print("\n[bold]Recent Activity:[/bold]")

            # Show recent hosts
            recent_hosts = sorted(hosts, key=lambda h: h.get("last_seen", ""), reverse=True)[:3]
            if recent_hosts:
                console.print("  📋 Recent hosts:")
                for host in recent_hosts:
                    status_emoji = "🟢" if host.get("status") == "online" else "🔴"
                    console.print(f"    {status_emoji} {host.get('name', 'Unknown')} ({host.get('ip', 'Unknown')})")

            # Show recent containers
            recent_containers = sorted(containers, key=lambda c: c.get("created_at", ""), reverse=True)[:3]
            if recent_containers:
                console.print("  📦 Recent containers:")
                for container in recent_containers:
                    status_emoji = "🟢" if container.get("status") == "running" else "🔴"
                    console.print(f"    {status_emoji} {container.get('name', 'Unknown')} ({container.get('image', 'Unknown')})")

    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")
        raise typer.Exit(1)

@app.command("version")
def version():
    """Show version information."""
    try:
        from anvyl import __version__, __author__, __email__

        console.print(Panel(
            f"[bold blue]Anvyl Infrastructure Orchestrator[/bold blue]\n\n"
            f"Version: [green]{__version__}[/green]\n"
            f"Author: [cyan]{__author__}[/cyan]\n"
            f"Email: [cyan]{__email__}[/cyan]",
            title="Version Info"
        ))
    except Exception as e:
        console.print(f"[red]Error getting version info: {e}[/red]")
        raise typer.Exit(1)

# Agent Management Commands
agent_group = typer.Typer(
    help="Manage AI agents for infrastructure automation.",
    no_args_is_help=True,
    add_completion=False
)
app.add_typer(agent_group, name="agent")

@agent_group.command("start")
def start_agent(
    lmstudio_url: str = typer.Option("http://localhost:1234/v1", "--lmstudio-url", help="LMStudio API URL"),
    lmstudio_model: str = typer.Option("llama-3.2-3b-instruct", "--model", help="LMStudio model name"),
    port: int = typer.Option(4200, "--port", help="Agent API port"),
    build: bool = typer.Option(True, "--build/--no-build", help="Build container image before starting")
):
    """Start the AI agent in a container using the infrastructure service."""
    try:
        console.print("🤖 [bold blue]Starting Anvyl AI Agent[/bold blue]")

        from anvyl.infrastructure_client import get_infrastructure_client
        infrastructure_client = get_infrastructure_client(infrastructure_api_url)

        # Start the agent container
        result = infrastructure_client.start_agent_container(
            lmstudio_model=lmstudio_model,
            lmstudio_url=lmstudio_url,
            port=port
        )

        if result is None:
            console.print("[red]❌ Failed to start agent container[/red]")
            raise typer.Exit(1)

        console.print(f"✅ Agent container started successfully")
        console.print(f"🌐 Agent API: http://localhost:{port}")
        console.print(f"📋 API Docs: http://localhost:{port}/docs")
        console.print(f"🧠 LLM: LMStudio at {lmstudio_url}")
        console.print(f"🤖 Model: {lmstudio_model}")
        console.print(f"🐳 Container ID: {result.get('id', 'unknown')}")
        console.print()
        console.print("Use 'anvyl agent logs' to view logs")
        console.print("Use 'anvyl agent stop' to stop the container")

    except Exception as e:
        console.print(f"[red]Error starting agent: {e}[/red]")
        raise typer.Exit(1)

@agent_group.command("stop")
def stop_agent(
    infrastructure_api_url: str = typer.Option("http://localhost:4200", "--infra-api-url", help="Infrastructure API URL")
):
    """Stop the AI agent container using the infrastructure service."""
    try:
        console.print("🛑 [bold blue]Stopping Anvyl AI Agent[/bold blue]")

        from anvyl.infrastructure_client import get_infrastructure_client
        infrastructure_client = get_infrastructure_client(infrastructure_api_url)

        if not infrastructure_client.stop_agent_container():
            console.print("[red]❌ Failed to stop agent container[/red]")
            raise typer.Exit(1)

        console.print("[green]✅ Agent container stopped[/green]")

    except Exception as e:
        console.print(f"[red]Error stopping agent: {e}[/red]")
        raise typer.Exit(1)

@agent_group.command("logs")
def logs_agent(
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines to show"),
    infrastructure_api_url: str = typer.Option("http://localhost:4200", "--infra-api-url", help="Infrastructure API URL")
):
    """Show logs from the AI agent container using the infrastructure service."""
    try:
        console.print("📋 [bold blue]Anvyl AI Agent Logs[/bold blue]")

        from anvyl.infrastructure_client import get_infrastructure_client
        infrastructure_client = get_infrastructure_client(infrastructure_api_url)

        logs = infrastructure_client.get_agent_logs(follow=follow, tail=tail)

        if logs is None:
            console.print("[red]❌ Failed to get agent logs[/red]")
            raise typer.Exit(1)

        console.print(logs)

    except Exception as e:
        console.print(f"[red]Error viewing agent logs: {e}[/red]")
        raise typer.Exit(1)

@agent_group.command("info")
def get_agent_info(
    port: int = typer.Option(4201, "--port", "-p", help="Agent API port"),
    infrastructure_api_url: str = typer.Option("http://localhost:4200", "--infra-api-url", help="Infrastructure API URL")
):
    """Get comprehensive information about the agent including container status and agent capabilities."""
    try:
        import requests

        # First check if the agent container is running
        from anvyl.infrastructure_client import get_infrastructure_client
        infrastructure_client = get_infrastructure_client(infrastructure_api_url)

        container_status = infrastructure_client.get_agent_container_status()
        if not container_status:
            console.print("[yellow]Agent container is not running[/yellow]")
            console.print("[yellow]Use 'anvyl agent start' to start the agent[/yellow]")
            return

        # Display comprehensive information
        console.print("📊 [bold blue]Anvyl AI Agent Information[/bold blue]")

        # Container Information Section
        console.print("\n[bold cyan]Container Information:[/bold cyan]")
        from rich.table import Table

        container_table = Table(show_header=False, box=None)
        container_table.add_column("Property", style="cyan", width=15)
        container_table.add_column("Value", style="green")

        container_table.add_row("Container ID", container_status.get("id", "N/A")[:12])
        container_table.add_row("Name", container_status.get("name", "N/A"))
        container_table.add_row("Status", container_status.get("status", "N/A"))
        container_table.add_row("Image", container_status.get("image", "N/A"))
        container_table.add_row("Created", container_status.get("created", "N/A"))

        # Add ports
        ports = container_status.get("ports", {})
        if ports:
            port_str = ", ".join([f"{k} -> {v[0]['HostPort']}" for k, v in ports.items() if v])
            container_table.add_row("Ports", port_str)

        console.print(container_table)

        # Configuration Information Section
        console.print("\n[bold cyan]Configuration:[/bold cyan]")
        config_table = Table(show_header=False, box=None)
        config_table.add_column("Property", style="cyan", width=15)
        config_table.add_column("Value", style="green")

        # Get model from labels
        labels = container_status.get("labels", {})
        model = labels.get("anvyl.model", "N/A")
        lmstudio_url = labels.get("anvyl.lmstudio_url", "N/A")

        config_table.add_row("Model", model)
        config_table.add_row("LMStudio URL", lmstudio_url)
        config_table.add_row("API Port", str(port))

        console.print(config_table)

        # Try to get agent API information
        try:
            url = f"http://localhost:{port}/agent/info"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                info = response.json()

                # Agent Information Section
                console.print("\n[bold cyan]Agent Information:[/bold cyan]")
                agent_table = Table(show_header=False, box=None)
                agent_table.add_column("Property", style="cyan", width=15)
                agent_table.add_column("Value", style="green")

                agent_table.add_row("Host ID", info.get('host_id', 'N/A'))
                agent_table.add_row("Host IP", info.get('host_ip', 'N/A'))
                agent_table.add_row("LLM Model", info.get('llm_model', 'N/A'))
                agent_table.add_row("Actual Model", info.get('actual_model_name', 'N/A'))

                # Tools information
                tools = info.get('tools_available', [])
                if tools:
                    tools_str = ", ".join(tools)
                    agent_table.add_row("Tools Available", tools_str)
                else:
                    agent_table.add_row("Tools Available", "None")

                console.print(agent_table)

                # Known hosts section
                known_hosts = info.get("known_hosts", {})
                if known_hosts:
                    console.print("\n[bold cyan]Known Hosts:[/bold cyan]")
                    hosts_table = Table()
                    hosts_table.add_column("Host ID", style="cyan")
                    hosts_table.add_column("IP Address", style="green")

                    for host_id, host_ip in known_hosts.items():
                        hosts_table.add_row(host_id, host_ip)

                    console.print(hosts_table)
                else:
                    console.print("\n[bold cyan]Known Hosts:[/bold cyan] [dim]None[/dim]")

            else:
                console.print(f"\n[bold cyan]Agent API:[/bold cyan] [yellow]Not ready (HTTP {response.status_code})[/yellow]")
                console.print("[dim]Agent may still be starting up...[/dim]")

        except requests.exceptions.RequestException as e:
            console.print(f"\n[bold cyan]Agent API:[/bold cyan] [yellow]Not accessible[/yellow]")
            console.print(f"[dim]Error: {e}[/dim]")
            console.print("[dim]Agent may still be starting up...[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting agent info: {e}[/red]")
        raise typer.Exit(1)

@agent_group.command("query")
def query_agent(
    query: str = typer.Argument(..., help="Query to send to the agent"),
    host_id: Optional[str] = typer.Option(None, "--host-id", help="Target host ID (default: local)"),
    port: int = typer.Option(4201, "--port", "-p", help="Agent API port")
):
    """Send a query to an AI agent."""
    try:
        import requests

        if host_id:
            # Query remote agent
            url = f"http://localhost:{port}/agent/remote-query"
            data = {"host_id": host_id, "query": query}
        else:
            # Query local agent
            url = f"http://localhost:{port}/agent/process"
            data = {"query": query}

        console.print(f"🤖 [bold blue]Sending query to agent:[/bold blue] {query}")

        response = requests.post(url, json=data)

        if response.status_code == 200:
            result = response.json()
            console.print(f"✅ [green]Agent response:[/green]")
            console.print(Panel(result.get("response", "No response"), title="Agent Response"))
        else:
            console.print(f"[red]Error: HTTP {response.status_code}[/red]")
            console.print(f"[red]Response: {response.text}[/red]")

    except Exception as e:
        console.print(f"[red]Error querying agent: {e}[/red]")
        raise typer.Exit(1)

@agent_group.command("hosts")
def list_agent_hosts(
    port: int = typer.Option(4201, "--port", "-p", help="Agent API port")
):
    """List hosts known to the agent."""
    try:
        import requests

        url = f"http://localhost:{port}/agent/hosts"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            known_hosts = data.get("known_hosts", {})

            if known_hosts:
                table = Table(title="Known Hosts")
                table.add_column("Host ID", style="cyan")
                table.add_column("IP Address", style="green")

                for host_id, host_ip in known_hosts.items():
                    table.add_row(host_id, host_ip)

                console.print(table)
            else:
                console.print("[yellow]No known hosts[/yellow]")
        else:
            console.print(f"[red]Error: HTTP {response.status_code}[/red]")

    except Exception as e:
        console.print(f"[red]Error listing agent hosts: {e}[/red]")
        raise typer.Exit(1)

@agent_group.command("add-host")
def add_agent_host(
    host_id: str = typer.Argument(..., help="Host ID"),
    host_ip: str = typer.Argument(..., help="Host IP address"),
    port: int = typer.Option(4201, "--port", "-p", help="Agent API port")
):
    """Add a host to the agent's known hosts list."""
    try:
        import requests

        url = f"http://localhost:{port}/agent/hosts"
        data = {"host_id": host_id, "host_ip": host_ip}

        response = requests.post(url, json=data)

        if response.status_code == 200:
            result = response.json()
            console.print(f"✅ [green]{result.get('message', 'Host added')}[/green]")
        else:
            console.print(f"[red]Error: HTTP {response.status_code}[/red]")
            console.print(f"[red]Response: {response.text}[/red]")

    except Exception as e:
        console.print(f"[red]Error adding host: {e}[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()