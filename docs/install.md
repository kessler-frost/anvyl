# Anvyl Installation Guide

This guide covers the complete installation and setup process for Anvyl Infrastructure Orchestrator.

## Prerequisites

- **macOS 15+** (Apple Silicon recommended)
- **Python 3.12+**
- **Docker Desktop** (for container management)
- **Homebrew** (for development tools)

## Quick Installation

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/anvyl.git
cd anvyl

# Run the automated setup script
./scripts/dev_setup.sh

# Start the infrastructure
anvyl up
```

### Option 2: Manual Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/anvyl.git
cd anvyl

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e .

# 4. Generate protobuf files (automatically done on first import)
python -c "from anvyl.proto_utils import ensure_protos_generated; ensure_protos_generated()"

# 5. Start the infrastructure
anvyl up
```

## Development Setup

### 1. Install Development Tools

```bash
# Install protobuf compiler
brew install protobuf

# Install with development dependencies
pip install -e ".[dev]"
```

### 2. Generate Protocol Buffers

```bash
# Generate Python code from proto files (done automatically)
python anvyl/generate_protos.py
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=anvyl

# Run specific test categories
pytest -m unit
pytest -m integration
```

## Docker Setup

### Building Images

```bash
# Build all images
anvyl up --build

# Build individual components
docker build -f Dockerfile.grpc-server -t anvyl/grpc-server:latest .
docker build -f ui/backend/Dockerfile -t anvyl/ui-backend:latest .
docker build -f ui/frontend/Dockerfile -t anvyl/ui-frontend:latest ui/frontend/
```

### Running with Docker Compose

```bash
# Start the complete stack
cd ui
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the stack
docker-compose down
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# gRPC Server Configuration
ANVYL_HOST=localhost
ANVYL_PORT=50051
ANVYL_DB_PATH=./anvyl.db

# UI Configuration
UI_FRONTEND_PORT=3000
UI_BACKEND_PORT=8000

# Docker Configuration
DOCKER_NETWORK=anvyl-network
```

### Database Configuration

The default SQLite database is automatically created at `./anvyl.db`. For production use, consider using PostgreSQL:

```python
# In your configuration
DATABASE_URL = "postgresql://user:password@localhost/anvyl"
```

## Verification

### 1. Check Installation

```bash
# Verify CLI installation
anvyl --version

# Test gRPC client
python -c "from anvyl.grpc_client import AnvylClient; print('✅ gRPC client imported successfully')"

# Test server connection
anvyl status
```

### 2. Access Points

After starting the infrastructure:

- **Web UI**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **gRPC Server**: localhost:50051

### 3. Basic Operations

```bash
# List hosts
anvyl host list

# Add a host
anvyl host add my-host 192.168.1.100

# List containers
anvyl container list

# Create a container
anvyl container create web-app nginx:latest --port 8080:80
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :50051

   # Kill the process
   kill -9 <PID>
   ```

2. **Docker Not Running**
   ```bash
   # Start Docker Desktop
   open -a Docker

   # Wait for Docker to be ready
   docker ps
   ```

3. **Permission Issues**
   ```bash
   # Fix file permissions
   chmod +x scripts/*.sh

   # Run with sudo if needed
   sudo anvyl up
   ```

4. **Protobuf Generation Issues**
   ```bash
   # Reinstall protobuf tools
   pip uninstall grpcio-tools
   pip install grpcio-tools

   # Regenerate protobuf files
   python anvyl/generate_protos.py
   ```

### Logs and Debugging

```bash
# View infrastructure logs
anvyl logs

# View specific service logs
anvyl logs frontend
anvyl logs backend
anvyl logs grpc-server

# Enable debug logging
export ANVYL_LOG_LEVEL=DEBUG
anvyl up
```

## Production Deployment

### Security Considerations

1. **Network Security**
   - Use HTTPS in production
   - Configure firewall rules
   - Use VPN for remote access

2. **Authentication**
   - Implement API key authentication
   - Use OAuth2 for web UI
   - Enable TLS for gRPC

3. **Data Protection**
   - Encrypt database at rest
   - Use secure environment variables
   - Regular backups

### Scaling

1. **Horizontal Scaling**
   - Deploy multiple gRPC server instances
   - Use load balancer for API
   - Implement service discovery

2. **Database Scaling**
   - Use PostgreSQL for production
   - Implement read replicas
   - Consider connection pooling

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/anvyl/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/anvyl/discussions)

---

For additional help, please refer to the [README.md](README.md) or create an issue on GitHub.