# Anvyl: The blacksmith for your self-hosted Apple infrastructure

A self-hosted infrastructure orchestrator designed specifically for **Apple Silicon (macOS 15+)** systems, with planned future support for macOS 16's native containerization platform.

## 🎯 Overview

Anvyl is a Python-based backend system with a gRPC server and client SDK, designed to control containers (Docker for now, Apple containers later) across multiple Macs connected via **Netbird** (WireGuard-based mesh network). It's not a dev tool or package — it's a full **product** with a UI planned.

## 🏗 System Architecture

- **gRPC Server** (`anvyl_grpc_server.py`): Runs on each macOS node, interacts with Docker to manage containers
- **Python SDK** (`anvyl_sdk/`): gRPC client that abstracts server APIs for easy integration
- **Communication**: gRPC over TCP using Netbird-assigned private IPs (future: Unix Domain Sockets for local)
- **Storage**: SQLite database for persistent state (per-host or centralized)
- **Networking**: Netbird mesh network for secure inter-Mac communication

## 🛠 Tech Stack

- **Python 3.12+**
- **gRPC** + `grpcio-tools`
- **Docker SDK** for Python
- **SQLite** (via SQLModel)
- **FastAPI** (planned for UI/dashboard)
- **Netbird** (manual setup for secure networking)
- **Future**: Swift-based sidecar for Apple Containerization APIs

## 🚀 Quick Start

### Prerequisites

- macOS 15+ on Apple Silicon
- Python 3.12+
- Docker Desktop for Mac
- Homebrew (for protobuf compiler)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd anvyl
   ```

2. **Run the setup script:**
   ```bash
   ./scripts/dev_setup.sh
   ```

3. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

4. **Start the gRPC server:**
   ```bash
   python anvyl_grpc_server.py
   ```

5. **Test the client:**
   ```python
   from anvyl_sdk import create_client

   # Connect to local server
   client = create_client()

   # List containers
   containers = client.list_containers()
   print(f"Found {len(containers)} containers")

   # Add a container
   container = client.add_container(
       name="test-nginx",
       image="nginx:alpine",
       ports=["8080:80"]
   )
   ```

## 📁 Project Structure

```
anvyl/
├── anvyl_grpc_server.py           # gRPC server with Docker integration
├── anvyl_sdk/                     # Python SDK
│   ├── __init__.py
│   └── client.py                  # gRPC client implementation
├── protos/
│   └── anvyl.proto                # gRPC service definitions
├── database/
│   └── models.py                  # SQLModel database models
├── generated/                     # Auto-generated gRPC code
├── scripts/
│   └── dev_setup.sh              # Development environment setup
├── requirements.txt               # Python dependencies
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

## 🔌 API Reference

### gRPC Service Methods

#### Host Management
- `ListHosts()` - List all registered hosts
- `AddHost(name, ip)` - Add a new host to the system

#### Container Management
- `ListContainers(host_id?)` - List containers (optionally filtered by host)
- `AddContainer(name, image, host_id?, labels?, ports?, volumes?, environment?)` - Create new container
- `StopContainer(container_id, timeout?)` - Stop a running container
- `GetLogs(container_id, follow?, tail?)` - Get container logs
- `ExecCommand(container_id, command, tty?)` - Execute command in container

### SDK Client Usage

```python
from anvyl_sdk import AnvylClient

# Create client
client = AnvylClient("192.168.1.100", 50051)
client.connect()

# Host operations
hosts = client.list_hosts()
new_host = client.add_host("macbook-pro", "192.168.1.101")

# Container operations
containers = client.list_containers()
new_container = client.add_container(
    name="web-app",
    image="nginx:alpine",
    ports=["8080:80"],
    labels={"app": "web", "env": "dev"}
)

# Cleanup
client.disconnect()
```

## 🔒 Security & Networking

### Netbird Integration

Anvyl is designed to work with Netbird for secure mesh networking:

1. **Install Netbird** on each Mac
2. **Configure mesh network** with private IPs
3. **Update client connections** to use Netbird IPs instead of localhost

### Future Security Enhancements

- TLS encryption for gRPC communication
- Authentication and authorization
- Certificate-based host verification
- Unix Domain Sockets for local communication

## 🗺 Roadmap

### Phase 1: Core Infrastructure ✅
- [x] gRPC server with Docker integration
- [x] Python SDK client
- [x] SQLite database with SQLModel
- [x] Basic container management (list, create)

### Phase 2: Enhanced Container Management
- [ ] Stop container functionality
- [ ] Container logs retrieval
- [ ] Command execution in containers
- [ ] Container health monitoring

### Phase 3: UI & Dashboard
- [ ] FastAPI-based web interface
- [ ] Real-time container status
- [ ] Host management dashboard
- [ ] Log streaming interface

### Phase 4: Apple Containerization
- [ ] Swift sidecar for Apple Container APIs
- [ ] Migration from Docker to Apple containers
- [ ] macOS 16+ native containerization support

### Phase 5: Advanced Features
- [ ] Multi-host orchestration
- [ ] Service discovery
- [ ] Load balancing
- [ ] Backup and restore
- [ ] Monitoring and alerting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Open an issue on GitHub
- Check the documentation
- Join our community discussions

---

**Anvyl** - Forging the future of self-hosted Apple infrastructure, one container at a time. 🔨
