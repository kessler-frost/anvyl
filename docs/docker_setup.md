# Anvyl Docker Containerization

Complete containerization setup for Anvyl infrastructure orchestrator with modern web UI.

## 🚀 Quick Start

### One-Command Setup
```bash
# Start everything with one command
anvyl up

# Or use the quick start script
./scripts/start_ui.sh
```

### Manual Setup
```bash
# 1. Build and start all services
cd ui
docker-compose up -d --build

# 2. Access the services
open http://localhost:3000  # Web UI
open http://localhost:8000  # API Server
```

## 🐳 Container Architecture

### Services Overview
```
┌─────────────────────────────────────────────────────────┐
│                    Anvyl Infrastructure                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────┐ │
│  │   Frontend      │  │    Backend      │  │  gRPC    │ │
│  │   (React)       │  │   (FastAPI)     │  │  Server  │ │
│  │   Port: 3000    │  │   Port: 8000    │  │  Port:   │ │
│  │                 │  │                 │  │  50051   │ │
│  └─────────────────┘  └─────────────────┘  └──────────┘ │
│           │                     │                │      │
│           └─────────────────────┼────────────────┘      │
│                                 │                       │
│                        ┌─────────────────┐              │
│                        │ Docker Network  │              │
│                        │ (anvyl-network) │              │
│                        └─────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

### Container Details

#### 1. `anvyl-grpc-server`
- **Image**: `anvyl/grpc-server:latest`
- **Port**: `50051:50051`
- **Purpose**: Core Anvyl gRPC server for infrastructure management
- **Health Check**: gRPC connection test
- **Volumes**: 
  - `anvyl-data:/data` (persistent storage)
  - `/var/run/docker.sock:/var/run/docker.sock` (Docker access)

#### 2. `anvyl-ui-backend`
- **Image**: `anvyl/ui-backend:latest`
- **Port**: `8000:8000`
- **Purpose**: FastAPI REST bridge to gRPC server
- **Health Check**: HTTP GET `/health`
- **Dependencies**: `anvyl-grpc-server`

#### 3. `anvyl-ui-frontend`
- **Image**: `anvyl/ui-frontend:latest`
- **Port**: `3000:80`
- **Purpose**: React frontend with modern design
- **Health Check**: HTTP GET `/health`
- **Dependencies**: `anvyl-ui-backend`

## 🛠 CLI Commands

### Infrastructure Management
```bash
# Start the complete infrastructure stack
anvyl up                    # Build and start all services
anvyl up --no-build        # Start without building images
anvyl up --logs            # Start and show logs

# Stop the infrastructure
anvyl down                  # Stop all services

# Check status
anvyl ps                    # Show running containers
anvyl status               # Show system status
```

### Logs and Monitoring
```bash
# View logs
anvyl logs                  # All services
anvyl logs frontend        # Frontend only
anvyl logs backend         # Backend only
anvyl logs grpc-server     # gRPC server only
anvyl logs -f              # Follow logs (real-time)
```

### Individual Container Management
```bash
# List containers managed by Anvyl
anvyl container list

# Create new containers
anvyl container create nginx-web nginx:alpine --port 8080:80

# Stop containers
anvyl container stop <container-id>
```

## 📁 File Structure

```
anvyl/
├── Dockerfile.grpc-server          # Main gRPC server container
├── pyproject.toml                  # Project configuration and dependencies
├── ui/
│   ├── docker-compose.yml          # Complete stack orchestration
│   ├── frontend/
│   │   ├── Dockerfile              # React app container
│   │   ├── package.json           # Node.js dependencies
│   │   └── nginx.conf             # Nginx configuration
│   └── backend/
│       ├── Dockerfile              # FastAPI container
│       └── requirements.txt       # Backend-specific dependencies
├── scripts/
│   └── start_ui.sh                # Quick start script
└── anvyl/cli.py                   # Enhanced CLI with container commands
```

## 🔧 Configuration

### Environment Variables

#### gRPC Server
```bash
ANVYL_DB_PATH=/data/anvyl.db        # Database location
ANVYL_LOG_LEVEL=INFO               # Logging level
```

#### UI Backend
```bash
ANVYL_GRPC_HOST=anvyl-grpc-server  # gRPC server hostname
ANVYL_GRPC_PORT=50051              # gRPC server port
PYTHONPATH=/app                    # Python path
```

### Network Configuration
- **Network**: `anvyl-network` (bridge)
- **Internal Communication**: Container hostnames
- **External Access**: Mapped ports

### Volume Configuration
- **anvyl-data**: Persistent storage for database and logs
- **Docker Socket**: Access to host Docker daemon

## 🏗 Building Images

### Build All Images
```bash
# Using CLI
anvyl up --build

# Using Docker Compose
cd ui
docker-compose build
```

### Build Individual Images
```bash
# gRPC Server
docker build -f Dockerfile.grpc-server -t anvyl/grpc-server:latest .

# UI Backend
docker build -f ui/backend/Dockerfile -t anvyl/ui-backend:latest .

# UI Frontend
cd ui/frontend
docker build -t anvyl/ui-frontend:latest .
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Docker Not Running
```bash
Error: Cannot connect to the Docker daemon
Solution: Start Docker Desktop or Docker service
```

#### 2. Port Conflicts
```bash
Error: Port 3000 already in use
Solution: Stop conflicting services or change ports in docker-compose.yml
```

#### 3. Build Failures
```bash
# Check Docker logs
docker logs anvyl-grpc-server
docker logs anvyl-ui-backend
docker logs anvyl-ui-frontend

# Rebuild with verbose output
docker-compose build --no-cache --progress=plain
```

#### 4. Network Issues
```bash
# Inspect network
docker network inspect anvyl-network

# Check container connectivity
docker exec anvyl-ui-backend ping anvyl-grpc-server
```

### Health Checks
```bash
# Check service health
curl http://localhost:3000/health     # Frontend
curl http://localhost:8000/health     # Backend API
anvyl status                          # Overall system
```

### Resource Usage
```bash
# Monitor resource usage
docker stats

# Check container logs
anvyl logs -f

# Inspect specific container
docker inspect anvyl-ui-frontend
```

## 🚀 Production Deployment

### Security Considerations
1. **Remove Development Ports**: Only expose necessary ports
2. **Use Secrets**: Store sensitive data in Docker secrets
3. **Network Isolation**: Use custom networks for isolation
4. **Health Monitoring**: Set up proper health checks
5. **Log Management**: Configure log rotation and shipping

### Production Compose File
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  anvyl-grpc-server:
    # ... production configuration
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Scaling
```bash
# Scale specific services
docker-compose up -d --scale anvyl-ui-backend=2

# Load balancing setup needed for multiple backend instances
```

## 📊 Monitoring & Observability

### Built-in Monitoring
- **Health Checks**: Automatic container health monitoring
- **Rich Logs**: Structured logging with Rich formatting
- **Status Dashboard**: Real-time status via `anvyl ps`

### Integration Options
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **ELK Stack**: Centralized logging
- **Jaeger**: Distributed tracing

## 🔄 Development Workflow

### Local Development
```bash
# Start in development mode
anvyl up --build

# Make changes to code
# Hot reload is enabled for frontend

# View logs in real-time
anvyl logs -f

# Rebuild specific service
docker-compose build anvyl-ui-backend
docker-compose up -d anvyl-ui-backend
```

### Testing
```bash
# Run tests in containers
docker-compose exec anvyl-ui-backend pytest
docker-compose exec anvyl-grpc-server python -m pytest

# Integration testing
anvyl status  # Verify all services are healthy
```

---

🎉 **Your Anvyl infrastructure is now fully containerized with modern web UI!**