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
RUN apk add --no-cache \\
    git \\
    curl \\
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy the anvyl package
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create agent script
RUN echo '{self._create_agent_script(config)}' > /app/agent_script.py \\
    && chmod +x /app/agent_script.py

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

        try:
            # Check if agent is already running
            status = self.get_agent_status(name)
            if status and status.get("running", False):
                logger.info(f"Agent '{name}' is already running")
                return True

            # Create agent directory
            agent_dir = self.config_dir / name
            agent_dir.mkdir(exist_ok=True)

            # Create Dockerfile
            dockerfile_path = agent_dir / "Dockerfile"
            with open(dockerfile_path, 'w') as f:
                f.write(self._create_dockerfile(config))

            # Build Docker image
            client = docker.from_env()
            image_name = f"anvyl-agent-{name}"

            logger.info(f"Building Docker image for agent '{name}'...")
            image, build_logs = client.images.build(
                path=str(agent_dir),
                dockerfile="Dockerfile",
                tag=image_name,
                rm=True
            )

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

                # Create agent script path
                agent_script_path = str(agent_dir / "agent_script.py")

                # Launch agent through infrastructure service
                agent_info = self.infrastructure_service.launch_agent(
                    name=name,
                    host_id=host_id,
                    entrypoint=agent_script_path,
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
                    # Clean up container
                    container.remove(force=True)
                    return False
            else:
                logger.error("No hosts available for agent")
                container.remove(force=True)
                return False

        except Exception as e:
            logger.error(f"Error starting agent '{name}': {e}")
            return False

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
                import shutil
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


# Global agent manager instance
_agent_manager = None

def get_agent_manager() -> AgentManager:
    """Get the global agent manager instance."""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager