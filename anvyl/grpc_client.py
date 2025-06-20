"""
Anvyl gRPC Client
gRPC client for Anvyl infrastructure orchestrator
"""

import grpc
import logging
import docker
import os
import subprocess
from typing import List, Dict, Optional, Iterator, Any, Union

# Ensure protobuf files are generated automatically
from anvyl.proto_utils import ensure_protos_generated
ensure_protos_generated()

# Import generated gRPC code
from anvyl.generated import anvyl_pb2  # type: ignore
from anvyl.generated import anvyl_pb2_grpc  # type: ignore

logger = logging.getLogger(__name__)

class AnvylClient:
    """Client for Anvyl gRPC server."""

    def __init__(self, host: str = "localhost", port: int = 50051):
        """Initialize the client with connection details."""
        self.host = host
        self.port = port
        self.address = f"{host}:{port}"
        self.channel: Optional[grpc.Channel] = None
        self.stub: Optional[Any] = None  # type: ignore
        self._docker_client = None

    @property
    def docker_client(self):
        """Get or create Docker client."""
        if self._docker_client is None:
            try:
                self._docker_client = docker.from_env()
            except Exception as e:
                logger.error(f"Failed to connect to Docker: {e}")
                raise ConnectionError("Docker is not available. Please ensure Docker is running.")
        return self._docker_client

    def connect(self) -> bool:
        """Establish connection to the gRPC server."""
        try:
            self.channel = grpc.insecure_channel(self.address)
            self.stub = anvyl_pb2_grpc.AnvylServiceStub(self.channel)

            # Test connection with a simple call
            if self.stub:
                self.stub.ListHosts(anvyl_pb2.ListHostsRequest())  # type: ignore
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

    # Docker image building methods
    def build_image(self, path: str, tag: str, dockerfile: str = "Dockerfile", **kwargs) -> bool:
        """Build a Docker image."""
        try:
            logger.info(f"Building Docker image {tag} from {path}")

            # Build the image
            image, build_logs = self.docker_client.images.build(
                path=path,
                tag=tag,
                dockerfile=dockerfile,
                rm=True,
                **kwargs
            )

            # Log build output
            for log in build_logs:
                if isinstance(log, dict) and 'stream' in log and isinstance(log['stream'], str):
                    logger.debug(log['stream'].strip())

            logger.info(f"Successfully built image {tag}")
            return True

        except Exception as e:
            logger.error(f"Failed to build image {tag}: {e}")
            return False

    def build_ui_images(self, project_root: str) -> Dict[str, bool]:
        """Build all UI-related Docker images."""
        results = {}

        # Build UI backend image
        logger.info("Building Anvyl UI backend image...")
        results['anvyl-ui-backend'] = self.build_image(
            path=project_root,
            tag="anvyl/ui-backend:latest",
            dockerfile="ui/backend/Dockerfile"
        )

        # Build UI frontend image
        logger.info("Building Anvyl UI frontend image...")
        results['anvyl-ui-frontend'] = self.build_image(
            path=os.path.join(project_root, "ui", "frontend"),
            tag="anvyl/ui-frontend:latest",
            dockerfile="Dockerfile"
        )

        return results

    def deploy_ui_stack(self, project_root: str) -> bool:
        """Deploy the complete UI stack using docker-compose."""
        try:
            ui_dir = os.path.join(project_root, "ui")
            compose_file = os.path.join(ui_dir, "docker-compose.yml")

            if not os.path.exists(compose_file):
                logger.error(f"Docker compose file not found: {compose_file}")
                return False

            logger.info("Deploying Anvyl UI stack...")

            # First, check if gRPC server is already running
            import socket
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 50051))
                sock.close()
                if result == 0:
                    logger.info("gRPC server is already running on port 50051")
                else:
                    logger.info("Starting gRPC server with Python...")
                    # Start gRPC server in background
                    import subprocess
                    import sys
                    grpc_process = subprocess.Popen([
                        sys.executable, "-m", "anvyl.grpc_server"
                    ], cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    # Wait a moment for the server to start
                    import time
                    time.sleep(3)

                    # Check if server started successfully
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('localhost', 50051))
                    sock.close()
                    if result != 0:
                        logger.error("Failed to start gRPC server")
                        return False
                    logger.info("gRPC server started successfully")
            except Exception as e:
                logger.error(f"Error starting gRPC server: {e}")
                return False

            # Run docker-compose up for UI stack
            result = subprocess.run([
                "docker-compose", "-f", compose_file, "up", "-d"
            ], cwd=ui_dir, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Successfully deployed UI stack")
                logger.info("UI available at:")
                logger.info("  Frontend: http://localhost:3000")
                logger.info("  Backend API: http://localhost:8000")
                logger.info("  gRPC Server: localhost:50051")
                return True
            else:
                logger.error(f"Failed to deploy UI stack: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error deploying UI stack: {e}")
            return False

    def stop_ui_stack(self, project_root: str) -> bool:
        """Stop the UI stack containers and gRPC server."""
        try:
            import subprocess
            import psutil

            ui_dir = os.path.join(project_root, "ui")
            compose_file = os.path.join(ui_dir, "docker-compose.yml")

            logger.info("Stopping Anvyl UI stack...")

            # Stop UI containers
            result = subprocess.run([
                "docker-compose", "-f", compose_file, "down"
            ], cwd=ui_dir, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Failed to stop UI stack: {result.stderr}")
                return False

            logger.info("Successfully stopped UI stack")

            # Stop gRPC server process
            logger.info("Stopping gRPC server...")

            # Find and kill gRPC server processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and 'anvyl.grpc_server' in ' '.join(cmdline):
                        logger.info(f"Stopping gRPC server process (PID: {proc.info['pid']})")
                        proc.terminate()
                        proc.wait(timeout=5)
                        logger.info("gRPC server stopped successfully")
                        break
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    pass
            else:
                logger.info("No gRPC server process found")

            return True

        except Exception as e:
            logger.error(f"Error stopping UI stack: {e}")
            return False

    def get_ui_stack_status(self) -> Dict[str, Any]:
        """Get status of UI stack containers and gRPC server."""
        try:
            containers = self.docker_client.containers.list(
                filters={"label": "anvyl.component"}
            )

            status = {
                "containers": [],
                "services": {
                    "grpc-server": {"status": "stopped", "container": None, "process": None},
                    "ui-backend": {"status": "stopped", "container": None},
                    "ui-frontend": {"status": "stopped", "container": None}
                }
            }

            # Check gRPC server process
            import psutil
            import socket

            grpc_process_info = None
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and 'anvyl.grpc_server' in ' '.join(cmdline):
                        grpc_process_info = {
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "status": proc.status()
                        }
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Check if gRPC server is listening on port 50051
            grpc_listening = False
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 50051))
                sock.close()
                grpc_listening = (result == 0)
            except:
                pass

            if grpc_process_info and grpc_listening:
                status["services"]["grpc-server"]["status"] = "running"
                status["services"]["grpc-server"]["process"] = grpc_process_info
            else:
                status["services"]["grpc-server"]["status"] = "stopped"

            # Check Docker containers
            for container in containers:
                labels = container.labels
                service = labels.get("anvyl.service", "unknown")

                container_info = {
                    "id": container.id[:12],
                    "name": container.name,
                    "service": service,
                    "status": container.status,
                    "ports": container.ports,
                    "created": container.attrs["Created"]
                }
                status["containers"].append(container_info)

                # Update service status
                if service in ["ui-backend", "ui-frontend"]:
                    status["services"][service] = {
                        "status": container.status,
                        "container": container_info
                    }

            return status

        except Exception as e:
            logger.error(f"Error getting UI stack status: {e}")
            return {"error": str(e)}

    # Host management methods
    def list_hosts(self) -> List[Any]:
        """List all registered hosts."""
        try:
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return []
            response = self.stub.ListHosts(anvyl_pb2.ListHostsRequest())  # type: ignore
            return list(response.hosts)
        except Exception as e:
            logger.error(f"Error listing hosts: {e}")
            return []

    def add_host(self, name: str, ip: str, os: str = "", tags: Optional[List[str]] = None) -> Optional[Any]:
        """Add a new host to the system."""
        try:
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return None
            request = anvyl_pb2.AddHostRequest(  # type: ignore
                name=name,
                ip=ip,
                os=os,
                tags=tags or []
            )
            response = self.stub.AddHost(request)  # type: ignore

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
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return None
            request = anvyl_pb2.UpdateHostRequest(  # type: ignore
                host_id=host_id,
                status=status,
                tags=tags or []
            )
            if resources:
                request.resources.CopyFrom(resources)

            response = self.stub.UpdateHost(request)  # type: ignore

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
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return None
            request = anvyl_pb2.GetHostMetricsRequest(host_id=host_id)  # type: ignore
            response = self.stub.GetHostMetrics(request)  # type: ignore

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
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return False
            request = anvyl_pb2.HostHeartbeatRequest(host_id=host_id)  # type: ignore
            response = self.stub.HostHeartbeat(request)  # type: ignore

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
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return []
            request = anvyl_pb2.ListContainersRequest()  # type: ignore
            if host_id:
                request.host_id = host_id

            response = self.stub.ListContainers(request)  # type: ignore
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
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return None
            request = anvyl_pb2.AddContainerRequest(  # type: ignore
                name=name,
                image=image,
                host_id=host_id or "",
                labels=labels or {},
                ports=ports or [],
                volumes=volumes or [],
                environment=environment or [],
                launched_by_agent_id=launched_by_agent_id or ""
            )

            response = self.stub.AddContainer(request)  # type: ignore

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
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return False
            request = anvyl_pb2.StopContainerRequest(  # type: ignore
                container_id=container_id,
                timeout=timeout
            )

            response = self.stub.StopContainer(request)  # type: ignore

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
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return None
            request = anvyl_pb2.GetLogsRequest(  # type: ignore
                container_id=container_id,
                follow=follow,
                tail=tail
            )

            response = self.stub.GetLogs(request)  # type: ignore

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
            if not self.stub:
                logger.error("Not connected to gRPC server")
                yield anvyl_pb2.StreamLogsResponse(  # type: ignore
                    log_line="",
                    timestamp="",
                    success=False,
                    error_message="Not connected to gRPC server"
                )
                return
            request = anvyl_pb2.StreamLogsRequest(  # type: ignore
                container_id=container_id,
                follow=follow
            )

            for response in self.stub.StreamLogs(request):  # type: ignore
                yield response

        except Exception as e:
            logger.error(f"Error streaming logs: {e}")
            # Yield error response
            yield anvyl_pb2.StreamLogsResponse(  # type: ignore
                log_line="",
                timestamp="",
                success=False,
                error_message=str(e)
            )

    def exec_command(self, container_id: str, command: List[str], tty: bool = False) -> Optional[Any]:
        """Execute command in container."""
        try:
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return None
            request = anvyl_pb2.ExecCommandRequest(  # type: ignore
                container_id=container_id,
                command=command,
                tty=tty
            )

            response = self.stub.ExecCommand(request)  # type: ignore
            return response

        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return None

    # Agent management methods
    def list_agents(self, host_id: Optional[str] = None) -> List[Any]:
        """List agents, optionally filtered by host."""
        try:
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return []
            request = anvyl_pb2.ListAgentsRequest()  # type: ignore
            if host_id:
                request.host_id = host_id

            response = self.stub.ListAgents(request)  # type: ignore
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
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return None
            request = anvyl_pb2.LaunchAgentRequest(  # type: ignore
                name=name,
                host_id=host_id,
                entrypoint=entrypoint,
                env=env or [],
                use_container=use_container,
                working_directory=working_directory,
                arguments=arguments or [],
                persistent=persistent
            )

            response = self.stub.LaunchAgent(request)  # type: ignore

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
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return False
            request = anvyl_pb2.StopAgentRequest(agent_id=agent_id)  # type: ignore
            response = self.stub.StopAgent(request)  # type: ignore

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
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return None
            request = anvyl_pb2.GetAgentStatusRequest(agent_id=agent_id)  # type: ignore
            response = self.stub.GetAgentStatus(request)  # type: ignore

            if response.success:
                return response.agent
            else:
                logger.error(f"Failed to get agent status: {response.error_message}")
                return None

        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return None

    def execute_agent_instruction(self, agent_name: str, instruction: str) -> Optional[Dict[str, Any]]:
        """Execute an instruction on an AI agent."""
        try:
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return None
            request = anvyl_pb2.ExecuteAgentInstructionRequest(  # type: ignore
                agent_name=agent_name,
                instruction=instruction
            )

            response = self.stub.ExecuteAgentInstruction(request)  # type: ignore

            if response.success:
                return {
                    "success": True,
                    "result": response.result,
                    "error_message": ""
                }
            else:
                return {
                    "success": False,
                    "result": "",
                    "error_message": response.error_message
                }

        except Exception as e:
            logger.error(f"Error executing agent instruction: {e}")
            return {
                "success": False,
                "result": "",
                "error_message": str(e)
            }

    # Host-level execution methods
    def exec_command_on_host(self,
                           host_id: str,
                           command: List[str],
                           working_directory: str = "",
                           env: Optional[List[str]] = None,
                           timeout: int = 0) -> Optional[Any]:
        """Execute command on host (Beszel agent functionality)."""
        try:
            if not self.stub:
                logger.error("Not connected to gRPC server")
                return None
            request = anvyl_pb2.ExecCommandOnHostRequest(  # type: ignore
                host_id=host_id,
                command=command,
                working_directory=working_directory,
                env=env or [],
                timeout=timeout
            )

            response = self.stub.ExecCommandOnHost(request)  # type: ignore
            return response

        except Exception as e:
            logger.error(f"Error executing command on host: {e}")
            return None

    def get_container_logs(self, container_id: str, follow: bool = False, tail: int = 100) -> Optional[str]:
        """Get container logs - alias for get_logs method."""
        return self.get_logs(container_id, follow, tail)

    def exec_container_command(self, container_id: str, command: List[str], tty: bool = False) -> Optional[Any]:
        """Execute command in container - alias for exec_command method."""
        return self.exec_command(container_id, command, tty)

# Convenience function for quick usage
def create_client(host: str = "localhost", port: int = 50051) -> AnvylClient:
    """Create and connect a client instance."""
    client = AnvylClient(host, port)
    if client.connect():
        return client
    else:
        raise ConnectionError(f"Failed to connect to Anvyl server at {host}:{port}")