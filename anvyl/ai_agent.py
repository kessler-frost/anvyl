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

# Conditional LMStudio import
try:
    import lmstudio
    LMSTUDIO_AVAILABLE = True
except ImportError:
    LMSTUDIO_AVAILABLE = False
    lmstudio = None


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
        
        # Initialize LMStudio client
        if not LMSTUDIO_AVAILABLE:
            raise ImportError("LMStudio is not available. Install with: pip install lmstudio")
        
        try:
            self.lms_client = lmstudio.get_default_client()
            logger.info(f"Connected to LMStudio with model: {model_id}")
        except Exception as e:
            logger.error(f"Failed to connect to LMStudio: {e}")
            raise ConnectionError("LMStudio is not available. Please ensure LMStudio is running.")
        
        # Define available functions for the AI agent
        self.functions = {
            "list_hosts": self._list_hosts,
            "add_host": self._add_host,
            "get_host_metrics": self._get_host_metrics,
            "list_containers": self._list_containers,
            "create_container": self._create_container,
            "stop_container": self._stop_container,
            "get_container_logs": self._get_container_logs,
            "exec_container_command": self._exec_container_command,
            "list_agents": self._list_agents,
            "launch_agent": self._launch_agent,
            "stop_agent": self._stop_agent,
            "get_system_status": self._get_system_status,
            "get_ui_status": self._get_ui_status,
        }
        
        # Function descriptions for LMStudio
        self.function_descriptions = {
            "list_hosts": {
                "description": "List all registered hosts in the Anvyl infrastructure",
                "parameters": {}
            },
            "add_host": {
                "description": "Add a new host to the Anvyl infrastructure",
                "parameters": {
                    "name": {"type": "string", "description": "Host name"},
                    "ip": {"type": "string", "description": "Host IP address"},
                    "os": {"type": "string", "description": "Operating system (optional)"},
                    "tags": {"type": "array", "description": "Host tags (optional)"}
                }
            },
            "get_host_metrics": {
                "description": "Get resource metrics for a specific host",
                "parameters": {
                    "host_id": {"type": "string", "description": "Host ID to get metrics for"}
                }
            },
            "list_containers": {
                "description": "List all containers in the Anvyl infrastructure",
                "parameters": {
                    "host_id": {"type": "string", "description": "Filter by host ID (optional)"}
                }
            },
            "create_container": {
                "description": "Create a new container",
                "parameters": {
                    "name": {"type": "string", "description": "Container name"},
                    "image": {"type": "string", "description": "Docker image"},
                    "host_id": {"type": "string", "description": "Target host ID (optional)"},
                    "ports": {"type": "array", "description": "Port mappings (optional)"},
                    "volumes": {"type": "array", "description": "Volume mounts (optional)"},
                    "environment": {"type": "array", "description": "Environment variables (optional)"}
                }
            },
            "stop_container": {
                "description": "Stop a running container",
                "parameters": {
                    "container_id": {"type": "string", "description": "Container ID to stop"},
                    "timeout": {"type": "integer", "description": "Stop timeout in seconds (optional)"}
                }
            },
            "get_container_logs": {
                "description": "Get logs from a container",
                "parameters": {
                    "container_id": {"type": "string", "description": "Container ID"},
                    "tail": {"type": "integer", "description": "Number of lines to show (optional)"}
                }
            },
            "exec_container_command": {
                "description": "Execute a command inside a container",
                "parameters": {
                    "container_id": {"type": "string", "description": "Container ID"},
                    "command": {"type": "array", "description": "Command to execute"}
                }
            },
            "list_agents": {
                "description": "List all agents in the Anvyl infrastructure",
                "parameters": {
                    "host_id": {"type": "string", "description": "Filter by host ID (optional)"}
                }
            },
            "launch_agent": {
                "description": "Launch a new agent",
                "parameters": {
                    "name": {"type": "string", "description": "Agent name"},
                    "host_id": {"type": "string", "description": "Target host ID"},
                    "entrypoint": {"type": "string", "description": "Agent entrypoint script"},
                    "use_container": {"type": "boolean", "description": "Run in container (optional)"},
                    "environment": {"type": "array", "description": "Environment variables (optional)"}
                }
            },
            "stop_agent": {
                "description": "Stop a running agent",
                "parameters": {
                    "agent_id": {"type": "string", "description": "Agent ID to stop"}
                }
            },
            "get_system_status": {
                "description": "Get overall system status including hosts, containers, and agents",
                "parameters": {}
            },
            "get_ui_status": {
                "description": "Get status of the Anvyl UI stack (frontend, backend, gRPC server)",
                "parameters": {}
            }
        }
    
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
    
    def _add_host(self, name: str, ip: str, os: str = "", tags: List[str] = None, **kwargs) -> Dict[str, Any]:
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
    
    def _list_containers(self, host_id: str = None, **kwargs) -> Dict[str, Any]:
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
    
    def _create_container(self, name: str, image: str, host_id: str = None, 
                         ports: List[str] = None, volumes: List[str] = None, 
                         environment: List[str] = None, **kwargs) -> Dict[str, Any]:
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
    
    def _list_agents(self, host_id: str = None, **kwargs) -> Dict[str, Any]:
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
                     use_container: bool = False, environment: List[str] = None, **kwargs) -> Dict[str, Any]:
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
    
    def chat(self, message: str) -> str:
        """
        Chat with the AI agent using LMStudio's act() function.
        
        Args:
            message: Natural language message from user
            
        Returns:
            AI response with action results
        """
        try:
            # Create system prompt
            agent_name_str = f"Agent name: {self.agent_name}\n" if self.agent_name else ""
            system_prompt = f"""You are an AI assistant that helps manage Anvyl infrastructure. {agent_name_str}You have access to the following functions:

{json.dumps(self.function_descriptions, indent=2)}

When a user asks you to do something, use the appropriate function(s) to accomplish the task. Always provide clear, helpful responses with the results of your actions.

Current Anvyl server: {self.host}:{self.port}
Available model: {self.model_id}

Remember to:
1. Use functions to perform actions
2. Provide clear explanations of what you're doing
3. Show results in a readable format
4. Handle errors gracefully
5. Ask for clarification if needed"""

            # Use LMStudio's act() function
            response = lmstudio.act(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                functions=self.functions,
                function_call="auto"
            )
            
            if self.verbose:
                console.print(Panel(f"AI Response: {response}", title="🤖 AI Agent", border_style="blue"))
            
            return response
            
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
                   agent_name: str = None) -> AnvylAIAgent:
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