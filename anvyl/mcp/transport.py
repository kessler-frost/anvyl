"""
MCP Transport Layer

This module provides transport mechanisms for MCP communication
including stdio and HTTP transports.
"""

import asyncio
import json
import subprocess
import sys
from abc import ABC, abstractmethod
from typing import Optional, Callable, Dict, Any
import logging

from .types import MCPMessage

logger = logging.getLogger(__name__)


class MCPTransport(ABC):
    """Abstract base class for MCP transports"""
    
    @abstractmethod
    async def send_message(self, message: MCPMessage) -> None:
        """Send a message through the transport"""
        pass
    
    @abstractmethod
    async def receive_message(self) -> Optional[MCPMessage]:
        """Receive a message from the transport"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the transport"""
        pass


class StdioTransport(MCPTransport):
    """Standard input/output transport for MCP"""
    
    def __init__(self, process: Optional[subprocess.Popen] = None):
        self.process = process
        self.stdin = process.stdin if process else sys.stdin
        self.stdout = process.stdout if process else sys.stdout
        self._closed = False
        
    async def send_message(self, message: MCPMessage) -> None:
        """Send a message via stdout"""
        if self._closed:
            raise RuntimeError("Transport is closed")
        
        json_msg = message.to_json()
        logger.debug(f"Sending message: {json_msg}")
        
        if hasattr(self.stdin, 'write'):
            self.stdin.write(json_msg + '\n')
            if hasattr(self.stdin, 'flush'):
                self.stdin.flush()
        else:
            print(json_msg, file=self.stdin)
    
    async def receive_message(self) -> Optional[MCPMessage]:
        """Receive a message via stdin"""
        if self._closed:
            return None
        
        try:
            if hasattr(self.stdout, 'readline'):
                line = self.stdout.readline()
                if not line:
                    return None
                line = line.decode() if isinstance(line, bytes) else line
            else:
                line = input()
            
            line = line.strip()
            if not line:
                return None
            
            logger.debug(f"Received message: {line}")
            return MCPMessage.from_json(line)
        except (EOFError, json.JSONDecodeError) as e:
            logger.error(f"Error receiving message: {e}")
            return None
    
    async def close(self) -> None:
        """Close the transport"""
        self._closed = True
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


class HTTPTransport(MCPTransport):
    """HTTP-based transport for MCP"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self._session = None
        self._closed = False
    
    async def _ensure_session(self):
        """Ensure HTTP session is available"""
        if not self._session:
            try:
                import httpx
                self._session = httpx.AsyncClient()
            except ImportError:
                raise RuntimeError("httpx is required for HTTP transport")
    
    async def send_message(self, message: MCPMessage) -> None:
        """Send a message via HTTP POST"""
        if self._closed:
            raise RuntimeError("Transport is closed")
        
        await self._ensure_session()
        
        try:
            response = await self._session.post(
                f"{self.base_url}/mcp",
                json=message.to_dict(),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            logger.debug(f"Sent message via HTTP: {message.to_json()}")
        except Exception as e:
            logger.error(f"Error sending HTTP message: {e}")
            raise
    
    async def receive_message(self) -> Optional[MCPMessage]:
        """Receive a message via HTTP GET"""
        if self._closed:
            return None
        
        await self._ensure_session()
        
        try:
            response = await self._session.get(f"{self.base_url}/mcp")
            response.raise_for_status()
            
            data = response.json()
            if data:
                logger.debug(f"Received message via HTTP: {data}")
                return MCPMessage.from_dict(data)
        except Exception as e:
            logger.error(f"Error receiving HTTP message: {e}")
        
        return None
    
    async def close(self) -> None:
        """Close the HTTP transport"""
        self._closed = True
        if self._session:
            await self._session.aclose()


class TransportFactory:
    """Factory for creating MCP transports"""
    
    @staticmethod
    def create_stdio_transport(command: str, args: list = None) -> StdioTransport:
        """Create a stdio transport with a subprocess"""
        if args is None:
            args = []
        
        full_command = [command] + args
        logger.info(f"Starting MCP server: {' '.join(full_command)}")
        
        try:
            process = subprocess.Popen(
                full_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return StdioTransport(process)
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise
    
    @staticmethod
    def create_http_transport(host: str = "localhost", port: int = 8080) -> HTTPTransport:
        """Create an HTTP transport"""
        return HTTPTransport(host, port)


class MessageHandler:
    """Handler for processing MCP messages"""
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
    
    def register_handler(self, method: str, handler: Callable):
        """Register a message handler for a specific method"""
        self.handlers[method] = handler
        logger.debug(f"Registered handler for method: {method}")
    
    async def handle_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Handle an incoming message"""
        if message.method in self.handlers:
            try:
                return await self.handlers[message.method](message)
            except Exception as e:
                logger.error(f"Error handling message {message.method}: {e}")
                return MCPMessage(
                    id=message.id,
                    type="response",
                    error={"code": -32603, "message": str(e)}
                )
        else:
            logger.warning(f"No handler found for method: {message.method}")
            return MCPMessage(
                id=message.id,
                type="response", 
                error={"code": -32601, "message": f"Method not found: {message.method}"}
            )