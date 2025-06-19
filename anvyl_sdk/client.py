"""
Anvyl SDK Client
gRPC client for Anvyl infrastructure orchestrator
"""

import grpc
import logging
from typing import List, Dict, Optional, Iterator, Any

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

    # Host management methods
    def list_hosts(self) -> List[Any]:
        """List all registered hosts."""
        try:
            response = self.stub.ListHosts(anvyl_pb2.ListHostsRequest())
            return list(response.hosts)
        except Exception as e:
            logger.error(f"Error listing hosts: {e}")
            return []

    def add_host(self, name: str, ip: str, os: str = "", tags: Optional[List[str]] = None) -> Optional[Any]:
        """Add a new host to the system."""
        try:
            request = anvyl_pb2.AddHostRequest(
                name=name, 
                ip=ip,
                os=os,
                tags=tags or []
            )
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

    def update_host(self, host_id: str, resources: Optional[Any] = None, 
                   status: str = "", tags: Optional[List[str]] = None) -> Optional[Any]:
        """Update host information."""
        try:
            request = anvyl_pb2.UpdateHostRequest(
                host_id=host_id,
                status=status,
                tags=tags or []
            )
            if resources:
                request.resources.CopyFrom(resources)

            response = self.stub.UpdateHost(request)

            if response.success:
                logger.info(f"Successfully updated host: {host_id}")
                return response.host
            else:
                logger.error(f"Failed to update host: {response.error_message}")
                return None

        except Exception as e:
            logger.error(f"Error updating host: {e}")
            return None

    def get_host_metrics(self, host_id: str) -> Optional[Any]:
        """Get current host metrics."""
        try:
            request = anvyl_pb2.GetHostMetricsRequest(host_id=host_id)
            response = self.stub.GetHostMetrics(request)

            if response.success:
                return response.resources
            else:
                logger.error(f"Failed to get host metrics: {response.error_message}")
                return None

        except Exception as e:
            logger.error(f"Error getting host metrics: {e}")
            return None

    def host_heartbeat(self, host_id: str) -> bool:
        """Update host heartbeat."""
        try:
            request = anvyl_pb2.HostHeartbeatRequest(host_id=host_id)
            response = self.stub.HostHeartbeat(request)

            if response.success:
                logger.info(f"Successfully updated heartbeat for host: {host_id}")
                return True
            else:
                logger.error(f"Failed to update heartbeat: {response.error_message}")
                return False

        except Exception as e:
            logger.error(f"Error updating heartbeat: {e}")
            return False

    # Container management methods
    def list_containers(self, host_id: Optional[str] = None) -> List[Any]:
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
                     environment: Optional[List[str]] = None,
                     launched_by_agent_id: Optional[str] = None) -> Optional[Any]:
        """Add a new container."""
        try:
            request = anvyl_pb2.AddContainerRequest(
                name=name,
                image=image,
                host_id=host_id or "",
                labels=labels or {},
                ports=ports or [],
                volumes=volumes or [],
                environment=environment or [],
                launched_by_agent_id=launched_by_agent_id or ""
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
        """Stop a container."""
        try:
            request = anvyl_pb2.StopContainerRequest(
                container_id=container_id,
                timeout=timeout
            )

            response = self.stub.StopContainer(request)
            
            if response.success:
                logger.info(f"Successfully stopped container: {container_id}")
                return True
            else:
                logger.error(f"Failed to stop container: {response.error_message}")
                return False

        except Exception as e:
            logger.error(f"Error stopping container: {e}")
            return False

    def get_logs(self, container_id: str, follow: bool = False, tail: int = 100) -> Optional[str]:
        """Get container logs."""
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

    def stream_logs(self, container_id: str, follow: bool = True) -> Iterator[Any]:
        """Stream container logs (streaming RPC)."""
        try:
            request = anvyl_pb2.StreamLogsRequest(
                container_id=container_id,
                follow=follow
            )

            for response in self.stub.StreamLogs(request):
                yield response

        except Exception as e:
            logger.error(f"Error streaming logs: {e}")
            # Yield error response
            yield anvyl_pb2.StreamLogsResponse(
                log_line="",
                timestamp="",
                success=False,
                error_message=str(e)
            )

    def exec_command(self, container_id: str, command: List[str], tty: bool = False) -> Optional[Any]:
        """Execute command in container."""
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

    # Agent management methods
    def list_agents(self, host_id: Optional[str] = None) -> List[Any]:
        """List agents, optionally filtered by host."""
        try:
            request = anvyl_pb2.ListAgentsRequest()
            if host_id:
                request.host_id = host_id

            response = self.stub.ListAgents(request)
            return list(response.agents)

        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            return []

    def launch_agent(self, 
                    name: str,
                    host_id: str,
                    entrypoint: str,
                    env: Optional[List[str]] = None,
                    use_container: bool = False,
                    working_directory: str = "",
                    arguments: Optional[List[str]] = None,
                    persistent: bool = False) -> Optional[Any]:
        """Launch a Python agent."""
        try:
            request = anvyl_pb2.LaunchAgentRequest(
                name=name,
                host_id=host_id,
                entrypoint=entrypoint,
                env=env or [],
                use_container=use_container,
                working_directory=working_directory,
                arguments=arguments or [],
                persistent=persistent
            )

            response = self.stub.LaunchAgent(request)

            if response.success:
                logger.info(f"Successfully launched agent: {name}")
                return response.agent
            else:
                logger.error(f"Failed to launch agent: {response.error_message}")
                return None

        except Exception as e:
            logger.error(f"Error launching agent: {e}")
            return None

    def stop_agent(self, agent_id: str) -> bool:
        """Stop an agent."""
        try:
            request = anvyl_pb2.StopAgentRequest(agent_id=agent_id)
            response = self.stub.StopAgent(request)

            if response.success:
                logger.info(f"Successfully stopped agent: {agent_id}")
                return True
            else:
                logger.error(f"Failed to stop agent: {response.error_message}")
                return False

        except Exception as e:
            logger.error(f"Error stopping agent: {e}")
            return False

    def get_agent_status(self, agent_id: str) -> Optional[Any]:
        """Get agent status."""
        try:
            request = anvyl_pb2.GetAgentStatusRequest(agent_id=agent_id)
            response = self.stub.GetAgentStatus(request)

            if response.success:
                return response.agent
            else:
                logger.error(f"Failed to get agent status: {response.error_message}")
                return None

        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return None

    # Host-level execution methods
    def exec_command_on_host(self, 
                           host_id: str,
                           command: List[str],
                           working_directory: str = "",
                           env: Optional[List[str]] = None,
                           timeout: int = 0) -> Optional[Any]:
        """Execute command on host (Beszel agent functionality)."""
        try:
            request = anvyl_pb2.ExecCommandOnHostRequest(
                host_id=host_id,
                command=command,
                working_directory=working_directory,
                env=env or [],
                timeout=timeout
            )

            response = self.stub.ExecCommandOnHost(request)
            return response

        except Exception as e:
            logger.error(f"Error executing command on host: {e}")
            return None

# Convenience function for quick usage
def create_client(host: str = "localhost", port: int = 50051) -> AnvylClient:
    """Create and connect a client instance."""
    client = AnvylClient(host, port)
    if client.connect():
        return client
    else:
        raise ConnectionError(f"Failed to connect to Anvyl server at {host}:{port}")