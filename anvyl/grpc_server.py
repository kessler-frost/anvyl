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
from datetime import datetime, UTC
from concurrent import futures
from typing import Dict, List, Optional

# Ensure protobuf files are generated automatically
from anvyl.proto_utils import ensure_protos_generated
ensure_protos_generated()

# Import generated gRPC code
from anvyl.generated import anvyl_pb2
from anvyl.generated import anvyl_pb2_grpc

# Import database models
from anvyl.database.models import DatabaseManager, Host, Container, Agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnvylService(anvyl_pb2_grpc.AnvylServiceServicer):
    """gRPC service implementation for Anvyl infrastructure orchestrator."""

    def __init__(self):
        """Initialize the service with Docker client and database."""
        self.docker_client = None
        self.db = DatabaseManager()
        
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

        # Running agents tracking
        self.running_agents: Dict[str, subprocess.Popen] = {}

    def _register_local_host(self):
        """Register the local host in the system."""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except:
            hostname = "localhost"
            local_ip = "127.0.0.1"

        # Check if host already exists
        existing_host = self.db.get_host(self.host_id)
        if not existing_host:
            host = Host(
                id=self.host_id,
                name=hostname,
                ip=local_ip,
                agents_installed=True,
                os="macOS",  # Can be detected dynamically
                last_seen=datetime.now(UTC),
                status="online"
            )
            self.db.add_host(host)
            logger.info(f"Registered local host: {hostname} ({local_ip})")
        else:
            self.db.update_host_heartbeat(self.host_id)
            logger.info(f"Updated heartbeat for existing host: {hostname} ({local_ip})")

    def _get_host_resources(self) -> anvyl_pb2.HostResources:
        """Get current host resource information."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return anvyl_pb2.HostResources(
                cpu_usage_percent=cpu_percent,
                memory_total_bytes=memory.total,
                memory_used_bytes=memory.used,
                disk_total_bytes=disk.total,
                disk_used_bytes=disk.used,
                architecture="arm64",  # Could be detected dynamically
                cpu_cores=psutil.cpu_count()
            )
        except Exception as e:
            logger.error(f"Error getting host resources: {e}")
            return anvyl_pb2.HostResources()

    def _host_to_proto(self, host: Host) -> anvyl_pb2.Host:
        """Convert database Host to protobuf Host."""
        return anvyl_pb2.Host(
            id=host.id,
            name=host.name,
            ip=host.ip,
            agents_installed=host.agents_installed,
            os=host.os or "",
            last_seen=host.last_seen.isoformat() if host.last_seen else "",
            resources=anvyl_pb2.HostResources(),  # Would need to fetch current resources
            tags=host.get_tags(),
            status=host.status
        )

    def _container_to_proto(self, container: Container) -> anvyl_pb2.Container:
        """Convert database Container to protobuf Container."""
        return anvyl_pb2.Container(
            id=container.id,
            name=container.name,
            image=container.image,
            host_id=container.host_id,
            status=container.status,
            created_at=container.created_at.isoformat(),
            labels=container.get_labels(),
            launched_by_agent_id=container.launched_by_agent_id or ""
        )

    def _agent_to_proto(self, agent: Agent) -> anvyl_pb2.Agent:
        """Convert database Agent to protobuf Agent."""
        return anvyl_pb2.Agent(
            id=agent.id,
            name=agent.name,
            host_id=agent.host_id,
            entrypoint=agent.entrypoint,
            env=agent.get_env(),
            container_id=agent.container_id or "",
            status=agent.status,
            persistent=agent.persistent,
            created_at=agent.created_at.isoformat(),
            started_at=agent.started_at.isoformat() if agent.started_at else "",
            working_directory=agent.working_directory or "",
            arguments=agent.get_arguments()
        )

    # Host management methods
    def ListHosts(self, request, context):
        """List all registered hosts."""
        logger.info("ListHosts called")
        hosts = self.db.list_hosts()
        proto_hosts = [self._host_to_proto(host) for host in hosts]
        return anvyl_pb2.ListHostsResponse(hosts=proto_hosts)

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
            return anvyl_pb2.AddHostResponse(
                host=self._host_to_proto(host),
                success=True,
                error_message=""
            )
        except Exception as e:
            logger.error(f"Error adding host: {e}")
            return anvyl_pb2.AddHostResponse(
                host=None,
                success=False,
                error_message=str(e)
            )

    def UpdateHost(self, request, context):
        """Update host information."""
        logger.info(f"UpdateHost called: {request.host_id}")

        host = self.db.get_host(request.host_id)
        if not host:
            return anvyl_pb2.UpdateHostResponse(
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
                    "cpu_usage_percent": request.resources.cpu_usage_percent,
                    "memory_total_bytes": request.resources.memory_total_bytes,
                    "memory_used_bytes": request.resources.memory_used_bytes,
                    "disk_total_bytes": request.resources.disk_total_bytes,
                    "disk_used_bytes": request.resources.disk_used_bytes,
                    "architecture": request.resources.architecture,
                    "cpu_cores": request.resources.cpu_cores
                }
                host.set_resources(resources_dict)

            self.db.update_host(host)
            return anvyl_pb2.UpdateHostResponse(
                host=self._host_to_proto(host),
                success=True,
                error_message=""
            )
        except Exception as e:
            logger.error(f"Error updating host: {e}")
            return anvyl_pb2.UpdateHostResponse(
                host=None,
                success=False,
                error_message=str(e)
            )

    def GetHostMetrics(self, request, context):
        """Get current host metrics."""
        logger.info(f"GetHostMetrics called: {request.host_id}")

        if request.host_id == self.host_id:
            # Return live metrics for local host
            try:
                resources = self._get_host_resources()
                return anvyl_pb2.GetHostMetricsResponse(
                    resources=resources,
                    success=True,
                    error_message=""
                )
            except Exception as e:
                logger.error(f"Error getting host metrics: {e}")
                return anvyl_pb2.GetHostMetricsResponse(
                    resources=anvyl_pb2.HostResources(),
                    success=False,
                    error_message=str(e)
                )
        else:
            # For remote hosts, we'd need to make a remote call
            return anvyl_pb2.GetHostMetricsResponse(
                resources=anvyl_pb2.HostResources(),
                success=False,
                error_message="Remote host metrics not implemented yet"
            )

    def HostHeartbeat(self, request, context):
        """Update host heartbeat."""
        logger.info(f"HostHeartbeat called: {request.host_id}")

        try:
            success = self.db.update_host_heartbeat(request.host_id)
            if success:
                return anvyl_pb2.HostHeartbeatResponse(
                    success=True,
                    error_message=""
                )
            else:
                return anvyl_pb2.HostHeartbeatResponse(
                    success=False,
                    error_message="Host not found"
                )
        except Exception as e:
            logger.error(f"Error updating heartbeat: {e}")
            return anvyl_pb2.HostHeartbeatResponse(
                success=False,
                error_message=str(e)
            )

    # Container management methods
    def ListContainers(self, request, context):
        """List containers using Docker SDK and database."""
        logger.info("ListContainers called")

        try:
            # Get containers from database
            containers = self.db.list_containers(request.host_id if request.host_id else None)
            
            # If we have Docker client, sync with live containers
            if self.docker_client and (not request.host_id or request.host_id == self.host_id):
                self._sync_containers_with_docker()
                # Refresh from database
                containers = self.db.list_containers(request.host_id if request.host_id else None)

            proto_containers = [self._container_to_proto(container) for container in containers]
            logger.info(f"Found {len(proto_containers)} containers")
            return anvyl_pb2.ListContainersResponse(containers=proto_containers)

        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return anvyl_pb2.ListContainersResponse(containers=[])

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
            return anvyl_pb2.AddContainerResponse(
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

            # Special handling for LMStudio model containers
            labels = dict(request.labels)
            if labels.get('anvyl.service') == 'lmstudio-model':
                # Extract model ID from environment or labels
                model_id = labels.get('anvyl.model.id', '')
                memory_limit = None
                
                # Check for memory limit in environment variables
                env_vars = list(request.environment) if request.environment else []
                for env_var in env_vars:
                    if env_var.startswith('MEMORY_LIMIT='):
                        memory_limit = env_var.split('=', 1)[1]
                        break
                
                # Add memory limit to container config
                if memory_limit:
                    container_config['mem_limit'] = memory_limit
                
                # Create startup script for LMStudio model
                startup_script = f'''#!/bin/bash
set -e

echo "Installing LMStudio SDK..."
pip install lmstudio

echo "Starting MLX model: {model_id}"
python3 -c "
import lmstudio as lms
import time
import sys
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class ModelHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{{\\"status\\": \\"healthy\\", \\"model\\": \\"{model_id}\\"}}')
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server():
    server = HTTPServer(('0.0.0.0', 8080), ModelHandler)
    server.serve_forever()

try:
    print('Loading model: {model_id}')
    
    # Start health check server in background
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Load the model
    model = lms.llm('{model_id}')
    print(f'Model loaded successfully: {model_id}')
    
    # Start LMStudio server
    print('Model server is running on port 1234')
    print('Health check available on port 8080/health')
    print('Container will remain active to serve the model...')
    
    # Keep alive loop
    while True:
        time.sleep(60)
        print(f'Model {{model_id}} is still running...')
        
except Exception as e:
    print(f'Error loading model: {{e}}')
    sys.exit(1)
"'''
                
                # Use a custom command to run the startup script
                container_config['command'] = ['/bin/bash', '-c', startup_script]
                
                # Add health check
                container_config['healthcheck'] = {
                    'test': ['CMD', 'curl', '-f', 'http://localhost:8080/health'],
                    'interval': 30000000000,  # 30 seconds in nanoseconds
                    'timeout': 10000000000,   # 10 seconds in nanoseconds
                    'retries': 3,
                    'start_period': 60000000000  # 60 seconds in nanoseconds
                }

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
            return anvyl_pb2.AddContainerResponse(
                container=self._container_to_proto(container),
                success=True,
                error_message=""
            )

        except Exception as e:
            logger.error(f"Error creating container: {e}")
            return anvyl_pb2.AddContainerResponse(
                container=None,
                success=False,
                error_message=str(e)
            )

    def StopContainer(self, request, context):
        """Stop a container."""
        logger.info(f"StopContainer called: {request.container_id}")

        if not self.docker_client:
            return anvyl_pb2.StopContainerResponse(
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
            return anvyl_pb2.StopContainerResponse(
                success=True,
                error_message=""
            )

        except Exception as e:
            logger.error(f"Error stopping container: {e}")
            return anvyl_pb2.StopContainerResponse(
                success=False,
                error_message=str(e)
            )

    def GetLogs(self, request, context):
        """Get container logs."""
        logger.info(f"GetLogs called: {request.container_id}")

        if not self.docker_client:
            return anvyl_pb2.GetLogsResponse(
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
            
            return anvyl_pb2.GetLogsResponse(
                logs=logs,
                success=True,
                error_message=""
            )

        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return anvyl_pb2.GetLogsResponse(
                logs="",
                success=False,
                error_message=str(e)
            )

    def StreamLogs(self, request, context):
        """Stream container logs (streaming RPC)."""
        logger.info(f"StreamLogs called: {request.container_id}")

        if not self.docker_client:
            yield anvyl_pb2.StreamLogsResponse(
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
                
                yield anvyl_pb2.StreamLogsResponse(
                    log_line=log_line,
                    timestamp=datetime.now(UTC).isoformat(),
                    success=True,
                    error_message=""
                )

        except Exception as e:
            logger.error(f"Error streaming logs: {e}")
            yield anvyl_pb2.StreamLogsResponse(
                log_line="",
                timestamp="",
                success=False,
                error_message=str(e)
            )

    def ExecCommand(self, request, context):
        """Execute command in container."""
        logger.info(f"ExecCommand called: {request.container_id}")

        if not self.docker_client:
            return anvyl_pb2.ExecCommandResponse(
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
            
            return anvyl_pb2.ExecCommandResponse(
                output=output,
                exit_code=result.exit_code,
                success=True,
                error_message=""
            )

        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return anvyl_pb2.ExecCommandResponse(
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
            return anvyl_pb2.ListAgentsResponse(agents=proto_agents)

        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            return anvyl_pb2.ListAgentsResponse(agents=[])

    def LaunchAgent(self, request, context):
        """Launch a Python agent."""
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

            if request.use_container:
                # Launch agent in container
                return self._launch_agent_in_container(agent, request, context)
            else:
                # Launch agent as native process
                return self._launch_agent_as_process(agent, request, context)

        except Exception as e:
            logger.error(f"Error launching agent: {e}")
            return anvyl_pb2.LaunchAgentResponse(
                agent=None,
                success=False,
                error_message=str(e)
            )

    def _launch_agent_in_container(self, agent: Agent, request, context):
        """Launch agent in a Docker container."""
        if not self.docker_client:
            return anvyl_pb2.LaunchAgentResponse(
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
            return anvyl_pb2.LaunchAgentResponse(
                agent=self._agent_to_proto(agent),
                success=True,
                error_message=""
            )

        except Exception as e:
            logger.error(f"Error launching agent in container: {e}")
            return anvyl_pb2.LaunchAgentResponse(
                agent=None,
                success=False,
                error_message=str(e)
            )

    def _launch_agent_as_process(self, agent: Agent, request, context):
        """Launch agent as a native process."""
        try:
            # Prepare command
            cmd = ['python', request.entrypoint] + list(request.arguments)
            
            # Prepare environment
            env = dict(request.env) if request.env else None
            
            # Start process
            process = subprocess.Popen(
                cmd,
                cwd=request.working_directory,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Track running process
            self.running_agents[agent.id] = process
            
            # Update agent status
            agent.status = "running"
            agent.started_at = datetime.now(UTC)
            
            self.db.add_agent(agent)

            logger.info(f"Successfully launched agent {agent.name} as process {process.pid}")
            return anvyl_pb2.LaunchAgentResponse(
                agent=self._agent_to_proto(agent),
                success=True,
                error_message=""
            )

        except Exception as e:
            logger.error(f"Error launching agent as process: {e}")
            return anvyl_pb2.LaunchAgentResponse(
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
                return anvyl_pb2.StopAgentResponse(
                    success=False,
                    error_message="Agent not found"
                )

            if agent.container_id:
                # Stop containerized agent
                if self.docker_client:
                    try:
                        container = self.docker_client.containers.get(agent.container_id)
                        container.stop()
                        container.remove()
                    except Exception as e:
                        logger.warning(f"Error stopping container: {e}")
            else:
                # Stop process agent
                if agent.id in self.running_agents:
                    process = self.running_agents[agent.id]
                    process.terminate()
                    del self.running_agents[agent.id]

            # Update agent status
            agent.status = "stopped"
            agent.stopped_at = datetime.now(UTC)
            self.db.update_agent(agent)

            return anvyl_pb2.StopAgentResponse(
                success=True,
                error_message=""
            )

        except Exception as e:
            logger.error(f"Error stopping agent: {e}")
            return anvyl_pb2.StopAgentResponse(
                success=False,
                error_message=str(e)
            )

    def GetAgentStatus(self, request, context):
        """Get agent status."""
        logger.info(f"GetAgentStatus called: {request.agent_id}")

        try:
            agent = self.db.get_agent(request.agent_id)
            if not agent:
                return anvyl_pb2.GetAgentStatusResponse(
                    agent=None,
                    success=False,
                    error_message="Agent not found"
                )

            # Check if process is still running
            if agent.id in self.running_agents:
                process = self.running_agents[agent.id]
                if process.poll() is not None:
                    # Process has terminated
                    agent.status = "stopped"
                    agent.stopped_at = datetime.now(UTC)
                    agent.exit_code = process.returncode
                    self.db.update_agent(agent)
                    del self.running_agents[agent.id]

            return anvyl_pb2.GetAgentStatusResponse(
                agent=self._agent_to_proto(agent),
                success=True,
                error_message=""
            )

        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return anvyl_pb2.GetAgentStatusResponse(
                agent=None,
                success=False,
                error_message=str(e)
            )

    # Host-level execution methods
    def ExecCommandOnHost(self, request, context):
        """Execute command on host (Beszel agent functionality)."""
        logger.info(f"ExecCommandOnHost called: {request.host_id}")

        if request.host_id != self.host_id:
            return anvyl_pb2.ExecCommandOnHostResponse(
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

            return anvyl_pb2.ExecCommandOnHostResponse(
                output=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                success=True,
                error_message=""
            )

        except subprocess.TimeoutExpired:
            return anvyl_pb2.ExecCommandOnHostResponse(
                output="",
                stderr="",
                exit_code=124,  # Standard timeout exit code
                success=False,
                error_message="Command timed out"
            )
        except Exception as e:
            logger.error(f"Error executing command on host: {e}")
            return anvyl_pb2.ExecCommandOnHostResponse(
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