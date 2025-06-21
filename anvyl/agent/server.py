"""
Agent Server

This module provides a FastAPI server for the Anvyl AI Agent that can run directly on the host.
"""

import logging
import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
import uuid
import socket

from anvyl.agent.host_agent import HostAgent
from anvyl.agent.communication import AgentCommunication
from anvyl.agent.tools import get_agent_tools

logger = logging.getLogger(__name__)

# Global agent instance and configuration
_agent: Optional[HostAgent] = None
_communication: Optional[AgentCommunication] = None
_agent_config = {
    "host_id": None,
    "host_ip": None,
    "port": 4201,
    "infrastructure_api_url": "http://localhost:4200",
    "model_provider_url": "http://localhost:1234/v1",
    "model_name": "llama-3.2-3b-instruct",
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
            local_host_id="local",
            local_host_ip="127.0.0.1",
            port=_agent_config["port"]
        )

        # Get tools
        tools = get_agent_tools(_agent_config["infrastructure_api_url"])

        # Create agent
        _agent = HostAgent(
            communication=_communication,
            tools=tools,
            infrastructure_api_url=_agent_config["infrastructure_api_url"],
            model_provider_url=_agent_config["model_provider_url"],
            model_name=_agent_config["model_name"],
            port=_agent_config["port"]
        )

        logger.info(f"Agent created successfully on port {_agent_config['port']}")
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
    # Test reload functionality - this comment should trigger a reload
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
    """Handle a broadcast from another agent."""
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
    infrastructure_api_url: str = "http://localhost:4200",
    model_provider_url: str = "http://localhost:1234/v1",
    model_name: str = "llama-3.2-3b-instruct",
    port: int = 4201
):
    """Set the agent configuration globally."""
    global _agent_config
    _agent_config.update({
        "infrastructure_api_url": infrastructure_api_url,
        "model_provider_url": model_provider_url,
        "model_name": model_name,
        "port": port
    })


def create_host_agent(
    host_id: str,
    host_ip: str,
    port: int = 4201,
    infrastructure_api_url: str = "http://localhost:4200",
    model_provider_url: str = "http://localhost:1234/v1",
    model_name: str = "llama-3.2-3b-instruct",
    tools: List = None
) -> HostAgent:
    """Create a new host agent instance."""
    if tools is None:
        tools = []

    # Create communication and tools
    communication = AgentCommunication(host_id=host_id, port=port)
    agent_tools = get_agent_tools(infrastructure_api_url)

    # Create the host agent
    agent = HostAgent(
        communication=communication,
        tools=agent_tools,
        infrastructure_api_url=infrastructure_api_url,
        host_id=host_id,
        host_ip=host_ip,
        model_provider_url=model_provider_url,
        model_name=model_name,
        port=port
    )

    return agent


def start_agent_server(
    host_id: str = None,
    host_ip: str = None,
    port: int = 4201,
    infrastructure_api_url: str = "http://localhost:4200",
    model_provider_url: str = "http://localhost:1234/v1",
    model_name: str = "llama-3.2-3b-instruct"
):
    """Start the agent server with the specified configuration."""
    if host_id is None:
        host_id = str(uuid.uuid4())
    if host_ip is None:
        host_ip = socket.gethostbyname(socket.gethostname())

    # Create agent configuration
    agent_config = {
        "host_id": host_id,
        "host_ip": host_ip,
        "port": port,
        "infrastructure_api_url": infrastructure_api_url,
        "model_provider_url": model_provider_url,
        "model_name": model_name
    }

    # Create and start the agent
    agent = create_host_agent(
        host_id=host_id,
        host_ip=host_ip,
        port=port,
        infrastructure_api_url=infrastructure_api_url,
        model_provider_url=model_provider_url,
        model_name=model_name
    )

    # Set the configuration
    set_agent_config(
        infrastructure_api_url=infrastructure_api_url,
        model_provider_url=model_provider_url,
        model_name=model_name,
        port=port
    )

    # Run the server with reload enabled
    uvicorn.run(
        "anvyl.agent.server:app",
        host=host_ip,
        port=port,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start an Anvyl host agent")
    parser.add_argument("--host-id", type=str, help="Host ID (default: auto-generated)")
    parser.add_argument("--host-ip", type=str, help="Host IP (default: auto-detected)")
    parser.add_argument("--port", type=int, default=4201, help="Agent port")
    parser.add_argument("--infrastructure-api-url", type=str, default="http://localhost:4200", help="Infrastructure API URL")
    parser.add_argument("--model-provider-url", type=str, default="http://localhost:1234/v1", help="Model provider API URL")
    parser.add_argument("--model", type=str, default="llama-3.2-3b-instruct", help="Model provider model name")

    args = parser.parse_args()

    start_agent_server(
        host_id=args.host_id,
        host_ip=args.host_ip,
        port=args.port,
        infrastructure_api_url=args.infrastructure_api_url,
        model_provider_url=args.model_provider_url,
        model_name=args.model
    )