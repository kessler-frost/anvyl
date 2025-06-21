"""
Infrastructure Tools for AI Agents

This module provides tools that AI agents can use to manage
infrastructure on their local host and query other hosts.
"""

import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from pydantic_ai.tools import Tool
import psutil
import socket
import json

from anvyl.infra.client import InfrastructureClient

logger = logging.getLogger(__name__)


class ListContainersInput(BaseModel):
    """Input for listing containers."""
    host_id: Optional[str] = Field(default=None, description="Host ID to query (None for local host)")


class ContainerActionInput(BaseModel):
    """Input for container actions."""
    container_id: str = Field(description="Container ID")
    host_id: Optional[str] = Field(default=None, description="Host ID (None for local host)")


class CreateContainerInput(BaseModel):
    """Input for creating containers."""
    name: str = Field(description="Container name")
    image: str = Field(description="Container image name")
    host_id: Optional[str] = Field(default=None, description="Host ID (None for local host)")
    ports: Optional[List[str]] = Field(default=None, description="Port mappings (e.g., ['8080:80'])")
    environment: Optional[List[str]] = Field(default=None, description="Environment variables")
    volumes: Optional[List[str]] = Field(default=None, description="Volume mappings")


class HostQueryInput(BaseModel):
    """Input for host queries."""
    host_id: Optional[str] = Field(default=None, description="Host ID to query (None for local host)")


class ListHostsInput(BaseModel):
    """Input for listing hosts (no parameters needed)."""
    pass


class ExecuteCommandInput(BaseModel):
    """Input for executing commands."""
    command: str = Field(description="Command to execute")
    host_id: Optional[str] = Field(default=None, description="Host ID (None for local host)")


class InfrastructureTools:
    """Tools for managing infrastructure that AI agents can use."""

    def __init__(self, infrastructure_client: InfrastructureClient):
        """Initialize tools with infrastructure client."""
        self._infrastructure_client = infrastructure_client

    def get_tools(self):
        """Get all available tools as a list of tool functions."""
        return [
            Tool(self.list_containers),
            Tool(self.get_container_info),
            Tool(self.start_container),
            Tool(self.stop_container),
            Tool(self.create_container),
            Tool(self.get_host_info),
            Tool(self.get_host_resources),
            Tool(self.list_hosts),
            Tool(self.execute_command),
        ]

    async def list_containers(self, host_id: Optional[str] = None, all: bool = False) -> str:
        """List all containers on a host. Use host_id=None for local host. If all=True, include all containers regardless of label or status."""
        try:
            containers = await self._infrastructure_client.list_containers(host_id, all=all)
            if not containers:
                return f"No containers found on host {host_id or 'local'}"

            result = []
            for container in containers:
                result.append(f"- {container['name']} ({container['id'][:12]}) - {container['status']}")

            return f"Containers on host {host_id or 'local'}:\n" + "\n".join(result)
        except Exception as e:
            return f"Error listing containers: {str(e)}"

    async def get_container_info(self, container_id: str, host_id: Optional[str] = None) -> str:
        """Get detailed information about a specific container."""
        try:
            containers = await self._infrastructure_client.list_containers(host_id)
            for container in containers:
                if container['id'] == container_id or container['id'].startswith(container_id):
                    return json.dumps(container, indent=2)
            return f"Container {container_id} not found"
        except Exception as e:
            return f"Error getting container info: {str(e)}"

    async def start_container(self, container_id: str, host_id: Optional[str] = None) -> str:
        """Start a stopped container."""
        try:
            # Use infrastructure client to start container
            # This will be implemented when we add container start functionality to the API
            return f"Container start functionality not yet implemented via infrastructure API"
        except Exception as e:
            return f"Error starting container: {str(e)}"

    async def stop_container(self, container_id: str, host_id: Optional[str] = None) -> str:
        """Stop a running container."""
        try:
            # Use infrastructure client to stop container
            success = await self._infrastructure_client.stop_container(container_id)
            if success:
                return f"Stopped container {container_id}"
            else:
                return f"Failed to stop container {container_id}"
        except Exception as e:
            return f"Error stopping container: {str(e)}"

    async def create_container(self, name: str, image: str, host_id: Optional[str] = None,
                        ports: Optional[List[str]] = None, environment: Optional[List[str]] = None,
                        volumes: Optional[List[str]] = None) -> str:
        """Create and start a new container."""
        try:
            container = await self._infrastructure_client.add_container(
                name=name,
                image=image,
                host_id=host_id,
                ports=ports,
                environment=environment,
                volumes=volumes
            )
            if container:
                return f"Created container {name} with ID {container['id']}"
            else:
                return f"Failed to create container {name}"
        except Exception as e:
            return f"Error creating container: {str(e)}"

    async def get_host_info(self, host_id: Optional[str] = None) -> str:
        """Get information about a specific host."""
        try:
            hosts = await self._infrastructure_client.list_hosts()
            if host_id is None:
                for host in hosts:
                    if host.get('tags') and 'local' in host['tags']:
                        return json.dumps(host, indent=2)
                return "Local host not found"
            else:
                for host in hosts:
                    if host['id'] == host_id:
                        return json.dumps(host, indent=2)
                return f"Host {host_id} not found"
        except Exception as e:
            return f"Error getting host info: {str(e)}"

    async def get_host_resources(self, host_id: Optional[str] = None) -> str:
        """Get current resource usage for a host."""
        try:
            if host_id is None:
                # Get local host resources
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                resources = {
                    "cpu_percent": cpu_percent,
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "percent": memory.percent
                    },
                    "disk": {
                        "total": disk.total,
                        "used": disk.used,
                        "free": disk.free,
                        "percent": (disk.used / disk.total) * 100
                    }
                }
                return json.dumps(resources, indent=2)
            else:
                # For remote hosts, we'd need to implement remote resource querying
                return f"Remote host resource querying not yet implemented for host {host_id}"
        except Exception as e:
            return f"Error getting host resources: {str(e)}"

    async def list_hosts(self) -> str:
        """List all hosts in the Anvyl network."""
        try:
            hosts = await self._infrastructure_client.list_hosts()
            if not hosts:
                return "No hosts found in the network"

            result = []
            for host in hosts:
                status = host.get('status', 'unknown')
                tags = host.get('tags', [])
                tags_str = f" [{', '.join(tags)}]" if tags else ""
                result.append(f"- {host['name']} ({host['ip']}) - {status}{tags_str}")

            return "Hosts in the network:\n" + "\n".join(result)
        except Exception as e:
            return f"Error listing hosts: {str(e)}"

    async def execute_command(self, command: str, host_id: Optional[str] = None) -> str:
        """Execute a command on a host."""
        try:
            if host_id is None:
                # Execute locally
                import subprocess
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    return f"Command executed successfully:\n{result.stdout}"
                else:
                    return f"Command failed (exit code {result.returncode}):\n{result.stderr}"
            else:
                # Execute on remote host
                result = await self._infrastructure_client.exec_command_on_host(
                    host_id, [command]
                )
                if result:
                    return json.dumps(result, indent=2)
                else:
                    return f"Failed to execute command on host {host_id}"
        except Exception as e:
            return f"Error executing command: {str(e)}"


def get_agent_tools(infrastructure_api_url: str = "http://localhost:4200"):
    """Get tools for the agent with the given infrastructure API URL."""
    from anvyl.infra.client import InfrastructureClient

    # Create infrastructure client
    infrastructure_client = InfrastructureClient(infrastructure_api_url)

    # Create tools instance
    tools_instance = InfrastructureTools(infrastructure_client)

    # Return the tools
    return tools_instance.get_tools()