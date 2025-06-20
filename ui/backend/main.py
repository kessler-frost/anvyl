"""
Anvyl UI Backend API

FastAPI backend that provides a REST API bridge to the Anvyl infrastructure orchestrator.
This allows the React frontend to interact with the Anvyl system through HTTP requests.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock Anvyl client for development (replace with actual gRPC client)
class AnvylClient:
    def __init__(self, host="localhost", port=50051):
        self.host = host
        self.port = port

    def connect(self):
        logger.info(f"Connecting to Anvyl at {self.host}:{self.port}")

    def disconnect(self):
        logger.info("Disconnecting from Anvyl")

    def list_hosts(self):
        return []

    def list_containers(self, host_id=None):
        return []

app = FastAPI(
    title="Anvyl UI API",
    description="REST API bridge for Anvyl infrastructure orchestrator",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global client instance
anvyl_client: Optional[AnvylClient] = None

def get_anvyl_client() -> AnvylClient:
    """Get or create the Anvyl gRPC client"""
    global anvyl_client
    if anvyl_client is None:
        anvyl_client = AnvylClient("localhost", 50051)
        anvyl_client.connect()
    return anvyl_client

# Pydantic models for API
class Host(BaseModel):
    id: str
    name: str
    ip: str
    os: str = ""
    status: str = "unknown"
    tags: List[str] = []

class Container(BaseModel):
    id: str
    name: str
    image: str
    status: str
    host_id: str = ""
    ports: List[str] = []
    labels: Dict[str, str] = {}
    environment: List[str] = []
    volumes: List[str] = []

class CreateHostRequest(BaseModel):
    name: str
    ip: str
    os: str = ""
    tags: List[str] = []

class CreateContainerRequest(BaseModel):
    name: str
    image: str
    host_id: str = ""
    ports: List[str] = []
    labels: Dict[str, str] = {}
    environment: List[str] = []
    volumes: List[str] = []

# API Routes

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Anvyl UI API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Extended health check with gRPC connection status"""
    try:
        client = get_anvyl_client()
        return {
            "status": "healthy",
            "grpc_connected": True,
            "server": f"{client.host}:{client.port}"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "grpc_connected": False,
            "error": str(e)
        }

# Host endpoints
@app.get("/api/hosts", response_model=List[Host])
async def list_hosts():
    """List all registered hosts"""
    try:
        client = get_anvyl_client()
        hosts = client.list_hosts()
        return [
            Host(
                id=getattr(host, 'id', ''),
                name=getattr(host, 'name', ''),
                ip=getattr(host, 'ip', ''),
                os=getattr(host, 'os', ''),
                status=getattr(host, 'status', 'unknown'),
                tags=list(getattr(host, 'tags', []))
            )
            for host in hosts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list hosts: {str(e)}")

@app.post("/api/hosts", response_model=Host)
async def create_host(host_data: CreateHostRequest):
    """Add a new host to the system"""
    try:
        client = get_anvyl_client()
        result = client.add_host(host_data.name, host_data.ip, host_data.os, host_data.tags)
        if result:
            return Host(
                id=getattr(result, 'id', ''),
                name=host_data.name,
                ip=host_data.ip,
                os=host_data.os,
                status="online",
                tags=host_data.tags
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to create host")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create host: {str(e)}")

@app.get("/api/hosts/{host_id}/metrics")
async def get_host_metrics(host_id: str):
    """Get host metrics"""
    try:
        client = get_anvyl_client()
        metrics = client.get_host_metrics(host_id)
        if metrics:
            return {
                "cpu_count": getattr(metrics, 'cpu_count', 0),
                "memory_total": getattr(metrics, 'memory_total', 0),
                "memory_available": getattr(metrics, 'memory_available', 0),
                "disk_total": getattr(metrics, 'disk_total', 0),
                "disk_available": getattr(metrics, 'disk_available', 0)
            }
        else:
            raise HTTPException(status_code=404, detail="Host not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get host metrics: {str(e)}")

# Container endpoints
@app.get("/api/containers", response_model=List[Container])
async def list_containers(host_id: Optional[str] = None):
    """List containers, optionally filtered by host"""
    try:
        client = get_anvyl_client()
        containers = client.list_containers(host_id)
        return [
            Container(
                id=getattr(container, 'id', ''),
                name=getattr(container, 'name', ''),
                image=getattr(container, 'image', ''),
                status=getattr(container, 'status', 'unknown'),
                host_id=getattr(container, 'host_id', ''),
                ports=list(getattr(container, 'ports', [])),
                labels=dict(getattr(container, 'labels', {}))
            )
            for container in containers
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list containers: {str(e)}")

@app.post("/api/containers", response_model=Container)
async def create_container(container_data: CreateContainerRequest):
    """Create a new container"""
    try:
        client = get_anvyl_client()
        result = client.add_container(
            name=container_data.name,
            image=container_data.image,
            host_id=container_data.host_id,
            ports=container_data.ports,
            labels=container_data.labels,
            environment=container_data.environment,
            volumes=container_data.volumes
        )
        if result:
            return Container(
                id=getattr(result, 'id', ''),
                name=container_data.name,
                image=container_data.image,
                status=getattr(result, 'status', 'unknown'),
                host_id=container_data.host_id,
                ports=container_data.ports,
                labels=container_data.labels,
                environment=container_data.environment,
                volumes=container_data.volumes
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to create container")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create container: {str(e)}")

@app.post("/api/containers/{container_id}/stop")
async def stop_container(container_id: str, timeout: int = 10):
    """Stop a container"""
    try:
        client = get_anvyl_client()
        success = client.stop_container(container_id, timeout)
        if success:
            return {"status": "success", "message": f"Container {container_id} stopped"}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop container")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop container: {str(e)}")

@app.get("/api/containers/{container_id}/logs")
async def get_container_logs(container_id: str, tail: int = 100):
    """Get container logs"""
    try:
        client = get_anvyl_client()
        logs = client.get_logs(container_id, tail=tail)
        if logs:
            return {"logs": logs}
        else:
            return {"logs": ""}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get container logs: {str(e)}")

# System status endpoint
@app.get("/api/system/status")
async def get_system_status():
    """Get overall system status"""
    try:
        client = get_anvyl_client()
        hosts = client.list_hosts()
        containers = client.list_containers()

        return {
            "hosts": {
                "total": len(hosts),
                "online": len([h for h in hosts if getattr(h, 'status', '') == 'online'])
            },
            "containers": {
                "total": len(containers),
                "running": len([c for c in containers if getattr(c, 'status', '') == 'running'])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)