# Anvyl: The blacksmith for your self-hosted Apple infrastructure

A self-hosted infrastructure orchestrator designed specifically for **Apple Silicon (macOS 15+)** systems, with planned future support for macOS 16's native containerization platform.

> **⚠️ Alpha Stage Notice**  
> This project is currently in **alpha stage** and is under active development. Features may be incomplete, APIs may change, and the software may contain bugs. Use with caution in production environments.

## 🎯 Overview

Anvyl is a Python-based backend system with a gRPC server and client SDK, designed to control containers (Docker for now, Apple containers later) across multiple Macs connected via **Netbird** (WireGuard-based mesh network). It's not a dev tool or package — it's a full **product** with a UI planned.

## 🚀 Quick Start

### One-Command Setup (NEW!)
```bash
# Start the complete infrastructure with beautiful UI
anvyl up

# Or use the quick start script
./scripts/start_ui.sh
```

This starts:
- **Web UI**: http://localhost:3000 (Modern design with glassmorphism effects)
- **API Server**: http://localhost:8000 
- **gRPC Server**: localhost:50051

### Traditional Setup
```bash
# 1. Clone and setup
git clone https://github.com/kessler-frost/anvyl
cd anvyl
./scripts/dev_setup.sh

# 2. Start gRPC server
python anvyl_grpc_server.py

# 3. Use CLI or SDK
anvyl status
```

## 🏗 System Architecture

- **gRPC Server** (`anvyl_grpc_server.py`): Runs on each macOS node, interacts with Docker to manage containers
- **Python SDK** (`anvyl_sdk/`): gRPC client that abstracts server APIs for easy integration
- **Web UI** (`ui/`): React + FastAPI beautiful interface with modern design principles
- **CLI** (`anvyl_cli.py`): Typer-based command-line interface with infrastructure management
- **Communication**: gRPC over TCP using Netbird-assigned private IPs (future: Unix Domain Sockets for local)
- **Storage**: SQLite database for persistent state (per-host or centralized)
- **Networking**: Netbird mesh network for secure inter-Mac communication
- **Containerization**: Docker with planned Apple Containerization support

## 🛠 Tech Stack

- **Python 3.12+**
- **gRPC** + `grpcio-tools`
- **Docker SDK** for Python
- **SQLite** (via SQLModel)
- **React + TypeScript** (UI Frontend)
- **FastAPI** (UI Backend/API Bridge)
- **Tailwind CSS** (Styling with glassmorphism effects)
- **Framer Motion** (Smooth animations)
- **Netbird** (manual setup for secure networking)
- **Future**: Swift-based sidecar for Apple Containerization APIs

## 🎨 Beautiful UI (NEW!)

Experience Anvyl through a stunning web interface with modern design principles:

- **Glassmorphism Effects**: Semi-transparent cards with backdrop blur
- **Dark Theme**: Beautiful gradient backgrounds
- **Responsive Design**: Works on all devices
- **Real-time Monitoring**: Live charts and status updates
- **Intuitive Navigation**: Clean, modern interface

![Anvyl UI Preview](ui/README.md) <!-- Link to UI documentation -->

## 🐳 Container Management (NEW!)

### Infrastructure Commands
```bash
# Start complete stack
anvyl up                    # Build and start all services
anvyl up --no-build        # Start without building

# Manage infrastructure
anvyl down                  # Stop all services
anvyl ps                    # Show container status
anvyl logs                  # View logs
anvyl logs frontend -f      # Follow frontend logs
```

### Application Containers
```bash
# Deploy your applications
anvyl container create web-app nginx:alpine --port 8080:80
anvyl container list
anvyl container stop <container-id>
anvyl container logs <container-id>
```

## 📖 Usage Examples

### Basic Host Management

```python
from anvyl_sdk import create_client

# Connect to Anvyl server
client = create_client("localhost", 50051)

# List all registered hosts
hosts = client.list_hosts()
for host in hosts:
    print(f"Host: {host.name} ({host.ip}) - Agents: {host.agents_installed}")

# Add a new host to the network
new_host = client.add_host("macbook-pro-2", "192.168.1.102")
print(f"Added host: {new_host.name}")

# Disconnect when done
client.disconnect()
```

### Container Management

```python
from anvyl_sdk import create_client

client = create_client()

# List all containers
containers = client.list_containers()
print(f"Found {len(containers)} containers")

# Create a web application container
web_container = client.add_container(
    name="my-web-app",
    image="nginx:alpine",
    ports=["8080:80"],
    labels={"app": "web", "env": "production"},
    environment=["NGINX_HOST=localhost"]
)

if web_container:
    print(f"Created container: {web_container.name} ({web_container.status})")

# Create a database container
db_container = client.add_container(
    name="postgres-db",
    image="postgres:15",
    ports=["5432:5432"],
    environment=[
        "POSTGRES_DB=myapp",
        "POSTGRES_USER=admin",
        "POSTGRES_PASSWORD=secret"
    ],
    volumes=["/tmp/postgres-data:/var/lib/postgresql/data"]
)

client.disconnect()
```

### Infrastructure Orchestration (NEW!)

```python
from anvyl_sdk import create_client

client = create_client()

# Build and deploy UI stack
success = client.deploy_ui_stack("/path/to/anvyl")
if success:
    print("UI stack deployed successfully!")
    print("Access at http://localhost:3000")

# Check UI stack status
status = client.get_ui_stack_status()
for service, info in status["services"].items():
    print(f"{service}: {info['status']}")

# Stop UI stack
client.stop_ui_stack("/path/to/anvyl")
```

## 🖥 Command Line Interface (CLI)

Anvyl includes a powerful CLI built with Typer that provides an intuitive command-line interface for all operations.

### CLI Installation

```bash
# Quick install using the provided script
./scripts/install_cli.sh

# Manual installation
pip install -r requirements.txt
pip install -e .
```

### Infrastructure Management (NEW!)
```bash
# Complete infrastructure lifecycle
anvyl up                           # Start everything
anvyl down                         # Stop everything  
anvyl ps                           # Show status
anvyl logs                         # View logs

# Individual services
anvyl logs frontend                # Frontend logs
anvyl logs backend                 # Backend logs
anvyl logs grpc-server            # Core server logs
```

### Traditional CLI Usage Examples

```bash
# Show system status
anvyl status

# Host management
anvyl host list
anvyl host add "macbook-pro" "192.168.1.101" --os "macOS 15" --tag "production"
anvyl host metrics "host-id-12345"

# Container management
anvyl container list
anvyl container create "web-app" "nginx:alpine" --port "8080:80" --label "env=production"
anvyl container stop "container-id-12345"
anvyl container logs "container-id-12345" --follow

# Agent management
anvyl agent list
anvyl agent launch "backup-agent" "host-12345" "/path/to/backup.py" --persistent

# Execute commands in containers
anvyl container exec "container-id-12345" ls -la /app
```

### CLI Features

- **Rich output formatting** with colors and tables
- **JSON output support** for scripting and automation
- **Progress indicators** for long-running operations
- **Comprehensive help system** with `--help` on any command
- **Remote server support** with `--host` and `--port` options
- **Streaming log support** with `--follow` option
- **Infrastructure orchestration** with `anvyl up/down/ps`

## 📁 Project Structure

```
anvyl/
├── anvyl_grpc_server.py           # gRPC server with Docker integration
├── anvyl_cli.py                   # Typer-based CLI interface
├── Dockerfile.grpc-server         # Main server containerization
├── setup.py                       # Package setup for CLI installation
├── anvyl_sdk/                     # Python SDK
│   ├── __init__.py
│   └── client.py                  # gRPC client implementation
├── ui/                            # Web Interface (NEW!)
│   ├── docker-compose.yml         # Complete stack orchestration
│   ├── frontend/                  # React + TypeScript UI
│   │   ├── Dockerfile
│   │   ├── src/components/        # Beautiful UI components
│   │   └── nginx.conf
│   └── backend/                   # FastAPI bridge
│       ├── Dockerfile
│       └── main.py
├── protos/
│   └── anvyl.proto                # gRPC service definitions
├── database/
│   └── models.py                  # SQLModel database models
├── generated/                     # Auto-generated gRPC code
├── scripts/
│   ├── dev_setup.sh              # Development environment setup
│   ├── install_cli.sh             # CLI installation script
│   └── start_ui.sh                # Quick UI start script (NEW!)
├── docs/
│   └── cli_usage.md              # Comprehensive CLI documentation
├── requirements.txt               # Python dependencies
├── DOCKER_SETUP.md               # Container documentation (NEW!)
└── README.md
```

## 🔧 Development

### Setting Up Development Environment

The `scripts/dev_setup.sh` script automates the entire setup process:

- Installs protobuf compiler via Homebrew
- Creates Python virtual environment
- Installs all dependencies
- Generates gRPC Python code from proto files
- Checks Docker installation
- Creates configuration files

### Working with the UI (NEW!)

```bash
# Start UI development environment
cd ui/frontend
npm install
npm run dev                        # Frontend dev server (hot reload)

# In another terminal
cd ui/backend
python main.py                     # Backend API server

# Or start everything with containers
anvyl up --build
```

### Working with gRPC

1. **Modify the proto file** (`protos/anvyl.proto`)
2. **Regenerate gRPC code:**
   ```bash
   python -m grpc_tools.protoc \
       --python_out=generated \
       --grpc_python_out=generated \
       --proto_path=protos \
       protos/anvyl.proto
   ```

### Database Operations

The database uses SQLModel for type-safe database operations:

```python
from database.models import DatabaseManager, Host, Container

# Initialize database
db = DatabaseManager()

# Add a host
host = Host(id="host-1", name="mac-mini", ip="192.168.1.100")
db.add_host(host)

# List all hosts
hosts = db.list_hosts()
```

## 🐳 Containerization (NEW!)

Anvyl is now fully containerized with Docker support:

### Quick Start
```bash
anvyl up                           # One command to rule them all
```

### Architecture
- **Multi-container setup** with Docker Compose
- **Health checks** and automatic restart
- **Persistent volumes** for data storage
- **Network isolation** with custom bridge network
- **Production ready** with security considerations

See [DOCKER_SETUP.md](DOCKER_SETUP.md) for complete containerization documentation.

## 🔌 API Reference

### gRPC Service Methods

#### Host Management
- `ListHosts()` - Get all registered hosts
- `AddHost(name, ip, os, tags)` - Register a new host
- `UpdateHost(host_id, resources, status)` - Update host information
- `GetHostMetrics(host_id)` - Get current host metrics
- `HostHeartbeat(host_id)` - Update host heartbeat

#### Container Management
- `ListContainers(host_id?)` - List containers (optionally by host)
- `AddContainer(...)` - Create a new container
- `StopContainer(container_id, timeout)` - Stop a container
- `GetLogs(container_id, follow, tail)` - Get container logs
- `StreamLogs(container_id)` - Stream container logs (streaming RPC)
- `ExecCommand(container_id, command, tty)` - Execute command in container

#### Agent Management
- `ListAgents(host_id?)` - List agents (optionally by host)
- `LaunchAgent(...)` - Launch a Python agent
- `StopAgent(agent_id)` - Stop an agent
- `GetAgentStatus(agent_id)` - Get agent status

#### Infrastructure Management (NEW!)
- Build and deploy Docker images
- Orchestrate multi-container stacks
- Monitor container health and status
- Manage container logs and networking

### REST API (NEW!)

The UI backend provides a REST API bridge:

- **Base URL**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

Key endpoints:
- `GET /api/hosts` - List hosts
- `POST /api/hosts` - Add host
- `GET /api/containers` - List containers
- `POST /api/containers` - Create container
- `GET /api/system/status` - System overview

## 🚀 Quick Usage Scenarios

### Scenario 1: Complete Infrastructure Setup
```bash
# Start everything at once
anvyl up

# Access the beautiful web UI
open http://localhost:3000

# Or use the CLI
anvyl status
anvyl host list
anvyl container list
```

### Scenario 2: Deploy Application Stack
```bash
# Deploy a web application
anvyl container create web nginx:alpine --port 8080:80

# Deploy a database
anvyl container create db postgres:15 --port 5432:5432

# Monitor everything
anvyl ps
anvyl logs web -f
```

### Scenario 3: Multi-Host Network (Future)
```bash
# Add remote hosts
anvyl host add "mac-studio" "192.168.1.103"
anvyl host add "macbook-air" "192.168.1.104"

# Deploy distributed services
anvyl container create web nginx --host mac-studio
anvyl container create db postgres --host macbook-air
anvyl container create cache redis --host mac-studio
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python -m pytest`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **gRPC** for robust communication
- **Docker** for containerization
- **React** ecosystem for beautiful UI
- **FastAPI** for modern Python web development
- **Modern web design community** for inspiration and best practices

---

**Ready to manage your Apple infrastructure with style!** 🍎✨

#### 3. `anvyl-ui-frontend`
- **Image**: `anvyl/ui-frontend:latest`
- **Port**: `3000:80`
- **Purpose**: React frontend with modern design
- **Health Check**: HTTP GET `/health`
- **Dependencies**: `anvyl-ui-backend`
