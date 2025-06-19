from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os

# Add the parent directory to the path to import from anvyl
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from anvyl.grpc_client import AnvylClient
except ImportError:
    # Fallback for development - create a mock client
    class AnvylClient:
        def __init__(self, host="localhost", port=50051):
            self.host = host
            self.port = port
            
        def connect(self):
            return True
            
        def disconnect(self):
            pass
            
        def list_hosts(self):
            return []
            
        def list_containers(self, host_id=None):
            return []
            
        def list_agents(self, host_id=None):
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

class Agent(BaseModel):
    id: str
    name: str
    host_id: str
    status: str
    entrypoint: str
    working_directory: str = ""
    persistent: bool = False
    arguments: List[str] = []
    environment: List[str] = []

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

class CreateAgentRequest(BaseModel):
    name: str
    host_id: str
    entrypoint: str
    working_directory: str = ""
    persistent: bool = False
    arguments: List[str] = []
    environment: List[str] = []

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
            labels=container_data.labels,
            ports=container_data.ports,
            volumes=container_data.volumes,
            environment=container_data.environment
        )
        if result:
            return Container(
                id=getattr(result, 'id', ''),
                name=container_data.name,
                image=container_data.image,
                status="creating",
                host_id=container_data.host_id,
                ports=container_data.ports,
                labels=container_data.labels
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
        logs = client.get_logs(container_id, follow=False, tail=tail)
        return {"logs": logs or ""}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get container logs: {str(e)}")

# Agent endpoints
@app.get("/api/agents", response_model=List[Agent])
async def list_agents(host_id: Optional[str] = None):
    """List agents, optionally filtered by host"""
    try:
        client = get_anvyl_client()
        agents = client.list_agents(host_id)
        return [
            Agent(
                id=getattr(agent, 'id', ''),
                name=getattr(agent, 'name', ''),
                host_id=getattr(agent, 'host_id', ''),
                status=getattr(agent, 'status', 'unknown'),
                entrypoint=getattr(agent, 'entrypoint', ''),
                working_directory=getattr(agent, 'working_directory', ''),
                persistent=getattr(agent, 'persistent', False)
            )
            for agent in agents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")

@app.post("/api/agents", response_model=Agent)
async def launch_agent(agent_data: CreateAgentRequest):
    """Launch a new agent"""
    try:
        client = get_anvyl_client()
        result = client.launch_agent(
            name=agent_data.name,
            host_id=agent_data.host_id,
            entrypoint=agent_data.entrypoint,
            env=agent_data.environment,
            working_directory=agent_data.working_directory,
            arguments=agent_data.arguments,
            persistent=agent_data.persistent
        )
        if result:
            return Agent(
                id=getattr(result, 'id', ''),
                name=agent_data.name,
                host_id=agent_data.host_id,
                status="starting",
                entrypoint=agent_data.entrypoint,
                working_directory=agent_data.working_directory,
                persistent=agent_data.persistent
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to launch agent")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to launch agent: {str(e)}")

@app.post("/api/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """Stop an agent"""
    try:
        client = get_anvyl_client()
        success = client.stop_agent(agent_id)
        if success:
            return {"status": "success", "message": f"Agent {agent_id} stopped"}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop agent")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop agent: {str(e)}")

# System endpoints
@app.get("/api/system/status")
async def get_system_status():
    """Get overall system status"""
    try:
        client = get_anvyl_client()
        hosts = client.list_hosts()
        containers = client.list_containers()
        agents = client.list_agents()
        
        return {
            "hosts": {
                "total": len(hosts),
                "online": len([h for h in hosts if getattr(h, 'status', '') == 'online'])
            },
            "containers": {
                "total": len(containers),
                "running": len([c for c in containers if getattr(c, 'status', '') == 'running'])
            },
            "agents": {
                "total": len(agents),
                "running": len([a for a in agents if getattr(a, 'status', '') == 'running'])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)