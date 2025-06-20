"""
Agent Manager

This module provides the main manager for the AI agent system,
including web API endpoints for agent communication.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import socket
import os
import uuid
from datetime import datetime

from anvyl.agent.host_agent import HostAgent
from anvyl.agent.communication import AgentCommunication, AgentMessage
from anvyl.agent.tools import InfrastructureTools
from anvyl.infrastructure_client import get_infrastructure_client

logger = logging.getLogger(__name__)


class AgentManager:
    """Manages the AI agent system and provides web API for communication."""

    def __init__(self,
                 infrastructure_api_url: str = "http://localhost:8080",
                 host_id: str = None,
                 host_ip: str = None,
                 lmstudio_url: Optional[str] = None,
                 lmstudio_model: str = "default",
                 port: int = 4200):
        """Initialize the agent manager."""
        self.infrastructure_client = get_infrastructure_client(infrastructure_api_url)

        self.host_id = host_id
        self.host_ip = host_ip
        self.port = port
        self.lmstudio_url = lmstudio_url
        self.lmstudio_model = lmstudio_model

        # Initialize communication and tools
        self.communication = AgentCommunication(
            local_host_id=host_id,
            local_host_ip=host_ip,
            port=port
        )
        self.tools = InfrastructureTools(self.infrastructure_client)

        # Initialize host agent
        self.host_agent = HostAgent(
            communication=self.communication,
            tools=self.tools.get_tools(),
            infrastructure_api_url=infrastructure_api_url,
            host_id=host_id,
            host_ip=host_ip,
            lmstudio_url=lmstudio_url,
            lmstudio_model=lmstudio_model,
            port=port
        )

        # Initialize FastAPI app
        self.app = self._create_fastapi_app()

        logger.info(f"Agent manager initialized for host {host_id}")

    def _create_fastapi_app(self) -> FastAPI:
        """Create the FastAPI application with endpoints."""
        app = FastAPI(
            title="Anvyl Agent API",
            description="API for AI agent communication and infrastructure management",
            version="1.0.0"
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Register endpoints
        self._register_endpoints(app)

        return app

    def _register_endpoints(self, app: FastAPI):
        """Register API endpoints."""

        @app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "message": "Anvyl Agent API",
                "host_id": self.host_id,
                "host_ip": self.host_ip,
                "status": "running"
            }

        @app.get("/health")
        async def health_check():
            """Health check endpoint for the agent."""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        @app.get("/agent/info")
        async def get_agent_info():
            """Get information about this agent."""
            return self.host_agent.get_agent_info()

        @app.post("/agent/query")
        async def handle_query(message_data: Dict[str, Any]):
            """Handle a query from another agent."""
            try:
                result = await self.host_agent.communication.handle_incoming_message(message_data)
                return result
            except Exception as e:
                logger.error(f"Error handling query: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/agent/broadcast")
        async def handle_broadcast(message_data: Dict[str, Any]):
            """Handle a broadcast message from another agent."""
            try:
                result = await self.host_agent.communication.handle_incoming_message(message_data)
                return result
            except Exception as e:
                logger.error(f"Error handling broadcast: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/agent/process")
        async def process_local_query(query: str):
            """Process a query locally using this agent."""
            try:
                result = await self.host_agent.process_query(query)
                return {"response": result}
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/agent/remote-query")
        async def query_remote_host(host_id: str, query: str):
            """Query a remote host's agent."""
            try:
                result = await self.host_agent.query_remote_host(host_id, query)
                return {"response": result}
            except Exception as e:
                logger.error(f"Error querying remote host: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/agent/hosts")
        async def get_known_hosts():
            """Get all known hosts."""
            return {"known_hosts": self.host_agent.get_known_hosts()}

        @app.post("/agent/hosts")
        async def add_known_host(host_id: str, host_ip: str):
            """Add a known host."""
            try:
                self.host_agent.add_known_host(host_id, host_ip)
                return {"message": f"Added host {host_id} -> {host_ip}"}
            except Exception as e:
                logger.error(f"Error adding host: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.delete("/agent/hosts/{host_id}")
        async def remove_known_host(host_id: str):
            """Remove a known host."""
            try:
                self.host_agent.remove_known_host(host_id)
                return {"message": f"Removed host {host_id}"}
            except Exception as e:
                logger.error(f"Error removing host: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/agent/broadcast")
        async def broadcast_message(message: str):
            """Broadcast a message to all known hosts."""
            try:
                results = await self.host_agent.broadcast_to_all_hosts(message)
                return {"results": results}
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/infrastructure/containers")
        async def list_containers(host_id: Optional[str] = None):
            """List containers on a host."""
            try:
                containers = self.infrastructure_client.list_containers(host_id)
                return {"containers": containers}
            except Exception as e:
                logger.error(f"Error listing containers: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/infrastructure/hosts")
        async def list_hosts():
            """List all hosts."""
            try:
                hosts = self.infrastructure_client.list_hosts()
                return {"hosts": hosts}
            except Exception as e:
                logger.error(f"Error listing hosts: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def start(self):
        """Start the agent manager."""
        logger.info(f"Starting agent manager on port {self.port}")
        config = uvicorn.Config(self.app, host="0.0.0.0", port=self.port)
        server = uvicorn.Server(config)
        await server.serve()

    def run(self):
        """Run the agent manager synchronously."""
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)

    async def stop(self):
        """Stop the agent manager."""
        logger.info("Stopping agent manager")


def create_agent_manager(lmstudio_url: Optional[str] = None, lmstudio_model: str = "default",
                        port: int = 4200, infrastructure_api_url: str = "http://localhost:8080") -> AgentManager:
    """Create an agent manager with default settings."""
    return AgentManager(
        infrastructure_api_url=infrastructure_api_url,
        lmstudio_url=lmstudio_url,
        lmstudio_model=lmstudio_model,
        port=port
    )