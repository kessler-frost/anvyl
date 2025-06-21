"""
Anvyl Infrastructure API

This module provides a FastAPI-based REST API for infrastructure management.
"""

import asyncio
import argparse
import logging
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
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

class QueryRequest(BaseModel):
    query: str
    host_id: Optional[str] = None

class AddHostRequest(BaseModel):
    host_id: str
    host_ip: str

# Initialize FastAPI app
app = FastAPI(
    title="Anvyl Infrastructure API",
    description="API for managing Anvyl infrastructure and hosts",
    version="1.0.0"
)

def get_infrastructure_service():
    """Get the infrastructure service instance."""
    from anvyl.infra.service import get_infrastructure_service as _get_service
    return _get_service()

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Anvyl Infrastructure API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Basic health check
        infrastructure_service = get_infrastructure_service()
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
        infrastructure_service = get_infrastructure_service()
        hosts = infrastructure_service.list_hosts()
        return {"hosts": hosts}
    except Exception as e:
        logger.error(f"Error listing hosts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/hosts")
async def add_host(host_data: HostCreate):
    """Add a new host."""
    try:
        infrastructure_service = get_infrastructure_service()
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
        infrastructure_service = get_infrastructure_service()
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
        infrastructure_service = get_infrastructure_service()
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
        infrastructure_service = get_infrastructure_service()
        success = infrastructure_service.host_heartbeat(host_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error sending heartbeat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Container management endpoints
@app.get("/containers")
async def list_containers(host_id: Optional[str] = None, all: bool = False):
    """List containers, optionally filtered by host. If all=True, include all containers regardless of label or status."""
    try:
        infrastructure_service = get_infrastructure_service()
        containers = infrastructure_service.list_containers(host_id, all=all)
        return {"containers": containers}
    except Exception as e:
        logger.error(f"Error listing containers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/containers")
async def add_container(container_data: ContainerCreate):
    """Add a new container."""
    try:
        infrastructure_service = get_infrastructure_service()
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
        infrastructure_service = get_infrastructure_service()
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
        infrastructure_service = get_infrastructure_service()
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
        infrastructure_service = get_infrastructure_service()
        result = infrastructure_service.exec_command(container_id, command, tty)
        if result:
            return {"result": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to execute command")
    except Exception as e:
        logger.error(f"Error executing command: {e}")
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
        infrastructure_service = get_infrastructure_service()
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

def run_infrastructure_api(host: str = "127.0.0.1", port: int = 4200):
    """Run the infrastructure API server."""
    uvicorn.run("anvyl.infra.api:app", host=host, port=port, reload=True)

def main():
    """Main entry point for the infrastructure API service."""
    parser = argparse.ArgumentParser(description="Run Anvyl Infrastructure API")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=4200, help="Port to bind to")
    args = parser.parse_args()
    run_infrastructure_api(host=args.host, port=args.port)

if __name__ == "__main__":
    main()