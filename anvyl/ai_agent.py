"""
Anvyl AI Agent - LMStudio integration for AI-powered infrastructure management

This module provides AI agents with access to Anvyl's gRPC client through LMStudio's act() function,
allowing natural language interaction with the infrastructure orchestrator.
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

logger = logging.getLogger(__name__)
console = Console()

import lmstudio as lms


class AnvylAIAgent:
    """
    AI Agent that uses LMStudio's act() function to interact with Anvyl infrastructure.
    
    This agent provides natural language access to:
    - Host management (list, add, monitor)
    - Container management (create, stop, logs, exec)
    - Agent management (launch, stop, monitor)
    - System status and monitoring
    """
    
    def __init__(self, 
                 model_id: str = "llama-3.2-1b-instruct-mlx",
                 host: str = "localhost", 
                 port: int = 50051,
                 verbose: bool = False,
                 agent_name: Optional[str] = None):
        """
        Initialize the AI agent.
        
        Args:
            model_id: LMStudio model to use for AI interactions
            host: Anvyl gRPC server host
            port: Anvyl gRPC server port
            verbose: Enable verbose logging
            agent_name: Name of the AI agent
        """
        self.model_id = model_id
        self.host = host
        self.port = port
        self.verbose = verbose
        self.agent_name = agent_name
        
        # Initialize gRPC client
        self.client = AnvylClient(host, port)
        if not self.client.connect():
            raise ConnectionError(f"Failed to connect to Anvyl server at {host}:{port}")
        
        # Initialize LMStudio model
        try:
            self.model = lms.llm(model_id)
            logger.info(f"Connected to LMStudio with model: {model_id}")
        except Exception as e:
            logger.error(f"Failed to connect to LMStudio: {e}")
            raise ConnectionError("LMStudio is not available. Please ensure LMStudio is running.")
        
        # Define available functions for the AI agent
        self.functions = [
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
                     use_container: bool = False, environment: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Launch an agent."""
        try:
            agent = self.client.launch_agent(
                name=name,
                host_id=host_id,
                entrypoint=entrypoint,
                use_container=use_container,
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
    
    def chat(self, message: str) -> str:
        """
        Chat with the AI agent using LMStudio's act() function.
        
        Args:
            message: Natural language message from user
            
        Returns:
            AI response with action results
        """
        try:
            # Use LMStudio's act() function with the model instance
            response = self.model.act(
                message,
                self.functions,
                on_message=lambda msg: None  # We'll capture the response differently
            )
            
            if self.verbose:
                console.print(Panel(f"AI Response: {response}", title="🤖 AI Agent", border_style="blue"))
            
            return str(response) if response else "No response received"
            
        except Exception as e:
            error_msg = f"Error in AI agent chat: {e}"
            logger.error(error_msg)
            return f"❌ {error_msg}"
    
    def interactive_chat(self):
        """Start an interactive chat session with the AI agent."""
        console.print(Panel(
            "🤖 Anvyl AI Agent Ready!\n\n"
            "I can help you manage your Anvyl infrastructure using natural language.\n"
            "Try commands like:\n"
            "• 'Show me all hosts'\n"
            "• 'Create a container with nginx'\n"
            "• 'What's the system status?'\n"
            "• 'Stop all containers'\n\n"
            "Type 'quit' or 'exit' to end the session.",
            title="🚀 Anvyl AI Agent", 
            border_style="green"
        ))
        
        while True:
            try:
                user_input = console.input("\n[bold cyan]You:[/bold cyan] ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    console.print("\n👋 Goodbye! Thanks for using Anvyl AI Agent.")
                    break
                
                if not user_input:
                    continue
                
                console.print("\n[bold blue]AI:[/bold blue] Thinking...")
                response = self.chat(user_input)
                console.print(f"\n[bold blue]AI:[/bold blue] {response}")
                
            except KeyboardInterrupt:
                console.print("\n\n👋 Goodbye! Thanks for using Anvyl AI Agent.")
                break
            except Exception as e:
                console.print(f"\n❌ Error: {e}")


def create_ai_agent(model_id: str = "llama-3.2-1b-instruct-mlx", 
                   host: str = "localhost", 
                   port: int = 50051,
                   verbose: bool = False,
                   agent_name: Optional[str] = None) -> AnvylAIAgent:
    """
    Create an Anvyl AI agent instance.
    
    Args:
        model_id: LMStudio model to use
        host: Anvyl gRPC server host
        port: Anvyl gRPC server port
        verbose: Enable verbose logging
        agent_name: Name of the AI agent
        
    Returns:
        Configured AnvylAIAgent instance
    """
    return AnvylAIAgent(model_id, host, port, verbose, agent_name=agent_name) 