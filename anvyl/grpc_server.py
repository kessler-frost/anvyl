#!/usr/bin/env python3
"""
Anvyl gRPC Server
A self-hosted infrastructure orchestrator for Apple Silicon systems.
"""

import grpc
import docker
import uuid
import socket
import logging
import subprocess
import asyncio
import psutil
from datetime import datetime, UTC, timezone
from concurrent import futures
from typing import Dict, List, Optional

# Ensure protobuf files are generated automatically
from anvyl.proto_utils import ensure_protos_generated
ensure_protos_generated()

# Import generated gRPC code
from anvyl.generated import anvyl_pb2  # type: ignore
from anvyl.generated import anvyl_pb2_grpc  # type: ignore

# Import database models
from anvyl.database.models import DatabaseManager, Host, Container, Agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use UTC for all timestamps
UTC = timezone.utc

class AnvylService(anvyl_pb2_grpc.AnvylServiceServicer):
    """gRPC service implementation for Anvyl infrastructure orchestrator."""

    def __init__(self):
        """Initialize the service with Docker client and database."""
        self.docker_client: Optional[docker.DockerClient] = None
        self.db: DatabaseManager = DatabaseManager()

        # Initialize Docker client
        try:
            # Try multiple approaches to connect to Docker
            import os

            # First try the default approach
            try:
                self.docker_client = docker.from_env()
                self.docker_client.ping()
                logger.info("Docker client initialized successfully with default settings")
            except Exception as e1:
                logger.warning(f"Default Docker connection failed: {e1}")

                # Try with explicit Unix socket
                try:
                    self.docker_client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
                    self.docker_client.ping()
                    logger.info("Docker client initialized successfully with Unix socket")
                except Exception as e2:
                    logger.warning(f"Unix socket connection failed: {e2}")

                    # Try with Docker Desktop socket
                    try:
                        self.docker_client = docker.DockerClient(base_url='unix:///Users/fimbulwinter/.docker/run/docker.sock')
                        self.docker_client.ping()
                        logger.info("Docker client initialized successfully with Docker Desktop socket")
                    except Exception as e3:
                        logger.error(f"All Docker connection attempts failed. Docker operations will be disabled.")
                        logger.error(f"Errors: Default={e1}, Unix={e2}, Desktop={e3}")
                        self.docker_client = None

        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.docker_client = None

        self.host_id = str(uuid.uuid4())

        # Register this host
        self._register_local_host()

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

    def _get_host_resources(self) -> anvyl_pb2.HostResources:  # type: ignore
        """Get current host resource information."""
        try:
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return anvyl_pb2.HostResources(  # type: ignore
                cpu_count=cpu_count,
                memory_total=memory.total // (1024 * 1024),  # Convert to MB
                memory_available=memory.available // (1024 * 1024),  # Convert to MB
                disk_total=disk.total // (1024 * 1024 * 1024),  # Convert to GB
                disk_available=disk.free // (1024 * 1024 * 1024)  # Convert to GB
            )
        except Exception as e:
            logger.error(f"Error getting host resources: {e}")
            return anvyl_pb2.HostResources(  # type: ignore
                cpu_count=0,
                memory_total=0,
                memory_available=0,
                disk_total=0,
                disk_available=0
            )

    def _host_to_proto(self, host: Host) -> anvyl_pb2.Host:  # type: ignore
        """Convert database Host to protobuf Host."""
        return anvyl_pb2.Host(  # type: ignore
            id=host.id,
            name=host.name,
            ip=host.ip,
            os=host.os or "",
            status=host.status,
            tags=list(host.tags),
            resources=self._get_host_resources() if host.id == self.host_id else None
        )

    def _container_to_proto(self, container: Container) -> anvyl_pb2.Container:  # type: ignore
        """Convert database Container to protobuf Container."""
        return anvyl_pb2.Container(  # type: ignore
            id=container.id,
            name=container.name,
            image=container.image,
            status=container.status,
            host_id=container.host_id,
            labels=container.get_labels(),
            ports=list(container.ports) if container.ports else [],
            volumes=list(container.volumes) if container.volumes else [],
            environment=list(container.environment) if container.environment else []
        )

    def _agent_to_proto(self, agent: Agent) -> anvyl_pb2.Agent:  # type: ignore
        """Convert database Agent to protobuf Agent."""
        return anvyl_pb2.Agent(  # type: ignore
            id=agent.id,
            name=agent.name,
            host_id=agent.host_id,
            entrypoint=agent.entrypoint,
            working_directory=agent.working_directory or "",
            status=agent.status,
            container_id=agent.container_id or "",
            persistent=agent.persistent,
            started_at=agent.started_at.isoformat() if agent.started_at else "",
            stopped_at=agent.stopped_at.isoformat() if agent.stopped_at else "",
            exit_code=agent.exit_code or 0
        )

    # Host management methods
    def ListHosts(self, request, context):
        """List all registered hosts."""
        logger.info("ListHosts called")
        hosts = self.db.list_hosts()
        proto_hosts = [self._host_to_proto(host) for host in hosts]
        return anvyl_pb2.ListHostsResponse(hosts=proto_hosts)  # type: ignore

    def AddHost(self, request, context):
        """Add a new host to the system."""
        logger.info(f"AddHost called: {request.name} ({request.ip})")

        host_id = str(uuid.uuid4())
        host = Host(
            id=host_id,
            name=request.name,
            ip=request.ip,
            agents_installed=False,
            os=request.os,
            last_seen=datetime.now(UTC),
            status="offline"
        )
        host.set_tags(list(request.tags))

        try:
            self.db.add_host(host)
            return anvyl_pb2.AddHostResponse(  # type: ignore
                host=self._host_to_proto(host),
                success=True,
                error_message=""
            )
        except Exception as e:
            logger.error(f"Error adding host: {e}")
            return anvyl_pb2.AddHostResponse(  # type: ignore
                host=None,
                success=False,
                error_message=str(e)
            )

    def UpdateHost(self, request, context):
        """Update host information."""
        logger.info(f"UpdateHost called: {request.host_id}")

        host = self.db.get_host(request.host_id)
        if not host:
            return anvyl_pb2.UpdateHostResponse(  # type: ignore
                host=None,
                success=False,
                error_message="Host not found"
            )

        try:
            # Update host fields
            if request.status:
                host.status = request.status
            if request.tags:
                host.set_tags(list(request.tags))
            if request.resources:
                # Store resources in database
                resources_dict = {
                    "cpu_count": request.resources.cpu_count,
                    "memory_total": request.resources.memory_total,
                    "memory_available": request.resources.memory_available,
                    "disk_total": request.resources.disk_total,
                    "disk_available": request.resources.disk_available
                }
                host.set_resources(resources_dict)

            self.db.update_host(host)
            return anvyl_pb2.UpdateHostResponse(  # type: ignore
                host=self._host_to_proto(host),
                success=True,
                error_message=""
            )
        except Exception as e:
            logger.error(f"Error updating host: {e}")
            return anvyl_pb2.UpdateHostResponse(  # type: ignore
                host=None,
                success=False,
                error_message=str(e)
            )

    def GetHostMetrics(self, request, context):
        """Get current host metrics."""
        logger.info(f"GetHostMetrics called: {request.host_id}")
        try:
            host = self.db.get_host(request.host_id)
            if not host:
                return anvyl_pb2.GetHostMetricsResponse(resources=None, success=False, error_message="Host not found")  # type: ignore
            resources = self._get_host_resources()
            return anvyl_pb2.GetHostMetricsResponse(resources=resources, success=True, error_message="")  # type: ignore
        except Exception as e:
            logger.error(f"Error getting host metrics: {e}")
            return anvyl_pb2.GetHostMetricsResponse(resources=None, success=False, error_message=str(e))  # type: ignore

    def HostHeartbeat(self, request, context):
        """Update host heartbeat."""
        logger.info(f"HostHeartbeat called: {request.host_id}")

        try:
            host = self.db.get_host(request.host_id)
            if not host:
                return anvyl_pb2.HostHeartbeatResponse(success=False, error_message="Host not found")  # type: ignore
            self.db.update_host_heartbeat(request.host_id)
            return anvyl_pb2.HostHeartbeatResponse(success=True, error_message="")  # type: ignore
        except Exception as e:
            logger.error(f"Error updating host heartbeat: {e}")
            return anvyl_pb2.HostHeartbeatResponse(success=False, error_message=str(e))  # type: ignore

    # Container management methods
    def ListContainers(self, request, context):
        """List containers, optionally filtered by host."""
        logger.info(f"ListContainers called: host_id={request.host_id}")
        containers = self.db.list_containers(host_id=request.host_id)
        proto_containers = [self._container_to_proto(c) for c in containers]
        return anvyl_pb2.ListContainersResponse(containers=proto_containers)  # type: ignore

    def _sync_containers_with_docker(self):
        """Sync database containers with live Docker containers."""
        if not self.docker_client:
            return

        try:
            live_containers = self.docker_client.containers.list(all=True)
            live_container_ids = {c.id for c in live_containers}

            # Get existing containers from database
            db_containers = self.db.list_containers(self.host_id)
            db_container_ids = {c.id for c in db_containers}

            # Add new containers
            for docker_container in live_containers:
                if docker_container.id not in db_container_ids:
                    container = Container(
                        id=docker_container.id,
                        name=docker_container.name,
                        image=docker_container.image.tags[0] if docker_container.image.tags else docker_container.image.id,
                        host_id=self.host_id,
                        status=docker_container.status,
                        created_at=datetime.fromtimestamp(docker_container.attrs['Created'])
                    )
                    container.set_labels(docker_container.labels)
                    self.db.add_container(container)

            # Update existing containers
            for docker_container in live_containers:
                if docker_container.id in db_container_ids:
                    db_container = self.db.get_container(docker_container.id)
                    if db_container and db_container.status != docker_container.status:
                        db_container.status = docker_container.status
                        self.db.update_container(db_container)

        except Exception as e:
            logger.error(f"Error syncing containers: {e}")

    def AddContainer(self, request, context):
        """Add a new container using Docker SDK."""
        logger.info(f"AddContainer called: {request.name} ({request.image})")

        if not self.docker_client:
            return anvyl_pb2.AddContainerResponse(  # type: ignore
                container=None,
                success=False,
                error_message="Docker client not available"
            )

        try:
            # Prepare container configuration
            container_config = {
                'image': request.image,
                'name': request.name,
                'labels': dict(request.labels),
                'detach': True
            }

            # Add port mappings if specified
            if request.ports:
                ports = {}
                for port_mapping in request.ports:
                    if ':' in port_mapping:
                        host_port, container_port = port_mapping.split(':', 1)
                        ports[container_port] = int(host_port)
                    else:
                        ports[port_mapping] = None
                container_config['ports'] = ports

            # Add volume mappings if specified
            if request.volumes:
                volumes = {}
                for volume_mapping in request.volumes:
                    if ':' in volume_mapping:
                        host_path, container_path = volume_mapping.split(':', 1)
                        volumes[host_path] = {'bind': container_path, 'mode': 'rw'}
                    else:
                        volumes[volume_mapping] = {'bind': volume_mapping, 'mode': 'rw'}
                container_config['volumes'] = volumes

            # Add environment variables if specified
            if request.environment:
                container_config['environment'] = list(request.environment)

            # Create and start the container
            docker_container = self.docker_client.containers.run(**container_config)

            # Save to database
            container = Container(
                id=docker_container.id,
                name=docker_container.name,
                image=docker_container.image.tags[0] if docker_container.image.tags else docker_container.image.id,
                host_id=self.host_id,
                status=docker_container.status,
                created_at=datetime.now(UTC),
                launched_by_agent_id=request.launched_by_agent_id if request.launched_by_agent_id else None
            )
            container.set_labels(docker_container.labels)
            container.set_ports(list(request.ports))
            container.set_volumes(list(request.volumes))
            container.set_environment(list(request.environment))

            self.db.add_container(container)

            logger.info(f"Successfully created container: {docker_container.name}")
            return anvyl_pb2.AddContainerResponse(  # type: ignore
                container=self._container_to_proto(container),
                success=True,
                error_message=""
            )

        except Exception as e:
            logger.error(f"Error creating container: {e}")
            return anvyl_pb2.AddContainerResponse(  # type: ignore
                container=None,
                success=False,
                error_message=str(e)
            )

    def StopContainer(self, request, context):
        """Stop a container."""
        logger.info(f"StopContainer called: {request.container_id}")

        if not self.docker_client:
            return anvyl_pb2.StopContainerResponse(  # type: ignore
                success=False,
                error_message="Docker client not available"
            )

        try:
            container = self.docker_client.containers.get(request.container_id)
            container.stop(timeout=request.timeout if request.timeout > 0 else 10)

            # Update database
            db_container = self.db.get_container(request.container_id)
            if db_container:
                db_container.status = "stopped"
                db_container.stopped_at = datetime.now(UTC)
                self.db.update_container(db_container)

            logger.info(f"Successfully stopped container: {request.container_id}")
            return anvyl_pb2.StopContainerResponse(  # type: ignore
                success=True,
                error_message=""
            )

        except Exception as e:
            logger.error(f"Error stopping container: {e}")
            return anvyl_pb2.StopContainerResponse(  # type: ignore
                success=False,
                error_message=str(e)
            )

    def GetLogs(self, request, context):
        """Get container logs."""
        logger.info(f"GetLogs called: {request.container_id}")

        if not self.docker_client:
            return anvyl_pb2.GetLogsResponse(  # type: ignore
                logs="",
                success=False,
                error_message="Docker client not available"
            )

        try:
            container = self.docker_client.containers.get(request.container_id)
            logs = container.logs(
                follow=request.follow,
                tail=request.tail if request.tail > 0 else "all"
            )

            if isinstance(logs, bytes):
                logs = logs.decode('utf-8')

            return anvyl_pb2.GetLogsResponse(  # type: ignore
                logs=logs,
                success=True,
                error_message=""
            )

        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return anvyl_pb2.GetLogsResponse(  # type: ignore
                logs="",
                success=False,
                error_message=str(e)
            )

    def StreamLogs(self, request, context):
        """Stream container logs (streaming RPC)."""
        logger.info(f"StreamLogs called: {request.container_id}")

        if not self.docker_client:
            yield anvyl_pb2.StreamLogsResponse(  # type: ignore
                log_line="",
                timestamp="",
                success=False,
                error_message="Docker client not available"
            )
            return

        try:
            container = self.docker_client.containers.get(request.container_id)
            for log_line in container.logs(stream=True, follow=request.follow):
                if isinstance(log_line, bytes):
                    log_line = log_line.decode('utf-8').strip()

                yield anvyl_pb2.StreamLogsResponse(  # type: ignore
                    log_line=log_line,
                    timestamp=datetime.now(UTC).isoformat(),
                    success=True,
                    error_message=""
                )

        except Exception as e:
            logger.error(f"Error streaming logs: {e}")
            yield anvyl_pb2.StreamLogsResponse(  # type: ignore
                log_line="",
                timestamp="",
                success=False,
                error_message=str(e)
            )

    def ExecCommand(self, request, context):
        """Execute command in container."""
        logger.info(f"ExecCommand called: {request.container_id}")

        if not self.docker_client:
            return anvyl_pb2.ExecCommandResponse(  # type: ignore
                output="",
                exit_code=1,
                success=False,
                error_message="Docker client not available"
            )

        try:
            container = self.docker_client.containers.get(request.container_id)
            result = container.exec_run(
                cmd=list(request.command),
                tty=request.tty
            )

            output = result.output.decode('utf-8') if isinstance(result.output, bytes) else result.output

            return anvyl_pb2.ExecCommandResponse(  # type: ignore
                output=output,
                exit_code=result.exit_code,
                success=True,
                error_message=""
            )

        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return anvyl_pb2.ExecCommandResponse(  # type: ignore
                output="",
                exit_code=1,
                success=False,
                error_message=str(e)
            )

    # Agent management methods
    def ListAgents(self, request, context):
        """List agents."""
        logger.info("ListAgents called")

        try:
            agents = self.db.list_agents(request.host_id if request.host_id else None)
            proto_agents = [self._agent_to_proto(agent) for agent in agents]
            return anvyl_pb2.ListAgentsResponse(agents=proto_agents)  # type: ignore

        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            return anvyl_pb2.ListAgentsResponse(agents=[])  # type: ignore

    def LaunchAgent(self, request, context):
        """Launch a Python agent in a container."""
        logger.info(f"LaunchAgent called: {request.name} on {request.host_id}")

        try:
            agent_id = str(uuid.uuid4())

            # Create agent record
            agent = Agent(
                id=agent_id,
                name=request.name,
                host_id=request.host_id,
                entrypoint=request.entrypoint,
                working_directory=request.working_directory,
                persistent=request.persistent,
                status="starting"
            )
            agent.set_env(list(request.env))
            agent.set_arguments(list(request.arguments))

            # Always launch agent in container
            return self._launch_agent_in_container(agent, request, context)

        except Exception as e:
            logger.error(f"Error launching agent: {e}")
            return anvyl_pb2.LaunchAgentResponse(  # type: ignore
                agent=None,
                success=False,
                error_message=str(e)
            )

    def _launch_agent_in_container(self, agent: Agent, request, context):
        """Launch agent in a Docker container."""
        if not self.docker_client:
            return anvyl_pb2.LaunchAgentResponse(  # type: ignore
                agent=None,
                success=False,
                error_message="Docker client not available"
            )

        try:
            # Create container for agent
            container_config = {
                'image': 'python:3.12-alpine',  # Default Python image
                'name': f"agent-{agent.name}-{agent.id[:8]}",
                'command': ['python', '-c', f'exec(open("{request.entrypoint}").read())'],
                'environment': list(request.env),
                'working_dir': request.working_directory or '/app',
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
            return anvyl_pb2.LaunchAgentResponse(  # type: ignore
                agent=self._agent_to_proto(agent),
                success=True,
                error_message=""
            )

        except Exception as e:
            logger.error(f"Error launching agent in container: {e}")
            return anvyl_pb2.LaunchAgentResponse(  # type: ignore
                agent=None,
                success=False,
                error_message=str(e)
            )

    def StopAgent(self, request, context):
        """Stop an agent."""
        logger.info(f"StopAgent called: {request.agent_id}")

        try:
            agent = self.db.get_agent(request.agent_id)
            if not agent:
                return anvyl_pb2.StopAgentResponse(  # type: ignore
                    success=False,
                    error_message="Agent not found"
                )

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

            return anvyl_pb2.StopAgentResponse(  # type: ignore
                success=True,
                error_message=""
            )

        except Exception as e:
            logger.error(f"Error stopping agent: {e}")
            return anvyl_pb2.StopAgentResponse(  # type: ignore
                success=False,
                error_message=str(e)
            )

    def GetAgentStatus(self, request, context):
        """Get agent status."""
        logger.info(f"GetAgentStatus called: {request.agent_id}")

        try:
            agent = self.db.get_agent(request.agent_id)
            if not agent:
                return anvyl_pb2.GetAgentStatusResponse(  # type: ignore
                    agent=None,
                    success=False,
                    error_message="Agent not found"
                )

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

            return anvyl_pb2.GetAgentStatusResponse(  # type: ignore
                agent=self._agent_to_proto(agent),
                success=True,
                error_message=""
            )

        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return anvyl_pb2.GetAgentStatusResponse(  # type: ignore
                agent=None,
                success=False,
                error_message=str(e)
            )

    def ExecuteAgentInstruction(self, request, context):
        """Execute an instruction on an AI agent."""
        logger.info(f"ExecuteAgentInstruction called: {request.agent_name}")

        try:
            # Import agent manager here to avoid circular imports
            from .agent_manager import get_agent_manager

            manager = get_agent_manager()

            # Check if agent exists and is running
            config = manager.get_agent_config(request.agent_name)
            if not config:
                return anvyl_pb2.ExecuteAgentInstructionResponse(  # type: ignore
                    result="",
                    success=False,
                    error_message=f"Agent '{request.agent_name}' not found"
                )

            status_info = manager.get_agent_status(request.agent_name)
            if not status_info or not status_info.get("running", False):
                return anvyl_pb2.ExecuteAgentInstructionResponse(  # type: ignore
                    result="",
                    success=False,
                    error_message=f"Agent '{request.agent_name}' is not running"
                )

            # For containerized agents, we need to execute the instruction in the container
            if config.container_id:
                # Execute the instruction in the agent container using Docker SDK
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
result = agent.act("{request.instruction}")
print(result)
'''

                    # Execute the command in the container
                    exec_result = container.exec_run(
                        cmd=['python', '-c', python_code],
                        timeout=300  # 5 minute timeout
                    )

                    if exec_result.exit_code == 0:
                        return anvyl_pb2.ExecuteAgentInstructionResponse(  # type: ignore
                            result=exec_result.output.decode('utf-8').strip(),
                            success=True,
                            error_message=""
                        )
                    else:
                        return anvyl_pb2.ExecuteAgentInstructionResponse(  # type: ignore
                            result="",
                            success=False,
                            error_message=f"Failed to execute instruction: {exec_result.output.decode('utf-8')}"
                        )

                except Exception as e:
                    return anvyl_pb2.ExecuteAgentInstructionResponse(  # type: ignore
                        result="",
                        success=False,
                        error_message=f"Error executing instruction in container: {e}"
                    )
            else:
                return anvyl_pb2.ExecuteAgentInstructionResponse(  # type: ignore
                    result="",
                    success=False,
                    error_message="Non-containerized agents not supported for instruction execution"
                )

        except subprocess.TimeoutExpired:
            return anvyl_pb2.ExecuteAgentInstructionResponse(  # type: ignore
                result="",
                success=False,
                error_message="Instruction execution timed out"
            )
        except Exception as e:
            logger.error(f"Error executing agent instruction: {e}")
            return anvyl_pb2.ExecuteAgentInstructionResponse(  # type: ignore
                result="",
                success=False,
                error_message=str(e)
            )

    # Host-level execution methods
    def ExecCommandOnHost(self, request, context):
        """Execute command on host (Beszel agent functionality)."""
        logger.info(f"ExecCommandOnHost called: {request.host_id}")

        if request.host_id != self.host_id:
            return anvyl_pb2.ExecCommandOnHostResponse(  # type: ignore
                output="",
                stderr="",
                exit_code=1,
                success=False,
                error_message="Can only execute commands on local host"
            )

        try:
            # Prepare environment
            env = dict(request.env) if request.env else None

            # Execute command
            result = subprocess.run(
                list(request.command),
                cwd=request.working_directory or None,
                env=env,
                capture_output=True,
                text=True,
                timeout=request.timeout if request.timeout > 0 else None
            )

            return anvyl_pb2.ExecCommandOnHostResponse(  # type: ignore
                output=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                success=True,
                error_message=""
            )

        except subprocess.TimeoutExpired:
            return anvyl_pb2.ExecCommandOnHostResponse(  # type: ignore
                output="",
                stderr="",
                exit_code=124,  # Standard timeout exit code
                success=False,
                error_message="Command timed out"
            )
        except Exception as e:
            logger.error(f"Error executing command on host: {e}")
            return anvyl_pb2.ExecCommandOnHostResponse(  # type: ignore
                output="",
                stderr="",
                exit_code=1,
                success=False,
                error_message=str(e)
            )

def serve():
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    anvyl_pb2_grpc.add_AnvylServiceServicer_to_server(AnvylService(), server)

    # Listen on all interfaces for remote connections
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)

    logger.info(f"Starting Anvyl gRPC server on {listen_addr}")
    server.start()

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.stop(0)

if __name__ == '__main__':
    serve()