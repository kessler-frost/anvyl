"""
Anvyl Infrastructure Service

This module provides infrastructure management functionality that was previously
handled by the gRPC server. It manages hosts and containers using
direct Python calls instead of gRPC.
"""

import logging
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import docker
import psutil
import socket
import json

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
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Docker client: {e}")
            self.docker_client = None

        # Register local host
        self._register_local_host()

        # Start container sync
        self._sync_containers_with_docker()

    def _register_local_host(self):
        """Register the local host in the system."""
        try:
            hostname = socket.gethostname()
            # Always use localhost IP to avoid multiple hosts for the same machine
            local_ip = "127.0.0.1"
        except:
            hostname = "localhost"
            local_ip = "127.0.0.1"

        # Check if a host with this IP already exists
        existing_host = self.db.get_host_by_ip(local_ip)
        if existing_host:
            # Use the existing host ID and update its information
            self.host_id = existing_host.id
            existing_host.name = hostname
            existing_host.last_seen = datetime.now(UTC)
            existing_host.status = "online"
            existing_host.set_tags(["local", "anvyl-server"])
            self.db.update_host(existing_host)
            logger.info(f"Updated existing local host: {hostname} ({local_ip})")
        else:
            # Create new host record
            host = Host(
                id=self.host_id,
                name=hostname,
                ip=local_ip,
                os="macOS",  # Can be detected dynamically
                last_seen=datetime.now(UTC),
                status="online",
                tags=json.dumps(["local", "anvyl-server"])
            )
            self.db.add_host(host)
            logger.info(f"Registered new local host: {hostname} ({local_ip})")

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
                tags=tags or []
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
    def list_containers(self, host_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List containers, optionally filtered by host. Only include Anvyl-managed containers."""
        containers = self.db.list_containers(host_id)
        result = []

        for container in containers:
            labels = container.get_labels()
            # Only include containers with the 'anvyl.type' label
            if not labels or not any(k.startswith("anvyl.") for k in labels):
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
        """Add a new container."""
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

            # Run the container
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

    def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a container."""
        if not self.docker_client:
            return False

        try:
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=timeout)

            # Update database
            db_container = self.db.get_container(container_id)
            if db_container:
                db_container.status = "stopped"
                self.db.update_container(db_container)
                # Refresh system status after stopping container
                self.db.refresh_system_status()

            return True
        except Exception as e:
            logger.error(f"Error stopping container: {e}")
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
            process_env = dict(env) if env else None

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

    # Agent container management methods
    def build_agent_image(self, dockerfile_path: str = "Dockerfile.agent",
                         context_path: str = ".", tag: str = "anvyl-agent:latest") -> bool:
        """Build the agent Docker image."""
        if not self.docker_client:
            return False

        try:
            logger.info(f"Building agent image: {tag}")

            # Build the image
            image, build_logs = self.docker_client.images.build(
                path=context_path,
                dockerfile=dockerfile_path,
                tag=tag,
                rm=True  # Remove intermediate containers
            )

            logger.info(f"Successfully built agent image: {image.tags}")
            return True

        except Exception as e:
            logger.error(f"Error building agent image: {e}")
            return False

    def start_agent_container(self, lmstudio_url: str = "http://localhost:1234/v1",
                            lmstudio_model: str = "llama-3.2-3b-instruct",
                            port: int = 4200, image_tag: str = "anvyl-agent:latest") -> Optional[Dict[str, Any]]:
        """Start the agent container."""
        if not self.docker_client:
            return None

        try:
            # Check if image exists, build if not
            try:
                self.docker_client.images.get(image_tag)
                logger.info(f"Using existing agent image: {image_tag}")
            except:
                logger.info(f"Agent image not found, building: {image_tag}")
                if not self.build_agent_image(tag=image_tag):
                    return None

            # Check if agent container already exists
            container_name = "anvyl-agent"
            try:
                existing_container = self.docker_client.containers.get(container_name)
                if existing_container.status == "running":
                    logger.info("Agent container is already running")
                    return {
                        "id": existing_container.id,
                        "name": container_name,
                        "status": "running",
                        "message": "Container already running"
                    }
                else:
                    # Remove stopped container
                    existing_container.remove()
                    logger.info("Removed stopped agent container")
            except:
                pass  # Container doesn't exist

            # Convert localhost to host.docker.internal for container-to-host communication
            container_lmstudio_url = lmstudio_url.replace("localhost", "host.docker.internal")

            # Prepare container configuration
            environment = [
                f"ANVYL_LMSTUDIO_URL={container_lmstudio_url}",
                f"ANVYL_LMSTUDIO_MODEL={lmstudio_model}",
                f"ANVYL_AGENT_PORT={port}",
                "PYTHONUNBUFFERED=1"
            ]

            # Mount Docker socket for container management
            volumes = {
                "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "ro"},
                "/": {"bind": "/host", "mode": "ro"}
            }

            # Container command
            command = [
                "python", "-m", "anvyl.cli", "agent", "start",
                "--lmstudio-url", container_lmstudio_url,
                "--model", lmstudio_model,
                "--port", "4200"
            ]

            # Run the container
            container = self.docker_client.containers.run(
                image=image_tag,
                name=container_name,
                environment=environment,
                volumes=volumes,
                ports={'4200/tcp': port},
                command=command,
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                labels={
                    "anvyl.type": "agent",
                    "anvyl.model": lmstudio_model,
                    "anvyl.lmstudio_url": lmstudio_url
                }
            )

            # Add to database
            db_container = Container(
                id=container.id,
                name=container_name,
                image=image_tag,
                host_id=self.host_id,
                status=container.status
            )
            db_container.set_labels({
                "anvyl.type": "agent",
                "anvyl.model": lmstudio_model,
                "anvyl.lmstudio_url": lmstudio_url
            })
            db_container.set_ports([f"{port}:4200"])
            db_container.set_environment(environment)

            self.db.add_container(db_container)
            # Refresh system status after adding agent container
            self.db.refresh_system_status()

            logger.info(f"Started agent container: {container.id}")
            return {
                "id": container.id,
                "name": container_name,
                "status": container.status,
                "port": port,
                "model": lmstudio_model,
                "lmstudio_url": lmstudio_url
            }

        except Exception as e:
            logger.error(f"Error starting agent container: {e}")
            return None

    def stop_agent_container(self) -> bool:
        """Stop the agent container."""
        if not self.docker_client:
            return False

        try:
            container_name = "anvyl-agent"
            container = self.docker_client.containers.get(container_name)

            # Stop the container
            container.stop(timeout=10)

            # Remove the container
            container.remove()

            # Remove from database
            db_container = self.db.get_container(container.id)
            if db_container:
                self.db.delete_container(container.id)
                # Refresh system status after removing agent container
                self.db.refresh_system_status()

            logger.info("Stopped and removed agent container")
            return True

        except Exception as e:
            logger.error(f"Error stopping agent container: {e}")
            return False

    def get_agent_container_status(self) -> Optional[Dict[str, Any]]:
        """Get the status of the agent container."""
        if not self.docker_client:
            return None

        try:
            container_name = "anvyl-agent"
            container = self.docker_client.containers.get(container_name)

            # Get container info
            container_info = container.attrs

            return {
                "id": container.id,
                "name": container.name,
                "status": container.status,
                "image": container_info['Config']['Image'],
                "created": container_info['Created'],
                "ports": container_info.get('NetworkSettings', {}).get('Ports', {}),
                "labels": container_info.get('Config', {}).get('Labels', {}),
                "environment": container_info.get('Config', {}).get('Env', [])
            }

        except Exception as e:
            logger.error(f"Error getting agent container status: {e}")
            return None

    def get_agent_logs(self, follow: bool = False, tail: int = 100) -> Optional[str]:
        """Get logs from the agent container."""
        if not self.docker_client:
            return "Error: Docker client not available"

        try:
            container_name = "anvyl-agent"
            container = self.docker_client.containers.get(container_name)

            # Check if container is running
            if container.status not in ["running", "restarting"]:
                return f"Container is not running (status: {container.status}). Use 'anvyl agent start' to start the agent."

            return container.logs(tail=tail, follow=follow).decode('utf-8')

        except Exception as e:
            logger.error(f"Error getting agent logs: {e}")
            return f"Error getting agent logs: {str(e)}"


# Global service instance
_infrastructure_service = None

def get_infrastructure_service() -> InfrastructureService:
    """Get the global infrastructure service instance."""
    global _infrastructure_service
    if _infrastructure_service is None:
        _infrastructure_service = InfrastructureService()
    return _infrastructure_service