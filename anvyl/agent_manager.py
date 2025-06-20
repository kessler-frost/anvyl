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

        # Update existing configs to use host.docker.internal on macOS
        if platform.system() == "Darwin":
            self._update_macos_configs()

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
        # Always use host.docker.internal for gRPC host on macOS
        grpc_host = "host.docker.internal" if platform.system() == "Darwin" else config.host
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
    from anvyl.grpc_client import AnvylClient
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
    print(f"   gRPC Server: {grpc_host}:{config.port}")

    # Wait for gRPC server to be available
    print("⏳ Waiting for gRPC server to be available...")
    max_retries = 30
    retry_count = 0

    while retry_count < max_retries:
        try:
            client = AnvylClient("{grpc_host}", {config.port})
            if client.connect():
                print("✅ Connected to gRPC server")
                break
            else:
                print(f"❌ Failed to connect to gRPC server (attempt {{retry_count + 1}}/{{max_retries}})")
        except Exception as e:
            print(f"❌ Connection error (attempt {{retry_count + 1}}/{{max_retries}}): {{e}}")

        retry_count += 1
        time.sleep(2)

    if retry_count >= max_retries:
        print("❌ Failed to connect to gRPC server after maximum retries")
        sys.exit(1)

    try:
        # Create and initialize the agent
        agent = create_ai_agent(
            model_provider="{config.provider}",
            model_id="{config.model_id}",
            host="{grpc_host}",
            port={config.port},
            verbose={config.verbose},
            agent_name="{config.name}"{', ' + ', '.join([f'{k}={repr(v)}' for k, v in provider_kwargs.items()]) if provider_kwargs else ''}
        )

        print("✅ Agent initialized successfully")
        print("🔄 Agent is running and ready to receive instructions")
        print("💡 Use 'anvyl agent act {config.name} <instruction>' to execute actions")

        # Keep the container running
        while True:
            time.sleep(60)  # Sleep for 1 minute

    except Exception as e:
        print(f"❌ Error running agent: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        return script_content

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
            provider: Model provider (lmstudio, ollama, openai, anthropic)
            model_id: Model identifier
            host: Anvyl gRPC server host
            port: Anvyl gRPC server port
            verbose: Enable verbose logging
            **provider_kwargs: Additional provider-specific arguments

        Returns:
            AgentConfig: The created agent configuration

        Raises:
            ValueError: If agent name already exists
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
        Start an agent by name in a Docker container.

        Args:
            name: Name of the agent to start

        Returns:
            bool: True if agent was started successfully

        Raises:
            ValueError: If agent doesn't exist or is already running
            RuntimeError: If Docker is not available
        """
        if name not in self.configurations:
            raise ValueError(f"Agent '{name}' not found. Use 'anvyl agent create' first.")

        if not self._check_docker():
            raise RuntimeError("Docker is not available. Please install and start Docker.")

        config = self.configurations[name]

        # Check if agent is already running
        if config.container_id:
            try:
                client = docker.from_env()
                container = client.containers.get(config.container_id)
                if container.status == "running":
                    raise ValueError(f"Agent '{name}' is already running in container {config.container_id}")
            except Exception:
                pass  # Container doesn't exist, we can start a new one

        # Create the agent script
        script_content = self._create_agent_script(config)

        # Determine the container image based on provider
        if config.provider == "lmstudio":
            base_image = "python:3.12-slim"
        elif config.provider == "ollama":
            base_image = "python:3.12-slim"
        elif config.provider in ["openai", "anthropic"]:
            base_image = "python:3.12-slim"
        else:
            base_image = "python:3.12-slim"

        # Set Docker build context to the directory containing pyproject.toml
        project_root = Path(__file__).parent.parent.resolve()

        # Write agent script and Dockerfile into anvyl/agents/ (inside build context)
        agents_dir = Path(__file__).parent / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        script_path = agents_dir / f"{config.name}_agent.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)

        # Prepare Dockerfile content
        dockerfile_content = f'''FROM {base_image}

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy agent script
COPY anvyl/agents/{config.name}_agent.py /app/agent.py

# Copy the entire anvyl directory and build files to /app
COPY . /app
'''
        dockerfile_content += '''
# Install anvyl in editable mode with all dependencies
RUN pip install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the agent
CMD ["python", "/app/agent.py"]
'''
        dockerfile_path = Path(__file__).parent / "agents" / f"{config.name}_Dockerfile"
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

        # Build the Docker image
        image_name = f"anvyl-agent-{config.name}"
        client = docker.from_env()
        logger.info(f"Building Docker image for agent {config.name}...")

        try:
            image, logs = client.images.build(
                path=str(project_root),
                dockerfile=str(dockerfile_path),
                tag=image_name,
                rm=True
            )
            logger.info(f"Successfully built image: {image_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to build Docker image: {e}")

        # Run the container
        container_name = f"anvyl-agent-{config.name}"
        logger.info(f"Starting container for agent {config.name}...")

        try:
            container = client.containers.run(
                image_name,
                name=container_name,
                detach=True,
                environment={
                    'ANVYL_HOST': config.host,
                    'ANVYL_PORT': str(config.port)
                }
            )
            logger.info(f"Successfully started container: {container.id}")
        except Exception as e:
            raise RuntimeError(f"Failed to start container: {e}")

        container_id = container.id
        config.container_id = container_id
        config.status = "running"
        self._save_configurations()
        logger.info(f"Started agent {config.name} in container {container_id}")
        return True

    def stop_agent(self, name: str) -> bool:
        """
        Stop a running agent container.

        Args:
            name: Name of the agent to stop

        Returns:
            bool: True if agent was stopped, False if not running
        """
        if name not in self.configurations:
            return False

        config = self.configurations[name]
        if not config.container_id:
            return False

        try:
            client = docker.from_env()
            container = client.containers.get(config.container_id)

            # Stop the container
            container.stop()

            # Remove the container
            container.remove()

            config.container_id = None
            config.status = "stopped"
            self._save_configurations()

            logger.info(f"Stopped agent {name}")
            return True

        except Exception as e:
            logger.error(f"Error stopping agent {name}: {e}")
            return False

    def get_agent_status(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of an agent container.

        Args:
            name: Name of the agent

        Returns:
            Dict with status information or None if agent not found
        """
        if name not in self.configurations:
            return None

        config = self.configurations[name]
        if not config.container_id:
            return {
                "name": name,
                "status": "stopped",
                "container_id": None
            }

        try:
            client = docker.from_env()
            container = client.containers.get(config.container_id)
            state = container.attrs['State']

            return {
                "name": name,
                "status": state['Status'],
                "container_id": config.container_id,
                "running": state['Running'],
                "started_at": state.get('StartedAt'),
                "finished_at": state.get('FinishedAt')
            }

        except Exception as e:
            # Container doesn't exist
            config.container_id = None
            config.status = "stopped"
            self._save_configurations()

            return {
                "name": name,
                "status": "stopped",
                "container_id": None
            }

    def get_agent_logs(self, name: str, tail: int = 100, follow: bool = False) -> Optional[str]:
        """
        Get logs from an agent container.

        Args:
            name: Name of the agent
            tail: Number of lines to show
            follow: Follow log output

        Returns:
            Log output or None if agent not found
        """
        if name not in self.configurations:
            return None

        config = self.configurations[name]
        if not config.container_id:
            return "Agent is not running"

        try:
            client = docker.from_env()
            container = client.containers.get(config.container_id)

            if follow:
                return container.logs(stream=True, tail=tail)
            else:
                return container.logs(tail=tail).decode('utf-8')

        except Exception as e:
            logger.error(f"Error getting logs for agent {name}: {e}")
            return None

    def get_agent_config(self, name: str) -> Optional[AgentConfig]:
        """
        Get agent configuration by name.

        Args:
            name: Name of the agent

        Returns:
            AgentConfig or None: The agent configuration
        """
        return self.configurations.get(name)

    def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all agent configurations with their current status.

        Returns:
            List of agent information dictionaries
        """
        agents = []
        for name, config in self.configurations.items():
            status_info = self.get_agent_status(name)
            if status_info:
                agent_info = asdict(config)
                agent_info.update(status_info)
                agents.append(agent_info)
        return agents

    def list_running_agents(self) -> List[str]:
        """
        List names of currently running agents.

        Returns:
            List of running agent names
        """
        running = []
        for name in self.configurations.keys():
            status_info = self.get_agent_status(name)
            if status_info and status_info.get("running", False):
                running.append(name)
        return running

    def remove_agent(self, name: str) -> bool:
        """
        Remove an agent configuration and stop its container.

        Args:
            name: Name of the agent to remove

        Returns:
            bool: True if agent was removed
        """
        # Stop the agent if running
        self.stop_agent(name)

        if name in self.configurations:
            del self.configurations[name]
            self._save_configurations()

            # Clean up Docker resources
            try:
                # Remove Docker image with force if needed
                image_name = f"anvyl-agent-{name}"
                client = docker.from_env()

                try:
                    image = client.images.get(image_name)
                    client.images.remove(image.id, force=True)
                    logger.info(f"Removed Docker image: {image_name}")
                except Exception as e:
                    logger.info(f"Image {image_name} not found or already removed: {e}")

                # Also try to remove any dangling images that might be related
                # This handles cases where the image might have been re-tagged or have multiple tags
                client.images.prune()

                # Remove script and Dockerfile
                script_path = self.config_dir / f"{name}_agent.py"
                dockerfile_path = self.config_dir / f"{name}_Dockerfile"

                if script_path.exists():
                    script_path.unlink()
                if dockerfile_path.exists():
                    dockerfile_path.unlink()

                # Also clean up files in the agents directory
                agents_dir = Path(__file__).parent / "agents"
                agents_script_path = agents_dir / f"{name}_agent.py"
                agents_dockerfile_path = agents_dir / f"{name}_Dockerfile"

                if agents_script_path.exists():
                    agents_script_path.unlink()
                if agents_dockerfile_path.exists():
                    agents_dockerfile_path.unlink()

            except Exception as e:
                logger.warning(f"Error cleaning up Docker resources for {name}: {e}")

            logger.info(f"Removed agent configuration: {name}")
            return True
        return False

    def update_agent(self, name: str, **kwargs) -> bool:
        """
        Update an agent configuration.

        Args:
            name: Name of the agent to update
            **kwargs: Configuration parameters to update

        Returns:
            bool: True if agent was updated
        """
        if name not in self.configurations:
            return False

        config = self.configurations[name]

        # Update allowed fields
        allowed_fields = ['provider', 'model_id', 'host', 'port', 'verbose', 'provider_kwargs']
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(config, field, value)

        self._save_configurations()
        logger.info(f"Updated agent configuration: {name}")

        # If agent is running, warn user to restart
        status_info = self.get_agent_status(name)
        if status_info and status_info.get("running", False):
            logger.warning(f"Agent '{name}' is running. Restart to apply changes.")

        return True

    def _update_macos_configs(self):
        """Update all existing agent configs to use host.docker.internal for gRPC host on macOS."""
        updated = False
        for config in self.configurations.values():
            if config.host in ["localhost", "127.0.0.1"]:
                config.host = "host.docker.internal"
                updated = True

        if updated:
            self._save_configurations()
            logger.info("Updated existing agent configs to use host.docker.internal for macOS")


# Global agent manager instance
_agent_manager = None

def get_agent_manager() -> AgentManager:
    """Get the global agent manager instance."""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager