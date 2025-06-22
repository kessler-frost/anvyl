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

from anvyl.infra.service import get_infrastructure_service as _get_service

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
async def remove_container(container_id: str, timeout: int = 10):
    """Remove a container."""
    try:
        infrastructure_service = get_infrastructure_service()
        success = infrastructure_service.remove_container(container_id, timeout)
        if success:
            return {"message": "Container removed successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to remove container")
    except Exception as e:
        logger.error(f"Error removing container: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove container: {str(e)}")

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
        result = infrastructure_service.exec_command(container_id, command, tty=tty)
        if result:
            return {"message": "Command executed successfully", "result": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to execute command")
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/containers/{container_id}/stats")
async def get_container_stats(container_id: str):
    """Get statistics for a container."""
    try:
        infrastructure_service = get_infrastructure_service()
        stats = infrastructure_service.get_container_stats(container_id)
        if stats:
            return {"stats": stats}
        else:
            raise HTTPException(status_code=404, detail="Container not found")
    except Exception as e:
        logger.error(f"Error getting container stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/containers/{container_id}/inspect")
async def inspect_container(container_id: str):
    """Get detailed information about a container."""
    try:
        infrastructure_service = get_infrastructure_service()
        container_info = infrastructure_service.inspect_container(container_id)
        if container_info:
            return {"container": container_info}
        else:
            raise HTTPException(status_code=404, detail="Container not found")
    except Exception as e:
        logger.error(f"Error inspecting container: {e}")
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
    """Execute a command on a host."""
    try:
        infrastructure_service = get_infrastructure_service()
        result = infrastructure_service.exec_command_on_host(
            host_id, command, working_directory, env, timeout
        )
        if result:
            return {"message": "Command executed successfully", "result": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to execute command")
    except Exception as e:
        logger.error(f"Error executing command on host: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Image management endpoints
@app.get("/images")
async def list_images():
    """List all Docker images."""
    try:
        infrastructure_service = get_infrastructure_service()
        images = infrastructure_service.list_images()
        return {"images": images}
    except Exception as e:
        logger.error(f"Error listing images: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/images/pull")
async def pull_image(image_name: str, tag: str = "latest"):
    """Pull a Docker image."""
    try:
        infrastructure_service = get_infrastructure_service()
        image = infrastructure_service.pull_image(image_name, tag)
        if image:
            return {"message": "Image pulled successfully", "image": image}
        else:
            raise HTTPException(status_code=400, detail="Failed to pull image")
    except Exception as e:
        logger.error(f"Error pulling image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/images/{image_id}")
async def remove_image(image_id: str, force: bool = False):
    """Remove a Docker image."""
    try:
        infrastructure_service = get_infrastructure_service()
        success = infrastructure_service.remove_image(image_id, force)
        if success:
            return {"message": f"Image {image_id} removed successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to remove image {image_id}")
    except Exception as e:
        logger.error(f"Error removing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/images/{image_id}/inspect")
async def inspect_image(image_id: str):
    """Inspect a Docker image."""
    try:
        infrastructure_service = get_infrastructure_service()
        image_info = infrastructure_service.inspect_image(image_id)
        if image_info:
            return {"image": image_info}
        else:
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
    except Exception as e:
        logger.error(f"Error inspecting image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# System information endpoints
@app.get("/system/info")
async def get_system_info():
    """Get system information."""
    try:
        infrastructure_service = get_infrastructure_service()
        info = infrastructure_service.get_system_info()
        return {"system_info": info}
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def run_infrastructure_api(host: str = "127.0.0.1", port: int = 4200):
    """Run the infrastructure API server."""
    print(f"[DEBUG] Calling uvicorn.run(app, host={host}, port={port})")
    uvicorn.run(app, host=host, port=port, log_level="info", reload=False)
    print("[DEBUG] uvicorn.run returned (this should not happen unless the server stopped)")

def main():
    """Main entry point for the infrastructure API."""
    import argparse

    parser = argparse.ArgumentParser(description="Anvyl Infrastructure API")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=4200, help="Port to bind to")

    args = parser.parse_args()

    print(f"Starting Anvyl Infrastructure API on {args.host}:{args.port}")
    run_infrastructure_api(args.host, args.port)

if __name__ == "__main__":
    main()