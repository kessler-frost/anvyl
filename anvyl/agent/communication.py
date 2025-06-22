"""
Agent Communication System

This module handles communication between AI agents running on different hosts.
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone
import aiohttp
import socket
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    """Message structure for agent communication."""
    sender_id: str
    sender_host: str
    message_type: str  # query, response, broadcast
    content: Dict[str, Any]
    recipient_id: Optional[str] = None
    recipient_host: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class AgentCommunication:
    """Handles communication between agents across hosts."""

    def __init__(self, local_host_id: str, local_host_ip: str, port: int = 4200):
        """Initialize agent communication."""
        self.local_host_id = local_host_id
        self.local_host_ip = local_host_ip
        self.port = port
        self.known_hosts: Dict[str, str] = {}  # host_id -> ip mapping
        self.message_handlers: Dict[str, Callable] = {}

    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type."""
        self.message_handlers[message_type] = handler

    async def send_query(self, target_host_id: str, query: str, tools: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send a query to an agent on another host."""
        if target_host_id not in self.known_hosts:
            return {"error": f"Unknown host {target_host_id}"}

        target_ip = self.known_hosts[target_host_id]
        message = AgentMessage(
            sender_id=self.local_host_id,
            sender_host=self.local_host_ip,
            recipient_host=target_ip,
            message_type="query",
            content={
                "query": query,
                "tools": tools or [],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{target_ip}:{self.port}/agent/query"
                async with session.post(url, json=message.__dict__, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"HTTP {response.status}: {await response.text()}"}
        except Exception as e:
            logger.error(f"Error sending query to {target_host_id}: {e}")
            return {"error": f"Communication error: {str(e)}"}

    async def broadcast_message(self, message_type: str, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Broadcast a message to all known hosts."""
        responses = []
        message = AgentMessage(
            sender_id=self.local_host_id,
            sender_host=self.local_host_ip,
            message_type="broadcast",
            content=content
        )

        for host_id, host_ip in self.known_hosts.items():
            if host_id != self.local_host_id:  # Don't send to self
                try:
                    async with aiohttp.ClientSession() as session:
                        url = f"http://{host_ip}:{self.port}/agent/broadcast"
                        async with session.post(url, json=message.__dict__, timeout=aiohttp.ClientTimeout(total=30)) as response:
                            if response.status == 200:
                                responses.append(await response.json())
                            else:
                                responses.append({"host_id": host_id, "error": f"HTTP {response.status}"})
                except Exception as e:
                    logger.error(f"Error broadcasting to {host_id}: {e}")
                    responses.append({"host_id": host_id, "error": str(e)})

        return responses

    def add_known_host(self, host_id: str, host_ip: str):
        """Add a host to the known hosts list."""
        self.known_hosts[host_id] = host_ip
        logger.info(f"Added known host: {host_id} -> {host_ip}")

    def remove_known_host(self, host_id: str):
        """Remove a host from the known hosts list."""
        if host_id in self.known_hosts:
            del self.known_hosts[host_id]
            logger.info(f"Removed known host: {host_id}")

    def get_known_hosts(self) -> Dict[str, str]:
        """Get all known hosts."""
        return self.known_hosts.copy()

    async def handle_incoming_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an incoming message from another agent."""
        try:
            message = AgentMessage(**message_data)
            logger.info(f"Received {message.message_type} message from {message.sender_host}")

            if message.message_type in self.message_handlers:
                return await self.message_handlers[message.message_type](message)
            else:
                return {"error": f"Unknown message type: {message.message_type}"}

        except Exception as e:
            logger.error(f"Error handling incoming message: {e}")
            return {"error": f"Message handling error: {str(e)}"}


class RemoteQueryTool:
    """Tool for querying remote agents."""

    def __init__(self, communication: AgentCommunication):
        self.communication = communication

    async def query_remote_agent(self, host_id: str, query: str) -> str:
        """Query a remote agent."""
        result = await self.communication.send_query(host_id, query)
        if "error" in result:
            return f"Error querying remote agent: {result['error']}"
        else:
            return json.dumps(result, indent=2)

    async def get_remote_containers(self, host_id: str) -> str:
        """Get containers from a remote host."""
        return await self.query_remote_agent(host_id, "List all containers on this host")

    async def get_remote_host_info(self, host_id: str) -> str:
        """Get host information from a remote host."""
        return await self.query_remote_agent(host_id, "Get host information and resources")

    async def get_remote_host_resources(self, host_id: str) -> str:
        """Get resource usage from a remote host."""
        return await self.query_remote_agent(host_id, "Get current resource usage")