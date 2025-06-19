# Anvyl: The blacksmith for your self-hosted Apple infrastructure

A self-hosted infrastructure orchestrator designed specifically for **Apple Silicon (macOS 15+)** systems, with planned future support for macOS 16's native containerization platform.

> **⚠️ Alpha Stage Notice**  
> This project is currently in **alpha stage** and is under active development. Features may be incomplete, APIs may change, and the software may contain bugs. Use with caution in production environments.

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
   git clone https://github.com/kessler-frost/anvyl
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

### Multi-Host Orchestration

```python
from anvyl_sdk import AnvylClient

# Connect to multiple hosts via Netbird
hosts = [
    ("192.168.1.100", 50051),  # Mac Mini
    ("192.168.1.101", 50051),  # MacBook Pro
    ("192.168.1.102", 50051),  # Mac Studio
]

clients = {}

# Connect to all hosts
for ip, port in hosts:
    try:
        client = AnvylClient(ip, port)
        if client.connect():
            clients[ip] = client
            print(f"Connected to {ip}")
        else:
            print(f"Failed to connect to {ip}")
    except Exception as e:
        print(f"Error connecting to {ip}: {e}")

# Deploy containers across hosts
for ip, client in clients.items():
    # Deploy web app on first host
    if ip == "192.168.1.100":
        container = client.add_container(
            name="web-app",
            image="nginx:alpine",
            ports=["8080:80"]
        )
        print(f"Deployed web app on {ip}")

    # Deploy database on second host
    elif ip == "192.168.1.101":
        container = client.add_container(
            name="database",
            image="postgres:15",
            ports=["5432:5432"]
        )
        print(f"Deployed database on {ip}")

    # Deploy monitoring on third host
    elif ip == "192.168.1.102":
        container = client.add_container(
            name="monitoring",
            image="grafana/grafana:latest",
            ports=["3000:3000"]
        )
        print(f"Deployed monitoring on {ip}")

# Cleanup
for client in clients.values():
    client.disconnect()
```

### Advanced Container Configuration

```python
from anvyl_sdk import create_client

client = create_client()

# Create a complex application stack
app_container = client.add_container(
    name="my-app",
    image="myapp:latest",
    ports=[
        "8080:80",      # HTTP
        "8443:443",     # HTTPS
        "9000:9000"     # Admin interface
    ],
    volumes=[
        "/Users/me/app-data:/app/data",           # Application data
        "/Users/me/app-logs:/app/logs",           # Log files
        "/Users/me/app-config:/app/config:ro"     # Read-only config
    ],
    environment=[
        "NODE_ENV=production",
        "DATABASE_URL=postgresql://user:pass@db:5432/myapp",
        "REDIS_URL=redis://cache:6379",
        "API_KEY=your-secret-key"
    ],
    labels={
        "app": "myapp",
        "version": "1.0.0",
        "environment": "production",
        "team": "backend"
    }
)

# Create a development environment
dev_container = client.add_container(
    name="dev-environment",
    image="node:18-alpine",
    ports=["3000:3000"],
    volumes=["/Users/me/project:/app"],
    environment=["NODE_ENV=development"],
    labels={"environment": "development"}
)

client.disconnect()
```

### Error Handling and Monitoring

```python
from anvyl_sdk import create_client
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    client = create_client()

    # Check system health
    hosts = client.list_hosts()
    containers = client.list_containers()

    logger.info(f"System Status: {len(hosts)} hosts, {len(containers)} containers")

    # Monitor container status
    for container in containers:
        logger.info(f"Container {container.name}: {container.status}")

        # Check for stopped containers
        if container.status == "exited":
            logger.warning(f"Container {container.name} has exited")

            # Attempt to restart
            # (This would be implemented in future versions)
            logger.info(f"Would restart container {container.name}")

    # Health check - try to create a test container
    test_container = client.add_container(
        name="health-check",
        image="alpine:latest",
        environment=["echo 'Health check passed'"]
    )

    if test_container:
        logger.info("Health check passed - container creation working")
    else:
        logger.error("Health check failed - container creation not working")

except Exception as e:
    logger.error(f"Anvyl client error: {e}")

finally:
    if 'client' in locals():
        client.disconnect()
```

### Integration with Other Tools

```python
from anvyl_sdk import create_client
import subprocess
import json

def deploy_with_ansible():
    """Deploy infrastructure using Ansible + Anvyl"""
    client = create_client()

    # Get current hosts
    hosts = client.list_hosts()

    # Generate Ansible inventory
    inventory = {
        "all": {
            "hosts": [host.ip for host in hosts],
            "vars": {
                "ansible_user": "admin",
                "ansible_ssh_private_key_file": "~/.ssh/id_rsa"
            }
        }
    }

    # Write inventory file
    with open("inventory.json", "w") as f:
        json.dump(inventory, f, indent=2)

    # Run Ansible playbook
    subprocess.run([
        "ansible-playbook",
        "-i", "inventory.json",
        "deploy.yml"
    ])

    client.disconnect()

def monitor_with_prometheus():
    """Export Anvyl metrics for Prometheus"""
    client = create_client()

    # Collect metrics
    hosts = client.list_hosts()
    containers = client.list_containers()

    metrics = {
        "anvyl_hosts_total": len(hosts),
        "anvyl_containers_total": len(containers),
        "anvyl_containers_running": len([c for c in containers if c.status == "running"]),
        "anvyl_containers_stopped": len([c for c in containers if c.status == "stopped"])
    }

    # Export in Prometheus format
    for metric, value in metrics.items():
        print(f"{metric} {value}")

    client.disconnect()
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

1. Fork the repository at https://github.com/kessler-frost/anvyl
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
