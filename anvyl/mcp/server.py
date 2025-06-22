"""
Anvyl MCP Server Implementation

This module implements an MCP server that provides tools for managing
Docker containers and infrastructure using the FastMCP package.
"""

import logging
import os
import platform
import socket
from typing import Any, Dict, List, Optional
from datetime import datetime
import warnings

import psutil
import uvicorn
from fastmcp import FastMCP

from anvyl.infra.service import InfrastructureService
from anvyl.config import get_settings

# Suppress websockets.legacy deprecation warning
warnings.filterwarnings(
    "ignore",
    message="websockets.legacy is deprecated;*",
    category=DeprecationWarning,
    module="websockets\\.legacy"
)

# Suppress WebSocketServerProtocol deprecation warning
warnings.filterwarnings(
    "ignore",
    message="websockets.server.WebSocketServerProtocol is deprecated*",
    category=DeprecationWarning,
    module="uvicorn\\.protocols\\.websockets\\.websockets_impl"
)

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Global FastMCP object
server = FastMCP("anvyl-infrastructure")

# Set up tools on the global server
infrastructure = InfrastructureService()

@server.tool()
async def list_hosts() -> str:
    """List all registered hosts in the infrastructure."""
    try:
        hosts = infrastructure.list_hosts()
        if not hosts:
            return "No hosts found in the infrastructure."

        result = "Registered hosts:\n"
        for host in hosts:
            result += f"• {host['name']} (ID: {host['id']}, IP: {host['ip']})\n"
            if host.get('os'):
                result += f"  OS: {host['os']}\n"
            if host.get('tags'):
                result += f"  Tags: {', '.join(host['tags'])}\n"
            result += "\n"

        return result
    except Exception as e:
        logger.error(f"Error listing hosts: {e}")
        return f"Error listing hosts: {str(e)}"

@server.tool()
async def list_containers(host_id: Optional[str] = None, all: bool = False) -> str:
    """List Docker containers managed by Anvyl."""
    try:
        containers = infrastructure.list_containers(host_id=host_id, all=all)
        if not containers:
            return "No containers found."

        result = "Docker containers:\n"
        for container in containers:
            result += f"• {container['name']} (ID: {container['id'][:12]})\n"
            result += f"  Image: {container['image']}\n"
            result += f"  Status: {container['status']}\n"
            result += f"  Host: {container.get('host_id', 'local')}\n"
            if container.get('ports'):
                result += f"  Ports: {', '.join(container['ports'])}\n"
            result += "\n"

        return result
    except Exception as e:
        logger.error(f"Error listing containers: {e}")
        return f"Error listing containers: {str(e)}"

@server.tool()
async def list_images() -> str:
    """List all Docker images available on the system."""
    try:
        images = infrastructure.list_images()

        if not images:
            return "ANVYL_DOCKER_IMAGES_TOOL_OUTPUT\nNo Docker images found on the system."

        # Header similar to docker images (without size)
        result = "ANVYL_DOCKER_IMAGES_TOOL_OUTPUT\nREPOSITORY          TAG         IMAGE ID       CREATED\n"
        for image in images:
            repo = image['repository']
            tag = image['tag']
            image_id = image['id']
            created = image['created'][:10] if image['created'] else "N/A"
            result += f"{repo:<18} {tag:<10} {image_id:<12} {created}\n"
        return result
    except Exception as e:
        logger.error(f"Error listing images: {e}")
        return f"ANVYL_DOCKER_IMAGES_TOOL_OUTPUT\nError listing images: {str(e)}"

@server.tool()
async def create_container(
    name: str,
    image: str,
    host_id: Optional[str] = None,
    ports: Optional[List[str]] = None,
    environment: Optional[List[str]] = None,
    volumes: Optional[List[str]] = None,
    labels: Optional[Dict[str, str]] = None
) -> str:
    """Create a new Docker container."""
    try:
        # Convert lists to proper format for infrastructure service
        port_mappings = ports or []
        env_vars = environment or []
        volume_mappings = volumes or []

        container = infrastructure.add_container(
            name=name,
            image=image,
            host_id=host_id,
            ports=port_mappings,
            environment=env_vars,
            volumes=volume_mappings,
            labels=labels or {}
        )

        if container:
            return f"Container '{name}' created successfully with ID: {container['id']}"
        else:
            return f"Failed to create container '{name}'"
    except Exception as e:
        logger.error(f"Error creating container: {e}")
        return f"Error creating container: {str(e)}"

@server.tool()
async def remove_container(container_id: str, timeout: int = 10) -> str:
    """Remove a Docker container."""
    try:
        success = infrastructure.remove_container(container_id, timeout=timeout)
        if success:
            return f"Container {container_id} removed successfully."
        else:
            return f"Failed to remove container {container_id}"
    except Exception as e:
        logger.error(f"Error removing container: {e}")
        return f"Error removing container: {str(e)}"

@server.tool()
async def get_container_logs(container_id: str, tail: int = 100, follow: bool = False) -> str:
    """Get logs from a Docker container."""
    try:
        logs = infrastructure.get_logs(container_id, tail=tail, follow=follow)
        if not logs:
            return f"No logs available for container {container_id}"

        return f"Logs for container {container_id}:\n{logs}"
    except Exception as e:
        logger.error(f"Error getting container logs: {e}")
        return f"Error getting container logs: {str(e)}"

@server.tool()
async def exec_container_command(container_id: str, command: List[str], tty: bool = False) -> str:
    """Execute a command inside a Docker container (safe - isolated within container)."""
    try:
        result = infrastructure.exec_command(container_id, command, tty=tty)
        if result:
            return f"Command executed successfully in container {container_id}:\n{result.get('output', 'No output')}"
        else:
            return f"Failed to execute command in container {container_id}"
    except Exception as e:
        logger.error(f"Error executing command in container: {e}")
        return f"Error executing command in container: {str(e)}"

@server.tool()
async def get_host_metrics(host_id: str) -> str:
    """Get resource metrics for a host."""
    try:
        metrics = infrastructure.get_host_metrics(host_id)
        if not metrics:
            return f"No metrics available for host {host_id}"

        result = f"Metrics for host {host_id}:\n"
        result += f"• CPU Usage: {metrics.get('cpu_percent', 'N/A')}%\n"
        result += f"• Memory Usage: {metrics.get('memory_percent', 'N/A')}%\n"
        result += f"• Disk Usage: {metrics.get('disk_percent', 'N/A')}%\n"
        result += f"• Network I/O: {metrics.get('network_io', 'N/A')}\n"

        return result
    except Exception as e:
        logger.error(f"Error getting host metrics: {e}")
        return f"Error getting host metrics: {str(e)}"

@server.tool()
async def add_host(name: str, ip: str, os: str = "", tags: Optional[List[str]] = None) -> str:
    """Add a new host to the infrastructure."""
    try:
        host = infrastructure.add_host(
            name=name,
            ip=ip,
            os=os,
            tags=tags or []
        )
        if host:
            return f"Host '{name}' added successfully with ID: {host['id']}"
        else:
            return f"Failed to add host '{name}'"
    except Exception as e:
        logger.error(f"Error adding host: {e}")
        return f"Error adding host: {str(e)}"

@server.tool()
async def system_status() -> str:
    """Get overall system status and health."""
    try:
        # Get basic system information
        hosts = infrastructure.list_hosts()
        containers = infrastructure.list_containers()

        result = "System Status:\n"
        result += f"• Total Hosts: {len(hosts)}\n"
        result += f"• Total Containers: {len(containers)}\n"

        # Count running containers
        running_containers = [c for c in containers if c['status'] == 'running']
        result += f"• Running Containers: {len(running_containers)}\n"

        # System health
        if len(hosts) > 0 and len(containers) >= 0:
            result += "• System Health: ✅ Healthy\n"
        else:
            result += "• System Health: ⚠️ No hosts configured\n"

        result += f"• Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return result
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return f"Error getting system status: {str(e)}"

@server.tool()
async def inspect_container(container_id: str) -> str:
    """Inspect a Docker container."""
    try:
        container_info = infrastructure.inspect_container(container_id)
        if not container_info:
            return f"Container {container_id} not found."

        result = f"Container {container_id}:\n"
        result += f"  Name: {container_info['name']}\n"
        result += f"  Image: {container_info['image']}\n"
        result += f"  Status: {container_info['status']}\n"
        result += f"  Created: {container_info['created']}\n"

        if container_info.get('ports'):
            result += f"  Ports: {container_info['ports']}\n"
        if container_info.get('mounts'):
            result += f"  Mounts: {container_info['mounts']}\n"
        if container_info.get('env'):
            result += f"  Environment: {container_info['env']}\n"
        if container_info.get('cmd'):
            result += f"  Command: {container_info['cmd']}\n"
        if container_info.get('labels'):
            result += f"  Labels: {container_info['labels']}\n"

        return result
    except Exception as e:
        logger.error(f"Error inspecting container: {e}")
        return f"Error inspecting container: {str(e)}"

@server.tool()
async def container_stats(container_id: str) -> str:
    """Get statistics for a Docker container."""
    try:
        stats = infrastructure.get_container_stats(container_id)
        if not stats:
            return f"Container {container_id} not found or not running."

        result = f"Statistics for container {container_id}:\n"
        result += f"  CPU Usage: {stats['cpu_percent']}%\n"
        result += f"  Memory Usage: {stats['memory_usage']} / {stats['memory_limit']} bytes ({stats['memory_percent']}%)\n"
        result += f"  Network RX: {stats['network_rx']} bytes\n"
        result += f"  Network TX: {stats['network_tx']} bytes\n"
        result += f"  Block Read: {stats['block_read']} bytes\n"
        result += f"  Block Write: {stats['block_write']} bytes\n"

        return result
    except Exception as e:
        logger.error(f"Error getting container stats: {e}")
        return f"Error getting container stats: {str(e)}"

@server.tool()
async def pull_image(image_name: str, tag: str = "latest") -> str:
    """Pull a Docker image."""
    try:
        image = infrastructure.pull_image(image_name, tag)
        if image:
            return f"Image {image_name}:{tag} pulled successfully with ID: {image['id']}"
        else:
            return f"Failed to pull image {image_name}:{tag}"
    except Exception as e:
        logger.error(f"Error pulling image: {e}")
        return f"Error pulling image: {str(e)}"

@server.tool()
async def remove_image(image_id: str, force: bool = False) -> str:
    """Remove a Docker image."""
    try:
        success = infrastructure.remove_image(image_id, force)
        if success:
            return f"Image {image_id} removed successfully."
        else:
            return f"Failed to remove image {image_id}"
    except Exception as e:
        logger.error(f"Error removing image: {e}")
        return f"Error removing image: {str(e)}"

@server.tool()
async def inspect_image(image_id: str) -> str:
    """Inspect a Docker image."""
    try:
        image_info = infrastructure.inspect_image(image_id)
        if not image_info:
            return f"Image {image_id} not found."

        result = f"Image {image_id}:\n"
        result += f"  Tags: {image_info['tags']}\n"
        result += f"  Created: {image_info['created']}\n"
        result += f"  Size: {image_info['size']} bytes\n"
        result += f"  Architecture: {image_info['architecture']}\n"
        result += f"  OS: {image_info['os']}\n"

        if image_info.get('config'):
            config = image_info['config']
            if config.get('Cmd'):
                result += f"  Default Command: {config['Cmd']}\n"
            if config.get('Entrypoint'):
                result += f"  Entrypoint: {config['Entrypoint']}\n"
            if config.get('Env'):
                result += f"  Environment: {config['Env']}\n"

        return result
    except Exception as e:
        logger.error(f"Error inspecting image: {e}")
        return f"Error inspecting image: {str(e)}"

@server.tool()
async def get_system_info() -> str:
    """Get system information."""
    try:
        info = infrastructure.get_system_info()
        if not info:
            return "Unable to get system information."

        result = "System Information:\n"
        result += f"  Platform: {info['platform']}\n"
        result += f"  Platform Version: {info['platform_version']}\n"
        result += f"  Architecture: {info['architecture']}\n"
        result += f"  Processor: {info['processor']}\n"
        result += f"  Hostname: {info['hostname']}\n"
        result += f"  CPU Count: {info['cpu_count']}\n"
        result += f"  Memory Total: {info['memory_total']} bytes\n"
        result += f"  Memory Available: {info['memory_available']} bytes\n"
        result += f"  Disk Total: {info['disk_usage']} bytes\n"

        return result
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return f"Error getting system info: {str(e)}"

@server.tool()
async def list_available_tools() -> str:
    """List all available tools that can be used for infrastructure management."""
    tools_info = {
        "Docker Container Management": [
            "list_containers - List Docker containers",
            "create_container - Create a new Docker container",
            "remove_container - Remove a container",
            "inspect_container - Get detailed container information",
            "container_stats - Get real-time container resource usage",
            "get_container_logs - Get container logs",
            "exec_container_command - Execute commands inside containers (safe)"
        ],
        "Docker Image Management": [
            "list_images - List all Docker images",
            "pull_image - Pull an image from registry",
            "remove_image - Remove a Docker image",
            "inspect_image - Get detailed image information"
        ],

        "System Monitoring": [
            "get_system_info - Get OS, CPU, memory, and hardware details"
        ],
        "Host Management": [
            "list_hosts - List all registered infrastructure hosts",
            "add_host - Register a new host in the infrastructure",
            "get_host_metrics - Get resource metrics for a specific host",
            "system_status - Get overall system status"
        ]
    }

    result = "Available Tools for Infrastructure Management:\n\n"

    for category, tools in tools_info.items():
        result += f"📋 {category}:\n"
        for tool in tools:
            result += f"  • {tool}\n"
        result += "\n"

    result += "💡 Use these tools by describing what you want to accomplish in natural language.\n"
    result += "💡 Example: 'show me running containers' will use list_containers\n"
    result += "💡 Example: 'get system information' will use get_system_info\n"
    result += "💡 Example: 'list docker images' will use list_images\n"

    return result

def main():
    """Main entry point for the MCP server."""
    print(f"Starting Anvyl MCP Server using FastMCP on port {settings.mcp_port}")
    uvicorn.run(
        server.http_app,
        host=settings.infra_host,
        port=settings.mcp_port,
        log_level="info",
        reload=False,
        factory=True
    )

if __name__ == "__main__":
    main()