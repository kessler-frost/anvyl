"""
Anvyl Infrastructure Client

This module provides a client for interacting with the Anvyl Infrastructure API
via HTTP calls, allowing agents to manage infrastructure remotely.
"""

import logging
import requests
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class InfrastructureClient:
    """Client for interacting with the Anvyl Infrastructure API."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        """Initialize the infrastructure client."""
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the infrastructure API."""
        url = urljoin(self.base_url, endpoint)

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """Check the health of the infrastructure API."""
        return self._make_request('GET', '/health')

    # Host management methods
    def list_hosts(self) -> List[Dict[str, Any]]:
        """List all registered hosts."""
        response = self._make_request('GET', '/hosts')
        return response.get('hosts', [])

    def add_host(self, name: str, ip: str, os: str = "", tags: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Add a new host to the system."""
        data = {
            "name": name,
            "ip": ip,
            "os": os,
            "tags": tags or []
        }
        response = self._make_request('POST', '/hosts', json=data)
        return response.get('host')

    def update_host(self, host_id: str, resources: Optional[Dict[str, Any]] = None,
                   status: str = "", tags: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Update host information."""
        data = {
            "resources": resources,
            "status": status,
            "tags": tags
        }
        response = self._make_request('PUT', f'/hosts/{host_id}', json=data)
        return response.get('host')

    def get_host_metrics(self, host_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific host."""
        response = self._make_request('GET', f'/hosts/{host_id}/metrics')
        return response.get('metrics')

    def host_heartbeat(self, host_id: str) -> bool:
        """Send a heartbeat for a host."""
        response = self._make_request('POST', f'/hosts/{host_id}/heartbeat')
        return response.get('success', False)

    # Container management methods
    def list_containers(self, host_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List containers, optionally filtered by host."""
        params = {}
        if host_id:
            params['host_id'] = host_id
        response = self._make_request('GET', '/containers', params=params)
        return response.get('containers', [])

    def add_container(self, name: str, image: str, host_id: Optional[str] = None,
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
        response = self._make_request('POST', '/containers', json=data)
        return response.get('container')

    def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a container."""
        params = {'timeout': timeout}
        response = self._make_request('DELETE', f'/containers/{container_id}', params=params)
        return 'message' in response

    def get_logs(self, container_id: str, follow: bool = False, tail: int = 100) -> Optional[str]:
        """Get logs from a container."""
        params = {'follow': follow, 'tail': tail}
        response = self._make_request('GET', f'/containers/{container_id}/logs', params=params)
        return response.get('logs')

    def exec_command(self, container_id: str, command: List[str], tty: bool = False) -> Optional[Dict[str, Any]]:
        """Execute a command in a container."""
        data = {
            "command": command,
            "tty": tty
        }
        response = self._make_request('POST', f'/containers/{container_id}/exec', json=data)
        return response.get('result')

    # Agent management methods
    def start_agent_container(self, lmstudio_url: str = "http://localhost:1234/v1",
                            lmstudio_model: str = "llama-3.2-3b-instruct",
                            port: int = 4200, image_tag: str = "anvyl-agent:latest") -> Optional[Dict[str, Any]]:
        """Start the agent container."""
        data = {
            "lmstudio_url": lmstudio_url,
            "lmstudio_model": lmstudio_model,
            "port": port,
            "image_tag": image_tag
        }
        response = self._make_request('POST', '/agent/start', json=data)
        return response.get('result')

    def stop_agent_container(self) -> bool:
        """Stop the agent container."""
        response = self._make_request('POST', '/agent/stop')
        return 'message' in response

    def get_agent_container_status(self) -> Optional[Dict[str, Any]]:
        """Get the status of the agent container."""
        response = self._make_request('GET', '/agent/status')
        return response.get('status')

    def get_agent_logs(self, follow: bool = False, tail: int = 100) -> Optional[str]:
        """Get logs from the agent container."""
        params = {'follow': follow, 'tail': tail}
        response = self._make_request('GET', '/agent/logs', params=params)
        return response.get('logs')

    # Host command execution
    def exec_command_on_host(self, host_id: str, command: List[str],
                           working_directory: str = "", env: Optional[List[str]] = None,
                           timeout: int = 0) -> Optional[Dict[str, Any]]:
        """Execute a command on a specific host."""
        data = {
            "command": command,
            "working_directory": working_directory,
            "env": env,
            "timeout": timeout
        }
        response = self._make_request('POST', f'/hosts/{host_id}/exec', json=data)
        return response.get('result')


def get_infrastructure_client(base_url: str = "http://localhost:8080") -> InfrastructureClient:
    """Get an infrastructure client instance."""
    return InfrastructureClient(base_url)