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

    # Agent management methods
    async def start_agent_container(self, lmstudio_url: str = "http://localhost:1234/v1",
                            lmstudio_model: str = "llama-3.2-3b-instruct",
                            port: int = 4200, image_tag: str = "anvyl-agent:latest") -> Optional[Dict[str, Any]]:
        """Start the agent container."""
        data = {
            "lmstudio_url": lmstudio_url,
            "lmstudio_model": lmstudio_model,
            "port": port,
            "image_tag": image_tag
        }
        response = await self._make_request('POST', '/agent/start', json=data)
        return response.get('result')

    async def stop_agent_container(self) -> bool:
        """Stop the agent container."""
        response = await self._make_request('POST', '/agent/stop')
        return 'message' in response

    async def get_agent_container_status(self) -> Optional[Dict[str, Any]]:
        """Get the status of the agent container."""
        response = await self._make_request('GET', '/agent/status')
        return response.get('status')

    async def get_agent_status(self) -> tuple[str, str, str]:
        """Get comprehensive agent status including container and API status.

        Returns:
            tuple: (container_status, api_status, details)
        """
        try:
            # Get container status
            container_status = await self.get_agent_container_status()

            if not container_status:
                return "🔴 Stopped", "🔴 Unreachable", "Agent container not found"

            # Determine container status emoji
            if container_status.get("status") == "running":
                container_status_emoji = "🟢 Running"
            else:
                container_status_emoji = "🔴 Stopped"

            # Try to check agent API health
            try:
                # Get port from container status
                ports = container_status.get("ports", {})
                agent_port = None
                for port_mapping in ports.values():
                    if port_mapping and len(port_mapping) > 0:
                        agent_port = port_mapping[0].get("HostPort")
                        break

                if not agent_port:
                    # Try to get port from environment variables
                    env_vars = container_status.get("environment", [])
                    for env_var in env_vars:
                        if env_var.startswith("ANVYL_AGENT_PORT="):
                            agent_port = env_var.split("=", 1)[1]
                            break

                if agent_port:
                    # Check agent API health
                    agent_url = f"http://localhost:{agent_port}/health"
                    import requests
                    resp = requests.get(agent_url, timeout=2)
                    if resp.status_code == 200:
                        api_status = "🟢 Healthy"
                    else:
                        api_status = "🟡 Unhealthy"
                else:
                    api_status = "🔴 Unknown"

            except Exception:
                api_status = "🔴 Unreachable"

            # Create details string
            details = f"Container: {container_status.get('name', 'unknown')} | Port: {agent_port or 'unknown'}"

            return container_status_emoji, api_status, details

        except Exception as e:
            return "🔴 Error", "🔴 Error", f"Error getting status: {str(e)}"

    async def get_agent_logs(self, follow: bool = False, tail: int = 100) -> Optional[str]:
        """Get logs from the agent container."""
        params = {'follow': follow, 'tail': tail}
        response = await self._make_request('GET', '/agent/logs', params=params)
        return response.get('logs')

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