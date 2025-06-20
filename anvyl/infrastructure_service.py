"""
Anvyl Infrastructure Service

This module provides infrastructure management functionality that was previously
handled by the gRPC server. It manages hosts, containers, and agents using
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

from .database.models import DatabaseManager, Host, Container, Agent

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
                agents_installed=True,
                os="macOS",  # Can be detected dynamically
                last_seen=datetime.now(UTC),
                status="online",
                tags=["local", "anvyl-server"]
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
                agents_installed=False,
                os=os,
                last_seen=datetime.now(UTC),
                status="offline"
            )
            host.set_tags(tags or [])

            self.db.add_host(host)

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
        """List containers, optionally filtered by host."""
        containers = self.db.list_containers(host_id)
        result = []

        for container in containers:
            container_dict = {
                "id": container.id,
                "name": container.name,
                "image": container.image,
                "status": container.status,
                "host_id": container.host_id,
                "labels": container.get_labels(),
                "ports": container.get_ports(),
                "volumes": container.get_volumes(),
                "environment": container.get_environment()
            }
            result.append(container_dict)

        return result

    def add_container(self, name: str, image: str, host_id: Optional[str] = None,
                     labels: Optional[Dict[str, str]] = None, ports: Optional[List[str]] = None,
                     volumes: Optional[List[str]] = None, environment: Optional[List[str]] = None,
                     launched_by_agent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
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
                status=docker_container.status,
                launched_by_agent_id=launched_by_agent_id
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
            result = container.exec_run(command, tty=tty)

            return {
                "output": result.output.decode('utf-8') if result.output else "",
                "exit_code": result.exit_code,
                "success": result.exit_code == 0
            }
        except Exception as e:
            logger.error(f"Error executing command in container: {e}")
            return None

    # Agent management methods
    def list_agents(self, host_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List agents, optionally filtered by host."""
        agents = self.db.list_agents(host_id)
        result = []

        for agent in agents:
            agent_dict = {
                "id": agent.id,
                "name": agent.name,
                "host_id": agent.host_id,
                "entrypoint": agent.entrypoint,
                "working_directory": agent.working_directory,
                "status": agent.status,
                "container_id": agent.container_id,
                "persistent": agent.persistent,
                "started_at": agent.started_at.isoformat() if agent.started_at else "",
                "stopped_at": agent.stopped_at.isoformat() if agent.stopped_at else "",
                "exit_code": agent.exit_code or 0
            }
            result.append(agent_dict)

        return result

    def launch_agent(self, name: str, host_id: str, entrypoint: str,
                    env: Optional[List[str]] = None, working_directory: str = "",
                    arguments: Optional[List[str]] = None, persistent: bool = False) -> Optional[Dict[str, Any]]:
        """Launch a Python agent in a container."""
        if not self.docker_client:
            return None

        try:
            agent_id = str(uuid.uuid4())

            # Create agent record
            agent = Agent(
                id=agent_id,
                name=name,
                host_id=host_id,
                entrypoint=entrypoint,
                working_directory=working_directory,
                persistent=persistent,
                status="starting"
            )
            agent.set_env(env or [])
            agent.set_arguments(arguments or [])

            # Launch agent in container
            return self._launch_agent_in_container(agent)

        except Exception as e:
            logger.error(f"Error launching agent: {e}")
            return None

    def _launch_agent_in_container(self, agent: Agent) -> Optional[Dict[str, Any]]:
        """Launch agent in a Docker container."""
        if not self.docker_client:
            return None

        try:
            # Create container for agent
            container_config = {
                'image': 'python:3.12-alpine',  # Default Python image
                'name': f"agent-{agent.name}-{agent.id[:8]}",
                'command': ['python', '-c', f'exec(open("{agent.entrypoint}").read())'],
                'environment': agent.get_env(),
                'working_dir': agent.working_directory or '/app',
                'detach': True,
                'labels': {
                    'anvyl.agent.id': agent.id,
                    'anvyl.agent.name': agent.name,
                    'anvyl.component': 'agent'
                }
            }

            docker_container = self.docker_client.containers.run(**container_config)

            # Update agent with container info
            agent.container_id = docker_container.id
            agent.status = "running"
            agent.started_at = datetime.now(UTC)

            self.db.add_agent(agent)

            logger.info(f"Successfully launched agent {agent.name} in container {docker_container.id}")

            return {
                "id": agent.id,
                "name": agent.name,
                "host_id": agent.host_id,
                "entrypoint": agent.entrypoint,
                "working_directory": agent.working_directory,
                "status": agent.status,
                "container_id": agent.container_id,
                "persistent": agent.persistent,
                "started_at": agent.started_at.isoformat() if agent.started_at else "",
                "stopped_at": agent.stopped_at.isoformat() if agent.stopped_at else "",
                "exit_code": agent.exit_code or 0
            }

        except Exception as e:
            logger.error(f"Error launching agent in container: {e}")
            return None

    def stop_agent(self, agent_id: str) -> bool:
        """Stop an agent."""
        try:
            agent = self.db.get_agent(agent_id)
            if not agent:
                return False

            # Stop containerized agent
            if agent.container_id and self.docker_client:
                try:
                    container = self.docker_client.containers.get(agent.container_id)
                    container.stop()
                    container.remove()
                except Exception as e:
                    logger.warning(f"Error stopping container: {e}")

            # Update agent status
            agent.status = "stopped"
            agent.stopped_at = datetime.now(UTC)
            self.db.update_agent(agent)

            return True

        except Exception as e:
            logger.error(f"Error stopping agent: {e}")
            return False

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent status."""
        try:
            agent = self.db.get_agent(agent_id)
            if not agent:
                return None

            # For containerized agents, check container status
            if agent.container_id and self.docker_client:
                try:
                    container = self.docker_client.containers.get(agent.container_id)
                    if container.status != "running":
                        # Container has stopped
                        agent.status = "stopped"
                        agent.stopped_at = datetime.now(UTC)
                        agent.exit_code = container.attrs.get('State', {}).get('ExitCode', 0)
                        self.db.update_agent(agent)
                except Exception as e:
                    # Container doesn't exist
                    agent.status = "stopped"
                    agent.stopped_at = datetime.now(UTC)
                    self.db.update_agent(agent)

            return {
                "id": agent.id,
                "name": agent.name,
                "host_id": agent.host_id,
                "entrypoint": agent.entrypoint,
                "working_directory": agent.working_directory,
                "status": agent.status,
                "container_id": agent.container_id,
                "persistent": agent.persistent,
                "started_at": agent.started_at.isoformat() if agent.started_at else "",
                "stopped_at": agent.stopped_at.isoformat() if agent.stopped_at else "",
                "exit_code": agent.exit_code or 0
            }

        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return None

    def execute_agent_instruction(self, agent_name: str, instruction: str) -> Optional[Dict[str, Any]]:
        """Execute an instruction on an AI agent."""
        try:
            # Import agent manager here to avoid circular imports
            from .agent_manager import get_agent_manager

            manager = get_agent_manager()

            # Check if agent exists and is running
            config = manager.get_agent_config(agent_name)
            if not config:
                return {
                    "success": False,
                    "result": "",
                    "error_message": f"Agent '{agent_name}' not found"
                }

            status_info = manager.get_agent_status(agent_name)
            if not status_info or not status_info.get("running", False):
                return {
                    "success": False,
                    "result": "",
                    "error_message": f"Agent '{agent_name}' is not running"
                }

            # For containerized agents, we need to execute the instruction in the container
            if config.container_id and self.docker_client:
                try:
                    container = self.docker_client.containers.get(config.container_id)

                    # Prepare the Python code to execute
                    python_code = f'''
import sys
sys.path.insert(0, "/app")
from anvyl.ai_agent import create_ai_agent

# Create agent instance
agent = create_ai_agent(
    model_provider="{config.provider}",
    model_id="{config.model_id}",
    host="{config.host}",
    port={config.port},
    verbose={config.verbose},
    agent_name="{config.name}",
    {', '.join([f'{k}={repr(v)}' for k, v in config.provider_kwargs.items()])}
)

# Execute instruction
result = agent.act("{instruction}")
print(result)
'''

                    # Execute the command in the container
                    exec_result = container.exec_run(
                        cmd=['python', '-c', python_code],
                        timeout=300  # 5 minute timeout
                    )

                    if exec_result.exit_code == 0:
                        return {
                            "success": True,
                            "result": exec_result.output.decode('utf-8').strip(),
                            "error_message": ""
                        }
                    else:
                        return {
                            "success": False,
                            "result": "",
                            "error_message": f"Failed to execute instruction: {exec_result.output.decode('utf-8')}"
                        }

                except Exception as e:
                    return {
                        "success": False,
                        "result": "",
                        "error_message": f"Error executing instruction in container: {e}"
                    }
            else:
                return {
                    "success": False,
                    "result": "",
                    "error_message": "Non-containerized agents not supported for instruction execution"
                }

        except Exception as e:
            logger.error(f"Error executing agent instruction: {e}")
            return {
                "success": False,
                "result": "",
                "error_message": str(e)
            }

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


# Global service instance
_infrastructure_service = None

def get_infrastructure_service() -> InfrastructureService:
    """Get the global infrastructure service instance."""
    global _infrastructure_service
    if _infrastructure_service is None:
        _infrastructure_service = InfrastructureService()
    return _infrastructure_service