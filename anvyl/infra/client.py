"""
Anvyl Infrastructure Client

This module provides a client for interacting with the Anvyl Infrastructure API
via HTTP calls, allowing agents to manage infrastructure remotely.
"""

import logging
import aiohttp
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class InfrastructureClient:
    """Client for interacting with the Anvyl Infrastructure API."""

    def __init__(self, base_url: str = "http://localhost:4200"):
        """Initialize the infrastructure client."""
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
        return self.session

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the infrastructure API."""
        url = urljoin(self.base_url, endpoint)
        session = await self._get_session()

        try:
            async with session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {e}")
            raise

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

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
    async def list_containers(self, host_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List containers, optionally filtered by host."""
        params = {}
        if host_id:
            params['host_id'] = host_id
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

    async def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a container."""
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


async def get_infrastructure_client(base_url: str = "http://localhost:4200") -> InfrastructureClient:
    """Get an infrastructure client instance. Use as 'async with await get_infrastructure_client() as client:' for proper cleanup."""
    return InfrastructureClient(base_url)