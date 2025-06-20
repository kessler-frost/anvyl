# Anvyl Infrastructure Orchestrator

A self-hosted infrastructure management platform designed specifically for Apple Silicon,
providing container orchestration capabilities.

## Features

- **Host Management**: Register and monitor macOS hosts in your network
- **Container Orchestration**: Create, manage, and monitor Docker containers
- **Infrastructure Service**: Core service managing hosts and containers
- **Web UI**: Modern web interface for infrastructure management
- **CLI Interface**: Comprehensive command-line interface for automation

## Quick Start

1. **Install Anvyl**:
   ```bash
   pip install anvyl
   ```

2. **Start the infrastructure**:
   ```bash
   anvyl up
   ```

3. **Access the web interface**:
   Open http://localhost:3000 in your browser

4. **Use the CLI**:
   ```bash
   # Show system status
   anvyl status

   # List hosts
   anvyl host list

   # List containers
   anvyl container list
   ```

## CLI Commands

### Infrastructure Management

```bash
# Start the infrastructure stack
anvyl up

# Stop the infrastructure stack
anvyl down

# Show infrastructure status
anvyl ps

# Show system logs
anvyl logs

# Show overall system status
anvyl status
```

### Host Operations

```bash
# List all hosts
anvyl host list

# Add a new host
anvyl host add my-host 192.168.1.100 --os "macOS" --tag "web-server"

# Get host metrics
anvyl host metrics <host-id>
```

### Container Operations

```bash
# List containers
anvyl container list

# Create a container
anvyl container create my-app nginx:latest --port 8080:80

# Stop a container
anvyl container stop <container-id>

# Get container logs
anvyl container logs <container-id> --follow

# Execute command in container
anvyl container exec <container-id> ls -la
```

## Architecture

```
anvyl/
├── anvyl/                    # Core package
│   ├── cli.py               # Command-line interface
│   ├── infrastructure_service.py  # Infrastructure management
│   └── database/
│       └── models.py        # Database models
├── ui/                      # Web interface
│   ├── frontend/            # React frontend
│   └── backend/             # FastAPI backend
├── examples/                # Usage examples
└── tests/                   # Test suite
```

## Development

### Prerequisites

- Python 3.12+
- Docker Desktop
- macOS (Apple Silicon recommended)

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/anvyl.git
   cd anvyl
   ```

2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Run tests**:
   ```bash
   pytest
   ```

4. **Start development environment**:
   ```bash
   anvyl up
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/your-org/anvyl/issues)
- Discussions: [GitHub Discussions](https://github.com/your-org/anvyl/discussions)