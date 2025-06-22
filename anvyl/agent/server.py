"""
Agent Server

This module provides a FastAPI server for the Anvyl AI Agent that uses MCP server
for infrastructure management.
"""

import logging
import asyncio
import uvicorn
import argparse
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
import uuid
import socket

from anvyl.agent.core import AnvylAgent
from anvyl.agent.communication import AgentCommunication
from anvyl.config import get_settings

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Global agent instance and configuration
_agent: Optional[AnvylAgent] = None
_communication: Optional[AgentCommunication] = None
_agent_config = {
    "host_id": settings.agent_host_id,
    "host_ip": settings.agent_host,
    "port": settings.agent_port,
    "mcp_server_url": settings.mcp_server_url,
    "model_provider_url": settings.model_provider_url,
    "tools": []
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    global _agent, _communication, _agent_config

    # Startup
    logger.info("Starting Anvyl AI Agent server...")

    try:
        # Create communication instance
        _communication = AgentCommunication(
            local_host_id=_agent_config["host_id"],
            local_host_ip=_agent_config["host_ip"],
            port=_agent_config["port"]
        )

        # Create agent
        _agent = AnvylAgent(
            communication=_communication,
            mcp_server_url=_agent_config["mcp_server_url"],
            host_id=_agent_config["host_id"],
            host_ip=_agent_config["host_ip"],
            model_provider_url=_agent_config["model_provider_url"],
            port=_agent_config["port"]
        )

        logger.info(f"Agent created successfully on port {_agent_config['port']}")
        logger.info(f"Using MCP server: {_agent_config['mcp_server_url']}")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        _agent = None
        _communication = None

    yield

    # Shutdown
    logger.info("Shutting down Anvyl AI Agent server...")
    _agent = None
    _communication = None


app = FastAPI(
    title="Anvyl AI Agent",
    version="1.0.0",
    lifespan=lifespan
)


class QueryRequest(BaseModel):
    query: str


class RemoteQueryRequest(BaseModel):
    host_id: str
    query: str


class AddHostRequest(BaseModel):
    host_id: str
    host_ip: str


class BroadcastRequest(BaseModel):
    message: str


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "anvyl-agent"}


@app.get("/agent/info")
async def get_agent_info():
    """Get information about the agent."""
    global _agent
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    return _agent.get_agent_info()


@app.post("/agent/process")
async def process_query(request: QueryRequest):
    """Process a query using the AI agent."""
    global _agent
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        result = await _agent.process_query(request.query)
        return {"response": result}
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/remote-query")
async def remote_query(request: RemoteQueryRequest):
    """Query a remote agent."""
    global _agent
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        result = await _agent.query_remote_host(request.host_id, request.query)
        return {"response": result}
    except Exception as e:
        logger.error(f"Error querying remote host: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/hosts")
async def list_hosts():
    """List known hosts."""
    global _agent
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    return {"hosts": _agent.get_known_hosts()}


@app.post("/agent/add-host")
async def add_host(request: AddHostRequest):
    """Add a host to the known hosts list."""
    global _agent
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        _agent.add_known_host(request.host_id, request.host_ip)
        return {"message": f"Host {request.host_id} added successfully"}
    except Exception as e:
        logger.error(f"Error adding host: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/broadcast")
async def broadcast_message(request: BroadcastRequest):
    """Broadcast a message to all known hosts."""
    global _agent
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        result = await _agent.broadcast_to_all_hosts(request.message)
        return {"responses": result}
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/query")
async def handle_query(message_data: Dict[str, Any]):
    """Handle a query from another agent."""
    global _communication
    if _communication is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        result = await _communication.handle_incoming_message(message_data)
        return result
    except Exception as e:
        logger.error(f"Error handling query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/broadcast")
async def handle_broadcast(message_data: Dict[str, Any]):
    """Handle a broadcast message from another agent."""
    global _communication
    if _communication is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        result = await _communication.handle_incoming_message(message_data)
        return result
    except Exception as e:
        logger.error(f"Error handling broadcast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def set_agent_config(
    mcp_server_url: Optional[str] = None,
    model_provider_url: Optional[str] = None,
    port: Optional[int] = None
):
    """Set the agent configuration."""
    global _agent_config

    if mcp_server_url is not None:
        _agent_config["mcp_server_url"] = mcp_server_url
    if model_provider_url is not None:
        _agent_config["model_provider_url"] = model_provider_url
    if port is not None:
        _agent_config["port"] = port


def create_anvyl_agent(
    host_id: str,
    host_ip: str,
    port: Optional[int] = None,
    mcp_server_url: Optional[str] = None,
    model_provider_url: Optional[str] = None
) -> AnvylAgent:
    """Create a new host agent instance."""
    communication = AgentCommunication(
        local_host_id=host_id,
        local_host_ip=host_ip,
        port=port or settings.agent_port
    )

    return AnvylAgent(
        communication=communication,
        mcp_server_url=mcp_server_url,
        host_id=host_id,
        host_ip=host_ip,
        model_provider_url=model_provider_url,
        port=port
    )


def start_agent_server(
    host_id: Optional[str] = None,
    host_ip: Optional[str] = None,
    port: Optional[int] = None,
    mcp_server_url: Optional[str] = None,
    model_provider_url: Optional[str] = None
):
    """Start the agent server with the given configuration."""
    # Update configuration
    if host_id is not None:
        _agent_config["host_id"] = host_id
    if host_ip is not None:
        _agent_config["host_ip"] = host_ip
    if port is not None:
        _agent_config["port"] = port
    if mcp_server_url is not None:
        _agent_config["mcp_server_url"] = mcp_server_url
    if model_provider_url is not None:
        _agent_config["model_provider_url"] = model_provider_url

    # Start the server
    uvicorn.run(
        app,
        host=_agent_config["host_ip"],
        port=_agent_config["port"],
        log_level="info"
    )


def main():
    """Main entry point for the agent server."""
    parser = argparse.ArgumentParser(description="Anvyl AI Agent Server")
    parser.add_argument("--host-id", default=settings.agent_host_id, help="Host ID")
    parser.add_argument("--host-ip", default=settings.agent_host, help="Host IP")
    parser.add_argument("--port", type=int, default=settings.agent_port, help="Port to bind to")
    parser.add_argument("--mcp-server-url", default=settings.mcp_server_url, help="MCP server URL")
    parser.add_argument("--model-provider-url", default=settings.model_provider_url, help="Model provider URL")

    args = parser.parse_args()

    print(f"Starting Anvyl AI Agent on port {args.port}")
    start_agent_server(
        host_id=args.host_id,
        host_ip=args.host_ip,
        port=args.port,
        mcp_server_url=args.mcp_server_url,
        model_provider_url=args.model_provider_url
    )


if __name__ == "__main__":
    main()