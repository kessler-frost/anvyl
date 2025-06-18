#!/usr/bin/env python3
"""
Anvyl gRPC Server
A self-hosted infrastructure orchestrator for Apple Silicon systems.
"""

import grpc
import docker
import uuid
import logging
from datetime import datetime
from concurrent import futures
from typing import Dict, List

# Import generated gRPC code
import generated.anvyl_pb2 as anvyl_pb2
import generated.anvyl_pb2_grpc as anvyl_pb2_grpc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnvylService(anvyl_pb2_grpc.AnvylServiceServicer):
    """gRPC service implementation for Anvyl infrastructure orchestrator."""

    def __init__(self):
        """Initialize the service with Docker client."""
        self.docker_client = None
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

        # In-memory storage for hosts (will be replaced with SQLite)
        self.hosts: Dict[str, anvyl_pb2.Host] = {}
        self.host_id = str(uuid.uuid4())

        # Register this host
        self._register_local_host()

    def _register_local_host(self):
        """Register the local host in the system."""
        import socket
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except:
            hostname = "localhost"
            local_ip = "127.0.0.1"

        host = anvyl_pb2.Host(
            id=self.host_id,
            name=hostname,
            ip=local_ip,
            agents_installed=True
        )
        self.hosts[self.host_id] = host
        logger.info(f"Registered local host: {hostname} ({local_ip})")

    def ListHosts(self, request, context):
        """List all registered hosts."""
        logger.info("ListHosts called")
        return anvyl_pb2.ListHostsResponse(hosts=list(self.hosts.values()))

    def AddHost(self, request, context):
        """Add a new host to the system."""
        logger.info(f"AddHost called: {request.name} ({request.ip})")

        host_id = str(uuid.uuid4())
        host = anvyl_pb2.Host(
            id=host_id,
            name=request.name,
            ip=request.ip,
            agents_installed=False  # Will be set to True when agent connects
        )

        self.hosts[host_id] = host

        return anvyl_pb2.AddHostResponse(
            host=host,
            success=True,
            error_message=""
        )

    def ListContainers(self, request, context):
        """List containers using Docker SDK."""
        logger.info("ListContainers called")

        if not self.docker_client:
            return anvyl_pb2.ListContainersResponse(containers=[])

        try:
            containers = []
            for container in self.docker_client.containers.list(all=True):
                # Convert Docker container to our proto format
                proto_container = anvyl_pb2.Container(
                    id=container.id,
                    name=container.name,
                    image=container.image.tags[0] if container.image.tags else container.image.id,
                    host_id=self.host_id,
                    status=container.status,
                    created_at=datetime.fromtimestamp(container.attrs['Created']).isoformat(),
                    labels=container.labels
                )
                containers.append(proto_container)

            logger.info(f"Found {len(containers)} containers")
            return anvyl_pb2.ListContainersResponse(containers=containers)

        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return anvyl_pb2.ListContainersResponse(containers=[])

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

            # Create and start the container
            container = self.docker_client.containers.run(**container_config)

            # Convert to proto format
            proto_container = anvyl_pb2.Container(
                id=container.id,
                name=container.name,
                image=container.image.tags[0] if container.image.tags else container.image.id,
                host_id=self.host_id,
                status=container.status,
                created_at=datetime.fromtimestamp(container.attrs['Created']).isoformat(),
                labels=container.labels
            )

            logger.info(f"Successfully created container: {container.name}")
            return anvyl_pb2.AddContainerResponse(
                container=proto_container,
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
        """Stop a container (stub implementation)."""
        logger.info(f"StopContainer called: {request.container_id}")
        return anvyl_pb2.StopContainerResponse(
            success=False,
            error_message="Not implemented yet"
        )

    def GetLogs(self, request, context):
        """Get container logs (stub implementation)."""
        logger.info(f"GetLogs called: {request.container_id}")
        return anvyl_pb2.GetLogsResponse(
            logs="",
            success=False,
            error_message="Not implemented yet"
        )

    def ExecCommand(self, request, context):
        """Execute command in container (stub implementation)."""
        logger.info(f"ExecCommand called: {request.container_id}")
        return anvyl_pb2.ExecCommandResponse(
            output="",
            exit_code=1,
            success=False,
            error_message="Not implemented yet"
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