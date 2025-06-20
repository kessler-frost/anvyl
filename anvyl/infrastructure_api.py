"""
Anvyl Infrastructure API

This module provides a FastAPI service that exposes infrastructure management
functionality via HTTP endpoints, allowing agents to interact with the
infrastructure service remotely.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

from anvyl.infrastructure_service import get_infrastructure_service

logger = logging.getLogger(__name__)

# Pydantic models for request/response
class HostCreate(BaseModel):
    name: str
    ip: str
    os: str = ""
    tags: Optional[List[str]] = None

class HostUpdate(BaseModel):
    resources: Optional[Dict[str, Any]] = None
    status: str = ""
    tags: Optional[List[str]] = None

class ContainerCreate(BaseModel):
    name: str
    image: str
    host_id: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    ports: Optional[List[str]] = None
    volumes: Optional[List[str]] = None
    environment: Optional[List[str]] = None

class AgentStartRequest(BaseModel):
    lmstudio_url: str = "http://localhost:1234/v1"
    lmstudio_model: str = "llama-3.2-3b-instruct"
    port: int = 4200
    image_tag: str = "anvyl-agent:latest"

class QueryRequest(BaseModel):
    query: str
    host_id: Optional[str] = None

class AddHostRequest(BaseModel):
    host_id: str
    host_ip: str

# Create FastAPI app
app = FastAPI(
    title="Anvyl Infrastructure API",
    description="API for infrastructure management and agent communication",
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

# Get infrastructure service instance
infrastructure_service = get_infrastructure_service()

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Anvyl Infrastructure API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Basic health check
        hosts = infrastructure_service.list_hosts()
        return {
            "status": "healthy",
            "hosts_count": len(hosts),
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Host management endpoints
@app.get("/hosts")
async def list_hosts():
    """List all registered hosts."""
    try:
        hosts = infrastructure_service.list_hosts()
        return {"hosts": hosts}
    except Exception as e:
        logger.error(f"Error listing hosts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/hosts")
async def add_host(host_data: HostCreate):
    """Add a new host to the system."""
    try:
        host = infrastructure_service.add_host(
            name=host_data.name,
            ip=host_data.ip,
            os=host_data.os,
            tags=host_data.tags
        )
        if host:
            return {"message": "Host added successfully", "host": host}
        else:
            raise HTTPException(status_code=400, detail="Failed to add host")
    except Exception as e:
        logger.error(f"Error adding host: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/hosts/{host_id}")
async def update_host(host_id: str, host_data: HostUpdate):
    """Update host information."""
    try:
        host = infrastructure_service.update_host(
            host_id=host_id,
            resources=host_data.resources,
            status=host_data.status,
            tags=host_data.tags
        )
        if host:
            return {"message": "Host updated successfully", "host": host}
        else:
            raise HTTPException(status_code=404, detail="Host not found")
    except Exception as e:
        logger.error(f"Error updating host: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/hosts/{host_id}/metrics")
async def get_host_metrics(host_id: str):
    """Get metrics for a specific host."""
    try:
        metrics = infrastructure_service.get_host_metrics(host_id)
        if metrics:
            return {"metrics": metrics}
        else:
            raise HTTPException(status_code=404, detail="Host not found")
    except Exception as e:
        logger.error(f"Error getting host metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/hosts/{host_id}/heartbeat")
async def host_heartbeat(host_id: str):
    """Send a heartbeat for a host."""
    try:
        success = infrastructure_service.host_heartbeat(host_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error sending heartbeat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Container management endpoints
@app.get("/containers")
async def list_containers(host_id: Optional[str] = None):
    """List containers, optionally filtered by host."""
    try:
        containers = infrastructure_service.list_containers(host_id)
        return {"containers": containers}
    except Exception as e:
        logger.error(f"Error listing containers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/containers")
async def add_container(container_data: ContainerCreate):
    """Add a new container."""
    try:
        container = infrastructure_service.add_container(
            name=container_data.name,
            image=container_data.image,
            host_id=container_data.host_id,
            labels=container_data.labels,
            ports=container_data.ports,
            volumes=container_data.volumes,
            environment=container_data.environment
        )
        if container:
            return {"message": "Container added successfully", "container": container}
        else:
            raise HTTPException(status_code=400, detail="Failed to add container")
    except Exception as e:
        logger.error(f"Error adding container: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/containers/{container_id}")
async def stop_container(container_id: str, timeout: int = 10):
    """Stop a container."""
    try:
        success = infrastructure_service.stop_container(container_id, timeout)
        if success:
            return {"message": "Container stopped successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop container")
    except Exception as e:
        logger.error(f"Error stopping container: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/containers/{container_id}/logs")
async def get_container_logs(container_id: str, follow: bool = False, tail: int = 100):
    """Get logs from a container."""
    try:
        logs = infrastructure_service.get_logs(container_id, follow=follow, tail=tail)
        if logs is not None:
            return {"logs": logs}
        else:
            raise HTTPException(status_code=404, detail="Container not found")
    except Exception as e:
        logger.error(f"Error getting container logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/containers/{container_id}/exec")
async def exec_command(container_id: str, command: List[str], tty: bool = False):
    """Execute a command in a container."""
    try:
        result = infrastructure_service.exec_command(container_id, command, tty)
        if result:
            return {"result": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to execute command")
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent management endpoints
@app.post("/agent/start")
async def start_agent(request: AgentStartRequest):
    """Start the agent container."""
    try:
        result = infrastructure_service.start_agent_container(
            lmstudio_url=request.lmstudio_url,
            lmstudio_model=request.lmstudio_model,
            port=request.port,
            image_tag=request.image_tag
        )
        if result:
            return {"message": "Agent started successfully", "result": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to start agent")
    except Exception as e:
        logger.error(f"Error starting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/stop")
async def stop_agent():
    """Stop the agent container."""
    try:
        success = infrastructure_service.stop_agent_container()
        if success:
            return {"message": "Agent stopped successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop agent")
    except Exception as e:
        logger.error(f"Error stopping agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/status")
async def get_agent_status():
    """Get the status of the agent container."""
    try:
        status = infrastructure_service.get_agent_container_status()
        if status:
            return {"status": status}
        else:
            return {"status": None, "message": "Agent container not found"}
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/logs")
async def get_agent_logs(follow: bool = False, tail: int = 100):
    """Get logs from the agent container."""
    try:
        logs = infrastructure_service.get_agent_logs(follow=follow, tail=tail)
        if logs is not None:
            return {"logs": logs}
        else:
            raise HTTPException(status_code=404, detail="Agent container not found")
    except Exception as e:
        logger.error(f"Error getting agent logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Host command execution endpoint
@app.post("/hosts/{host_id}/exec")
async def exec_command_on_host(
    host_id: str,
    command: List[str],
    working_directory: str = "",
    env: Optional[List[str]] = None,
    timeout: int = 0
):
    """Execute a command on a specific host."""
    try:
        result = infrastructure_service.exec_command_on_host(
            host_id=host_id,
            command=command,
            working_directory=working_directory,
            env=env,
            timeout=timeout
        )
        if result:
            return {"result": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to execute command")
    except Exception as e:
        logger.error(f"Error executing command on host: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def run_infrastructure_api(host: str = "0.0.0.0", port: int = 8080):
    """Run the infrastructure API server."""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_infrastructure_api()