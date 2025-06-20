"""
Anvyl AI Agent Manager

This module manages the lifecycle of AI agents, including starting, stopping,
and tracking agent configurations. Agents run in Docker containers for isolation
and persistence.
"""

import logging
import json
import os
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict, field
from datetime import datetime
import platform
import socket
import docker
import shutil

from .ai_agent import AnvylAIAgent, create_ai_agent
from .model_providers import ModelProvider
from .infrastructure_service import get_infrastructure_service

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for an AI agent."""
    name: str
    provider: str
    model_id: str
    host: str = "localhost"
    port: int = 50051
    verbose: bool = False
    provider_kwargs: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None
    status: str = "stopped"
    container_id: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class AgentManager:
    """Manages AI agent lifecycle and configurations using Docker containers."""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the agent manager.

        Args:
            config_dir: Directory to store agent configurations
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/.anvyl/agents")

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "agents.json"

        # Load existing configurations
        self.configurations = self._load_configurations()

        # Get infrastructure service
        self.infrastructure_service = get_infrastructure_service()

    def _load_configurations(self) -> Dict[str, AgentConfig]:
        """Load agent configurations from file."""
        configurations = {}
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for name, config_data in data.items():
                        configurations[name] = AgentConfig(**config_data)
            except Exception as e:
                logger.error(f"Error loading agent configurations: {e}")
        return configurations

    def _save_configurations(self):
        """Save agent configurations to file."""
        try:
            data = {name: asdict(config) for name, config in self.configurations.items()}
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving agent configurations: {e}")

    def _check_docker(self) -> bool:
        """Check if Docker is available and running."""
        try:
            client = docker.from_env()
            client.ping()
            return True
        except Exception:
            return False

    def _create_agent_script(self, config: AgentConfig) -> str:
        """Create a Python script for the agent to run in container."""
        # Use localhost for infrastructure service on macOS
        infrastructure_host = "host.docker.internal" if platform.system() == "Darwin" else "localhost"
        # Use host.docker.internal for LM Studio on macOS
        lmstudio_host = "host.docker.internal" if platform.system() == "Darwin" else "localhost"

        # Copy provider_kwargs and set LM Studio host if needed
        provider_kwargs = config.provider_kwargs.copy()
        if config.provider == "lmstudio":
            provider_kwargs["lmstudio_host"] = lmstudio_host

        script_content = f'''#!/usr/bin/env python3
"""
Anvyl AI Agent Container Script
Agent: {config.name}
Provider: {config.provider}
Model: {config.model_id}
"""

import sys
import os
import time
import signal
import logging
from pathlib import Path

# Add the anvyl package to Python path
sys.path.insert(0, '/app')

try:
    from anvyl.ai_agent import create_ai_agent
    from anvyl.infrastructure_service import get_infrastructure_service
except ImportError as e:
    print(f"Error importing anvyl: {{e}}")
    print("Make sure the anvyl package is installed in the container")
    sys.exit(1)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\\n🛑 Received shutdown signal. Stopping agent...")
    sys.exit(0)

def main():
    """Main agent container entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO if {config.verbose} else logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print(f"🚀 Starting Anvyl AI Agent: {config.name}")
    print(f"   Provider: {config.provider}")
    print(f"   Model: {config.model_id}")
    print(f"   Infrastructure Service: {infrastructure_host}")

    # Wait for infrastructure service to be available
    print("⏳ Waiting for infrastructure service to be available...")
    max_retries = 30
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Try to get infrastructure service (this will fail if not available)
            service = get_infrastructure_service()
            print("✅ Infrastructure service available")
            break
        except Exception as e:
            print(f"❌ Infrastructure service not available (attempt {{retry_count + 1}}/{{max_retries}}): {{e}}")

        retry_count += 1
        time.sleep(2)

    if retry_count >= max_retries:
        print("❌ Failed to connect to infrastructure service after maximum retries")
        sys.exit(1)

    try:
        # Create and initialize the agent
        agent = create_ai_agent(
            model_provider="{config.provider}",
            model_id="{config.model_id}",
            host="{infrastructure_host}",
            port={config.port},
            verbose={config.verbose},
            agent_name="{config.name}"{', ' + ', '.join([f'{k}={repr(v)}' for k, v in provider_kwargs.items()]) if provider_kwargs else ''}
        )

        print("✅ Agent initialized successfully")
        print("🔄 Agent is running and ready to receive instructions")
        print("💡 Use 'anvyl agent act {config.name} <instruction>' to execute actions")

        # Keep the container running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\\n🛑 Agent stopped by user")
    except Exception as e:
        print(f"❌ Agent error: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        return script_content

    def _create_dockerfile(self, config: AgentConfig) -> str:
        """Create a Dockerfile for the agent container."""
        dockerfile_content = f'''FROM python:3.12-alpine

# Install system dependencies
RUN apk add --no-cache \
    git \
    curl \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy Anvyl source and install dependencies
COPY . /app/
RUN pip install --no-cache-dir .

# Copy agent script
COPY agent_script.py /app/agent_script.py
RUN chmod +x /app/agent_script.py

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the agent
CMD ["python", "/app/agent_script.py"]
'''
        return dockerfile_content

    def create_agent(self,
                    name: str,
                    provider: str = "lmstudio",
                    model_id: str = "deepseek/deepseek-r1-0528-qwen3-8b",
                    host: str = "localhost",
                    port: int = 50051,
                    verbose: bool = False,
                    **provider_kwargs) -> AgentConfig:
        """
        Create a new AI agent configuration.

        Args:
            name: Unique name for the agent
            provider: Model provider (lmstudio, openai, etc.)
            model_id: Model identifier
            host: Infrastructure service host
            port: Infrastructure service port
            verbose: Enable verbose logging
            **provider_kwargs: Additional provider-specific arguments

        Returns:
            AgentConfig object
        """
        if name in self.configurations:
            raise ValueError(f"Agent '{name}' already exists")

        config = AgentConfig(
            name=name,
            provider=provider,
            model_id=model_id,
            host=host,
            port=port,
            verbose=verbose,
            provider_kwargs=provider_kwargs
        )

        self.configurations[name] = config
        self._save_configurations()

        logger.info(f"Created agent configuration: {name}")
        return config

    def _cleanup_failed_startup(self, name: str, container=None, image_name=None, temp_build_dir=None):
        """
        Clean up resources when agent startup fails.

        Args:
            name: Name of the agent
            container: Docker container object (if created)
            image_name: Docker image name
            temp_build_dir: Temporary build directory path
        """
        logger.info(f"🧹 Cleaning up failed startup for agent '{name}'")

        try:
            client = docker.from_env()

            # Clean up container if it exists
            if container:
                try:
                    container.remove(force=True)
                    logger.info(f"Removed failed container for agent '{name}'")
                except Exception as e:
                    logger.warning(f"Error removing container for agent '{name}': {e}")

            # Also try to remove container by name in case container object is invalid
            container_name = f"anvyl-agent-{name}"
            try:
                existing_container = client.containers.get(container_name)
                existing_container.remove(force=True)
                logger.info(f"Removed container by name: {container_name}")
            except docker.errors.NotFound:
                pass
            except Exception as e:
                logger.warning(f"Error removing container by name {container_name}: {e}")

            # NOTE: We do NOT remove Docker's intermediate build containers or dangling images here.
            # Users should run 'docker system prune -f' for global cleanup of Docker's own intermediates.

            # Clean up Docker image if it exists
            if image_name:
                try:
                    # Try to get image by name
                    image = client.images.get(image_name)
                    client.images.remove(image.id, force=True)
                    logger.info(f"Removed Docker image: {image_name}")
                except docker.errors.ImageNotFound:
                    # Try to find image by pattern
                    try:
                        images = client.images.list(filters={"reference": f"anvyl-agent-{name}*"})
                        for img in images:
                            client.images.remove(img.id, force=True)
                            logger.info(f"Removed Docker image: {img.tags[0] if img.tags else img.id}")
                    except Exception as e:
                        logger.warning(f"Error removing Docker images by pattern: {e}")
                except Exception as e:
                    logger.warning(f"Error removing Docker image {image_name}: {e}")

            # Clean up temporary build directory
            if temp_build_dir and temp_build_dir.exists():
                try:
                    shutil.rmtree(temp_build_dir)
                    logger.info(f"Removed temporary build directory: {temp_build_dir}")
                except Exception as e:
                    logger.warning(f"Error removing temporary build directory: {e}")

            # Reset agent configuration status
            config = self.configurations.get(name)
            if config:
                config.status = "stopped"
                config.container_id = None
                self._save_configurations()
                logger.info(f"Reset agent '{name}' status to stopped")

        except Exception as e:
            logger.error(f"Error during cleanup for agent '{name}': {e}")

    def start_agent(self, name: str) -> bool:
        """
        Start an AI agent in a Docker container.

        Args:
            name: Name of the agent to start

        Returns:
            True if agent started successfully, False otherwise
        """
        config = self.configurations.get(name)
        if not config:
            logger.error(f"Agent '{name}' not found")
            return False

        if not self._check_docker():
            logger.error("Docker is not available or not running")
            return False

        # Initialize cleanup variables
        container = None
        image_name = f"anvyl-agent-{name}"
        temp_build_dir = None
        image = None

        try:
            # Check if agent is already running
            status = self.get_agent_status(name)
            if status and status.get("running", False):
                logger.info(f"Agent '{name}' is already running")
                return True

            # Create agent directory for configuration
            agent_dir = self.config_dir / name
            agent_dir.mkdir(exist_ok=True)

            # Create temporary build directory at project root level
            import tempfile
            import os
            from pathlib import Path

            # Get the actual project root (parent of anvyl package)
            project_root = Path(__file__).parent.parent.resolve()

            # Create temporary build directory at project root level
            temp_build_dir = project_root / f"_temp_build_{name}"
            if temp_build_dir.exists():
                shutil.rmtree(temp_build_dir)
            temp_build_dir.mkdir(exist_ok=True)

            # Write agent script to temporary build directory
            agent_script_path = temp_build_dir / "agent_script.py"
            with open(agent_script_path, 'w') as f:
                f.write(self._create_agent_script(config))

            # Create Dockerfile in temporary build directory
            dockerfile_path = temp_build_dir / "Dockerfile"
            with open(dockerfile_path, 'w') as f:
                f.write(self._create_dockerfile(config))

            # Copy the entire anvyl package to the temp build directory for Docker context
            anvyl_package_dir = temp_build_dir / "anvyl"
            shutil.copytree(Path(__file__).parent, anvyl_package_dir, dirs_exist_ok=True)

            # Copy pyproject.toml and other necessary files to temp build directory
            shutil.copy(project_root / "pyproject.toml", temp_build_dir / "pyproject.toml")
            if (project_root / "MANIFEST.in").exists():
                shutil.copy(project_root / "MANIFEST.in", temp_build_dir / "MANIFEST.in")

            # Build Docker image using temp build directory as context
            client = docker.from_env()

            logger.info(f"Building Docker image for agent '{name}'...")
            try:
                image, build_logs = client.images.build(
                    path=str(temp_build_dir),  # Use temp build directory as build context
                    dockerfile="Dockerfile",  # Dockerfile is in the temp directory
                    tag=image_name,
                    rm=True
                )
            except Exception as build_error:
                logger.error(f"Failed to build Docker image for agent '{name}': {build_error}")
                # Clean up any partial images that might have been created
                self._cleanup_failed_startup(name, None, image_name, temp_build_dir)
                return False

            # Run container
            container_name = f"anvyl-agent-{name}"

            # Remove existing container if it exists
            try:
                existing_container = client.containers.get(container_name)
                existing_container.remove(force=True)
            except docker.errors.NotFound:
                pass

            # Create and start container
            container = client.containers.run(
                image_name,
                name=container_name,
                detach=True,
                environment={
                    'PYTHONPATH': '/app',
                    'PYTHONUNBUFFERED': '1'
                },
                labels={
                    'anvyl.agent.name': name,
                    'anvyl.component': 'agent'
                }
            )

            # Update configuration
            config.container_id = container.id
            config.status = "running"
            self._save_configurations()

            # Register agent with infrastructure service
            hosts = self.infrastructure_service.list_hosts()
            if hosts:
                host_id = hosts[0]["id"]  # Use first available host

                # Launch agent through infrastructure service
                agent_info = self.infrastructure_service.launch_agent(
                    name=name,
                    host_id=host_id,
                    entrypoint=str(agent_script_path),
                    env=[
                        f"PYTHONPATH=/app",
                        f"PYTHONUNBUFFERED=1"
                    ],
                    working_directory="/app",
                    persistent=True
                )

                if agent_info:
                    logger.info(f"Successfully started agent '{name}' in container {container.id}")
                    return True
                else:
                    logger.error(f"Failed to register agent '{name}' with infrastructure service")
                    # Clean up on infrastructure service failure
                    logger.info(f"🛑 Starting cleanup due to infrastructure service registration failure")
                    self._cleanup_failed_startup(name, container, image_name, temp_build_dir)
                    return False
            else:
                logger.error("No hosts available for agent")
                # Clean up on no hosts available
                logger.info(f"🛑 Starting cleanup due to no hosts available")
                self._cleanup_failed_startup(name, container, image_name, temp_build_dir)
                return False

        except Exception as e:
            logger.error(f"Error starting agent '{name}': {e}")
            # Clean up on any exception
            logger.info(f"🛑 Starting cleanup due to exception: {e}")
            self._cleanup_failed_startup(name, container, image_name, temp_build_dir)
            return False

        finally:
            # Clean up temporary build directory (always)
            if temp_build_dir and temp_build_dir.exists():
                try:
                    shutil.rmtree(temp_build_dir)
                except Exception as e:
                    logger.warning(f"Error cleaning up temp build directory: {e}")

    def stop_agent(self, name: str) -> bool:
        """
        Stop an AI agent.

        Args:
            name: Name of the agent to stop

        Returns:
            True if agent stopped successfully, False otherwise
        """
        config = self.configurations.get(name)
        if not config:
            logger.error(f"Agent '{name}' not found")
            return False

        try:
            # Stop agent through infrastructure service
            agents = self.infrastructure_service.list_agents()
            agent_info = next((a for a in agents if a["name"] == name), None)

            if agent_info:
                success = self.infrastructure_service.stop_agent(agent_info["id"])
                if success:
                    # Update configuration
                    config.status = "stopped"
                    config.container_id = None
                    self._save_configurations()
                    logger.info(f"Successfully stopped agent '{name}'")
                    return True
                else:
                    logger.error(f"Failed to stop agent '{name}' through infrastructure service")
                    return False
            else:
                logger.warning(f"Agent '{name}' not found in infrastructure service")
                # Update configuration anyway
                config.status = "stopped"
                config.container_id = None
                self._save_configurations()
                return True

        except Exception as e:
            logger.error(f"Error stopping agent '{name}': {e}")
            return False

    def get_agent_status(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of an agent.

        Args:
            name: Name of the agent

        Returns:
            Dictionary with agent status information
        """
        config = self.configurations.get(name)
        if not config:
            return None

        try:
            # Get status from infrastructure service
            agents = self.infrastructure_service.list_agents()
            agent_info = next((a for a in agents if a["name"] == name), None)

            if agent_info:
                return {
                    "name": name,
                    "running": agent_info["status"] == "running",
                    "status": agent_info["status"],
                    "container_id": agent_info["container_id"],
                    "started_at": agent_info["started_at"],
                    "stopped_at": agent_info["stopped_at"],
                    "exit_code": agent_info["exit_code"]
                }
            else:
                return {
                    "name": name,
                    "running": False,
                    "status": "not_found",
                    "container_id": None,
                    "started_at": None,
                    "stopped_at": None,
                    "exit_code": None
                }

        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return None

    def get_agent_logs(self, name: str, tail: int = 100, follow: bool = False) -> Optional[str]:
        """
        Get logs from an agent container.

        Args:
            name: Name of the agent
            tail: Number of lines to return
            follow: Whether to follow the logs

        Returns:
            Log content as string
        """
        config = self.configurations.get(name)
        if not config:
            return None

        try:
            # Get logs from infrastructure service
            agents = self.infrastructure_service.list_agents()
            agent_info = next((a for a in agents if a["name"] == name), None)

            if agent_info and agent_info["container_id"]:
                return self.infrastructure_service.get_logs(
                    agent_info["container_id"],
                    follow=follow,
                    tail=tail
                )
            else:
                return None

        except Exception as e:
            logger.error(f"Error getting agent logs: {e}")
            return None

    def get_agent_config(self, name: str) -> Optional[AgentConfig]:
        """Get agent configuration."""
        return self.configurations.get(name)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agent configurations with their status."""
        result = []
        for name, config in self.configurations.items():
            status = self.get_agent_status(name)
            result.append({
                "name": name,
                "provider": config.provider,
                "model_id": config.model_id,
                "status": status["status"] if status else "unknown",
                "running": status["running"] if status else False,
                "created_at": config.created_at
            })
        return result

    def list_running_agents(self) -> List[str]:
        """List names of running agents."""
        running = []
        for name in self.configurations:
            status = self.get_agent_status(name)
            if status and status.get("running", False):
                running.append(name)
        return running

    def remove_agent(self, name: str) -> bool:
        """
        Remove an agent and its Docker image.

        Args:
            name: Name of the agent to remove

        Returns:
            True if agent removed successfully, False otherwise
        """
        config = self.configurations.get(name)
        if not config:
            logger.error(f"Agent '{name}' not found")
            return False

        try:
            # Stop agent if running
            if self.get_agent_status(name) and self.get_agent_status(name).get("running", False):
                self.stop_agent(name)

            # Remove agent from infrastructure service
            agents = self.infrastructure_service.list_agents()
            agent_info = next((a for a in agents if a["name"] == name), None)

            if agent_info:
                self.infrastructure_service.stop_agent(agent_info["id"])

            # Remove Docker image
            client = docker.from_env()
            image_name = f"anvyl-agent-{name}"

            try:
                image = client.images.get(image_name)
                client.images.remove(image.id, force=True)
                logger.info(f"Removed Docker image: {image_name}")
            except docker.errors.ImageNotFound:
                logger.info(f"Docker image {image_name} not found")
            except Exception as e:
                logger.warning(f"Error removing Docker image {image_name}: {e}")

            # Remove agent directory and files
            agent_dir = self.config_dir / name
            if agent_dir.exists():
                shutil.rmtree(agent_dir)
                logger.info(f"Removed agent directory: {agent_dir}")

            # Remove configuration
            del self.configurations[name]
            self._save_configurations()

            logger.info(f"Successfully removed agent '{name}'")
            return True

        except Exception as e:
            logger.error(f"Error removing agent '{name}': {e}")
            return False

    def update_agent(self, name: str, **kwargs) -> bool:
        """
        Update agent configuration.

        Args:
            name: Name of the agent to update
            **kwargs: Configuration parameters to update

        Returns:
            True if update successful, False otherwise
        """
        config = self.configurations.get(name)
        if not config:
            logger.error(f"Agent '{name}' not found")
            return False

        try:
            # Update configuration
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            self._save_configurations()
            logger.info(f"Updated agent configuration: {name}")
            return True

        except Exception as e:
            logger.error(f"Error updating agent '{name}': {e}")
            return False

    def cleanup_orphaned_resources(self, name: str = None) -> bool:
        """
        Clean up orphaned Docker containers and images for agents.

        Args:
            name: Specific agent name to clean up, or None to clean up all orphaned resources

        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            client = docker.from_env()
            cleaned_count = 0

            if name:
                # Clean up specific agent
                container_name = f"anvyl-agent-{name}"
                image_name = f"anvyl-agent-{name}"

                # Remove container
                try:
                    container = client.containers.get(container_name)
                    container.remove(force=True)
                    logger.info(f"Removed orphaned container: {container_name}")
                    cleaned_count += 1
                except docker.errors.NotFound:
                    pass
                except Exception as e:
                    logger.warning(f"Error removing container {container_name}: {e}")

                # Remove image
                try:
                    image = client.images.get(image_name)
                    client.images.remove(image.id, force=True)
                    logger.info(f"Removed orphaned image: {image_name}")
                    cleaned_count += 1
                except docker.errors.ImageNotFound:
                    pass
                except Exception as e:
                    logger.warning(f"Error removing image {image_name}: {e}")
            else:
                # Clean up all orphaned anvyl agent resources
                # Find containers with anvyl agent labels
                containers = client.containers.list(all=True, filters={"label": "anvyl.component=agent"})
                for container in containers:
                    try:
                        container.remove(force=True)
                        logger.info(f"Removed orphaned container: {container.name}")
                        cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"Error removing container {container.name}: {e}")

                # Find and remove anvyl agent images
                images = client.images.list(filters={"reference": "anvyl-agent-*"})
                for image in images:
                    try:
                        client.images.remove(image.id, force=True)
                        logger.info(f"Removed orphaned image: {image.tags[0] if image.tags else image.id}")
                        cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"Error removing image {image.id}: {e}")

                # NOTE: We do NOT remove Docker's intermediate build containers or dangling images here.
                # Users should run 'docker system prune -f' for global cleanup of Docker's own intermediates.

            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned up {cleaned_count} orphaned resources")
            else:
                logger.info("✅ No orphaned resources found")

            return True

        except Exception as e:
            logger.error(f"Error during orphaned resource cleanup: {e}")
            return False


# Global agent manager instance
_agent_manager = None

def get_agent_manager() -> AgentManager:
    """Get the global agent manager instance."""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager