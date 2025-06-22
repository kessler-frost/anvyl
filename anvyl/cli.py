#!/usr/bin/env python3
"""
Anvyl CLI - Command Line Interface for Anvyl Infrastructure Orchestrator

This module provides a comprehensive CLI for managing Anvyl infrastructure,
including hosts, containers, and monitoring capabilities.
"""

# Standard library imports
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# Third-party imports
import psutil
import requests
import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table

# Local imports - Remove problematic imports that cause pydantic conflicts
# from anvyl.agent.server import start_agent_server  # This causes import issues
from anvyl.database.models import DatabaseManager
# from anvyl.infra.api import main  # This causes import issues
from anvyl.infra.client import get_infrastructure_client
from anvyl.infra.service import get_infrastructure_service
from anvyl.utils import get_service_manager
from anvyl.config import get_settings

# Initialize rich console
console = Console()
app = typer.Typer(
    help="Anvyl Infrastructure Orchestrator CLI",
    no_args_is_help=True,
    add_completion=False
)

# Get settings
settings = get_settings()

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
        if all(os.path.exists(os.path.join(current_dir, f)) for f in ["anvyl", "pyproject.toml"]):
            return current_dir
        current_dir = os.path.dirname(current_dir)

    # If not found, assume current directory
    return os.getcwd()

def start_agent_server(host_id: str, host_ip: str, port: int, mcp_server_url: str, model_provider_url: str):
    """Start the agent server using subprocess to avoid import issues."""
    try:
        cmd = [
            sys.executable, "-m", "anvyl.agent.server",
            "--host-id", host_id,
            "--host-ip", host_ip,
            "--port", str(port),
            "--mcp-server-url", mcp_server_url,
            "--model-provider-url", model_provider_url
        ]

        console.print(f"🚀 Starting agent server with command: {' '.join(cmd)}")
        subprocess.run(cmd)
    except Exception as e:
        console.print(f"[red]Error starting agent server: {e}[/red]")
        raise typer.Exit(1)

# UI and Infrastructure Management Commands
@app.command("up")
def start_all(
    infra_port: int = typer.Option(settings.infra_port, "--infra-port", help="Infrastructure API port"),
    agent_port: int = typer.Option(settings.agent_port, "--agent-port", help="Agent port"),
    mcp_port: int = typer.Option(settings.mcp_port, "--mcp-port", help="MCP server port"),
    model_provider_url: str = typer.Option(settings.model_provider_url, "--model-provider-url", help="Model provider URL"),
    logs: bool = typer.Option(False, "--logs", "-l", help="Show logs after starting")
) -> None:
    """Start all Anvyl services (infrastructure, agent, and MCP)."""
    try:
        console.print("🚀 [bold blue]Starting Anvyl Services[/bold blue]")

        # Get service manager
        service_manager = get_service_manager()

        # Check what services are already running
        all_services = service_manager.get_all_services_status()
        running_services = [name for name, status in all_services.items() if status.get("active", False)]

        if running_services:
            console.print(f"⚠️  [yellow]Found {len(running_services)} already running service(s): {', '.join(running_services)}[/yellow]")

        console.print("🏗️ Starting services in dependency order...")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            # Start services individually with better feedback
            started_services = []
            failed_services = []
            skipped_services = []
            task = progress.add_task("Starting services...", total=None)

            # Start infrastructure API first
            if "anvyl-infrastructure-api" in running_services:
                console.print("⏩ [yellow]Infrastructure API already running[/yellow]")
                skipped_services.append("anvyl-infrastructure-api")
            else:
                progress.update(task, description="Starting infrastructure API...")
                if service_manager.start_infrastructure_api(infra_port):
                    started_services.append("anvyl-infrastructure-api")
                    console.print("✅ [green]Infrastructure API started[/green]")
                else:
                    failed_services.append("anvyl-infrastructure-api")
                    console.print("❌ [red]Failed to start infrastructure API[/red]")

            # Start MCP server
            if "anvyl-mcp-server" in running_services:
                console.print("⏩ [yellow]MCP server already running[/yellow]")
                skipped_services.append("anvyl-mcp-server")
            else:
                progress.update(task, description="Starting MCP server...")
                if service_manager.start_mcp_server(mcp_port):
                    started_services.append("anvyl-mcp-server")
                    console.print("✅ [green]MCP server started[/green]")
                else:
                    failed_services.append("anvyl-mcp-server")
                    console.print("❌ [red]Failed to start MCP server[/red]")

            # Start agent service
            if "anvyl-agent" in running_services:
                console.print("⏩ [yellow]Agent service already running[/yellow]")
                skipped_services.append("anvyl-agent")
            else:
                progress.update(task, description="Starting agent service...")
                if service_manager.start_agent_service(
                    host_id="local",
                    host_ip="127.0.0.1",
                    port=agent_port,
                    model_provider_url=model_provider_url,
                    mcp_server_url=f"http://localhost:{mcp_port}/mcp/"
                ):
                    started_services.append("anvyl-agent")
                    console.print("✅ [green]Agent service started[/green]")
                else:
                    failed_services.append("anvyl-agent")
                    console.print("❌ [red]Failed to start agent service[/red]")

            progress.update(task, description="Services started", visible=False)

        # Summary
        total_services = len(started_services) + len(skipped_services)
        if started_services and not failed_services:
            console.print(f"\n✅ [bold green]All services are now running! ({len(started_services)} started, {len(skipped_services)} already running)[/bold green]")
        elif started_services and failed_services:
            console.print(f"\n⚠️ [yellow]Partial success: {len(started_services)} started, {len(failed_services)} failed, {len(skipped_services)} already running[/yellow]")
            console.print(f"[red]Failed services: {', '.join(failed_services)}[/red]")
            raise typer.Exit(1)
        elif skipped_services and not started_services and not failed_services:
            console.print(f"\n✅ [bold green]All services were already running! ({len(skipped_services)} services)[/bold green]")
        elif failed_services:
            console.print(f"\n❌ [red]Failed to start services: {', '.join(failed_services)}[/red]")
            raise typer.Exit(1)

        if total_services > 0:
            console.print("\n🌐 [bold]Access Points:[/bold]")
            console.print(f"  • Infrastructure API: {settings.infra_url}")
            console.print(f"  • Agent API:   {settings.agent_url}")
            console.print(f"  • MCP Server:  {settings.mcp_server_url}")

        if logs:
            console.print("💡 Use 'anvyl down' to stop the services")

    except Exception as e:
        console.print(f"[red]Error starting services: {e}[/red]")
        raise typer.Exit(1)

@app.command("down")
def stop_infrastructure():
    """Stop the Anvyl infrastructure stack."""
    try:
        console.print("🛑 [bold red]Stopping Anvyl Infrastructure Stack[/bold red]")

        # Get service manager
        service_manager = get_service_manager()

        # Check what services are currently running
        all_services = service_manager.get_all_services_status()
        running_services = [name for name, status in all_services.items() if status.get("active", False)]

        if not running_services:
            console.print("ℹ️ [yellow]No running services found[/yellow]")
            return

        console.print(f"📋 Found {len(running_services)} running service(s): {', '.join(running_services)}")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            # Stop services individually with better feedback
            stopped_services = []
            failed_services = []

            # Stop agent first
            if "anvyl-agent" in running_services:
                progress.update(progress.add_task("Stopping agent service...", total=None))
                if service_manager.stop_agent_service():
                    stopped_services.append("anvyl-agent")
                    console.print("✅ [green]Agent service stopped[/green]")
                else:
                    failed_services.append("anvyl-agent")
                    console.print("❌ [red]Failed to stop agent service[/red]")

            # Stop MCP server
            if "anvyl-mcp-server" in running_services:
                progress.update(progress.add_task("Stopping MCP server...", total=None))
                if service_manager.stop_mcp_server():
                    stopped_services.append("anvyl-mcp-server")
                    console.print("✅ [green]MCP server stopped[/green]")
                else:
                    failed_services.append("anvyl-mcp-server")
                    console.print("❌ [red]Failed to stop MCP server[/red]")

            # Stop infrastructure API
            if "anvyl-infrastructure-api" in running_services:
                progress.update(progress.add_task("Stopping infrastructure API...", total=None))
                if service_manager.stop_infrastructure_api():
                    stopped_services.append("anvyl-infrastructure-api")
                    console.print("✅ [green]Infrastructure API stopped[/green]")
                else:
                    failed_services.append("anvyl-infrastructure-api")
                    console.print("❌ [red]Failed to stop infrastructure API[/red]")

        # Summary
        if stopped_services and not failed_services:
            console.print(f"\n✅ [bold green]All services stopped successfully! ({len(stopped_services)} services)[/bold green]")
        elif stopped_services and failed_services:
            console.print(f"\n⚠️ [yellow]Partial success: {len(stopped_services)} stopped, {len(failed_services)} failed[/yellow]")
            console.print(f"[red]Failed services: {', '.join(failed_services)}[/red]")
            raise typer.Exit(1)
        elif failed_services:
            console.print(f"\n❌ [red]Failed to stop any services: {', '.join(failed_services)}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error stopping infrastructure: {e}[/red]")
        raise typer.Exit(1)

@app.command("status")
def show_status():
    """Show status of all Anvyl services."""
    try:
        service_manager = get_service_manager()
        db = service_manager.db

        # Get all service statuses from database
        services = db.list_service_statuses()

        if not services:
            console.print("ℹ️ [yellow]No services found in database[/yellow]")
            return

        # Create a table to display services
        table = Table(title="Anvyl Services Status")
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("PID", style="blue")
        table.add_column("Port", style="yellow")
        table.add_column("Started", style="white")
        table.add_column("Last Heartbeat", style="white")

        for service in services:
            # Check if process is actually running
            is_active = service_manager.is_service_running(service.id)

            # Color code the status
            if service.status == "running" and is_active:
                status_style = "green"
                status_text = "🟢 Running"
            elif service.status == "running" and not is_active:
                status_style = "red"
                status_text = "🔴 Stale"
            elif service.status == "stopped":
                status_style = "yellow"
                status_text = "🟡 Stopped"
            elif service.status == "error":
                status_style = "red"
                status_text = "🔴 Error"
            else:
                status_style = "white"
                status_text = service.status

            table.add_row(
                service.id,
                service.service_type,
                status_text,
                str(service.pid) if service.pid else "N/A",
                str(service.port) if service.port else "N/A",
                service.started_at.strftime("%H:%M:%S") if service.started_at else "N/A",
                service.last_heartbeat.strftime("%H:%M:%S") if service.last_heartbeat else "N/A"
            )

        console.print(table)

        # Show summary
        running_count = len([s for s in services if s.status == "running" and service_manager.is_service_running(s.id)])
        total_count = len(services)
        console.print(f"\n📊 Summary: {running_count}/{total_count} services running")

    except Exception as e:
        console.print(f"[red]Error showing service status: {e}[/red]")
        raise typer.Exit(1)

@app.command("purge")
def purge_data(
    force: bool = typer.Option(False, "--force", "-f", help="Force purge without confirmation")
):
    """Purge all Anvyl data including database and ~/.anvyl directory."""

    # Get paths to clean up
    anvyl_home = Path.home() / ".anvyl"
    db_file = anvyl_home / "anvyl.db"

    # Check what exists
    items_to_remove = []

    if anvyl_home.exists():
        items_to_remove.append(f"~/.anvyl directory ({anvyl_home})")

    if db_file.exists():
        items_to_remove.append(f"Database file ({db_file})")

    if not items_to_remove:
        console.print("✅ [green]No Anvyl data found to purge[/green]")
        return

    # Show what will be removed
    console.print("🗑️ [bold red]The following items will be permanently deleted:[/bold red]")
    for item in items_to_remove:
        console.print(f"  • {item}")

    # Ask for confirmation unless force flag is used
    if not force:
        if not Confirm.ask("Are you sure you want to proceed?", default=False):
            console.print("❌ [yellow]Purge cancelled[/yellow]")
            raise typer.Exit(0)

    # Stop all services only after confirmation
    try:
        service_manager = get_service_manager()
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Stopping all services...", total=None)
            service_manager.stop_all_services()
        console.print("✅ [green]All services stopped before purge[/green]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not stop all services before purge: {e}[/yellow]")

    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Purging Anvyl data...", total=None)

            # Remove ~/.anvyl directory
            if anvyl_home.exists():
                shutil.rmtree(anvyl_home)
                console.print(f"✅ [green]Removed ~/.anvyl directory[/green]")

            # Remove database file
            if db_file.exists():
                db_file.unlink()
                console.print(f"✅ [green]Removed database file[/green]")

        console.print("\n🎉 [bold green]Anvyl data purged successfully![/bold green]")
        console.print("\n💡 [dim]You can now start fresh with 'anvyl up'[/dim]")

    except Exception as e:
        console.print(f"[red]Error during purge: {e}[/red]")
        raise typer.Exit(1)

@app.command("restart")
def restart_all(
    infra_port: int = typer.Option(settings.infra_port, "--infra-port", help="Infrastructure API port"),
    agent_port: int = typer.Option(settings.agent_port, "--agent-port", help="Agent port"),
    mcp_port: int = typer.Option(settings.mcp_port, "--mcp-port", help="MCP server port"),
    model_provider_url: str = typer.Option(settings.model_provider_url, "--model-provider-url", help="Model provider URL")
):
    """Restart all Anvyl services."""
    try:
        console.print("🔄 [bold blue]Restarting Anvyl Services[/bold blue]")

        # Get service manager
        service_manager = get_service_manager()

        # Check what services are currently running
        all_services = service_manager.get_all_services_status()
        running_services = [name for name, status in all_services.items() if status.get("active", False)]

        if not running_services:
            console.print("⚠️  [yellow]No running services found. Starting all services instead...[/yellow]")
            # Delegate to the start command logic by calling start_all directly
            start_all(
                infra_port=infra_port, agent_port=agent_port, mcp_port=mcp_port,
                model_provider_url=model_provider_url
            )
            return

        # Define all services that should be restarted (not just currently running ones)
        all_service_names = ["anvyl-infrastructure-api", "anvyl-mcp-server", "anvyl-agent"]
        services_to_restart = [name for name in all_service_names if name in all_services]

        console.print(f"📋 Found {len(running_services)} running service(s): {', '.join(running_services)}")
        console.print("🔄 Restarting services (stop → start)...")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            # Phase 1: Stop all services that exist (regardless of status)
            console.print("\n🛑 [bold red]Stopping Services[/bold red]")
            stopped_services = []
            stop_failed_services = []
            task = progress.add_task("Stopping services...", total=None)

            # Stop services in reverse dependency order
            if "anvyl-agent" in services_to_restart:
                progress.update(task, description="Stopping agent service...")
                if service_manager.stop_agent_service():
                    stopped_services.append("anvyl-agent")
                    console.print("✅ [green]Agent service stopped[/green]")
                else:
                    stop_failed_services.append("anvyl-agent")
                    console.print("❌ [red]Failed to stop agent service[/red]")

            if "anvyl-mcp-server" in services_to_restart:
                progress.update(task, description="Stopping MCP server...")
                if service_manager.stop_mcp_server():
                    stopped_services.append("anvyl-mcp-server")
                    console.print("✅ [green]MCP server stopped[/green]")
                else:
                    stop_failed_services.append("anvyl-mcp-server")
                    console.print("❌ [red]Failed to stop MCP server[/red]")

            if "anvyl-infrastructure-api" in services_to_restart:
                progress.update(task, description="Stopping infrastructure API...")
                if service_manager.stop_infrastructure_api():
                    stopped_services.append("anvyl-infrastructure-api")
                    console.print("✅ [green]Infrastructure API stopped[/green]")
                else:
                    stop_failed_services.append("anvyl-infrastructure-api")
                    console.print("❌ [red]Failed to stop infrastructure API[/red]")

            # Check stop phase results
            if stop_failed_services:
                console.print(f"\n❌ [red]Failed to stop some services: {', '.join(stop_failed_services)}[/red]")
                console.print("[yellow]Proceeding with restart for stopped services only...[/yellow]")

            # Phase 2: Start services back up
            console.print("\n🚀 [bold blue]Starting Services[/bold blue]")
            started_services = []
            start_failed_services = []

            # Start services in dependency order (all services that should be restarted)
            if "anvyl-infrastructure-api" in services_to_restart:
                progress.update(task, description="Starting infrastructure API...")
                if service_manager.start_infrastructure_api(host=settings.infra_host, port=infra_port):
                    started_services.append("anvyl-infrastructure-api")
                    console.print("✅ [green]Infrastructure API started[/green]")
                else:
                    start_failed_services.append("anvyl-infrastructure-api")
                    console.print("❌ [red]Failed to start infrastructure API[/red]")

            if "anvyl-mcp-server" in services_to_restart:
                progress.update(task, description="Starting MCP server...")
                if service_manager.start_mcp_server(mcp_port):
                    started_services.append("anvyl-mcp-server")
                    console.print("✅ [green]MCP server started[/green]")
                else:
                    start_failed_services.append("anvyl-mcp-server")
                    console.print("❌ [red]Failed to start MCP server[/red]")

            if "anvyl-agent" in services_to_restart:
                progress.update(task, description="Starting agent service...")
                if service_manager.start_agent_service(
                    host_id="local", host_ip="127.0.0.1", port=agent_port,
                    model_provider_url=model_provider_url,
                    mcp_server_url=f"http://localhost:{mcp_port}/mcp/"
                ):
                    started_services.append("anvyl-agent")
                    console.print("✅ [green]Agent service started[/green]")
                else:
                    start_failed_services.append("anvyl-agent")
                    console.print("❌ [red]Failed to start agent service[/red]")

            progress.update(task, description="Restart complete", visible=False)

        # Final summary
        if started_services and not start_failed_services and not stop_failed_services:
            console.print(f"\n✅ [bold green]All services restarted successfully! ({len(started_services)} services)[/bold green]")
        elif started_services and (start_failed_services or stop_failed_services):
            total_failed = len(set(start_failed_services + stop_failed_services))
            console.print(f"\n⚠️ [yellow]Partial restart: {len(started_services)} restarted, {total_failed} failed[/yellow]")
            if start_failed_services:
                console.print(f"[red]Failed to start: {', '.join(start_failed_services)}[/red]")
            if stop_failed_services:
                console.print(f"[red]Failed to stop: {', '.join(stop_failed_services)}[/red]")
            raise typer.Exit(1)
        elif start_failed_services or stop_failed_services:
            console.print(f"\n❌ [red]Restart failed[/red]")
            raise typer.Exit(1)

        if started_services:
            console.print("\n🌐 [bold]Access Points:[/bold]")
            console.print(f"  • Infrastructure API: {settings.infra_url}")
            console.print(f"  • Agent API:   {settings.agent_url}")
            console.print(f"  • MCP Server:  {settings.mcp_server_url}")

    except Exception as e:
        console.print(f"[red]Error restarting services: {e}[/red]")
        raise typer.Exit(1)

# Infrastructure API Management Commands
infra_group = typer.Typer(
    help="Manage the Anvyl Infrastructure API",
    no_args_is_help=True
)
app.add_typer(infra_group, name="infra")

@infra_group.command("up")
def start_infra_api(
    host: str = typer.Option(settings.infra_host, "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(settings.infra_port, "--port", "-p", help="Port to bind to"),
    background: bool = typer.Option(True, "--background/--foreground", help="Run in background")
):
    """Start the Anvyl infrastructure API."""
    try:
        # Get service manager
        service_manager = get_service_manager()

        console.print("🚀 [bold blue]Starting Infrastructure API[/bold blue]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Starting infrastructure API...", total=None)

            # Start the infrastructure API service
            success = service_manager.start_infrastructure_api(host, port)

            if success:
                console.print("✅ [green]Infrastructure API started successfully![/green]")
                console.print(f"🌐 Infrastructure API available at: http://{host}:{port}")
            else:
                console.print("[red]Failed to start Infrastructure API[/red]")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error starting Infrastructure API: {e}[/red]")
        raise typer.Exit(1)

@infra_group.command("down")
def stop_infra_api():
    """Stop the infrastructure API service."""
    try:
        # Get service manager
        service_manager = get_service_manager()

        console.print("🛑 [bold red]Stopping Infrastructure API[/bold red]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Stopping service...", total=None)

            success = service_manager.stop_infrastructure_api()

            if success:
                console.print("✅ [green]Infrastructure API stopped successfully![/green]")
            else:
                console.print("[red]Failed to stop Infrastructure API[/red]")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error stopping Infrastructure API: {e}[/red]")
        raise typer.Exit(1)

@infra_group.command("status")
def status_infra_api():
    """Show status of the infrastructure API service."""
    try:
        # Get service manager
        service_manager = get_service_manager()

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Checking service status...", total=None)
            status = service_manager.get_service_status("anvyl-infrastructure-api")

        if status is None:
            console.print("[yellow]Infrastructure API is not running[/yellow]")
        elif status.get("active"):
            console.print("✅ [green]Infrastructure API is running[/green]")

            # Create status table
            status_table = Table(title="Infrastructure API Status")
            status_table.add_column("Property", style="cyan")
            status_table.add_column("Value", style="green")

            status_table.add_row("Status", "Running")
            status_table.add_row("PID", str(status.get("pid", "N/A")))
            status_table.add_row("Port", "4200")
            status_table.add_row("Start Time", status.get("start_time", "N/A"))
            status_table.add_row("Runtime", status.get("runtime", "N/A"))

            console.print(status_table)
        else:
            console.print("[red]Infrastructure API is stopped[/red]")

    except Exception as e:
        console.print(f"[red]Error checking Infrastructure API status: {e}[/red]")
        raise typer.Exit(1)

@infra_group.command("logs")
def logs_infra_api(
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    lines: int = typer.Option(100, "--lines", "-n", help="Number of lines to show")
):
    """Show logs for the infrastructure API service with enhanced formatting."""
    try:
        service_manager = get_service_manager()
        service_name = "anvyl-infrastructure-api"

        def get_service_status() -> str:
            try:
                status = service_manager.get_service_status(service_name)
                if status and status.get("active"):
                    pid = status.get("pid", "N/A")
                    return f"[bold green]●[/bold green] [green]Running[/green] [dim]PID:{pid}[/dim]"
                else:
                    return f"[bold red]●[/bold red] [red]Stopped[/red]"
            except:
                return f"[bold yellow]●[/bold yellow] [yellow]Unknown[/yellow]"

        def format_log_line(line: str) -> str:
            if not line.strip():
                return ""

            if any(level in line.upper() for level in ['ERROR:', 'CRITICAL:', 'EXCEPTION', 'FAILED']):
                return f"[bold red]🚨[/bold red] [red]{line}[/red]"
            elif any(level in line.upper() for level in ['WARNING:', 'WARN:']):
                return f"[bold yellow]⚠️[/bold yellow] [yellow]{line}[/yellow]"
            elif 'INFO:' in line.upper():
                return f"[bold blue]ℹ️[/bold blue] [bright_blue]{line}[/bright_blue]"
            elif 'DEBUG:' in line.upper():
                return f"[dim]🔍 {line}[/dim]"
            elif any(word in line for word in ['Starting', '✅', 'Started', 'Ready', 'SUCCESS']):
                return f"[bold green]🚀[/bold green] [green]{line}[/green]"
            elif any(word in line for word in ['Stopping', 'Stopped', 'Shutdown']):
                return f"[bold magenta]🛑[/bold magenta] [magenta]{line}[/magenta]"
            elif any(indicator in line for indicator in ['127.0.0.1', 'localhost', 'HTTP/', 'GET', 'POST']):
                return f"[bold cyan]🌐[/bold cyan] [cyan]{line}[/cyan]"
            elif 'Docker' in line or 'container' in line.lower():
                return f"[bold blue]🐳[/bold blue] [blue]{line}[/blue]"
            elif any(word in line for word in ['uvicorn', 'fastapi', 'server']):
                return f"[bold purple]⚡[/bold purple] [purple]{line}[/purple]"
            else:
                return f"[white]📝 {line}[/white]"

        if follow:
            console.print(f"[bold cyan]🔧 Infrastructure API Logs[/bold cyan] [dim]- Following (Press Ctrl+C to stop)[/dim]")

            try:
                with Live(refresh_per_second=2, console=console) as live:
                    while True:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        status = get_service_status()

                        logs = service_manager.get_service_logs(service_name, lines=20)
                        if logs:
                            formatted_lines = []
                            for line in logs.splitlines()[-20:]:
                                if line.strip():
                                    formatted_lines.append(format_log_line(line))
                            content = "\n".join(formatted_lines)
                        else:
                            content = "[dim]No logs available[/dim]"

                        title = f"🔧 INFRASTRUCTURE API {status} [dim]({timestamp})[/dim]"
                        panel = Panel(content, title=title, border_style="magenta", padding=(1, 2))
                        live.update(panel)
                        time.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]📋 Log following stopped[/yellow]")
        else:
            timestamp = datetime.now().strftime('%H:%M:%S')
            status = get_service_status()

            logs = service_manager.get_service_logs(service_name, lines)
            if logs:
                formatted_lines = []
                for line in logs.splitlines():
                    if line.strip():
                        formatted_lines.append(format_log_line(line))
                content = "\n".join(formatted_lines)
            else:
                content = "[dim]No logs available[/dim]"

            title = f"🔧 INFRASTRUCTURE API {status} [dim]({timestamp})[/dim]"
            panel = Panel(content, title=title, border_style="magenta", padding=(1, 2))
            console.print(panel)

    except Exception as e:
        console.print(f"[red]Error showing Infrastructure API logs: {e}[/red]")
        raise typer.Exit(1)

@infra_group.command("restart")
def restart_infra_api(
    host: str = typer.Option(settings.infra_host, "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(settings.infra_port, "--port", "-p", help="Port to bind to")
):
    """Restart the Anvyl infrastructure API."""
    try:
        # Get service manager
        service_manager = get_service_manager()

        console.print("🔄 [bold blue]Restarting Infrastructure API[/bold blue]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Restarting infrastructure API...", total=None)

            # Use the service manager's restart method
            success = service_manager.restart_service("anvyl-infrastructure-api")

            if success:
                console.print("✅ [green]Infrastructure API restarted successfully![/green]")
                console.print(f"🌐 Infrastructure API available at: http://{host}:{port}")
            else:
                console.print("[red]Failed to restart Infrastructure API[/red]")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error restarting Infrastructure API: {e}[/red]")
        raise typer.Exit(1)

# Create a simple custom agent command that handles direct queries
@app.command("agent")
def agent_command(
    query_or_subcommand: str = typer.Argument(..., help="Query to send to agent OR subcommand (up, down, logs, etc.)"),
    host_id: Optional[str] = typer.Option(None, "--host-id", help="Target host ID (default: local)"),
    port: int = typer.Option(settings.agent_port, "--port", "-p", help="Agent API port"),
    model_provider_url: str = typer.Option(settings.model_provider_url, "--model-provider-url", help="Model provider API URL"),
    mcp_server_url: str = typer.Option(settings.mcp_server_url, "--mcp-server-url", help="MCP server URL"),
    background: bool = typer.Option(True, "--background/--foreground", help="Run in background"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    lines: int = typer.Option(100, "--lines", "-n", help="Number of lines to show")
):
    """
    Send queries to AI agent or manage agent service.

    Examples:
      anvyl agent "list docker images"     # Send query
      anvyl agent up                       # Start agent
      anvyl agent down                     # Stop agent
      anvyl agent logs                     # Show logs
    """
    # Handle subcommands
    if query_or_subcommand == "up":
        _agent_up(model_provider_url, port, "local", "127.0.0.1", mcp_server_url, background)
    elif query_or_subcommand == "down":
        _agent_down()
    elif query_or_subcommand == "logs":
        _agent_logs(follow, lines)
    elif query_or_subcommand == "restart":
        _agent_restart(model_provider_url, port, "local", "127.0.0.1", mcp_server_url)
    elif query_or_subcommand == "info":
        _agent_info(port)
    elif query_or_subcommand == "hosts":
        _agent_hosts(port)
    elif query_or_subcommand == "query":
        # This shouldn't happen since we handle queries directly, but for backwards compatibility
        console.print("[yellow]Note: You can now send queries directly: anvyl agent \"your query\"[/yellow]")
        console.print("[yellow]Please provide the query as an argument[/yellow]")
    else:
        # Treat as a query
        _execute_agent_query(query_or_subcommand, host_id, port)

def _execute_agent_query(query: str, host_id: Optional[str] = None, port: int = None):
    """Execute a query to the agent."""
    port = port or settings.agent_port
    try:
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
            output = result.get("response", "No response")

            # Parse AgentRunResult-style output
            if isinstance(output, dict) and "output" in output:
                output = output["output"]
            elif isinstance(output, str):
                # Handle AgentRunResult string format
                if output.startswith("AgentRunResult("):
                    match = re.search(r'output=(\"|\')((?:[^\\]|\\.)*?)\1', output, re.DOTALL)
                    if match:
                        output = match.group(2)
                        output = output.replace('\\"', '"').replace("\\'", "'").replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
                else:
                    output = output.replace('\\"', '"').replace("\\'", "'")

            console.print(f"✅ [green]Agent response:[/green]")
            if not isinstance(output, str):
                output = json.dumps(output, indent=2)
            console.print(Panel(output, title="Agent Response"))
        else:
            console.print(f"[red]Error: HTTP {response.status_code}[/red]")
            console.print(f"[red]Response: {response.text}[/red]")

    except Exception as e:
        console.print(f"[red]Error querying agent: {e}[/red]")
        raise typer.Exit(1)

# Helper functions for agent subcommands
def _agent_up(model_provider_url: str, port: int, host_id: str, host_ip: str, mcp_server_url: str, background: bool):
    """Start the agent."""
    try:
        service_manager = get_service_manager()
        service_status = service_manager.get_service_status("anvyl-agent")
        if service_status and service_status.get("active"):
            console.print("ℹ️ [yellow]Anvyl AI Agent is already running[/yellow]")
            return

        console.print(f"🚀 [bold blue]Starting Anvyl AI Agent on {host_ip}:{port}[/bold blue]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Starting agent...", total=None)
            success = service_manager.start_agent_service(
                host_id=host_id, host_ip=host_ip, port=port,
                model_provider_url=model_provider_url, mcp_server_url=mcp_server_url
            )

            if success:
                console.print("✅ [green]Agent started successfully![/green]")
                console.print(f"🌐 Agent API available at: http://{host_ip}:{port}")
                console.print(f"🤖 Using model provider: {model_provider_url}")
                console.print(f"🔗 MCP Server: {mcp_server_url}")
                console.print("📋 Use 'anvyl agent logs' to view logs")
            else:
                console.print("[red]Failed to start agent[/red]")
                raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error starting agent: {e}[/red]")
        raise typer.Exit(1)

def _agent_down():
    """Stop the agent."""
    try:
        service_manager = get_service_manager()
        console.print("🛑 [bold red]Stopping Anvyl AI Agent[/bold red]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Stopping agent...", total=None)
            success = service_manager.stop_agent_service()

            if success:
                console.print("✅ [green]Agent stopped successfully![/green]")
            else:
                console.print("[red]Failed to stop agent[/red]")
                raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error stopping agent: {e}[/red]")
        raise typer.Exit(1)

def _agent_logs(follow: bool, lines: int):
    """Show agent logs with enhanced formatting."""
    try:
        service_manager = get_service_manager()
        service_name = "anvyl-agent"

        def get_service_status() -> str:
            try:
                status = service_manager.get_service_status(service_name)
                if status and status.get("active"):
                    pid = status.get("pid", "N/A")
                    return f"[bold green]●[/bold green] [green]Running[/green] [dim]PID:{pid}[/dim]"
                else:
                    return f"[bold red]●[/bold red] [red]Stopped[/red]"
            except:
                return f"[bold yellow]●[/bold yellow] [yellow]Unknown[/yellow]"

        def format_log_line(line: str) -> str:
            if not line.strip():
                return ""

            if any(level in line.upper() for level in ['ERROR:', 'CRITICAL:', 'EXCEPTION', 'FAILED']):
                return f"[bold red]🚨[/bold red] [red]{line}[/red]"
            elif any(level in line.upper() for level in ['WARNING:', 'WARN:']):
                return f"[bold yellow]⚠️[/bold yellow] [yellow]{line}[/yellow]"
            elif 'INFO:' in line.upper():
                return f"[bold blue]ℹ️[/bold blue] [bright_blue]{line}[/bright_blue]"
            elif 'DEBUG:' in line.upper():
                return f"[dim]🔍 {line}[/dim]"
            elif any(word in line for word in ['Starting', '✅', 'Started', 'Ready', 'SUCCESS']):
                return f"[bold green]🚀[/bold green] [green]{line}[/green]"
            elif any(word in line for word in ['Stopping', 'Stopped', 'Shutdown']):
                return f"[bold magenta]🛑[/bold magenta] [magenta]{line}[/magenta]"
            elif any(indicator in line for indicator in ['Agent', 'AI', 'LLM', 'model']):
                return f"[bold cyan]🤖[/bold cyan] [cyan]{line}[/cyan]"
            elif 'query' in line.lower() or 'request' in line.lower():
                return f"[bold purple]💬[/bold purple] [purple]{line}[/purple]"
            elif 'response' in line.lower() or 'answer' in line.lower():
                return f"[bold green]💡[/bold green] [green]{line}[/green]"
            elif any(word in line for word in ['tool', 'function', 'execute']):
                return f"[bold magenta]🔧[/bold magenta] [magenta]{line}[/magenta]"
            else:
                return f"[white]📝 {line}[/white]"

        if follow:
            console.print(f"[bold cyan]🤖 Agent Logs[/bold cyan] [dim]- Following (Press Ctrl+C to stop)[/dim]")

            try:
                with Live(refresh_per_second=2, console=console) as live:
                    while True:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        status = get_service_status()

                        logs = service_manager.get_service_logs(service_name, lines=20)
                        if logs:
                            formatted_lines = []
                            for line in logs.splitlines()[-20:]:
                                if line.strip():
                                    formatted_lines.append(format_log_line(line))
                            content = "\n".join(formatted_lines)
                        else:
                            content = "[dim]No logs available[/dim]"

                        title = f"🤖 ANVYL AGENT {status} [dim]({timestamp})[/dim]"
                        panel = Panel(content, title=title, border_style="green", padding=(1, 2))
                        live.update(panel)
                        time.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]📋 Log following stopped[/yellow]")
        else:
            timestamp = datetime.now().strftime('%H:%M:%S')
            status = get_service_status()

            logs = service_manager.get_service_logs(service_name, lines)
            if logs:
                formatted_lines = []
                for line in logs.splitlines():
                    if line.strip():
                        formatted_lines.append(format_log_line(line))
                content = "\n".join(formatted_lines)
            else:
                content = "[dim]No logs available[/dim]"

            title = f"🤖 ANVYL AGENT {status} [dim]({timestamp})[/dim]"
            panel = Panel(content, title=title, border_style="green", padding=(1, 2))
            console.print(panel)
    except Exception as e:
        console.print(f"[red]Error showing agent logs: {e}[/red]")
        raise typer.Exit(1)

def _agent_restart(model_provider_url: str, port: int, host_id: str, host_ip: str, mcp_server_url: str):
    """Restart the agent."""
    try:
        service_manager = get_service_manager()
        console.print("🔄 [bold blue]Restarting Anvyl AI Agent[/bold blue]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Restarting agent...", total=None)
            success = service_manager.restart_service("anvyl-agent")

            if success:
                console.print("✅ [green]Agent restarted successfully![/green]")
                console.print(f"🌐 Agent API available at: http://{host_ip}:{port}")
                console.print(f"🤖 Using model provider: {model_provider_url}")
                console.print(f"🔗 MCP Server: {mcp_server_url}")
            else:
                console.print("[red]Failed to restart agent[/red]")
                raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error restarting agent: {e}[/red]")
        raise typer.Exit(1)

def _agent_info(port: int):
    """Get agent info."""
    try:
        console.print("📊 [bold blue]Anvyl AI Agent Information[/bold blue]")

        url = f"http://localhost:{port}/agent/info"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            info = response.json()
            table = Table(show_header=False, box=None)
            table.add_column("Property", style="cyan", width=15)
            table.add_column("Value", style="green")

            for key, value in info.items():
                table.add_row(key.replace('_', ' ').title(), str(value))

            console.print(table)
        else:
            console.print(f"[red]Error: HTTP {response.status_code}[/red]")
    except Exception as e:
        console.print(f"[red]Error getting agent info: {e}[/red]")
        raise typer.Exit(1)

def _agent_hosts(port: int):
    """List agent hosts."""
    try:
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

# Agent Management Commands (keeping the old group for reference/backwards compatibility)
agent_group = typer.Typer(
    help="Manage AI agents for infrastructure automation.",
    no_args_is_help=True,
    add_completion=False
)

@agent_group.command("up")
def agent_up(
    model_provider_url: str = typer.Option(settings.model_provider_url, "--model-provider-url", help="Model provider API URL"),
    port: int = typer.Option(settings.agent_port, "--port", help="Agent port"),
    host_id: str = typer.Option(settings.agent_host_id, "--host-id", help="Host ID for this agent"),
    host_ip: str = typer.Option(settings.agent_host, "--host-ip", help="Host IP for this agent"),
    mcp_server_url: str = typer.Option(settings.mcp_server_url, "--mcp-server-url", help="MCP server URL"),
    background: bool = typer.Option(True, "--background/--foreground", help="Run in background")
):
    """Start the Anvyl AI Agent."""
    try:
        # Get service manager
        service_manager = get_service_manager()

        # Check if service is already running
        service_status = service_manager.get_service_status("anvyl-agent")
        if service_status and service_status.get("active"):
            console.print("ℹ️ [yellow]Anvyl AI Agent is already running[/yellow]")
            console.print(f"   PID: {service_status.get('pid', 'N/A')}")
            console.print(f"   Port: {service_status.get('port', 'N/A')}")
            console.print(f"   Started: {service_status.get('start_time', 'N/A')}")
            return

        if background:
            console.print(f"🚀 [bold blue]Starting Anvyl AI Agent on {host_ip}:{port}[/bold blue]")

            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Starting agent...", total=None)

                success = service_manager.start_agent_service(
                    host_id=host_id,
                    host_ip=host_ip,
                    port=port,
                    model_provider_url=model_provider_url,
                    mcp_server_url=mcp_server_url
                )

                if success:
                    console.print("✅ [green]Agent started successfully![/green]")
                    console.print(f"🌐 Agent API available at: http://{host_ip}:{port}")
                    console.print(f"🤖 Using model provider: {model_provider_url}")
                    console.print(f"🔗 MCP Server: {mcp_server_url}")
                    console.print("📋 Use 'anvyl agent logs' to view logs")
                else:
                    console.print("[red]Failed to start agent[/red]")
                    raise typer.Exit(1)
        else:
            # Run in foreground
            console.print(f"🚀 [bold blue]Starting Anvyl AI Agent on {host_ip}:{port} (foreground)[/bold blue]")
            start_agent_server(
                host_id=host_id,
                host_ip=host_ip,
                port=port,
                mcp_server_url=mcp_server_url,
                model_provider_url=model_provider_url
            )

    except Exception as e:
        console.print(f"[red]Error starting agent: {e}[/red]")
        raise typer.Exit(1)

@agent_group.command("down")
def down_agent():
    """Stop the Anvyl AI Agent service."""
    try:
        # Get service manager
        service_manager = get_service_manager()

        console.print("🛑 [bold red]Stopping Anvyl AI Agent[/bold red]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Stopping agent...", total=None)

            success = service_manager.stop_agent_service()

            if success:
                console.print("✅ [green]Agent stopped successfully![/green]")
            else:
                console.print("[red]Failed to stop agent[/red]")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error stopping agent: {e}[/red]")
        raise typer.Exit(1)

@agent_group.command("logs")
def logs_agent(
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    lines: int = typer.Option(100, "--lines", "-n", help="Number of lines to show")
):
    """Show logs for the Anvyl AI Agent service with enhanced formatting."""
    try:
        service_manager = get_service_manager()
        service_name = "anvyl-agent"

        def get_service_status() -> str:
            try:
                status = service_manager.get_service_status(service_name)
                if status and status.get("active"):
                    pid = status.get("pid", "N/A")
                    return f"[bold green]●[/bold green] [green]Running[/green] [dim]PID:{pid}[/dim]"
                else:
                    return f"[bold red]●[/bold red] [red]Stopped[/red]"
            except:
                return f"[bold yellow]●[/bold yellow] [yellow]Unknown[/yellow]"

        def format_log_line(line: str) -> str:
            if not line.strip():
                return ""

            if any(level in line.upper() for level in ['ERROR:', 'CRITICAL:', 'EXCEPTION', 'FAILED']):
                return f"[bold red]🚨[/bold red] [red]{line}[/red]"
            elif any(level in line.upper() for level in ['WARNING:', 'WARN:']):
                return f"[bold yellow]⚠️[/bold yellow] [yellow]{line}[/yellow]"
            elif 'INFO:' in line.upper():
                return f"[bold blue]ℹ️[/bold blue] [bright_blue]{line}[/bright_blue]"
            elif 'DEBUG:' in line.upper():
                return f"[dim]🔍 {line}[/dim]"
            elif any(word in line for word in ['Starting', '✅', 'Started', 'Ready', 'SUCCESS']):
                return f"[bold green]🚀[/bold green] [green]{line}[/green]"
            elif any(word in line for word in ['Stopping', 'Stopped', 'Shutdown']):
                return f"[bold magenta]🛑[/bold magenta] [magenta]{line}[/magenta]"
            elif any(indicator in line for indicator in ['Agent', 'AI', 'LLM', 'model']):
                return f"[bold cyan]🤖[/bold cyan] [cyan]{line}[/cyan]"
            elif 'query' in line.lower() or 'request' in line.lower():
                return f"[bold purple]💬[/bold purple] [purple]{line}[/purple]"
            elif 'response' in line.lower() or 'answer' in line.lower():
                return f"[bold green]💡[/bold green] [green]{line}[/green]"
            elif any(word in line for word in ['tool', 'function', 'execute']):
                return f"[bold magenta]🔧[/bold magenta] [magenta]{line}[/magenta]"
            else:
                return f"[white]📝 {line}[/white]"

        if follow:
            console.print(f"[bold cyan]🤖 Agent Logs[/bold cyan] [dim]- Following (Press Ctrl+C to stop)[/dim]")

            try:
                with Live(refresh_per_second=2, console=console) as live:
                    while True:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        status = get_service_status()

                        logs = service_manager.get_service_logs(service_name, lines=20)
                        if logs:
                            formatted_lines = []
                            for line in logs.splitlines()[-20:]:
                                if line.strip():
                                    formatted_lines.append(format_log_line(line))
                            content = "\n".join(formatted_lines)
                        else:
                            content = "[dim]No logs available[/dim]"

                        title = f"🤖 ANVYL AGENT {status} [dim]({timestamp})[/dim]"
                        panel = Panel(content, title=title, border_style="green", padding=(1, 2))
                        live.update(panel)
                        time.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]📋 Log following stopped[/yellow]")
        else:
            timestamp = datetime.now().strftime('%H:%M:%S')
            status = get_service_status()

            logs = service_manager.get_service_logs(service_name, lines)
            if logs:
                formatted_lines = []
                for line in logs.splitlines():
                    if line.strip():
                        formatted_lines.append(format_log_line(line))
                content = "\n".join(formatted_lines)
            else:
                content = "[dim]No logs available[/dim]"

            title = f"🤖 ANVYL AGENT {status} [dim]({timestamp})[/dim]"
            panel = Panel(content, title=title, border_style="green", padding=(1, 2))
            console.print(panel)

    except Exception as e:
        console.print(f"[red]Error showing agent logs: {e}[/red]")
        raise typer.Exit(1)

@agent_group.command("restart")
def restart_agent(
    model_provider_url: str = typer.Option(settings.model_provider_url, "--model-provider-url", help="Model provider API URL"),
    port: int = typer.Option(settings.agent_port, "--port", help="Agent port"),
    host_id: str = typer.Option(settings.agent_host_id, "--host-id", help="Host ID for this agent"),
    host_ip: str = typer.Option(settings.agent_host, "--host-ip", help="Host IP for this agent"),
    mcp_server_url: str = typer.Option(settings.mcp_server_url, "--mcp-server-url", help="MCP server URL"),
    background: bool = typer.Option(True, "--background/--foreground", help="Run in background")
):
    """Restart the Anvyl AI Agent service."""
    try:
        # Get service manager
        service_manager = get_service_manager()

        console.print("🔄 [bold blue]Restarting Anvyl AI Agent[/bold blue]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Restarting agent...", total=None)

            # Use the service manager's restart method
            success = service_manager.restart_service("anvyl-agent")

            if success:
                console.print("✅ [green]Agent restarted successfully![/green]")
                console.print(f"🌐 Agent API available at: http://{host_ip}:{port}")
                console.print(f"🤖 Using model provider: {model_provider_url}")
                console.print(f"🔗 MCP Server: {mcp_server_url}")
            else:
                console.print("[red]Failed to restart agent[/red]")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error restarting agent: {e}[/red]")
        raise typer.Exit(1)

@agent_group.command("info")
def get_agent_info(
    port: int = typer.Option(4202, "--port", "-p", help="Agent API port")
):
    """Get comprehensive information about the agent including service status and agent capabilities."""
    try:
        service_manager = get_service_manager()

        # Check if the agent service is running
        service_status = service_manager.get_service_status("anvyl_agent")
        if not service_status or not service_status.get("running", False):
            console.print("[yellow]Agent is not running[/yellow]")
            console.print("[yellow]Use 'anvyl agent up' to start the agent[/yellow]")
            return

        # Display comprehensive information
        console.print("📊 [bold blue]Anvyl AI Agent Information[/bold blue]")

        # Service Information Section
        console.print("\n[bold cyan]Service Information:[/bold cyan]")

        service_table = Table(show_header=False, box=None)
        service_table.add_column("Property", style="cyan", width=15)
        service_table.add_column("Value", style="green")

        service_table.add_row("Service Name", "anvyl_agent")
        service_table.add_row("Status", "Running" if service_status.get("running") else "Stopped")
        service_table.add_row("PID", str(service_status.get("pid", "N/A")))
        service_table.add_row("Started", service_status.get("started_at", "N/A"))
        service_table.add_row("Port", str(port))

        console.print(service_table)

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
                    if known_hosts:
                        console.print(Panel(json.dumps(known_hosts, indent=2), title="Known Hosts"))
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
    port: int = typer.Option(4202, "--port", "-p", help="Agent API port")
):
    """Send a query to an AI agent (explicit command - same as just using: anvyl agent "your query")."""
    # Directly execute the query logic instead of calling the callback
    try:
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
            output = result.get("response", "No response")

            # Parse AgentRunResult-style output
            if isinstance(output, dict) and "output" in output:
                output = output["output"]
            elif isinstance(output, str):
                # Handle AgentRunResult string format
                if output.startswith("AgentRunResult("):
                    match = re.search(r'output=(\"|\')((?:[^\\]|\\.)*?)\1', output, re.DOTALL)
                    if match:
                        output = match.group(2)
                        output = output.replace('\\"', '"').replace("\\'", "'").replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
                else:
                    output = output.replace('\\"', '"').replace("\\'", "'")

            console.print(f"✅ [green]Agent response:[/green]")
            if not isinstance(output, str):
                output = json.dumps(output, indent=2)
            console.print(Panel(output, title="Agent Response"))
        else:
            console.print(f"[red]Error: HTTP {response.status_code}[/red]")
            console.print(f"[red]Response: {response.text}[/red]")

    except Exception as e:
        console.print(f"[red]Error querying agent: {e}[/red]")
        raise typer.Exit(1)

@agent_group.command("hosts")
def list_agent_hosts(
    port: int = typer.Option(4202, "--port", "-p", help="Agent API port")
):
    """List hosts known to the agent."""
    try:
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
    port: int = typer.Option(4202, "--port", "-p", help="Agent API port")
):
    """Add a host to the agent's known hosts list."""
    try:
        url = f"http://localhost:{port}/agent/add-host"
        data = {"host_id": host_id, "host_ip": host_ip}

        response = requests.post(url, json=data)

        if response.status_code == 200:
            result = response.json()
            console.print(f"✅ [green]{result.get('message', 'Host added successfully')}[/green]")
        else:
            console.print(f"[red]Error: HTTP {response.status_code}[/red]")
            console.print(f"[red]Response: {response.text}[/red]")

    except Exception as e:
        console.print(f"[red]Error adding host: {e}[/red]")
        raise typer.Exit(1)

# MCP Management Commands
mcp_group = typer.Typer(
    help="MCP server management commands",
    no_args_is_help=True,
    add_completion=False
)
app.add_typer(mcp_group, name="mcp")

@mcp_group.command("up")
def start_mcp_server(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to (streamable-http mode)"),
    port: int = typer.Option(4201, "--port", "-p", help="Port to bind to (streamable-http mode)")
):
    """Start the MCP server service."""
    try:
        # Get service manager
        service_manager = get_service_manager()

        # Check if service is already running
        service_status = service_manager.get_service_status("anvyl-mcp-server")
        if service_status and service_status.get("active"):
            console.print("ℹ️ [yellow]MCP Server is already running[/yellow]")
            console.print(f"   PID: {service_status.get('pid', 'N/A')}")
            console.print(f"   Port: {service_status.get('port', 'N/A')}")
            console.print(f"   Started: {service_status.get('start_time', 'N/A')}")
            return

        console.print(f"🚀 [bold blue]Starting MCP Server on port {port}[/bold blue]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Starting MCP server...", total=None)

            success = service_manager.start_mcp_server(port)

            if success:
                console.print("✅ [green]MCP Server started successfully![/green]")
                console.print(f"🔗 MCP Server available at: http://{host}:{port}")
                console.print("📋 Use 'anvyl mcp logs' to view logs")
            else:
                console.print("[red]Failed to start MCP Server[/red]")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error starting MCP Server: {e}[/red]")
        raise typer.Exit(1)

@mcp_group.command("down")
def stop_mcp_server():
    """Stop the MCP server service."""
    try:
        # Get service manager
        service_manager = get_service_manager()

        console.print("🛑 [bold red]Stopping MCP Server[/bold red]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Stopping MCP server...", total=None)

            success = service_manager.stop_mcp_server()

            if success:
                console.print("✅ [green]MCP Server stopped successfully![/green]")
            else:
                console.print("[red]Failed to stop MCP Server[/red]")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error stopping MCP Server: {e}[/red]")
        raise typer.Exit(1)

@mcp_group.command("logs")
def mcp_logs(
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    lines: int = typer.Option(100, "--lines", "-n", help="Number of lines to show")
):
    """Show logs for the MCP server service with enhanced formatting."""
    try:
        service_manager = get_service_manager()
        service_name = "anvyl-mcp-server"

        def get_service_status() -> str:
            try:
                status = service_manager.get_service_status(service_name)
                if status and status.get("active"):
                    pid = status.get("pid", "N/A")
                    return f"[bold green]●[/bold green] [green]Running[/green] [dim]PID:{pid}[/dim]"
                else:
                    return f"[bold red]●[/bold red] [red]Stopped[/red]"
            except:
                return f"[bold yellow]●[/bold yellow] [yellow]Unknown[/yellow]"

        def format_log_line(line: str) -> str:
            if not line.strip():
                return ""

            if any(level in line.upper() for level in ['ERROR:', 'CRITICAL:', 'EXCEPTION', 'FAILED']):
                return f"[bold red]🚨[/bold red] [red]{line}[/red]"
            elif any(level in line.upper() for level in ['WARNING:', 'WARN:']):
                return f"[bold yellow]⚠️[/bold yellow] [yellow]{line}[/yellow]"
            elif 'INFO:' in line.upper():
                return f"[bold blue]ℹ️[/bold blue] [bright_blue]{line}[/bright_blue]"
            elif 'DEBUG:' in line.upper():
                return f"[dim]🔍 {line}[/dim]"
            elif any(word in line for word in ['Starting', '✅', 'Started', 'Ready', 'SUCCESS']):
                return f"[bold green]🚀[/bold green] [green]{line}[/green]"
            elif any(word in line for word in ['Stopping', 'Stopped', 'Shutdown']):
                return f"[bold magenta]🛑[/bold magenta] [magenta]{line}[/magenta]"
            elif any(indicator in line for indicator in ['MCP', 'Model Context Protocol', 'server']):
                return f"[bold cyan]🔗[/bold cyan] [cyan]{line}[/cyan]"
            elif 'tool' in line.lower() or 'function' in line.lower():
                return f"[bold purple]🔧[/bold purple] [purple]{line}[/purple]"
            elif 'client' in line.lower() or 'connection' in line.lower():
                return f"[bold green]🔌[/bold green] [green]{line}[/green]"
            else:
                return f"[white]📝 {line}[/white]"

        if follow:
            console.print(f"[bold cyan]🔗 MCP Server Logs[/bold cyan] [dim]- Following (Press Ctrl+C to stop)[/dim]")

            try:
                with Live(refresh_per_second=2, console=console) as live:
                    while True:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        status = get_service_status()

                        logs = service_manager.get_service_logs(service_name, lines=20)
                        if logs:
                            formatted_lines = []
                            for line in logs.splitlines()[-20:]:
                                if line.strip():
                                    formatted_lines.append(format_log_line(line))
                            content = "\n".join(formatted_lines)
                        else:
                            content = "[dim]No logs available[/dim]"

                        title = f"🔗 MCP SERVER {status} [dim]({timestamp})[/dim]"
                        panel = Panel(content, title=title, border_style="cyan", padding=(1, 2))
                        live.update(panel)
                        time.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]📋 Log following stopped[/yellow]")
        else:
            timestamp = datetime.now().strftime('%H:%M:%S')
            status = get_service_status()

            logs = service_manager.get_service_logs(service_name, lines)
            if logs:
                formatted_lines = []
                for line in logs.splitlines():
                    if line.strip():
                        formatted_lines.append(format_log_line(line))
                content = "\n".join(formatted_lines)
            else:
                content = "[dim]No logs available[/dim]"

            title = f"🔗 MCP SERVER {status} [dim]({timestamp})[/dim]"
            panel = Panel(content, title=title, border_style="cyan", padding=(1, 2))
            console.print(panel)

    except Exception as e:
        console.print(f"[red]Error showing MCP logs: {e}[/red]")
        raise typer.Exit(1)

@mcp_group.command("restart")
def restart_mcp_server(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to (streamable-http mode)"),
    port: int = typer.Option(4201, "--port", "-p", help="Port to bind to (streamable-http mode)")
):
    """Restart the MCP server service."""
    try:
        # Get service manager
        service_manager = get_service_manager()

        console.print("🔄 [bold blue]Restarting MCP Server[/bold blue]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Restarting MCP server...", total=None)

            # Use the service manager's restart method
            success = service_manager.restart_service("anvyl-mcp-server")

            if success:
                console.print("✅ [green]MCP Server restarted successfully![/green]")
                console.print(f"🔗 MCP Server available at: http://{host}:{port}")
            else:
                console.print("[red]Failed to restart MCP Server[/red]")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error restarting MCP Server: {e}[/red]")
        raise typer.Exit(1)

@mcp_group.command("status")
def mcp_status():
    """Show status of the MCP server service."""
    try:
        # Get service manager
        service_manager = get_service_manager()

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Checking MCP server status...", total=None)
            status = service_manager.get_service_status("anvyl-mcp-server")

        if status is None:
            console.print("[yellow]MCP Server is not running[/yellow]")
        elif status.get("active"):
            console.print("✅ [green]MCP Server is running[/green]")

            # Create status table
            status_table = Table(title="MCP Server Status")
            status_table.add_column("Property", style="cyan")
            status_table.add_column("Value", style="green")

            status_table.add_row("Status", "Running")
            status_table.add_row("PID", str(status.get("pid", "N/A")))
            status_table.add_row("Port", "4201")
            status_table.add_row("Start Time", status.get("start_time", "N/A"))
            status_table.add_row("Runtime", status.get("runtime", "N/A"))

            console.print(status_table)
        else:
            console.print("[red]MCP Server is stopped[/red]")

    except Exception as e:
        console.print(f"[red]Error checking MCP Server status: {e}[/red]")
        raise typer.Exit(1)

def _show_status():
    """Show the status of all Anvyl services."""
    console.print("\n[bold blue]Anvyl Services Status[/bold blue]")
    console.print("=" * 40)

    # Get service manager
    service_manager = get_service_manager()

    # Check each service
    services = [
        ("Infrastructure API", f"{settings.infra_url}"),
        ("Agent API", f"{settings.agent_url}"),
        ("MCP Server", f"{settings.mcp_server_url}")
    ]

    for service_name, url in services:
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                console.print(f"✅ [green]{service_name}[/green]: {url}")
            else:
                console.print(f"⚠️  [yellow]{service_name}[/yellow]: {url} (HTTP {response.status_code})")
        except requests.RequestException:
            console.print(f"❌ [red]{service_name}[/red]: {url} (not responding)")

@app.command("infra")
def infrastructure_command(
    subcommand: str = typer.Argument(..., help="Subcommand (up, down, status, etc.)"),
    host: str = typer.Option(settings.infra_host, "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(settings.infra_port, "--port", "-p", help="Port to bind to"),
    background: bool = typer.Option(True, "--background/--foreground", help="Run in background"),
    logs: bool = typer.Option(False, "--logs", "-l", help="Show logs after starting")
):
    """Manage the Anvyl infrastructure API."""
    # ... existing code ...

@app.command("mcp")
def mcp_command(
    subcommand: str = typer.Argument(..., help="Subcommand (up, down, status, etc.)"),
    host: str = typer.Option(settings.infra_host, "--host", "-h", help="Host to bind to (streamable-http mode)"),
    port: int = typer.Option(settings.mcp_port, "--port", "-p", help="Port to bind to (streamable-http mode)"),
    background: bool = typer.Option(True, "--background/--foreground", help="Run in background"),
    logs: bool = typer.Option(False, "--logs", "-l", help="Show logs after starting")
):
    """Manage the Anvyl MCP server."""
    # ... existing code ...

@app.command("heartbeat")
def update_heartbeats():
    """Update heartbeats for all running services."""
    try:
        service_manager = get_service_manager()

        # Get all running services
        running_services = service_manager.db.get_running_services()

        if not running_services:
            console.print("ℹ️ [yellow]No running services found[/yellow]")
            return

        console.print(f"🔄 [bold blue]Updating heartbeats for {len(running_services)} services...[/bold blue]")

        updated_count = 0
        for service in running_services:
            if service_manager.update_service_heartbeat(service.id):
                updated_count += 1
                console.print(f"✅ Updated heartbeat for {service.id}")
            else:
                console.print(f"❌ Failed to update heartbeat for {service.id}")

        console.print(f"\n📊 Updated {updated_count}/{len(running_services)} service heartbeats")

    except Exception as e:
        console.print(f"[red]Error updating heartbeats: {e}[/red]")
        raise typer.Exit(1)

# Host Management Commands
host_group = typer.Typer(
    help="Manage hosts (not implemented yet)",
    no_args_is_help=True
)
app.add_typer(host_group, name="host")

@host_group.command("list")
def list_hosts(
    output: str = typer.Option("table", "--output", "-o", help="Output format (table, json)")
):
    """List all registered hosts (not implemented yet)."""
    console.print("⚠️  [yellow]Host management is not implemented yet.[/yellow]")
    console.print("This feature is planned for future releases.")
    console.print("For now, only the local host is automatically registered.")
    raise typer.Exit(1)

@host_group.command("add")
def add_host(
    name: str = typer.Argument(..., help="Host name"),
    ip: str = typer.Argument(..., help="Host IP address"),
    os: str = typer.Option("", "--os", help="Operating system"),
    tag: List[str] = typer.Option([], "--tag", "-t", help="Host tags")
):
    """Add a new host (not implemented yet)."""
    console.print("⚠️  [yellow]Host management is not implemented yet.[/yellow]")
    console.print("This feature is planned for future releases.")
    console.print("For now, only the local host is automatically registered.")
    raise typer.Exit(1)

@host_group.command("metrics")
def get_host_metrics(
    host_id: str = typer.Argument(..., help="Host ID")
):
    """Get metrics for a specific host (not implemented yet)."""
    console.print("⚠️  [yellow]Host management is not implemented yet.[/yellow]")
    console.print("This feature is planned for future releases.")
    console.print("For now, only the local host is automatically registered.")
    raise typer.Exit(1)

# Container Management Commands
container_group = typer.Typer(
    help="Manage containers (not implemented yet)",
    no_args_is_help=True
)
app.add_typer(container_group, name="container")

@container_group.command("list")
def list_containers(
    output: str = typer.Option("table", "--output", "-o", help="Output format (table, json)")
):
    """List all containers (not implemented yet)."""
    console.print("⚠️  [yellow]Container management is not implemented yet.[/yellow]")
    console.print("This feature is planned for future releases.")
    console.print("For now, containers are managed through the infrastructure API.")
    raise typer.Exit(1)

@container_group.command("create")
def create_container(
    name: str = typer.Argument(..., help="Container name"),
    image: str = typer.Argument(..., help="Docker image"),
    port: List[str] = typer.Option([], "--port", "-p", help="Port mappings"),
    volume: List[str] = typer.Option([], "--volume", "-v", help="Volume mappings"),
    env: List[str] = typer.Option([], "--env", "-e", help="Environment variables")
):
    """Create a new container (not implemented yet)."""
    console.print("⚠️  [yellow]Container management is not implemented yet.[/yellow]")
    console.print("This feature is planned for future releases.")
    console.print("For now, containers are managed through the infrastructure API.")
    raise typer.Exit(1)

@container_group.command("stop")
def stop_container(
    container_id: str = typer.Argument(..., help="Container ID")
):
    """Stop a container (not implemented yet)."""
    console.print("⚠️  [yellow]Container management is not implemented yet.[/yellow]")
    console.print("This feature is planned for future releases.")
    console.print("For now, containers are managed through the infrastructure API.")
    raise typer.Exit(1)

@container_group.command("logs")
def get_container_logs(
    container_id: str = typer.Argument(..., help="Container ID"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output")
):
    """Get container logs (not implemented yet)."""
    console.print("⚠️  [yellow]Container management is not implemented yet.[/yellow]")
    console.print("This feature is planned for future releases.")
    console.print("For now, containers are managed through the infrastructure API.")
    raise typer.Exit(1)

@container_group.command("exec")
def exec_container_command(
    container_id: str = typer.Argument(..., help="Container ID"),
    command: List[str] = typer.Argument(..., help="Command to execute")
):
    """Execute a command in a container (not implemented yet)."""
    console.print("⚠️  [yellow]Container management is not implemented yet.[/yellow]")
    console.print("This feature is planned for future releases.")
    console.print("For now, containers are managed through the infrastructure API.")
    raise typer.Exit(1)

if __name__ == "__main__":
    app()