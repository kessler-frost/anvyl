"""
MCP Server Implementation

This module provides the MCP server that can expose tools, resources,
and prompts to MCP clients.
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime

from .types import (
    Tool, Resource, Prompt, MCPMessage, MCPRequest, MCPResponse, 
    ServerCapabilities, InitializeParams, InitializeResult,
    ToolCallRequest, ToolCallResult, ResourceReadRequest, ResourceReadResult,
    PromptGetRequest, PromptGetResult, METHODS, PROTOCOL_VERSION
)
from .transport import MCPTransport, MessageHandler

logger = logging.getLogger(__name__)


class MCPServer:
    """Model Context Protocol Server implementation"""
    
    def __init__(self, name: str = "anvyl-mcp-server", version: str = "0.1.0"):
        self.name = name
        self.version = version
        self.transport: Optional[MCPTransport] = None
        self.message_handler = MessageHandler()
        self.capabilities = ServerCapabilities()
        
        # Storage for server capabilities
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        self.prompts: Dict[str, Prompt] = {}
        
        # Handlers for tool calls, resource reads, and prompt gets
        self.tool_handlers: Dict[str, Callable] = {}
        self.resource_handlers: Dict[str, Callable] = {}
        self.prompt_handlers: Dict[str, Callable] = {}
        
        # Initialize default message handlers
        self._setup_message_handlers()
        
        # Server state
        self.initialized = False
        self.running = False
    
    def _setup_message_handlers(self):
        """Set up default message handlers"""
        self.message_handler.register_handler(METHODS["INITIALIZE"], self._handle_initialize)
        self.message_handler.register_handler(METHODS["INITIALIZED"], self._handle_initialized)
        self.message_handler.register_handler(METHODS["LIST_TOOLS"], self._handle_list_tools)
        self.message_handler.register_handler(METHODS["CALL_TOOL"], self._handle_call_tool)
        self.message_handler.register_handler(METHODS["LIST_RESOURCES"], self._handle_list_resources)
        self.message_handler.register_handler(METHODS["READ_RESOURCE"], self._handle_read_resource)
        self.message_handler.register_handler(METHODS["LIST_PROMPTS"], self._handle_list_prompts)
        self.message_handler.register_handler(METHODS["GET_PROMPT"], self._handle_get_prompt)
        self.message_handler.register_handler(METHODS["PING"], self._handle_ping)
    
    def add_tool(self, tool: Tool, handler: Callable):
        """Add a tool to the server"""
        self.tools[tool.name] = tool
        self.tool_handlers[tool.name] = handler
        self.capabilities.tools = True
        logger.info(f"Added tool: {tool.name}")
    
    def add_resource(self, resource: Resource, handler: Callable):
        """Add a resource to the server"""
        self.resources[resource.uri] = resource
        self.resource_handlers[resource.uri] = handler
        self.capabilities.resources = True
        logger.info(f"Added resource: {resource.uri}")
    
    def add_prompt(self, prompt: Prompt, handler: Callable):
        """Add a prompt to the server"""
        self.prompts[prompt.name] = prompt
        self.prompt_handlers[prompt.name] = handler
        self.capabilities.prompts = True
        logger.info(f"Added prompt: {prompt.name}")
    
    def tool(self, name: str, description: str, parameters: Dict[str, Any], required: List[str] = None):
        """Decorator for registering tools"""
        def decorator(func: Callable):
            tool = Tool(name=name, description=description, parameters=parameters, required=required or [])
            self.add_tool(tool, func)
            return func
        return decorator
    
    def resource(self, uri: str, name: str, description: str, mime_type: str = "text/plain"):
        """Decorator for registering resources"""
        def decorator(func: Callable):
            resource = Resource(uri=uri, name=name, description=description, mime_type=mime_type)
            self.add_resource(resource, func)
            return func
        return decorator
    
    def prompt(self, name: str, description: str, template: str, parameters: Dict[str, Any] = None):
        """Decorator for registering prompts"""
        def decorator(func: Callable):
            prompt = Prompt(name=name, description=description, template=template, parameters=parameters or {})
            self.add_prompt(prompt, func)
            return func
        return decorator
    
    async def _handle_initialize(self, message: MCPMessage) -> MCPResponse:
        """Handle initialization request"""
        logger.info("Handling initialize request")
        
        # Parse initialization parameters
        params = InitializeParams.from_dict(message.params)
        
        # Check protocol version compatibility
        if params.protocol_version not in [PROTOCOL_VERSION]:
            return MCPResponse(
                id=message.id,
                error={"code": -32602, "message": f"Unsupported protocol version: {params.protocol_version}"}
            )
        
        # Create initialization result
        result = InitializeResult(
            protocol_version=PROTOCOL_VERSION,
            capabilities=self.capabilities,
            server_info={"name": self.name, "version": self.version}
        )
        
        return MCPResponse(id=message.id, result=result.to_dict())
    
    async def _handle_initialized(self, message: MCPMessage) -> None:
        """Handle initialized notification"""
        logger.info("Server initialized successfully")
        self.initialized = True
    
    async def _handle_list_tools(self, message: MCPMessage) -> MCPResponse:
        """Handle list tools request"""
        logger.info("Handling list tools request")
        
        tools_list = [tool.to_dict() for tool in self.tools.values()]
        return MCPResponse(id=message.id, result={"tools": tools_list})
    
    async def _handle_call_tool(self, message: MCPMessage) -> MCPResponse:
        """Handle tool call request"""
        logger.info(f"Handling tool call request: {message.params}")
        
        request = ToolCallRequest(**message.params)
        
        if request.name not in self.tool_handlers:
            return MCPResponse(
                id=message.id,
                error={"code": -32601, "message": f"Tool not found: {request.name}"}
            )
        
        try:
            handler = self.tool_handlers[request.name]
            result = await handler(**request.arguments) if asyncio.iscoroutinefunction(handler) else handler(**request.arguments)
            
            tool_result = ToolCallResult(content=str(result), is_error=False)
            return MCPResponse(id=message.id, result=tool_result.to_dict())
        except Exception as e:
            logger.error(f"Error calling tool {request.name}: {e}")
            tool_result = ToolCallResult(content=str(e), is_error=True)
            return MCPResponse(id=message.id, result=tool_result.to_dict())
    
    async def _handle_list_resources(self, message: MCPMessage) -> MCPResponse:
        """Handle list resources request"""
        logger.info("Handling list resources request")
        
        resources_list = [resource.to_dict() for resource in self.resources.values()]
        return MCPResponse(id=message.id, result={"resources": resources_list})
    
    async def _handle_read_resource(self, message: MCPMessage) -> MCPResponse:
        """Handle read resource request"""
        logger.info(f"Handling read resource request: {message.params}")
        
        request = ResourceReadRequest(**message.params)
        
        if request.uri not in self.resource_handlers:
            return MCPResponse(
                id=message.id,
                error={"code": -32601, "message": f"Resource not found: {request.uri}"}
            )
        
        try:
            handler = self.resource_handlers[request.uri]
            content = await handler() if asyncio.iscoroutinefunction(handler) else handler()
            
            resource = self.resources[request.uri]
            result = ResourceReadResult(content=str(content), mime_type=resource.mime_type)
            return MCPResponse(id=message.id, result=result.to_dict())
        except Exception as e:
            logger.error(f"Error reading resource {request.uri}: {e}")
            return MCPResponse(
                id=message.id,
                error={"code": -32603, "message": f"Error reading resource: {str(e)}"}
            )
    
    async def _handle_list_prompts(self, message: MCPMessage) -> MCPResponse:
        """Handle list prompts request"""
        logger.info("Handling list prompts request")
        
        prompts_list = [prompt.to_dict() for prompt in self.prompts.values()]
        return MCPResponse(id=message.id, result={"prompts": prompts_list})
    
    async def _handle_get_prompt(self, message: MCPMessage) -> MCPResponse:
        """Handle get prompt request"""
        logger.info(f"Handling get prompt request: {message.params}")
        
        request = PromptGetRequest(**message.params)
        
        if request.name not in self.prompt_handlers:
            return MCPResponse(
                id=message.id,
                error={"code": -32601, "message": f"Prompt not found: {request.name}"}
            )
        
        try:
            handler = self.prompt_handlers[request.name]
            content = await handler(**request.arguments) if asyncio.iscoroutinefunction(handler) else handler(**request.arguments)
            
            result = PromptGetResult(content=str(content))
            return MCPResponse(id=message.id, result=result.to_dict())
        except Exception as e:
            logger.error(f"Error getting prompt {request.name}: {e}")
            return MCPResponse(
                id=message.id,
                error={"code": -32603, "message": f"Error getting prompt: {str(e)}"}
            )
    
    async def _handle_ping(self, message: MCPMessage) -> MCPResponse:
        """Handle ping request"""
        logger.debug("Handling ping request")
        return MCPResponse(id=message.id, method=METHODS["PONG"], result={"timestamp": datetime.now().isoformat()})
    
    async def run(self, transport: MCPTransport):
        """Run the server with the given transport"""
        self.transport = transport
        self.running = True
        
        logger.info(f"Starting MCP server '{self.name}' v{self.version}")
        
        try:
            while self.running:
                # Receive message from transport
                message = await transport.receive_message()
                if message is None:
                    continue
                
                # Handle the message
                response = await self.message_handler.handle_message(message)
                
                # Send response if there is one
                if response:
                    await transport.send_message(response)
                
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            await transport.close()
    
    async def stop(self):
        """Stop the server"""
        logger.info("Stopping MCP server")
        self.running = False
        if self.transport:
            await self.transport.close()


# Example MCP server with basic tools and resources
class ExampleMCPServer(MCPServer):
    """Example MCP server with basic capabilities"""
    
    def __init__(self):
        super().__init__(name="example-mcp-server", version="0.1.0")
        self._setup_example_capabilities()
    
    def _setup_example_capabilities(self):
        """Set up example tools, resources, and prompts"""
        
        # Example tool: echo
        @self.tool("echo", "Echo the input text", {"text": {"type": "string", "description": "Text to echo"}}, ["text"])
        def echo_tool(text: str) -> str:
            return f"Echo: {text}"
        
        # Example tool: add numbers
        @self.tool("add", "Add two numbers", {
            "a": {"type": "number", "description": "First number"},
            "b": {"type": "number", "description": "Second number"}
        }, ["a", "b"])
        def add_tool(a: float, b: float) -> float:
            return a + b
        
        # Example tool: get system info
        @self.tool("system_info", "Get system information", {}, [])
        def system_info_tool() -> str:
            import platform
            import os
            return f"System: {platform.system()} {platform.release()}, Python: {platform.python_version()}, PID: {os.getpid()}"
        
        # Example resource: server status
        @self.resource("anvyl://server/status", "Server Status", "Current server status information")
        def server_status_resource() -> str:
            return f"Server: {self.name} v{self.version}, Initialized: {self.initialized}, Running: {self.running}"
        
        # Example resource: capabilities
        @self.resource("anvyl://server/capabilities", "Server Capabilities", "Server capability information", "application/json")
        def capabilities_resource() -> str:
            import json
            return json.dumps(self.capabilities.to_dict(), indent=2)
        
        # Example prompt: greeting
        @self.prompt("greeting", "Generate a greeting", "Hello {name}! Welcome to {service}.", {
            "name": {"type": "string", "description": "Name to greet"},
            "service": {"type": "string", "description": "Service name"}
        })
        def greeting_prompt(name: str = "User", service: str = "Anvyl") -> str:
            return f"Hello {name}! Welcome to {service}."
        
        # Example prompt: code review
        @self.prompt("code_review", "Code review template", "Please review this code:\n\n{code}\n\nFocus on: {focus_areas}", {
            "code": {"type": "string", "description": "Code to review"},
            "focus_areas": {"type": "string", "description": "Areas to focus on"}
        })
        def code_review_prompt(code: str, focus_areas: str = "security, performance, maintainability") -> str:
            return f"Please review this code:\n\n{code}\n\nFocus on: {focus_areas}"