"""
Anvyl AI Agent - Model Provider Abstraction for AI-powered infrastructure management

This module provides AI agents with access to Anvyl's infrastructure service through configurable
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

from .infrastructure_service import get_infrastructure_service
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
                 model_id: str = "deepseek/deepseek-r1-0528-qwen3-8b",
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
            host: Infrastructure service host
            port: Infrastructure service port
            verbose: Enable verbose logging
            agent_name: Name of the AI agent
            **provider_kwargs: Additional provider-specific configuration
        """
        self.host = host
        self.port = port
        self.verbose = verbose
        self.agent_name = agent_name

        # Initialize infrastructure service
        self.infrastructure_service = get_infrastructure_service()

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
            hosts = self.infrastructure_service.list_hosts()
            return {
                "success": True,
                "hosts": hosts
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _add_host(self, name: str, ip: str, os: str = "", tags: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Add a new host."""
        try:
            host = self.infrastructure_service.add_host(name, ip, os, tags)
            if host:
                return {
                    "success": True,
                    "host": host
                }
            return {"success": False, "error": "Failed to add host"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_host_metrics(self, host_id: str, **kwargs) -> Dict[str, Any]:
        """Get host metrics."""
        try:
            metrics = self.infrastructure_service.get_host_metrics(host_id)
            if metrics:
                return {
                    "success": True,
                    "metrics": metrics
                }
            return {"success": False, "error": "Failed to get metrics"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _list_containers(self, host_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """List containers."""
        try:
            containers = self.infrastructure_service.list_containers(host_id)
            return {
                "success": True,
                "containers": containers
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_container(self, name: str, image: str, host_id: Optional[str] = None,
                         ports: Optional[List[str]] = None, volumes: Optional[List[str]] = None,
                         environment: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Create a container."""
        try:
            container = self.infrastructure_service.add_container(
                name=name,
                image=image,
                host_id=host_id,
                ports=ports,
                volumes=volumes,
                environment=environment
            )
            if container:
                return {
                    "success": True,
                    "container": container
                }
            return {"success": False, "error": "Failed to create container"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _stop_container(self, container_id: str, timeout: int = 10, **kwargs) -> Dict[str, Any]:
        """Stop a container."""
        try:
            success = self.infrastructure_service.stop_container(container_id, timeout)
            return {
                "success": success,
                "message": "Container stopped successfully" if success else "Failed to stop container"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_container_logs(self, container_id: str, tail: int = 100, **kwargs) -> Dict[str, Any]:
        """Get container logs."""
        try:
            logs = self.infrastructure_service.get_logs(container_id, tail=tail)
            if logs:
                return {
                    "success": True,
                    "logs": logs
                }
            return {"success": False, "error": "Failed to get logs"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _exec_container_command(self, container_id: str, command: List[str], **kwargs) -> Dict[str, Any]:
        """Execute command in container."""
        try:
            result = self.infrastructure_service.exec_command(container_id, command)
            if result:
                return {
                    "success": result["success"],
                    "output": result["output"],
                    "exit_code": result["exit_code"]
                }
            return {"success": False, "error": "Failed to execute command"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _list_agents(self, host_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """List agents."""
        try:
            agents = self.infrastructure_service.list_agents(host_id)
            return {
                "success": True,
                "agents": [
                    {
                        "id": agent["id"],
                        "name": agent["name"],
                        "host_id": agent["host_id"],
                        "entrypoint": agent["entrypoint"],
                        "working_directory": agent["working_directory"],
                        "status": agent["status"],
                        "container_id": agent["container_id"],
                        "persistent": agent["persistent"],
                        "started_at": agent["started_at"],
                        "stopped_at": agent["stopped_at"],
                        "exit_code": agent["exit_code"]
                    }
                    for agent in agents
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _launch_agent(self, name: str, host_id: str, entrypoint: str,
                     environment: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Launch an agent."""
        try:
            agent = self.infrastructure_service.launch_agent(
                name=name,
                host_id=host_id,
                entrypoint=entrypoint,
                env=environment
            )
            if agent:
                return {
                    "success": True,
                    "agent": agent
                }
            return {"success": False, "error": "Failed to launch agent"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _stop_agent(self, agent_id: str, **kwargs) -> Dict[str, Any]:
        """Stop an agent."""
        try:
            success = self.infrastructure_service.stop_agent(agent_id)
            return {
                "success": success,
                "message": "Agent stopped successfully" if success else "Failed to stop agent"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_system_status(self, **kwargs) -> Dict[str, Any]:
        """Get overall system status."""
        try:
            hosts = self.infrastructure_service.list_hosts()
            containers = self.infrastructure_service.list_containers()
            agents = self.infrastructure_service.list_agents()

            return {
                "success": True,
                "status": {
                    "hosts": {
                        "total": len(hosts),
                        "online": len([h for h in hosts if h.get("status") == "online"]),
                        "offline": len([h for h in hosts if h.get("status") == "offline"])
                    },
                    "containers": {
                        "total": len(containers),
                        "running": len([c for c in containers if c.get("status") == "running"]),
                        "stopped": len([c for c in containers if c.get("status") == "stopped"])
                    },
                    "agents": {
                        "total": len(agents),
                        "running": len([a for a in agents if a.get("status") == "running"]),
                        "stopped": len([a for a in agents if a.get("status") == "stopped"])
                    }
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_ui_status(self, **kwargs) -> Dict[str, Any]:
        """Get UI status."""
        try:
            # Check if UI containers are running
            containers = self.infrastructure_service.list_containers()
            ui_containers = [c for c in containers if "ui" in c.get("name", "").lower() or "frontend" in c.get("name", "").lower()]

            return {
                "success": True,
                "ui_status": {
                    "containers": len(ui_containers),
                    "running": len([c for c in ui_containers if c.get("status") == "running"])
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _discover_agents(self, **kwargs) -> Dict[str, Any]:
        """Discover available agents."""
        try:
            # Import agent manager to get agent configurations
            from .agent_manager import get_agent_manager

            manager = get_agent_manager()
            agent_configs = manager.list_agents()

            return {
                "success": True,
                "agents": [
                    {
                        "name": agent["name"],
                        "provider": agent["provider"],
                        "model_id": agent["model_id"],
                        "status": agent["status"],
                        "running": agent["running"]
                    }
                    for agent in agent_configs
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _route_to_agent(self, agent_name: str, command: str, **kwargs) -> Dict[str, Any]:
        """Route a command to a specific agent."""
        try:
            result = self.infrastructure_service.execute_agent_instruction(agent_name, command)
            if result:
                return {
                    "success": result["success"],
                    "result": result["result"],
                    "error_message": result.get("error_message", "")
                }
            return {"success": False, "error": "Failed to execute instruction"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def act(self, instruction: str) -> str:
        """
        Execute an action based on natural language instruction.

        Args:
            instruction: Natural language instruction

        Returns:
            Result of the action execution
        """
        try:
            # Use the model provider to determine the action
            response = self.model_provider.generate_response(
                instruction=instruction,
                available_actions=self.get_available_actions(),
                context="You are an AI agent that can execute infrastructure management actions."
            )

            # Parse the response to determine the action
            action_name, action_args = self._parse_action_response(response, instruction)

            if action_name:
                # Execute the action
                action_func = next((action for action in self.available_actions
                                  if action.__name__.replace('_', ' ').title() == action_name), None)

                if action_func:
                    result = action_func(**action_args)
                    return self._format_action_result(result)
                else:
                    return f"❌ Unknown action: {action_name}"
            else:
                return f"❌ Could not determine action from instruction: {instruction}"

        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return f"❌ Error executing action: {str(e)}"

    def execute_instruction(self, instruction: str) -> str:
        """Execute an instruction and return the result."""
        return self.act(instruction)

    def interactive_action_session(self):
        """Start an interactive session for executing actions."""
        console.print(Panel.fit(
            "[bold blue]Anvyl AI Agent - Interactive Action Session[/bold blue]\n"
            "Type 'help' for available commands, 'quit' to exit.",
            border_style="blue"
        ))

        while True:
            try:
                instruction = console.input("\n[bold green]Action:[/bold green] ").strip()

                if instruction.lower() in ['quit', 'exit', 'q']:
                    console.print("👋 Goodbye!")
                    break
                elif instruction.lower() == 'help':
                    self._show_help()
                elif instruction.lower() == 'actions':
                    self._show_available_actions()
                elif instruction:
                    console.print(f"\n[bold yellow]Executing:[/bold yellow] {instruction}")
                    result = self.act(instruction)
                    console.print(f"\n[bold cyan]Result:[/bold cyan]\n{result}")
                else:
                    continue

            except KeyboardInterrupt:
                console.print("\n👋 Goodbye!")
                break
            except Exception as e:
                console.print(f"\n❌ Error: {e}")

    def _show_help(self):
        """Show help information."""
        help_text = """
[bold]Available Commands:[/bold]
• help - Show this help message
• actions - Show available actions
• quit/exit/q - Exit the session
• [any instruction] - Execute an action

[bold]Example Instructions:[/bold]
• "List all hosts"
• "Show running containers"
• "Get system status"
• "Launch a new agent"
        """
        console.print(Panel(help_text, title="Help", border_style="green"))

    def _show_available_actions(self):
        """Show available actions."""
        actions = self.get_available_actions()

        table = Table(title="Available Actions")
        table.add_column("Action", style="cyan")
        table.add_column("Description", style="white")

        for action in actions:
            table.add_row(action, f"Execute {action.lower()}")

        console.print(table)

    def _parse_action_response(self, response: str, original_instruction: str) -> tuple:
        """Parse the model response to determine action and arguments."""
        # Simple parsing - in a real implementation, you'd want more sophisticated parsing
        response_lower = response.lower()

        # Map common instructions to actions
        action_mapping = {
            "list hosts": "List Hosts",
            "show hosts": "List Hosts",
            "get hosts": "List Hosts",
            "add host": "Add Host",
            "create host": "Add Host",
            "host metrics": "Get Host Metrics",
            "list containers": "List Containers",
            "show containers": "List Containers",
            "get containers": "List Containers",
            "create container": "Create Container",
            "add container": "Create Container",
            "stop container": "Stop Container",
            "container logs": "Get Container Logs",
            "exec container": "Exec Container Command",
            "list agents": "List Agents",
            "show agents": "List Agents",
            "get agents": "List Agents",
            "launch agent": "Launch Agent",
            "start agent": "Launch Agent",
            "stop agent": "Stop Agent",
            "system status": "Get System Status",
            "status": "Get System Status",
            "ui status": "Get Ui Status",
            "discover agents": "Discover Agents",
            "route to agent": "Route To Agent"
        }

        for instruction_pattern, action_name in action_mapping.items():
            if instruction_pattern in response_lower or instruction_pattern in original_instruction.lower():
                return action_name, {}

        return None, {}

    def _format_action_result(self, result: Dict[str, Any]) -> str:
        """Format action result for display."""
        if not result.get("success", False):
            return f"❌ Error: {result.get('error', 'Unknown error')}"

        # Format based on action type
        if "hosts" in result:
            return self._format_hosts_result(result["hosts"])
        elif "containers" in result:
            return self._format_containers_result(result["containers"])
        elif "agents" in result:
            return self._format_agents_result(result["agents"])
        elif "status" in result:
            return self._format_status_result(result["status"])
        elif "message" in result:
            return f"✅ {result['message']}"
        else:
            return f"✅ Action completed successfully: {result}"

    def _format_hosts_result(self, hosts: List[Dict[str, Any]]) -> str:
        """Format hosts result."""
        if not hosts:
            return "📋 No hosts found"

        result = "📋 Hosts:\n"
        for host in hosts:
            status_emoji = "🟢" if host.get("status") == "online" else "🔴"
            result += f"  {status_emoji} {host.get('name', 'Unknown')} ({host.get('ip', 'Unknown')}) - {host.get('status', 'Unknown')}\n"
        return result

    def _format_containers_result(self, containers: List[Dict[str, Any]]) -> str:
        """Format containers result."""
        if not containers:
            return "📦 No containers found"

        result = "📦 Containers:\n"
        for container in containers:
            status_emoji = "🟢" if container.get("status") == "running" else "🔴"
            result += f"  {status_emoji} {container.get('name', 'Unknown')} ({container.get('image', 'Unknown')}) - {container.get('status', 'Unknown')}\n"
        return result

    def _format_agents_result(self, agents: List[Dict[str, Any]]) -> str:
        """Format agents result."""
        if not agents:
            return "🤖 No agents found"

        result = "🤖 Agents:\n"
        for agent in agents:
            status_emoji = "🟢" if agent.get("status") == "running" else "🔴"
            result += f"  {status_emoji} {agent.get('name', 'Unknown')} - {agent.get('status', 'Unknown')}\n"
        return result

    def _format_status_result(self, status: Dict[str, Any]) -> str:
        """Format status result."""
        result = "📊 System Status:\n"

        if "hosts" in status:
            hosts = status["hosts"]
            result += f"  🖥️  Hosts: {hosts['total']} total, {hosts['online']} online, {hosts['offline']} offline\n"

        if "containers" in status:
            containers = status["containers"]
            result += f"  📦 Containers: {containers['total']} total, {containers['running']} running, {containers['stopped']} stopped\n"

        if "agents" in status:
            agents = status["agents"]
            result += f"  🤖 Agents: {agents['total']} total, {agents['running']} running, {agents['stopped']} stopped\n"

        return result

    def chat(self, message: str) -> str:
        """Chat with the AI agent."""
        return self.act(message)

    def interactive_chat(self):
        """Start an interactive chat session."""
        console.print(Panel.fit(
            "[bold blue]Anvyl AI Agent - Interactive Chat[/bold blue]\n"
            "Type 'quit' to exit.",
            border_style="blue"
        ))

        while True:
            try:
                message = console.input("\n[bold green]You:[/bold green] ").strip()

                if message.lower() in ['quit', 'exit', 'q']:
                    console.print("👋 Goodbye!")
                    break
                elif message:
                    response = self.chat(message)
                    console.print(f"\n[bold cyan]Agent:[/bold cyan] {response}")
                else:
                    continue

            except KeyboardInterrupt:
                console.print("\n👋 Goodbye!")
                break
            except Exception as e:
                console.print(f"\n❌ Error: {e}")


def create_ai_agent(model_provider: Union[str, ModelProvider] = "lmstudio",
                   model_id: str = "deepseek/deepseek-r1-0528-qwen3-8b",
                   host: str = "localhost",
                   port: int = 50051,
                   verbose: bool = False,
                   agent_name: Optional[str] = None,
                   **provider_kwargs) -> AnvylAIAgent:
    """
    Create an AI agent instance.

    Args:
        model_provider: Model provider to use
        model_id: Model identifier
        host: Infrastructure service host
        port: Infrastructure service port
        verbose: Enable verbose logging
        agent_name: Name of the AI agent
        **provider_kwargs: Additional provider-specific configuration

    Returns:
        AnvylAIAgent instance
    """
    return AnvylAIAgent(
        model_provider=model_provider,
        model_id=model_id,
        host=host,
        port=port,
        verbose=verbose,
        agent_name=agent_name,
        **provider_kwargs
    )