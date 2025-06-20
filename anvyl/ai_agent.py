"""
Anvyl AI Agent - Model Provider Abstraction for AI-powered infrastructure management

This module provides AI agents with access to Anvyl's gRPC client through configurable
model providers, allowing natural language instruction execution with the infrastructure orchestrator.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
import json
import asyncio
from datetime import datetime

from .grpc_client import AnvylClient
from .model_providers import ModelProvider, create_model_provider

logger = logging.getLogger(__name__)
console = Console()


class AnvylAIAgent:
    """
    AI Agent that uses configurable model providers to execute infrastructure actions.

    This agent provides natural language instruction execution for:
    - Host management (list, add, monitor)
    - Container management (create, stop, logs, exec)
    - Agent management (launch, stop, monitor)
    - System status and monitoring

    Supports multiple model providers:
    - LM Studio (default)
    - Ollama
    - OpenAI
    - Anthropic
    """

    def __init__(self,
                 model_provider: Union[str, ModelProvider] = "lmstudio",
                 model_id: str = "llama-3.2-1b-instruct-mlx",
                 host: str = "localhost",
                 port: int = 50051,
                 verbose: bool = False,
                 agent_name: Optional[str] = None,
                 **provider_kwargs):
        """
        Initialize the AI agent.

        Args:
            model_provider: Model provider to use ("lmstudio", "ollama", "openai", "anthropic")
                           or a ModelProvider instance
            model_id: Model identifier to use
            host: Anvyl gRPC server host
            port: Anvyl gRPC server port
            verbose: Enable verbose logging
            agent_name: Name of the AI agent
            **provider_kwargs: Additional provider-specific configuration
        """
        self.host = host
        self.port = port
        self.verbose = verbose
        self.agent_name = agent_name

        # Initialize gRPC client
        self.client = AnvylClient(host, port)
        if not self.client.connect():
            raise ConnectionError(f"Failed to connect to Anvyl server at {host}:{port}")

        # Initialize model provider
        if isinstance(model_provider, str):
            self.model_provider = create_model_provider(
                provider_type=model_provider,
                model_id=model_id,
                **provider_kwargs
            )
        else:
            self.model_provider = model_provider

        # Initialize the model provider
        if not self.model_provider.initialize():
            provider_name = self.model_provider.__class__.__name__
            raise ConnectionError(f"{provider_name} is not available. Please ensure it's properly configured.")

        # Define available actions for the AI agent
        self.available_actions = [
            self._list_hosts,
            self._add_host,
            self._get_host_metrics,
            self._list_containers,
            self._create_container,
            self._stop_container,
            self._get_container_logs,
            self._exec_container_command,
            self._list_agents,
            self._launch_agent,
            self._stop_agent,
            self._get_system_status,
            self._get_ui_status,
            self._discover_agents,
            self._route_to_agent,
        ]

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model provider."""
        return self.model_provider.get_model_info()

    def get_available_actions(self) -> List[str]:
        """Get list of available actions."""
        return [action.__name__.replace('_', ' ').title() for action in self.available_actions]

    def _list_hosts(self, **kwargs) -> Dict[str, Any]:
        """List all hosts."""
        try:
            hosts = self.client.list_hosts()
            return {
                "success": True,
                "hosts": [
                    {
                        "id": getattr(host, 'id', ''),
                        "name": getattr(host, 'name', ''),
                        "ip": getattr(host, 'ip', ''),
                        "status": getattr(host, 'status', ''),
                        "os": getattr(host, 'os', ''),
                        "tags": getattr(host, 'tags', [])
                    }
                    for host in hosts
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _add_host(self, name: str, ip: str, os: str = "", tags: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Add a new host."""
        try:
            host = self.client.add_host(name, ip, os, tags or [])
            if host:
                return {
                    "success": True,
                    "host": {
                        "id": getattr(host, 'id', ''),
                        "name": getattr(host, 'name', ''),
                        "ip": getattr(host, 'ip', ''),
                        "status": getattr(host, 'status', '')
                    }
                }
            return {"success": False, "error": "Failed to add host"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_host_metrics(self, host_id: str, **kwargs) -> Dict[str, Any]:
        """Get host metrics."""
        try:
            metrics = self.client.get_host_metrics(host_id)
            if metrics:
                return {
                    "success": True,
                    "metrics": {
                        "cpu_usage": getattr(metrics, 'cpu_usage', 0),
                        "memory_usage": getattr(metrics, 'memory_usage', 0),
                        "disk_usage": getattr(metrics, 'disk_usage', 0),
                        "network_usage": getattr(metrics, 'network_usage', 0)
                    }
                }
            return {"success": False, "error": "Failed to get metrics"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _list_containers(self, host_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """List containers."""
        try:
            containers = self.client.list_containers(host_id)
            return {
                "success": True,
                "containers": [
                    {
                        "id": getattr(container, 'id', ''),
                        "name": getattr(container, 'name', ''),
                        "image": getattr(container, 'image', ''),
                        "status": getattr(container, 'status', ''),
                        "host_id": getattr(container, 'host_id', '')
                    }
                    for container in containers
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_container(self, name: str, image: str, host_id: Optional[str] = None,
                         ports: Optional[List[str]] = None, volumes: Optional[List[str]] = None,
                         environment: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Create a container."""
        try:
            container = self.client.add_container(
                name=name,
                image=image,
                host_id=host_id,
                ports=ports or [],
                volumes=volumes or [],
                environment=environment or []
            )
            if container:
                return {
                    "success": True,
                    "container": {
                        "id": getattr(container, 'id', ''),
                        "name": getattr(container, 'name', ''),
                        "image": getattr(container, 'image', ''),
                        "status": getattr(container, 'status', '')
                    }
                }
            return {"success": False, "error": "Failed to create container"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _stop_container(self, container_id: str, timeout: int = 10, **kwargs) -> Dict[str, Any]:
        """Stop a container."""
        try:
            success = self.client.stop_container(container_id, timeout)
            return {"success": success, "message": "Container stopped" if success else "Failed to stop container"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_container_logs(self, container_id: str, tail: int = 100, **kwargs) -> Dict[str, Any]:
        """Get container logs."""
        try:
            logs = self.client.get_logs(container_id, tail=tail)
            return {"success": True, "logs": logs or "No logs available"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _exec_container_command(self, container_id: str, command: List[str], **kwargs) -> Dict[str, Any]:
        """Execute command in container."""
        try:
            result = self.client.exec_command(container_id, command)
            if result:
                return {"success": True, "output": str(result)}
            return {"success": False, "error": "Failed to execute command"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _list_agents(self, host_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """List agents."""
        try:
            agents = self.client.list_agents(host_id)
            return {
                "success": True,
                "agents": [
                    {
                        "id": getattr(agent, 'id', ''),
                        "name": getattr(agent, 'name', ''),
                        "status": getattr(agent, 'status', ''),
                        "host_id": getattr(agent, 'host_id', '')
                    }
                    for agent in agents
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _launch_agent(self, name: str, host_id: str, entrypoint: str,
                     environment: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Launch an agent in a container."""
        try:
            agent = self.client.launch_agent(
                name=name,
                host_id=host_id,
                entrypoint=entrypoint,
                env=environment or []
            )
            if agent:
                return {
                    "success": True,
                    "agent": {
                        "id": getattr(agent, 'id', ''),
                        "name": getattr(agent, 'name', ''),
                        "status": getattr(agent, 'status', ''),
                        "host_id": getattr(agent, 'host_id', '')
                    }
                }
            return {"success": False, "error": "Failed to launch agent"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _stop_agent(self, agent_id: str, **kwargs) -> Dict[str, Any]:
        """Stop an agent."""
        try:
            success = self.client.stop_agent(agent_id)
            return {"success": success, "message": "Agent stopped" if success else "Failed to stop agent"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_system_status(self, **kwargs) -> Dict[str, Any]:
        """Get overall system status."""
        try:
            hosts = self.client.list_hosts()
            containers = self.client.list_containers()
            agents = self.client.list_agents()

            return {
                "success": True,
                "status": {
                    "hosts": {
                        "total": len(hosts),
                        "online": len([h for h in hosts if getattr(h, 'status', '') == 'online'])
                    },
                    "containers": {
                        "total": len(containers),
                        "running": len([c for c in containers if getattr(c, 'status', '') == 'running'])
                    },
                    "agents": {
                        "total": len(agents),
                        "running": len([a for a in agents if getattr(a, 'status', '') == 'running'])
                    }
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_ui_status(self, **kwargs) -> Dict[str, Any]:
        """Get UI stack status."""
        try:
            status = self.client.get_ui_stack_status()
            return {"success": True, "ui_status": status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _discover_agents(self, **kwargs) -> Dict[str, Any]:
        """Discover all agents across all connected hosts."""
        try:
            hosts = self.client.list_hosts()
            all_agents = []

            for host in hosts:
                host_id = getattr(host, 'id', '')
                host_name = getattr(host, 'name', '')
                host_ip = getattr(host, 'ip', '')

                # Get agents for this host
                agents = self.client.list_agents(host_id)
                for agent in agents:
                    agent_info = {
                        "id": getattr(agent, 'id', ''),
                        "name": getattr(agent, 'name', ''),
                        "status": getattr(agent, 'status', ''),
                        "host_id": host_id,
                        "host_name": host_name,
                        "host_ip": host_ip
                    }
                    all_agents.append(agent_info)

            return {
                "success": True,
                "agents": all_agents,
                "total": len(all_agents)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _route_to_agent(self, agent_name: str, command: str, **kwargs) -> Dict[str, Any]:
        """Route a command to a specific agent by name."""
        try:
            # First discover all agents
            discovery_result = self._discover_agents()
            if not discovery_result["success"]:
                return discovery_result

            # Find the target agent
            target_agent = None
            for agent in discovery_result["agents"]:
                if agent["name"] == agent_name:
                    target_agent = agent
                    break

            if not target_agent:
                return {
                    "success": False,
                    "error": f"Agent '{agent_name}' not found. Available agents: {[a['name'] for a in discovery_result['agents']]}"
                }

            # Execute command on the target agent
            # This would typically involve connecting to the agent's host and executing the command
            # For now, we'll simulate this by returning agent info and command
            return {
                "success": True,
                "agent": target_agent,
                "command": command,
                "message": f"Command '{command}' routed to agent '{agent_name}' on host {target_agent['host_name']} ({target_agent['host_ip']})"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def act(self, instruction: str) -> str:
        """
        Execute an instruction using the configured model provider.

        Args:
            instruction: Natural language instruction to execute

        Returns:
            Result of the action execution
        """
        try:
            # Use the model provider's act method
            result = self.model_provider.act(
                instruction,
                self.available_actions,
                on_message=lambda msg: None  # We'll capture the response differently
            )

            if self.verbose:
                console.print(Panel(f"Action Result: {result}", title="🤖 AI Agent", border_style="blue"))

            return str(result) if result else "No action result received"

        except Exception as e:
            error_msg = f"Error in AI agent action execution: {e}"
            logger.error(error_msg)
            return f"❌ {error_msg}"

    def execute_instruction(self, instruction: str) -> str:
        """
        Alias for act() method for clearer action-oriented interface.

        Args:
            instruction: Natural language instruction to execute

        Returns:
            Result of the instruction execution
        """
        return self.act(instruction)

    def interactive_action_session(self):
        """
        Start an interactive action execution session.
        Allow users to give instructions and see results.
        """
        console.print(Panel(
            f"🚀 Interactive Action Session Started\n\n"
            f"Agent: {self.agent_name or 'Unnamed'}\n"
            f"Provider: {self.model_provider.__class__.__name__}\n"
            f"Model: {self.model_provider.model_id}\n\n"
            "Give me instructions to execute on your infrastructure.\n"
            "Type 'help' for available actions, 'quit' to exit.",
            title="🤖 Anvyl AI Agent - Action Mode",
            border_style="blue"
        ))

        while True:
            try:
                # Get user instruction
                instruction = console.input("\n[bold cyan]Instruction:[/bold cyan] ")

                if instruction.lower() in ['quit', 'exit', 'q']:
                    console.print("[yellow]Ending interactive session. Goodbye![/yellow]")
                    break
                elif instruction.lower() in ['help', 'h']:
                    self._show_help()
                    continue
                elif instruction.lower() in ['actions', 'a']:
                    self._show_available_actions()
                    continue
                elif not instruction.strip():
                    continue

                # Execute the instruction
                console.print(f"\n🔄 [bold blue]Executing:[/bold blue] {instruction}")
                console.print("⏳ Processing...")

                result = self.act(instruction)

                console.print(f"✅ [bold green]Result:[/bold green]")
                console.print(result)

            except KeyboardInterrupt:
                console.print("\n[yellow]Session interrupted. Type 'quit' to exit.[/yellow]")
            except Exception as e:
                console.print(f"\n❌ [red]Error: {e}[/red]")

    def _show_help(self):
        """Show help information."""
        console.print(Panel(
            "🔧 Available Commands:\n\n"
            "• Type any natural language instruction\n"
            "• 'help' or 'h' - Show this help\n"
            "• 'actions' or 'a' - Show available actions\n"
            "• 'quit' or 'q' - Exit session\n\n"
            "Example Instructions:\n"
            "• 'Show me all hosts'\n"
            "• 'Create a nginx container'\n"
            "• 'List running containers'\n"
            "• 'Get system status'\n"
            "• 'Launch a new agent on host-1'",
            title="Help",
            border_style="yellow"
        ))

    def _show_available_actions(self):
        """Show available actions."""
        table = Table(title="Available Actions")
        table.add_column("Action", style="cyan")
        table.add_column("Description", style="white")

        for action in self.available_actions:
            action_name = action.__name__.replace('_', ' ').title()
            description = action.__doc__ or "No description available"
            # Get first line of docstring
            description = description.split('\n')[0].strip()
            table.add_row(action_name, description)

        console.print(table)

    # Legacy method for backward compatibility
    def chat(self, message: str) -> str:
        """
        Legacy chat method - redirects to act() for backward compatibility.

        Args:
            message: Natural language message/instruction

        Returns:
            Result of the action execution
        """
        console.print("[yellow]Note: chat() is deprecated. Use act() or execute_instruction() instead.[/yellow]")
        return self.act(message)

    def interactive_chat(self):
        """
        Legacy interactive chat method - redirects to interactive_action_session().
        """
        console.print("[yellow]Note: interactive_chat() is deprecated. Use interactive_action_session() instead.[/yellow]")
        return self.interactive_action_session()


def create_ai_agent(model_provider: Union[str, ModelProvider] = "lmstudio",
                   model_id: str = "llama-3.2-1b-instruct-mlx",
                   host: str = "localhost",
                   port: int = 50051,
                   verbose: bool = False,
                   agent_name: Optional[str] = None,
                   **provider_kwargs) -> AnvylAIAgent:
    """
    Create an Anvyl AI agent instance for executing infrastructure actions.

    Args:
        model_provider: Model provider to use ("lmstudio", "ollama", "openai", "anthropic")
                       or a ModelProvider instance
        model_id: Model identifier to use
        host: Anvyl gRPC server host
        port: Anvyl gRPC server port
        verbose: Enable verbose logging
        agent_name: Name of the AI agent
        **provider_kwargs: Additional provider-specific configuration

    Returns:
        Configured AnvylAIAgent instance ready to execute actions

    Examples:
        # LM Studio (default)
        agent = create_ai_agent()

        # Ollama
        agent = create_ai_agent("ollama", "llama3.2", host="localhost", port=11434)

        # OpenAI
        agent = create_ai_agent("openai", "gpt-4o-mini", api_key="your-key")

        # Anthropic
        agent = create_ai_agent("anthropic", "claude-3-haiku-20240307", api_key="your-key")

        # Execute actions
        result = agent.act("Show me all hosts")
        result = agent.execute_instruction("Create a nginx container")
    """
    return AnvylAIAgent(model_provider, model_id, host, port, verbose, agent_name, **provider_kwargs)