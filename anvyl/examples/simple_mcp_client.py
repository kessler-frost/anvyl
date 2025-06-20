#!/usr/bin/env python3
"""
Simple MCP Client Example

This is a standalone example of an MCP client that demonstrates
connecting to an MCP server and using its capabilities.
"""

import asyncio
import json
import subprocess
import sys
import uuid
from typing import Dict, Any, Optional


class SimpleMCPClient:
    """A simple MCP client implementation for demonstration"""
    
    def __init__(self):
        self.name = "simple-mcp-client"
        self.version = "0.1.0"
        self.process: Optional[subprocess.Popen] = None
        self.connected = False
        self.server_capabilities = {}
        
    async def connect_to_server(self, command: str, args: list = None) -> bool:
        """Connect to an MCP server by starting a subprocess"""
        if args is None:
            args = []
        
        full_command = [command] + args
        print(f"Starting MCP server: {' '.join(full_command)}")
        
        try:
            self.process = subprocess.Popen(
                full_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send initialization request
            init_request = {
                "id": str(uuid.uuid4()),
                "method": "initialize",
                "params": {
                    "protocol_version": "2024-11-05",
                    "capabilities": {
                        "sampling": False,
                        "roots": False
                    },
                    "client_info": {
                        "name": self.name,
                        "version": self.version
                    }
                }
            }
            
            await self._send_message(init_request)
            response = await self._receive_message()
            
            if response and response.get("result"):
                self.server_capabilities = response["result"].get("capabilities", {})
                print(f"Connected to server: {response['result'].get('server_info', {})}")
                
                # Send initialized notification
                initialized_notification = {
                    "id": str(uuid.uuid4()),
                    "method": "initialized"
                }
                await self._send_message(initialized_notification)
                
                self.connected = True
                return True
            else:
                print("Failed to initialize connection")
                return False
                
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    async def _send_message(self, message: Dict[str, Any]):
        """Send a message to the server"""
        if not self.process:
            raise RuntimeError("Not connected to server")
        
        json_msg = json.dumps(message)
        self.process.stdin.write(json_msg + '\n')
        self.process.stdin.flush()
    
    async def _receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive a message from the server"""
        if not self.process:
            return None
        
        try:
            line = self.process.stdout.readline()
            if not line:
                return None
            
            line = line.strip()
            if not line:
                return None
            
            return json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Error receiving message: {e}")
            return None
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Any:
        """Send a request and wait for response"""
        if not self.connected:
            raise RuntimeError("Client not connected")
        
        request_id = str(uuid.uuid4())
        request = {
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        await self._send_message(request)
        
        # Wait for response
        response = await self._receive_message()
        if response and response.get("id") == request_id:
            if response.get("error"):
                raise Exception(f"Server error: {response['error']}")
            return response.get("result")
        
        return None
    
    async def list_tools(self) -> list:
        """List available tools from the server"""
        result = await self._send_request("tools/list")
        return result.get("tools", []) if result else []
    
    async def call_tool(self, name: str, arguments: Dict[str, Any] = None) -> str:
        """Call a tool on the server"""
        params = {
            "name": name,
            "arguments": arguments or {}
        }
        result = await self._send_request("tools/call", params)
        
        if result and result.get("is_error"):
            raise Exception(f"Tool error: {result.get('content')}")
        
        return result.get("content", "") if result else ""
    
    async def list_resources(self) -> list:
        """List available resources from the server"""
        result = await self._send_request("resources/list")
        return result.get("resources", []) if result else []
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource from the server"""
        params = {"uri": uri}
        result = await self._send_request("resources/read", params)
        return result.get("content", "") if result else ""
    
    async def list_prompts(self) -> list:
        """List available prompts from the server"""
        result = await self._send_request("prompts/list")
        return result.get("prompts", []) if result else []
    
    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None) -> str:
        """Get a prompt from the server"""
        params = {
            "name": name,
            "arguments": arguments or {}
        }
        result = await self._send_request("prompts/get", params)
        return result.get("content", "") if result else ""
    
    async def ping(self) -> Dict[str, Any]:
        """Ping the server"""
        return await self._send_request("ping")
    
    async def disconnect(self):
        """Disconnect from the server"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        
        self.connected = False
        self.process = None
        print("Disconnected from MCP server")
    
    async def interactive_session(self):
        """Run an interactive session with the server"""
        print("\n🤖 MCP Interactive Client")
        print("Available commands:")
        print("  list-tools           - List available tools")
        print("  call-tool <name>     - Call a tool")
        print("  list-resources       - List available resources")
        print("  read-resource <uri>  - Read a resource")
        print("  list-prompts         - List available prompts")
        print("  get-prompt <name>    - Get a prompt")
        print("  ping                 - Ping the server")
        print("  quit                 - Exit")
        
        while True:
            try:
                cmd_line = input("\nmcp> ").strip()
                if not cmd_line:
                    continue
                
                parts = cmd_line.split()
                cmd = parts[0]
                
                if cmd == "quit":
                    break
                elif cmd == "list-tools":
                    tools = await self.list_tools()
                    print("Available tools:")
                    for tool in tools:
                        print(f"  • {tool['name']}: {tool['description']}")
                
                elif cmd == "call-tool":
                    if len(parts) < 2:
                        print("Usage: call-tool <name> [args...]")
                        continue
                    
                    tool_name = parts[1]
                    
                    # Simple argument parsing for demo
                    if tool_name == "echo" and len(parts) > 2:
                        args = {"text": " ".join(parts[2:])}
                    elif tool_name == "add" and len(parts) >= 4:
                        args = {"a": float(parts[2]), "b": float(parts[3])}
                    else:
                        args = {}
                    
                    try:
                        result = await self.call_tool(tool_name, args)
                        print(f"Tool result: {result}")
                    except Exception as e:
                        print(f"Error: {e}")
                
                elif cmd == "list-resources":
                    resources = await self.list_resources()
                    print("Available resources:")
                    for resource in resources:
                        print(f"  • {resource['uri']}: {resource['description']}")
                
                elif cmd == "read-resource":
                    if len(parts) < 2:
                        print("Usage: read-resource <uri>")
                        continue
                    
                    uri = parts[1]
                    try:
                        content = await self.read_resource(uri)
                        print(f"Resource content:\n{content}")
                    except Exception as e:
                        print(f"Error: {e}")
                
                elif cmd == "list-prompts":
                    prompts = await self.list_prompts()
                    print("Available prompts:")
                    for prompt in prompts:
                        print(f"  • {prompt['name']}: {prompt['description']}")
                
                elif cmd == "get-prompt":
                    if len(parts) < 2:
                        print("Usage: get-prompt <name>")
                        continue
                    
                    prompt_name = parts[1]
                    
                    # Simple argument parsing for demo
                    if prompt_name == "greeting":
                        args = {"name": "Demo User", "service": "MCP Demo"}
                    else:
                        args = {}
                    
                    try:
                        content = await self.get_prompt(prompt_name, args)
                        print(f"Prompt content: {content}")
                    except Exception as e:
                        print(f"Error: {e}")
                
                elif cmd == "ping":
                    try:
                        result = await self.ping()
                        print(f"Ping result: {result}")
                    except Exception as e:
                        print(f"Error: {e}")
                
                else:
                    print(f"Unknown command: {cmd}")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python simple_mcp_client.py <server_command> [server_args...]")
        print("Example: python simple_mcp_client.py python simple_mcp_server.py")
        return
    
    server_command = sys.argv[1]
    server_args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    client = SimpleMCPClient()
    
    try:
        # Connect to server
        if await client.connect_to_server(server_command, server_args):
            print("✅ Connected successfully!")
            
            # Run interactive session
            await client.interactive_session()
        else:
            print("❌ Failed to connect to server")
    
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())