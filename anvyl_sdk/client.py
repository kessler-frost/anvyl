"""
Anvyl SDK Client
gRPC client for Anvyl infrastructure orchestrator
"""

import grpc
import logging
from typing import List, Dict, Optional

# Import generated gRPC code
import generated.anvyl_pb2 as anvyl_pb2
import generated.anvyl_pb2_grpc as anvyl_pb2_grpc

logger = logging.getLogger(__name__)

class AnvylClient:
    """Client for Anvyl gRPC server."""

    def __init__(self, host: str = "localhost", port: int = 50051):
        """Initialize the client with connection details."""
        self.host = host
        self.port = port
        self.address = f"{host}:{port}"
        self.channel = None
        self.stub = None

    def connect(self) -> bool:
        """Establish connection to the gRPC server."""
        try:
            self.channel = grpc.insecure_channel(self.address)
            self.stub = anvyl_pb2_grpc.AnvylServiceStub(self.channel)

            # Test connection with a simple call
            self.stub.ListHosts(anvyl_pb2.ListHostsRequest())
            logger.info(f"Connected to Anvyl server at {self.address}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to {self.address}: {e}")
            return False

    def disconnect(self):
        """Close the connection."""
        if self.channel:
            self.channel.close()
            logger.info("Disconnected from Anvyl server")

    def list_hosts(self) -> List[anvyl_pb2.Host]:
        """List all registered hosts."""
        try:
            response = self.stub.ListHosts(anvyl_pb2.ListHostsRequest())
            return list(response.hosts)
        except Exception as e:
            logger.error(f"Error listing hosts: {e}")
            return []

    def add_host(self, name: str, ip: str) -> Optional[anvyl_pb2.Host]:
        """Add a new host to the system."""
        try:
            request = anvyl_pb2.AddHostRequest(name=name, ip=ip)
            response = self.stub.AddHost(request)

            if response.success:
                logger.info(f"Successfully added host: {name} ({ip})")
                return response.host
            else:
                logger.error(f"Failed to add host: {response.error_message}")
                return None

        except Exception as e:
            logger.error(f"Error adding host: {e}")
            return None

    def list_containers(self, host_id: Optional[str] = None) -> List[anvyl_pb2.Container]:
        """List containers, optionally filtered by host."""
        try:
            request = anvyl_pb2.ListContainersRequest()
            if host_id:
                request.host_id = host_id

            response = self.stub.ListContainers(request)
            return list(response.containers)

        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return []

    def add_container(self,
                     name: str,
                     image: str,
                     host_id: Optional[str] = None,
                     labels: Optional[Dict[str, str]] = None,
                     ports: Optional[List[str]] = None,
                     volumes: Optional[List[str]] = None,
                     environment: Optional[List[str]] = None) -> Optional[anvyl_pb2.Container]:
        """Add a new container."""
        try:
            request = anvyl_pb2.AddContainerRequest(
                name=name,
                image=image,
                host_id=host_id or "",
                labels=labels or {},
                ports=ports or [],
                volumes=volumes or [],
                environment=environment or []
            )

            response = self.stub.AddContainer(request)

            if response.success:
                logger.info(f"Successfully created container: {name} ({image})")
                return response.container
            else:
                logger.error(f"Failed to create container: {response.error_message}")
                return None

        except Exception as e:
            logger.error(f"Error creating container: {e}")
            return None

    def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a container (stub implementation)."""
        try:
            request = anvyl_pb2.StopContainerRequest(
                container_id=container_id,
                timeout=timeout
            )

            response = self.stub.StopContainer(request)
            return response.success

        except Exception as e:
            logger.error(f"Error stopping container: {e}")
            return False

    def get_logs(self, container_id: str, follow: bool = False, tail: int = 100) -> Optional[str]:
        """Get container logs (stub implementation)."""
        try:
            request = anvyl_pb2.GetLogsRequest(
                container_id=container_id,
                follow=follow,
                tail=tail
            )

            response = self.stub.GetLogs(request)

            if response.success:
                return response.logs
            else:
                logger.error(f"Failed to get logs: {response.error_message}")
                return None

        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return None

    def exec_command(self, container_id: str, command: List[str], tty: bool = False) -> Optional[anvyl_pb2.ExecCommandResponse]:
        """Execute command in container (stub implementation)."""
        try:
            request = anvyl_pb2.ExecCommandRequest(
                container_id=container_id,
                command=command,
                tty=tty
            )

            response = self.stub.ExecCommand(request)
            return response

        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return None

# Convenience function for quick usage
def create_client(host: str = "localhost", port: int = 50051) -> AnvylClient:
    """Create and connect a client instance."""
    client = AnvylClient(host, port)
    if client.connect():
        return client
    else:
        raise ConnectionError(f"Failed to connect to Anvyl server at {host}:{port}")