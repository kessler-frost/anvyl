"""
Anvyl AI Agent Manager

This module manages the lifecycle of AI agents, including starting, stopping,
and tracking agent configurations. Agents run in Docker containers for isolation
and persistence.
"""

import logging
import json
import os
import subprocess
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict, field
from datetime import datetime

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
        self.config_dir = Path(config_dir or os.path.expanduser("~/.anvyl/agents"))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "agents.json"

        # Load existing configurations
        self.configurations = self._load_configurations()

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
            result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _create_agent_script(self, config: AgentConfig) -> str:
        """Create a Python script for the agent to run in container."""
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

    print(f"🚀 Starting Anvyl AI Agent: {{config.name}}")
    print(f"   Provider: {{config.provider}}")
    print(f"   Model: {{config.model_id}}")
    print(f"   gRPC Server: {{config.host}}:{{config.port}}")

    # Wait for gRPC server to be available
    print("⏳ Waiting for gRPC server to be available...")
    max_retries = 30
    retry_count = 0

    while retry_count < max_retries:
        try:
            client = AnvylClient("{config.host}", {config.port})
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
            host="{config.host}",
            port={config.port},
            verbose={config.verbose},
            agent_name="{config.name}",
            {', '.join([f'{k}={repr(v)}' for k, v in config.provider_kwargs.items()])}
        )

        print("✅ Agent initialized successfully")
        print("🔄 Agent is running and ready to receive instructions")
        print("💡 Use 'anvyl agent act {config.name} \"<instruction>\"' to execute actions")

        # Keep the container running
        while True:
            time.sleep(60)  # Sleep for 1 minute
            # Optional: Add health check or keepalive logic here

    except Exception as e:
        print(f"❌ Error initializing agent: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

        script_path = self.config_dir / f"{config.name}_agent.py"
        with open(script_path, 'w') as f:
            f.write(script_content)

        # Make script executable
        os.chmod(script_path, 0o755)
        return str(script_path)

    def create_agent(self,
                    name: str,
                    provider: str = "lmstudio",
                    model_id: str = "llama-3.2-1b-instruct-mlx",
                    host: str = "localhost",
                    port: int = 50051,
                    verbose: bool = False,
                    **provider_kwargs) -> AgentConfig:
        """
        Create a new agent configuration.

        Args:
            name: Unique name for the agent
            provider: Model provider type
            model_id: Model identifier
            host: Anvyl server host
            port: Anvyl server port
            verbose: Enable verbose logging
            **provider_kwargs: Provider-specific configuration

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
                result = subprocess.run(['docker', 'inspect', config.container_id],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    raise ValueError(f"Agent '{name}' is already running in container {config.container_id}")
            except Exception:
                pass  # Container doesn't exist, we can start a new one

        # Create the agent script
        script_path = self._create_agent_script(config)

        # Determine the container image based on provider
        if config.provider == "lmstudio":
            base_image = "python:3.12-slim"
        elif config.provider == "ollama":
            base_image = "python:3.12-slim"
        elif config.provider in ["openai", "anthropic"]:
            base_image = "python:3.12-slim"
        else:
            base_image = "python:3.12-slim"

        # Create Dockerfile for the agent
        dockerfile_content = f'''FROM {base_image}

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy agent script
COPY {os.path.basename(script_path)} /app/agent.py

# Install Python dependencies
RUN pip install --no-cache-dir \\
    anvyl \\
    rich \\
    typer

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the agent
CMD ["python", "/app/agent.py"]
'''

        dockerfile_path = self.config_dir / f"{name}_Dockerfile"
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

        # Build the Docker image
        image_name = f"anvyl-agent-{name}"
        build_cmd = [
            'docker', 'build',
            '-f', str(dockerfile_path),
            '-t', image_name,
            str(self.config_dir)
        ]

        logger.info(f"Building Docker image for agent {name}...")
        result = subprocess.run(build_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to build Docker image: {result.stderr}")

        # Run the container
        container_name = f"anvyl-agent-{name}"
        run_cmd = [
            'docker', 'run',
            '-d',  # Detached mode
            '--name', container_name,
            '--network', 'host',  # Use host network to access gRPC server
            '-e', f'ANVYL_HOST={config.host}',
            '-e', f'ANVYL_PORT={config.port}',
            image_name
        ]

        logger.info(f"Starting container for agent {name}...")
        result = subprocess.run(run_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to start container: {result.stderr}")

        container_id = result.stdout.strip()
        config.container_id = container_id
        config.status = "running"
        self._save_configurations()

        logger.info(f"Started agent {name} in container {container_id}")
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
            # Stop the container
            stop_cmd = ['docker', 'stop', config.container_id]
            result = subprocess.run(stop_cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # Remove the container
                rm_cmd = ['docker', 'rm', config.container_id]
                subprocess.run(rm_cmd, capture_output=True, text=True)

                config.container_id = None
                config.status = "stopped"
                self._save_configurations()

                logger.info(f"Stopped agent {name}")
                return True
            else:
                logger.warning(f"Failed to stop container {config.container_id}: {result.stderr}")
                return False

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
            # Get container status
            inspect_cmd = ['docker', 'inspect', config.container_id]
            result = subprocess.run(inspect_cmd, capture_output=True, text=True)

            if result.returncode == 0:
                import json
                container_info = json.loads(result.stdout)[0]
                state = container_info['State']

                return {
                    "name": name,
                    "status": state['Status'],
                    "container_id": config.container_id,
                    "running": state['Running'],
                    "started_at": state.get('StartedAt'),
                    "finished_at": state.get('FinishedAt')
                }
            else:
                # Container doesn't exist
                config.container_id = None
                config.status = "stopped"
                self._save_configurations()

                return {
                    "name": name,
                    "status": "stopped",
                    "container_id": None
                }

        except Exception as e:
            logger.error(f"Error getting status for agent {name}: {e}")
            return None

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
            cmd = ['docker', 'logs']
            if follow:
                cmd.append('-f')
            cmd.extend(['--tail', str(tail), config.container_id])

            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout if result.returncode == 0 else result.stderr

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
                # Remove Docker image
                image_name = f"anvyl-agent-{name}"
                subprocess.run(['docker', 'rmi', image_name], capture_output=True)

                # Remove script and Dockerfile
                script_path = self.config_dir / f"{name}_agent.py"
                dockerfile_path = self.config_dir / f"{name}_Dockerfile"

                if script_path.exists():
                    script_path.unlink()
                if dockerfile_path.exists():
                    dockerfile_path.unlink()

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


# Global agent manager instance
_agent_manager = None

def get_agent_manager() -> AgentManager:
    """Get the global agent manager instance."""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager