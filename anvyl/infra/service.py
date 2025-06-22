"""
Anvyl Infrastructure Service

This module provides infrastructure management functionality that was previously
handled by the gRPC server. It manages hosts and containers using
direct Python calls instead of gRPC.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import docker
import psutil
import socket
import json
import platform

from anvyl.database.models import DatabaseManager, Host, Container

logger = logging.getLogger(__name__)

# Use UTC for all timestamps
UTC = timezone.utc


class InfrastructureService:
    """Service for managing Anvyl infrastructure."""

    def __init__(self):
        """Initialize the service."""
        self.db = DatabaseManager()
        self.host_id = str(uuid.uuid4())

        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Failed to initialize Docker client: {e}")
            self.docker_client = None

        # Register local host
        self._register_local_host()

        # Start container sync
        self._sync_containers_with_docker()

    def _register_local_host(self):
        """Register the local host in the database."""
        hostname = platform.node()
        local_ip = self._get_local_ip()

        # Detect OS and architecture dynamically
        detected_os = platform.system()
        detected_arch = platform.machine()

        # Check if host already exists
        existing_host = self.db.get_host_by_ip(local_ip)
        if existing_host:
            # Update existing host
            existing_host.last_seen = datetime.now(UTC)
            existing_host.os = detected_os
            existing_host.architecture = detected_arch
            self.db.update_host(existing_host)
            logger.info(f"Updated existing local host: {hostname} ({local_ip})")
        else:
            # Create new host
            host = Host(
                id=self.host_id,
                name=hostname,
                ip=local_ip,
                os=detected_os,
                architecture=detected_arch,
                last_seen=datetime.now(UTC),
                status="online",
                tags=json.dumps(["local", "anvyl-server"])
            )
            self.db.add_host(host)
            logger.info(f"Registered new local host: {hostname} ({local_ip})")

    def _get_local_ip(self) -> str:
        """Get the local IP address."""
        try:
            # Try to get the local IP by connecting to a remote address
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Doesn't actually connect, just gets the local IP
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            # Fallback to localhost
            return "127.0.0.1"

    def _get_host_resources(self) -> Dict[str, Any]:
        """Get current host resource information."""
        try:
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                "cpu_count": cpu_count,
                "memory_total": memory.total // (1024 * 1024),  # Convert to MB
                "memory_available": memory.available // (1024 * 1024),  # Convert to MB
                "disk_total": disk.total // (1024 * 1024 * 1024),  # Convert to GB
                "disk_available": disk.free // (1024 * 1024 * 1024)  # Convert to GB
            }
        except Exception as e:
            logger.error(f"Error getting host resources: {e}")
            return {
                "cpu_count": 0,
                "memory_total": 0,
                "memory_available": 0,
                "disk_total": 0,
                "disk_available": 0
            }

    def _sync_containers_with_docker(self):
        """Sync container information with Docker."""
        if not self.docker_client:
            logger.warning("Docker client not available, skipping container sync")
            return

        try:
            # Get all containers from Docker
            docker_containers = self.docker_client.containers.list(all=True)

            # Get existing containers from database
            db_containers = self.db.list_containers()
            db_container_ids = {c.id for c in db_containers}

            # Update or add containers
            for docker_container in docker_containers:
                container_info = docker_container.attrs

                if docker_container.id not in db_container_ids:
                    # Add new container
                    container = Container(
                        id=docker_container.id,
                        name=container_info['Name'].lstrip('/'),
                        image=container_info['Config']['Image'],
                        host_id=self.host_id,
                        status=container_info['State']['Status']
                    )

                    # Set labels
                    labels = container_info.get('Config', {}).get('Labels', {})
                    container.set_labels(labels)

                    # Set ports
                    ports = []
                    port_bindings = container_info.get('HostConfig', {}).get('PortBindings', {})
                    for container_port, host_bindings in port_bindings.items():
                        if host_bindings:
                            for binding in host_bindings:
                                host_port = binding.get('HostPort', '')
                                host_ip = binding.get('HostIp', '0.0.0.0')
                                ports.append(f"{host_port}:{host_ip}")
                    container.set_ports(ports)

                    # Set environment
                    env = container_info.get('Config', {}).get('Env', [])
                    container.set_environment(env)

                    self.db.add_container(container)
                    logger.info(f"Added container: {container.name}")
                else:
                    # Update existing container
                    container = self.db.get_container(docker_container.id)
                    if container:
                        container.status = container_info['State']['Status']
                        self.db.update_container(container)

            # Remove containers that no longer exist in Docker
            docker_container_ids = {c.id for c in docker_containers}
            for db_container in db_containers:
                if db_container.id not in docker_container_ids:
                    self.db.delete_container(db_container.id)
                    logger.info(f"Removed container: {db_container.name}")

        except Exception as e:
            logger.error(f"Error syncing containers: {e}")

        # Refresh system status after container sync
        self.db.refresh_system_status()

    # Host management methods
    def list_hosts(self) -> List[Dict[str, Any]]:
        """List all registered hosts."""
        hosts = self.db.list_hosts()
        result = []

        for host in hosts:
            host_dict = {
                "id": host.id,
                "name": host.name,
                "ip": host.ip,
                "os": host.os or "",
                "status": host.status,
                "tags": host.get_tags(),
                "resources": self._get_host_resources() if host.id == self.host_id else None
            }
            result.append(host_dict)

        return result

    def add_host(self, name: str, ip: str, os: str = "", tags: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Add a new host to the system."""
        try:
            host_id = str(uuid.uuid4())
            host = Host(
                id=host_id,
                name=name,
                ip=ip,
                os=os,
                last_seen=datetime.now(UTC),
                status="online",
                tags=json.dumps(tags or [])
            )

            self.db.add_host(host)
            # Refresh system status after adding host
            self.db.refresh_system_status()

            return {
                "id": host.id,
                "name": host.name,
                "ip": host.ip,
                "os": host.os,
                "status": host.status,
                "tags": host.get_tags()
            }
        except Exception as e:
            logger.error(f"Error adding host: {e}")
            return None

    def update_host(self, host_id: str, resources: Optional[Dict[str, Any]] = None,
                   status: str = "", tags: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Update host information."""
        host = self.db.get_host(host_id)
        if not host:
            return None

        try:
            # Update host fields
            if status:
                host.status = status
            if tags:
                host.set_tags(tags)
            if resources:
                host.set_resources(resources)

            self.db.update_host(host)
            # Refresh system status after updating host
            self.db.refresh_system_status()

            return {
                "id": host.id,
                "name": host.name,
                "ip": host.ip,
                "os": host.os,
                "status": host.status,
                "tags": host.get_tags()
            }
        except Exception as e:
            logger.error(f"Error updating host: {e}")
            return None

    def get_host_metrics(self, host_id: str) -> Optional[Dict[str, Any]]:
        """Get current host metrics."""
        try:
            host = self.db.get_host(host_id)
            if not host:
                return None
            return self._get_host_resources()
        except Exception as e:
            logger.error(f"Error getting host metrics: {e}")
            return None

    def host_heartbeat(self, host_id: str) -> bool:
        """Update host heartbeat."""
        try:
            host = self.db.get_host(host_id)
            if not host:
                return False
            self.db.update_host_heartbeat(host_id)
            return True
        except Exception as e:
            logger.error(f"Error updating host heartbeat: {e}")
            return False

    # Container management methods
    def list_containers(self, host_id: Optional[str] = None, all: bool = False) -> List[Dict[str, Any]]:
        """List containers, optionally filtered by host. If all=True, include all containers regardless of label or status."""
        containers = self.db.list_containers(host_id)
        result = []

        for container in containers:
            labels = container.get_labels()
            # Only include containers with the 'anvyl.type' label unless all=True
            if not all and (not labels or not any(k.startswith("anvyl.") for k in labels)):
                continue
            container_dict = {
                "id": container.id,
                "name": container.name,
                "image": container.image,
                "status": container.status,
                "host_id": container.host_id,
                "labels": labels,
                "ports": container.get_ports(),
                "volumes": container.get_volumes(),
                "environment": container.get_environment()
            }
            result.append(container_dict)

        return result

    def add_container(self, name: str, image: str, host_id: Optional[str] = None,
                     labels: Optional[Dict[str, str]] = None, ports: Optional[List[str]] = None,
                     volumes: Optional[List[str]] = None, environment: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Add a new container (create and start)."""
        if not self.docker_client:
            return None

        try:
            # Use local host if not specified
            if not host_id:
                host_id = self.host_id

            # Prepare Docker run parameters
            run_params = {
                'image': image,
                'name': name,
                'detach': True
            }

            if ports:
                port_bindings = {}
                for port_mapping in ports:
                    if ':' in port_mapping:
                        host_port, container_port = port_mapping.split(':', 1)
                        port_bindings[container_port] = host_port
                run_params['ports'] = port_bindings

            if volumes:
                run_params['volumes'] = volumes

            if environment:
                run_params['environment'] = environment

            if labels:
                run_params['labels'] = labels

            # Run the container (create and start)
            docker_container = self.docker_client.containers.run(**run_params)

            # Add to database
            container = Container(
                id=docker_container.id,
                name=name,
                image=image,
                host_id=host_id,
                status=docker_container.status
            )

            if labels:
                container.set_labels(labels)
            if ports:
                container.set_ports(ports)
            if volumes:
                container.set_volumes(volumes)
            if environment:
                container.set_environment(environment)

            self.db.add_container(container)
            # Refresh system status after adding container
            self.db.refresh_system_status()

            return {
                "id": container.id,
                "name": container.name,
                "image": container.image,
                "status": container.status,
                "host_id": container.host_id
            }

        except Exception as e:
            logger.error(f"Error adding container: {e}")
            return None

    def remove_container(self, container_id: str, timeout: int = 10) -> bool:
        """Remove a container."""
        try:
            if not self.docker_client:
                logger.error("Docker client not available")
                return False

            # Stop and remove the container
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=timeout)
            container.remove()

            # Refresh system status after removing container
            self.db.refresh_system_status()

            logger.info(f"Removed container: {container_id}")
            return True

        except Exception as e:
            logger.error(f"Error removing container: {e}")
            return False

    def get_logs(self, container_id: str, follow: bool = False, tail: int = 100) -> Optional[str]:
        """Get container logs."""
        if not self.docker_client:
            return None

        try:
            container = self.docker_client.containers.get(container_id)
            return container.logs(tail=tail, follow=follow).decode('utf-8')
        except Exception as e:
            logger.error(f"Error getting container logs: {e}")
            return None

    def exec_command(self, container_id: str, command: List[str], tty: bool = False) -> Optional[Dict[str, Any]]:
        """Execute command in container."""
        if not self.docker_client:
            return None

        try:
            container = self.docker_client.containers.get(container_id)
            exec_result = container.exec_run(
                cmd=command,
                tty=tty,
                stream=False
            )

            return {
                "output": exec_result.output.decode('utf-8') if isinstance(exec_result.output, bytes) else exec_result.output,
                "exit_code": exec_result.exit_code,
                "success": exec_result.exit_code == 0
            }

        except Exception as e:
            logger.error(f"Error executing command in container: {e}")
            return None

    def exec_command_on_host(self, host_id: str, command: List[str],
                           working_directory: str = "", env: Optional[List[str]] = None,
                           timeout: int = 0) -> Optional[Dict[str, Any]]:
        """Execute command on host."""
        if host_id != self.host_id:
            return {
                "output": "",
                "stderr": "",
                "exit_code": 1,
                "success": False,
                "error_message": "Can only execute commands on local host"
            }

        try:
            import subprocess

            # Prepare environment
            process_env = None
            if env:
                process_env = {}
                for item in env:
                    if "=" in item:
                        k, v = item.split("=", 1)
                        process_env[k] = v

            # Execute command
            result = subprocess.run(
                command,
                cwd=working_directory or None,
                env=process_env,
                capture_output=True,
                text=True,
                timeout=timeout if timeout > 0 else None
            )

            return {
                "output": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "success": True,
                "error_message": ""
            }

        except subprocess.TimeoutExpired:
            return {
                "output": "",
                "stderr": "",
                "exit_code": 124,  # Standard timeout exit code
                "success": False,
                "error_message": "Command timed out"
            }
        except Exception as e:
            logger.error(f"Error executing command on host: {e}")
            return {
                "output": "",
                "stderr": "",
                "exit_code": 1,
                "success": False,
                "error_message": str(e)
            }

    # Additional Docker operations for MCP server
    def inspect_container(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Inspect a container."""
        if not self.docker_client:
            return None

        try:
            container = self.docker_client.containers.get(container_id)
            return {
                "id": container.id,
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else container.image.id,
                "status": container.status,
                "created": container.attrs['Created'],
                "ports": container.attrs['NetworkSettings']['Ports'],
                "mounts": container.attrs['Mounts'],
                "env": container.attrs['Config']['Env'],
                "cmd": container.attrs['Config']['Cmd'],
                "entrypoint": container.attrs['Config']['Entrypoint'],
                "labels": container.attrs['Config']['Labels']
            }
        except Exception as e:
            logger.error(f"Error inspecting container: {e}")
            return None

    def get_container_stats(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Get container statistics."""
        if not self.docker_client:
            return None

        try:
            container = self.docker_client.containers.get(container_id)
            stats = container.stats(stream=False)

            # Calculate CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            cpu_percent = 0.0
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100.0

            # Calculate memory usage
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0.0

            return {
                "cpu_percent": round(cpu_percent, 2),
                "memory_usage": memory_usage,
                "memory_limit": memory_limit,
                "memory_percent": round(memory_percent, 2),
                "network_rx": stats['networks']['eth0']['rx_bytes'] if 'networks' in stats and 'eth0' in stats['networks'] else 0,
                "network_tx": stats['networks']['eth0']['tx_bytes'] if 'networks' in stats and 'eth0' in stats['networks'] else 0,
                "block_read": stats['blkio_stats']['io_service_bytes'][0]['value'] if stats['blkio_stats']['io_service_bytes'] else 0,
                "block_write": stats['blkio_stats']['io_service_bytes'][1]['value'] if len(stats['blkio_stats']['io_service_bytes']) > 1 else 0
            }
        except Exception as e:
            logger.error(f"Error getting container stats: {e}")
            return None

    def list_images(self) -> List[Dict[str, Any]]:
        """List all Docker images."""
        if not self.docker_client:
            return []

        try:
            images = self.docker_client.images.list()
            result = []

            for image in images:
                tags = image.tags if image.tags else ["<none>:<none>"]
                for tag in tags:
                    if ":" in tag:
                        repo, tag_val = tag.split(":", 1)
                    else:
                        repo, tag_val = tag, "<none>"

                    result.append({
                        "id": image.short_id,
                        "repository": repo,
                        "tag": tag_val,
                        "created": image.attrs['Created'],
                        "size": image.attrs['Size']
                    })

            return result
        except Exception as e:
            logger.error(f"Error listing images: {e}")
            return []

    def pull_image(self, image_name: str, tag: str = "latest") -> Optional[Dict[str, Any]]:
        """Pull a Docker image."""
        if not self.docker_client:
            return None

        try:
            full_name = f"{image_name}:{tag}"
            image = self.docker_client.images.pull(image_name, tag=tag)

            return {
                "id": image.short_id,
                "tags": image.tags,
                "created": image.attrs['Created'],
                "size": image.attrs['Size']
            }
        except Exception as e:
            logger.error(f"Error pulling image: {e}")
            return None

    def remove_image(self, image_id: str, force: bool = False) -> bool:
        """Remove a Docker image."""
        if not self.docker_client:
            return False

        try:
            self.docker_client.images.remove(image_id, force=force)
            return True
        except Exception as e:
            logger.error(f"Error removing image: {e}")
            return False

    def inspect_image(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Inspect a Docker image."""
        if not self.docker_client:
            return None

        try:
            image = self.docker_client.images.get(image_id)
            return {
                "id": image.id,
                "tags": image.tags,
                "created": image.attrs['Created'],
                "size": image.attrs['Size'],
                "architecture": image.attrs['Architecture'],
                "os": image.attrs['Os'],
                "config": image.attrs['Config']
            }
        except Exception as e:
            logger.error(f"Error inspecting image: {e}")
            return None

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        try:
            import platform
            import psutil

            return {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": psutil.disk_usage('/').total
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}


# Global service instance
_infrastructure_service = None

def get_infrastructure_service() -> InfrastructureService:
    """Get the global infrastructure service instance."""
    global _infrastructure_service
    if _infrastructure_service is None:
        _infrastructure_service = InfrastructureService()
    return _infrastructure_service