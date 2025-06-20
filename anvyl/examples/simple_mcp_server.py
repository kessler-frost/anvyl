#!/usr/bin/env python3
"""
Simple MCP Server Example

This is a standalone example of an MCP server that demonstrates
basic tools, resources, and prompts functionality.
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, Any


class SimpleMCPServer:
    """A simple MCP server implementation for demonstration"""
    
    def __init__(self):
        self.name = "simple-mcp-server"
        self.version = "0.1.0"
        self.initialized = False
        
        # Available capabilities
        self.tools = {
            "echo": {
                "name": "echo",
                "description": "Echo the input text",
                "parameters": {
                    "text": {"type": "string", "description": "Text to echo"}
                },
                "required": ["text"]
            },
            "add": {
                "name": "add", 
                "description": "Add two numbers",
                "parameters": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                "required": ["a", "b"]
            },
            "get_time": {
                "name": "get_time",
                "description": "Get current time",
                "parameters": {},
                "required": []
            }
        }
        
        self.resources = {
            "server://status": {
                "uri": "server://status",
                "name": "Server Status",
                "description": "Current server status",
                "mime_type": "text/plain"
            },
            "server://tools": {
                "uri": "server://tools", 
                "name": "Available Tools",
                "description": "List of available tools",
                "mime_type": "application/json"
            }
        }
        
        self.prompts = {
            "greeting": {
                "name": "greeting",
                "description": "Generate a greeting",
                "template": "Hello {name}! Welcome to {service}.",
                "parameters": {
                    "name": {"type": "string", "description": "Name to greet"},
                    "service": {"type": "string", "description": "Service name"}
                }
            }
        }
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP messages"""
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        if method == "initialize":
            return await self._handle_initialize(msg_id, params)
        elif method == "initialized":
            self.initialized = True
            return None  # No response needed for notifications
        elif method == "tools/list":
            return await self._handle_list_tools(msg_id)
        elif method == "tools/call":
            return await self._handle_call_tool(msg_id, params)
        elif method == "resources/list":
            return await self._handle_list_resources(msg_id)
        elif method == "resources/read":
            return await self._handle_read_resource(msg_id, params)
        elif method == "prompts/list":
            return await self._handle_list_prompts(msg_id)
        elif method == "prompts/get":
            return await self._handle_get_prompt(msg_id, params)
        elif method == "ping":
            return await self._handle_ping(msg_id)
        else:
            return {
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }
    
    async def _handle_initialize(self, msg_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request"""
        return {
            "id": msg_id,
            "result": {
                "protocol_version": "2024-11-05",
                "capabilities": {
                    "tools": True,
                    "resources": True,
                    "prompts": True
                },
                "server_info": {
                    "name": self.name,
                    "version": self.version
                }
            }
        }
    
    async def _handle_list_tools(self, msg_id: str) -> Dict[str, Any]:
        """Handle list tools request"""
        return {
            "id": msg_id,
            "result": {"tools": list(self.tools.values())}
        }
    
    async def _handle_call_tool(self, msg_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call request"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if name not in self.tools:
            return {
                "id": msg_id,
                "error": {"code": -32601, "message": f"Tool not found: {name}"}
            }
        
        try:
            if name == "echo":
                result = f"Echo: {arguments.get('text', '')}"
            elif name == "add":
                a = arguments.get("a", 0)
                b = arguments.get("b", 0)
                result = f"Result: {a + b}"
            elif name == "get_time":
                result = f"Current time: {datetime.now().isoformat()}"
            else:
                result = f"Unknown tool: {name}"
            
            return {
                "id": msg_id,
                "result": {"content": result, "is_error": False}
            }
        except Exception as e:
            return {
                "id": msg_id,
                "result": {"content": str(e), "is_error": True}
            }
    
    async def _handle_list_resources(self, msg_id: str) -> Dict[str, Any]:
        """Handle list resources request"""
        return {
            "id": msg_id,
            "result": {"resources": list(self.resources.values())}
        }
    
    async def _handle_read_resource(self, msg_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle read resource request"""
        uri = params.get("uri")
        
        if uri not in self.resources:
            return {
                "id": msg_id,
                "error": {"code": -32601, "message": f"Resource not found: {uri}"}
            }
        
        try:
            if uri == "server://status":
                content = f"Server: {self.name} v{self.version}\nInitialized: {self.initialized}\nTime: {datetime.now().isoformat()}"
            elif uri == "server://tools":
                content = json.dumps(list(self.tools.keys()), indent=2)
            else:
                content = f"Resource content for {uri}"
            
            return {
                "id": msg_id,
                "result": {
                    "content": content,
                    "mime_type": self.resources[uri]["mime_type"]
                }
            }
        except Exception as e:
            return {
                "id": msg_id,
                "error": {"code": -32603, "message": f"Error reading resource: {str(e)}"}
            }
    
    async def _handle_list_prompts(self, msg_id: str) -> Dict[str, Any]:
        """Handle list prompts request"""
        return {
            "id": msg_id,
            "result": {"prompts": list(self.prompts.values())}
        }
    
    async def _handle_get_prompt(self, msg_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get prompt request"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if name not in self.prompts:
            return {
                "id": msg_id,
                "error": {"code": -32601, "message": f"Prompt not found: {name}"}
            }
        
        try:
            if name == "greeting":
                prompt_name = arguments.get("name", "User")
                service = arguments.get("service", "MCP Server")
                content = f"Hello {prompt_name}! Welcome to {service}."
            else:
                content = f"Prompt content for {name}"
            
            return {
                "id": msg_id,
                "result": {"content": content}
            }
        except Exception as e:
            return {
                "id": msg_id,
                "error": {"code": -32603, "message": f"Error getting prompt: {str(e)}"}
            }
    
    async def _handle_ping(self, msg_id: str) -> Dict[str, Any]:
        """Handle ping request"""
        return {
            "id": msg_id,
            "result": {"timestamp": datetime.now().isoformat()}
        }
    
    async def run_stdio(self):
        """Run server using stdio transport"""
        print(f"Starting {self.name} v{self.version} on stdio", file=sys.stderr)
        
        try:
            while True:
                # Read message from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    message = json.loads(line)
                    response = await self.handle_message(message)
                    
                    if response:
                        print(json.dumps(response))
                        sys.stdout.flush()
                        
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}", file=sys.stderr)
                except Exception as e:
                    print(f"Error handling message: {e}", file=sys.stderr)
                    
        except KeyboardInterrupt:
            print("Server stopped by user", file=sys.stderr)
        except Exception as e:
            print(f"Server error: {e}", file=sys.stderr)


async def main():
    """Main entry point"""
    server = SimpleMCPServer()
    await server.run_stdio()


if __name__ == "__main__":
    asyncio.run(main())