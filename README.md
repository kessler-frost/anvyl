# Anvyl Infrastructure Orchestrator

A self-hosted infrastructure management platform designed specifically for Apple Silicon, providing container orchestration, host management, and agent deployment capabilities.

## 🏗️ Architecture

Anvyl consists of several key components:

- **gRPC Server** (`grpc_server.py`): Core orchestration service handling hosts, containers, and agents
- **gRPC Client** (`grpc_client.py`): Python client that abstracts server APIs for easy integration
- **CLI Tool** (`cli.py`): Command-line interface for managing infrastructure
- **Web UI** (`ui/`): React-based dashboard for visual management
- **Database** (`database/`): SQLite-based data persistence layer

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker Desktop
- Apple Silicon Mac (M1/M2/M3)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/anvyl.git
   cd anvyl
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Start the infrastructure:**
   ```bash
   anvyl up
   ```

4. **Access the web interface:**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000

## 📖 Usage

### Command Line Interface

The Anvyl CLI provides comprehensive infrastructure management:

```bash
# Start the complete stack
anvyl up

# View infrastructure status
anvyl ps

# Stop the stack
anvyl down

# View logs
anvyl logs

# Manage hosts
anvyl host list
anvyl host add my-host 192.168.1.100

# Manage containers
anvyl container list
anvyl container create my-app nginx:latest

# Manage agents
anvyl agent list
anvyl agent launch my-agent host-123 /path/to/script.py
```

### Python SDK

Use the gRPC client for programmatic access:

```python
from anvyl.grpc_client import create_client

# Create a client
client = create_client("localhost", 50051)

# List hosts
hosts = client.list_hosts()
for host in hosts:
    print(f"Host: {host.name} ({host.ip})")

# Create a container
container = client.add_container(
    name="my-app",
    image="nginx:latest",
    ports=["8080:80"]
)

# Launch an agent
agent = client.launch_agent(
    name="monitoring-agent",
    host_id="host-123",
    entrypoint="/path/to/monitor.py"
)
```

### Advanced Usage

```python
from anvyl.grpc_client import AnvylClient

# Custom client configuration
client = AnvylClient("custom-host", 50051)
if client.connect():
    # Build and deploy UI stack
    client.build_ui_images("/path/to/project")
    client.deploy_ui_stack("/path/to/project")
    
    # Get system status
    status = client.get_ui_stack_status()
    print(f"Services running: {len(status['containers'])}")
```

## 🏗️ Project Structure

```
anvyl/
├── anvyl/                      # Main package
│   ├── __init__.py
│   ├── grpc_server.py          # gRPC server implementation
│   ├── grpc_client.py          # gRPC client implementation
│   ├── cli.py                  # Command-line interface
│   ├── database/               # Database models and utilities
│   ├── protos/                 # Protocol buffer definitions
│   └── proto_utils.py          # Protobuf generation utilities
├── ui/                         # Web interface
│   ├── frontend/               # React application
│   └── backend/                # FastAPI server
├── tests/                      # Test suite
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
└── pyproject.toml              # Project configuration and dependencies
```

## 🔧 Development

### Development Dependencies

To install development dependencies for testing and code formatting:

```bash
# Install with development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=anvyl

# Run specific test file
pytest tests/test_grpc_client.py
```

### Building Docker Images

```bash
# Build all UI images
anvyl up --build

# Build specific components
docker build -f Dockerfile.grpc-server -t anvyl/grpc-server:latest .
docker build -f ui/backend/Dockerfile -t anvyl/ui-backend:latest .
docker build -f ui/frontend/Dockerfile -t anvyl/ui-frontend:latest ui/frontend/
```

### Development Mode

```bash
# Start development environment
./scripts/dev_setup.sh

# Run gRPC server in development
python -m anvyl.grpc_server

# Run UI backend in development
cd ui/backend && uvicorn main:app --reload

# Run UI frontend in development
cd ui/frontend && npm run dev
```

## 📚 API Reference

### Host Management

- `list_hosts()` - List all registered hosts
- `add_host(name, ip, os, tags)` - Register a new host
- `update_host(host_id, resources, status, tags)` - Update host information
- `get_host_metrics(host_id)` - Get host resource metrics

### Container Management

- `list_containers(host_id)` - List containers (optionally filtered by host)
- `add_container(name, image, host_id, ...)` - Create a new container
- `stop_container(container_id, timeout)` - Stop a running container
- `get_logs(container_id, follow, tail)` - Get container logs
- `exec_command(container_id, command, tty)` - Execute command in container

### Agent Management

- `list_agents(host_id)` - List agents (optionally filtered by host)
- `launch_agent(name, host_id, entrypoint, ...)` - Launch a new agent
- `stop_agent(agent_id)` - Stop a running agent
- `get_agent_status(agent_id)` - Get agent status

### Infrastructure Management

- `build_ui_images(project_root)` - Build all UI Docker images
- `deploy_ui_stack(project_root)` - Deploy complete UI stack
- `stop_ui_stack(project_root)` - Stop UI stack
- `get_ui_stack_status()` - Get status of all UI components

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/anvyl/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/anvyl/discussions)

---

Built with ❤️ for Apple Silicon

#### 3. `anvyl-ui-frontend`