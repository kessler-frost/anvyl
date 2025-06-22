"""
Anvyl Infrastructure Client

This module provides a client for interacting with the Anvyl Infrastructure API
via HTTP calls, allowing agents to manage infrastructure remotely.
"""

import logging
import aiohttp
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
from anvyl.config import get_settings

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


class InfrastructureClient:
    """Client for interacting with the Anvyl Infrastructure API."""

    def __init__(self, base_url: Optional[str] = None):
        """Initialize the infrastructure client."""
        self.base_url = base_url or settings.infra_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the infrastructure API."""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise

    # Health and status methods
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the infrastructure API."""
        return await self._make_request('GET', '/health')

    # Host management methods
    async def list_hosts(self) -> List[Dict[str, Any]]:
        """List all registered hosts."""
        response = await self._make_request('GET', '/hosts')
        return response.get('hosts', [])

    async def add_host(self, name: str, ip: str, os: str = "", tags: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Add a new host to the system."""
        data = {
            "name": name,
            "ip": ip,
            "os": os,
            "tags": tags or []
        }
        response = await self._make_request('POST', '/hosts', json=data)
        return response.get('host')

    async def update_host(self, host_id: str, resources: Optional[Dict[str, Any]] = None,
                   status: str = "", tags: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Update host information."""
        data = {
            "resources": resources,
            "status": status,
            "tags": tags
        }
        response = await self._make_request('PUT', f'/hosts/{host_id}', json=data)
        return response.get('host')

    async def get_host_metrics(self, host_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific host."""
        response = await self._make_request('GET', f'/hosts/{host_id}/metrics')
        return response.get('metrics')

    async def host_heartbeat(self, host_id: str) -> bool:
        """Send a heartbeat for a host."""
        response = await self._make_request('POST', f'/hosts/{host_id}/heartbeat')
        return response.get('success', False)

    # Container management methods
    async def list_containers(self, host_id: Optional[str] = None, all: bool = False) -> List[Dict[str, Any]]:
        """List containers, optionally filtered by host. If all=True, include all containers regardless of label or status."""
        params = {}
        if host_id:
            params['host_id'] = host_id
        if all:
            params['all'] = 'true'
        response = await self._make_request('GET', '/containers', params=params)
        return response.get('containers', [])

    async def add_container(self, name: str, image: str, host_id: Optional[str] = None,
                     labels: Optional[Dict[str, str]] = None, ports: Optional[List[str]] = None,
                     volumes: Optional[List[str]] = None, environment: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Add a new container."""
        data = {
            "name": name,
            "image": image,
            "host_id": host_id,
            "labels": labels,
            "ports": ports,
            "volumes": volumes,
            "environment": environment
        }
        response = await self._make_request('POST', '/containers', json=data)
        return response.get('container')

    async def remove_container(self, container_id: str, timeout: int = 10) -> bool:
        """Remove a container."""
        params = {'timeout': timeout}
        response = await self._make_request('DELETE', f'/containers/{container_id}', params=params)
        return 'message' in response

    async def get_logs(self, container_id: str, follow: bool = False, tail: int = 100) -> Optional[str]:
        """Get logs from a container."""
        params = {'follow': follow, 'tail': tail}
        response = await self._make_request('GET', f'/containers/{container_id}/logs', params=params)
        return response.get('logs')

    async def exec_command(self, container_id: str, command: List[str], tty: bool = False) -> Optional[Dict[str, Any]]:
        """Execute a command in a container."""
        data = {
            "command": command,
            "tty": tty
        }
        response = await self._make_request('POST', f'/containers/{container_id}/exec', json=data)
        return response.get('result')

    async def get_container_stats(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a container."""
        response = await self._make_request('GET', f'/containers/{container_id}/stats')
        return response.get('stats')

    async def inspect_container(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a container."""
        response = await self._make_request('GET', f'/containers/{container_id}/inspect')
        return response.get('container')

    # Host command execution
    async def exec_command_on_host(self, host_id: str, command: List[str],
                           working_directory: str = "", env: Optional[List[str]] = None,
                           timeout: int = 0) -> Optional[Dict[str, Any]]:
        """Execute a command on a specific host."""
        data = {
            "command": command,
            "working_directory": working_directory,
            "env": env,
            "timeout": timeout
        }
        response = await self._make_request('POST', f'/hosts/{host_id}/exec', json=data)
        return response.get('result')

    # Image management methods
    async def list_images(self) -> List[Dict[str, Any]]:
        """List all Docker images."""
        response = await self._make_request('GET', '/images')
        return response.get('images', [])

    async def pull_image(self, image_name: str, tag: str = "latest") -> bool:
        """Pull a Docker image."""
        params = {'tag': tag}
        response = await self._make_request('POST', f'/images/pull?image_name={image_name}', params=params)
        return 'message' in response

    async def remove_image(self, image_id: str, force: bool = False) -> bool:
        """Remove a Docker image."""
        params = {'force': force}
        response = await self._make_request('DELETE', f'/images/{image_id}', params=params)
        return 'message' in response

    async def inspect_image(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a Docker image."""
        response = await self._make_request('GET', f'/images/{image_id}/inspect')
        return response.get('image')

    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        response = await self._make_request('GET', '/system/info')
        return response


async def get_infrastructure_client(base_url: Optional[str] = None) -> InfrastructureClient:
    """Get an infrastructure client instance. Use as 'async with await get_infrastructure_client() as client:' for proper cleanup."""
    return InfrastructureClient(base_url)