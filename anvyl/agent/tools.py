"""
Infrastructure Tools for AI Agents

This module provides tools that AI agents can use to manage
infrastructure on their local host and query other hosts.
"""

import logging
from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
import psutil
import socket
import json

from anvyl.infrastructure_client import InfrastructureClient

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
        self.tools = self._create_tools()

    def _create_tools(self) -> List[BaseTool]:
        """Create all available tools."""
        return [
            ListContainersTool(self._infrastructure_client),
            GetContainerInfoTool(self._infrastructure_client),
            StartContainerTool(self._infrastructure_client),
            StopContainerTool(self._infrastructure_client),
            CreateContainerTool(self._infrastructure_client),
            GetHostInfoTool(self._infrastructure_client),
            GetHostResourcesTool(self._infrastructure_client),
            ListHostsTool(self._infrastructure_client),
            ExecuteCommandTool(self._infrastructure_client),
        ]

    def get_tools(self) -> List[BaseTool]:
        """Get all available tools."""
        return self.tools


class ListContainersTool(BaseTool):
    """Tool for listing containers on a host."""

    name: str = "list_containers"
    description: str = "List all containers on a host. Use host_id=None for local host."
    args_schema: type = ListContainersInput
    _infrastructure_client: Any = PrivateAttr()

    def __init__(self, infrastructure_client: InfrastructureClient):
        super().__init__()
        self._infrastructure_client = infrastructure_client

    def _run(self, host_id: Optional[str] = None) -> str:
        """List containers on the specified host."""
        try:
            containers = self._infrastructure_client.list_containers(host_id)
            if not containers:
                return f"No containers found on host {host_id or 'local'}"

            result = []
            for container in containers:
                result.append(f"- {container['name']} ({container['id'][:12]}) - {container['status']}")

            return f"Containers on host {host_id or 'local'}:\n" + "\n".join(result)
        except Exception as e:
            return f"Error listing containers: {str(e)}"


class GetContainerInfoTool(BaseTool):
    """Tool for getting detailed container information."""

    name: str = "get_container_info"
    description: str = "Get detailed information about a specific container."
    args_schema: type = ContainerActionInput
    _infrastructure_client: Any = PrivateAttr()

    def __init__(self, infrastructure_client: InfrastructureClient):
        super().__init__()
        self._infrastructure_client = infrastructure_client

    def _run(self, container_id: str, host_id: Optional[str] = None) -> str:
        """Get container information."""
        try:
            containers = self._infrastructure_client.list_containers(host_id)
            for container in containers:
                if container['id'] == container_id or container['id'].startswith(container_id):
                    return json.dumps(container, indent=2)
            return f"Container {container_id} not found"
        except Exception as e:
            return f"Error getting container info: {str(e)}"


class StartContainerTool(BaseTool):
    """Tool for starting a container."""

    name: str = "start_container"
    description: str = "Start a stopped container."
    args_schema: type = ContainerActionInput
    _infrastructure_client: Any = PrivateAttr()

    def __init__(self, infrastructure_client: InfrastructureClient):
        super().__init__()
        self._infrastructure_client = infrastructure_client

    def _run(self, container_id: str, host_id: Optional[str] = None) -> str:
        """Start a container."""
        try:
            # Use infrastructure client to start container
            # This will be implemented when we add container start functionality to the API
            return f"Container start functionality not yet implemented via infrastructure API"
        except Exception as e:
            return f"Error starting container: {str(e)}"


class StopContainerTool(BaseTool):
    """Tool for stopping a container."""

    name: str = "stop_container"
    description: str = "Stop a running container."
    args_schema: type = ContainerActionInput
    _infrastructure_client: Any = PrivateAttr()

    def __init__(self, infrastructure_client: InfrastructureClient):
        super().__init__()
        self._infrastructure_client = infrastructure_client

    def _run(self, container_id: str, host_id: Optional[str] = None) -> str:
        """Stop a container."""
        try:
            # Use infrastructure client to stop container
            success = self._infrastructure_client.stop_container(container_id)
            if success:
                return f"Stopped container {container_id}"
            else:
                return f"Failed to stop container {container_id}"
        except Exception as e:
            return f"Error stopping container: {str(e)}"


class CreateContainerTool(BaseTool):
    """Tool for creating a new container."""

    name: str = "create_container"
    description: str = "Create and start a new container."
    args_schema: type = CreateContainerInput
    _infrastructure_client: Any = PrivateAttr()

    def __init__(self, infrastructure_client: InfrastructureClient):
        super().__init__()
        self._infrastructure_client = infrastructure_client

    def _run(self, name: str, image: str, host_id: Optional[str] = None,
             ports: Optional[List[str]] = None, environment: Optional[List[str]] = None,
             volumes: Optional[List[str]] = None) -> str:
        """Create a new container."""
        try:
            container = self._infrastructure_client.add_container(
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


class GetHostInfoTool(BaseTool):
    """Tool for getting host information."""

    name: str = "get_host_info"
    description: str = "Get information about a specific host."
    args_schema: type = HostQueryInput
    _infrastructure_client: Any = PrivateAttr()

    def __init__(self, infrastructure_client: InfrastructureClient):
        super().__init__()
        self._infrastructure_client = infrastructure_client

    def _run(self, host_id: Optional[str] = None) -> str:
        """Get host information."""
        try:
            hosts = self._infrastructure_client.list_hosts()
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


class GetHostResourcesTool(BaseTool):
    """Tool for getting host resource usage."""

    name: str = "get_host_resources"
    description: str = "Get current resource usage for a host."
    args_schema: type = HostQueryInput
    _infrastructure_client: Any = PrivateAttr()

    def __init__(self, infrastructure_client: InfrastructureClient):
        super().__init__()
        self._infrastructure_client = infrastructure_client

    def _run(self, host_id: Optional[str] = None) -> str:
        """Get host resources."""
        try:
            if host_id is None:  # Local host
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                resources = {
                    "cpu_percent": cpu_percent,
                    "memory_total_gb": round(memory.total / (1024**3), 2),
                    "memory_used_gb": round(memory.used / (1024**3), 2),
                    "memory_percent": memory.percent,
                    "disk_total_gb": round(disk.total / (1024**3), 2),
                    "disk_used_gb": round(disk.used / (1024**3), 2),
                    "disk_percent": round((disk.used / disk.total) * 100, 2)
                }
                return json.dumps(resources, indent=2)
            else:
                return f"Remote host resources not yet implemented for host {host_id}"
        except Exception as e:
            return f"Error getting host resources: {str(e)}"


class ListHostsTool(BaseTool):
    """Tool for listing all hosts in the network."""

    name: str = "list_hosts"
    description: str = "List all hosts in the Anvyl network."
    args_schema: type = ListHostsInput
    _infrastructure_client: Any = PrivateAttr()

    def __init__(self, infrastructure_client: InfrastructureClient):
        super().__init__()
        self._infrastructure_client = infrastructure_client

    def _run(self) -> str:
        """List all hosts."""
        try:
            hosts = self._infrastructure_client.list_hosts()
            if not hosts:
                return "No hosts found in the network"

            result = []
            for host in hosts:
                status_emoji = "🟢" if host['status'] == 'online' else "🔴"
                result.append(f"{status_emoji} {host['name']} ({host['ip']}) - {host['status']}")

            return "Hosts in the network:\n" + "\n".join(result)
        except Exception as e:
            return f"Error listing hosts: {str(e)}"


class ExecuteCommandTool(BaseTool):
    """Tool for executing commands on a host."""

    name: str = "execute_command"
    description: str = "Execute a command on a host."
    args_schema: type = ExecuteCommandInput
    _infrastructure_client: Any = PrivateAttr()

    def __init__(self, infrastructure_client: InfrastructureClient):
        super().__init__()
        self._infrastructure_client = infrastructure_client

    def _run(self, command: str, host_id: Optional[str] = None) -> str:
        """Execute a command."""
        try:
            if host_id is None:  # Local host
                import subprocess
                result = subprocess.run(command.split(), capture_output=True, text=True)
                if result.returncode == 0:
                    return f"Command executed successfully:\n{result.stdout}"
                else:
                    return f"Command failed:\n{result.stderr}"
            else:
                return f"Remote command execution not yet implemented for host {host_id}"
        except Exception as e:
            return f"Error executing command: {str(e)}"