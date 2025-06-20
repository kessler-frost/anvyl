"""
MCP Client Implementation

This module provides the MCP client that can connect to MCP servers
and use their tools, resources, and prompts.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
import uuid

from .types import (
    Tool, Resource, Prompt, MCPMessage, MCPRequest, MCPResponse,
    ClientCapabilities, InitializeParams, InitializeResult,
    ToolCallRequest, ToolCallResult, ResourceReadRequest, ResourceReadResult,
    PromptGetRequest, PromptGetResult, METHODS, PROTOCOL_VERSION
)
from .transport import MCPTransport

logger = logging.getLogger(__name__)


class MCPClient:
    """Model Context Protocol Client implementation"""
    
    def __init__(self, name: str = "anvyl-mcp-client", version: str = "0.1.0"):
        self.name = name
        self.version = version
        self.transport: Optional[MCPTransport] = None
        self.capabilities = ClientCapabilities()
        
        # Server capabilities and resources
        self.server_capabilities: Optional[Dict[str, Any]] = None
        self.available_tools: Dict[str, Tool] = {}
        self.available_resources: Dict[str, Resource] = {}
        self.available_prompts: Dict[str, Prompt] = {}
        
        # Connection state
        self.connected = False
        self.initialized = False
        
        # Pending requests
        self.pending_requests: Dict[str, asyncio.Future] = {}
    
    async def connect(self, transport: MCPTransport) -> bool:
        """Connect to an MCP server using the given transport"""
        self.transport = transport
        
        try:
            # Send initialization request
            init_params = InitializeParams(
                protocol_version=PROTOCOL_VERSION,
                capabilities=self.capabilities,
                client_info={"name": self.name, "version": self.version}
            )
            
            init_request = MCPRequest(
                id=str(uuid.uuid4()),
                method=METHODS["INITIALIZE"],
                params=init_params.to_dict()
            )
            
            logger.info("Sending initialization request")
            await transport.send_message(init_request)
            
            # Wait for initialization response
            response = await transport.receive_message()
            if response and response.result:
                init_result = InitializeResult(**response.result)
                self.server_capabilities = init_result.capabilities.to_dict()
                logger.info(f"Connected to server: {init_result.server_info}")
                
                # Send initialized notification
                initialized_notification = MCPMessage(
                    id=str(uuid.uuid4()),
                    type="notification",
                    method=METHODS["INITIALIZED"]
                )
                await transport.send_message(initialized_notification)
                
                self.connected = True
                self.initialized = True
                
                # Load server capabilities
                await self._load_server_capabilities()
                
                return True
            else:
                logger.error("Failed to initialize connection")
                return False
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def _load_server_capabilities(self):
        """Load available tools, resources, and prompts from the server"""
        try:
            # Load tools
            if self.server_capabilities.get("tools", False):
                tools = await self.list_tools()
                for tool_data in tools:
                    tool = Tool(**tool_data)
                    self.available_tools[tool.name] = tool
                logger.info(f"Loaded {len(self.available_tools)} tools")
            
            # Load resources
            if self.server_capabilities.get("resources", False):
                resources = await self.list_resources()
                for resource_data in resources:
                    resource = Resource(**resource_data)
                    self.available_resources[resource.uri] = resource
                logger.info(f"Loaded {len(self.available_resources)} resources")
            
            # Load prompts
            if self.server_capabilities.get("prompts", False):
                prompts = await self.list_prompts()
                for prompt_data in prompts:
                    prompt = Prompt(**prompt_data)
                    self.available_prompts[prompt.name] = prompt
                logger.info(f"Loaded {len(self.available_prompts)} prompts")
                
        except Exception as e:
            logger.error(f"Error loading server capabilities: {e}")
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Any:
        """Send a request and wait for response"""
        if not self.connected:
            raise RuntimeError("Client not connected")
        
        request_id = str(uuid.uuid4())
        request = MCPRequest(
            id=request_id,
            method=method,
            params=params or {}
        )
        
        # Create future for response
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        try:
            await self.transport.send_message(request)
            logger.debug(f"Sent request: {method}")
            
            # Wait for response (with timeout)
            response = await asyncio.wait_for(
                self._wait_for_response(request_id),
                timeout=30.0
            )
            
            if response.error:
                raise Exception(f"Server error: {response.error}")
            
            return response.result
            
        except asyncio.TimeoutError:
            logger.error(f"Request timeout: {method}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {method}, error: {e}")
            raise
        finally:
            self.pending_requests.pop(request_id, None)
    
    async def _wait_for_response(self, request_id: str) -> MCPResponse:
        """Wait for a specific response"""
        while True:
            message = await self.transport.receive_message()
            if message and message.id == request_id:
                return message
            # Handle other messages or notifications here if needed
            await asyncio.sleep(0.01)
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the server"""
        result = await self._send_request(METHODS["LIST_TOOLS"])
        return result.get("tools", [])
    
    async def call_tool(self, name: str, arguments: Dict[str, Any] = None) -> str:
        """Call a tool on the server"""
        if name not in self.available_tools:
            raise ValueError(f"Tool '{name}' not available")
        
        params = ToolCallRequest(name=name, arguments=arguments or {}).to_dict()
        result = await self._send_request(METHODS["CALL_TOOL"], params)
        
        tool_result = ToolCallResult(**result)
        if tool_result.is_error:
            raise Exception(f"Tool error: {tool_result.content}")
        
        return tool_result.content
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from the server"""
        result = await self._send_request(METHODS["LIST_RESOURCES"])
        return result.get("resources", [])
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource from the server"""
        if uri not in self.available_resources:
            raise ValueError(f"Resource '{uri}' not available")
        
        params = ResourceReadRequest(uri=uri).to_dict()
        result = await self._send_request(METHODS["READ_RESOURCE"], params)
        
        resource_result = ResourceReadResult(**result)
        return resource_result.content
    
    async def list_prompts(self) -> List[Dict[str, Any]]:
        """List available prompts from the server"""
        result = await self._send_request(METHODS["LIST_PROMPTS"])
        return result.get("prompts", [])
    
    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None) -> str:
        """Get a prompt from the server"""
        if name not in self.available_prompts:
            raise ValueError(f"Prompt '{name}' not available")
        
        params = PromptGetRequest(name=name, arguments=arguments or {}).to_dict()
        result = await self._send_request(METHODS["GET_PROMPT"], params)
        
        prompt_result = PromptGetResult(**result)
        return prompt_result.content
    
    async def ping(self) -> Dict[str, Any]:
        """Ping the server"""
        return await self._send_request(METHODS["PING"])
    
    async def disconnect(self):
        """Disconnect from the server"""
        if self.transport:
            await self.transport.close()
        
        self.connected = False
        self.initialized = False
        self.transport = None
        
        # Clear server data
        self.server_capabilities = None
        self.available_tools.clear()
        self.available_resources.clear()
        self.available_prompts.clear()
        
        logger.info("Disconnected from MCP server")
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "connected": self.connected,
            "initialized": self.initialized,
            "capabilities": self.server_capabilities,
            "tools": list(self.available_tools.keys()),
            "resources": list(self.available_resources.keys()),
            "prompts": list(self.available_prompts.keys())
        }


class SimpleMCPClient:
    """Simplified MCP client for basic use cases"""
    
    def __init__(self):
        self.client = MCPClient()
    
    async def connect_to_server(self, command: str, args: List[str] = None) -> bool:
        """Connect to an MCP server by starting a subprocess"""
        from .transport import TransportFactory
        
        try:
            transport = TransportFactory.create_stdio_transport(command, args or [])
            return await self.client.connect(transport)
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return False
    
    async def use_tool(self, tool_name: str, **kwargs) -> str:
        """Use a tool with keyword arguments"""
        return await self.client.call_tool(tool_name, kwargs)
    
    async def read_resource(self, resource_uri: str) -> str:
        """Read a resource"""
        return await self.client.read_resource(resource_uri)
    
    async def get_prompt(self, prompt_name: str, **kwargs) -> str:
        """Get a prompt with keyword arguments"""
        return await self.client.get_prompt(prompt_name, kwargs)
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return list(self.client.available_tools.keys())
    
    def get_available_resources(self) -> List[str]:
        """Get list of available resource URIs"""
        return list(self.client.available_resources.keys())
    
    def get_available_prompts(self) -> List[str]:
        """Get list of available prompt names"""
        return list(self.client.available_prompts.keys())
    
    async def close(self):
        """Close the connection"""
        await self.client.disconnect()