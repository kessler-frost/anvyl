# Anvyl CLI Usage Guide

The Anvyl CLI provides a command-line interface for managing your Anvyl infrastructure orchestrator. It uses the same gRPC API as the Python SDK but provides a user-friendly CLI experience.

## 🚀 Installation

### Quick Installation
```bash
# Install the package with all dependencies
pip install -e .

# Verify installation
anvyl --help
```

### Development Installation
```bash
# Install with development dependencies
pip install -e ".[dev]"
```

## Basic Usage

All commands follow the pattern:
```bash
anvyl [OPTIONS] COMMAND [ARGS]...
```

### Global Options
- `--help` - Show help and exit
- Most commands also support:
  - `--host HOST` - Anvyl server host (default: localhost)
  - `--port PORT` - Anvyl server port (default: 50051)
  - `--output FORMAT` - Output format: table or json

## Commands Overview

### System Status
```bash
# Show overall system status
anvyl status

# Show version
anvyl version
```

## Host Management

### List Hosts
```bash
# List all hosts (table format)
anvyl host list

# List hosts in JSON format
anvyl host list --output json

# Connect to remote server
anvyl host list --host 192.168.1.100 --port 50051
```

### Add Host
```bash
# Add a new host
anvyl host add "macbook-pro" "192.168.1.101"

# Add host with OS and tags
anvyl host add "mac-studio" "192.168.1.102" --os "macOS 15" --tag "production" --tag "gpu"
```

### Host Metrics
```bash
# Get host metrics
anvyl host metrics "host-id-12345"

# Get metrics in JSON format
anvyl host metrics "host-id-12345" --output json
```

## Container Management

### List Containers
```bash
# List all containers
anvyl container list

# List containers on specific host
anvyl container list --host-id "host-id-12345"

# JSON output
anvyl container list --output json
```

### Create Containers
```bash
# Simple container
anvyl container create "web-app" "nginx:alpine"

# Container with port mapping
anvyl container create "web-server" "nginx:alpine" --port "8080:80"

# Full featured container
anvyl container create "my-app" "myapp:latest" \
  --host-id "host-12345" \
  --port "8080:80" \
  --port "8443:443" \
  --volume "/Users/me/data:/app/data" \
  --volume "/Users/me/logs:/app/logs:ro" \
  --env "NODE_ENV=production" \
  --env "DATABASE_URL=postgresql://user:pass@db:5432/myapp" \
  --label "app=web" \
  --label "env=production"
```

### Container Operations
```bash
# Stop a container
anvyl container stop "container-id-12345"

# Stop with custom timeout
anvyl container stop "container-id-12345" --timeout 30

# Get container logs
anvyl container logs "container-id-12345"

# Follow logs (real-time)
anvyl container logs "container-id-12345" --follow

# Get last 50 lines
anvyl container logs "container-id-12345" --tail 50

# Execute command in container
anvyl container exec "container-id-12345" ls -la /app

# Execute with TTY
anvyl container exec "container-id-12345" --tty bash
```

## Agent Management

### List Agents
```bash
# List all agents
anvyl agent list

# List agents on specific host
anvyl agent list --host-id "host-id-12345"

# JSON output
anvyl agent list --output json
```

### Launch Agents
```bash
# Simple agent
anvyl agent launch "backup-agent" "host-12345" "/path/to/backup.py"

# Agent with environment and arguments
anvyl agent launch "monitor-agent" "host-12345" "/path/to/monitor.py" \
  --env "LOG_LEVEL=DEBUG" \
  --env "CONFIG_PATH=/etc/monitor.conf" \
  --workdir "/opt/monitoring" \
  --arg "--interval" \
  --arg "60" \
  --persistent
```

### Agent Operations
```bash
# Stop an agent
anvyl agent stop "agent-id-12345"
```

## Advanced Usage Examples

### Multi-Host Deployment
```bash
# List all hosts to see available targets
anvyl host list

# Deploy web app on first host
anvyl container create "web-frontend" "nginx:alpine" \
  --host-id "mac-mini-001" \
  --port "8080:80" \
  --label "tier=frontend"

# Deploy database on second host
anvyl container create "postgres-db" "postgres:15" \
  --host-id "mac-studio-002" \
  --port "5432:5432" \
  --env "POSTGRES_DB=myapp" \
  --env "POSTGRES_USER=admin" \
  --env "POSTGRES_PASSWORD=secret123" \
  --volume "/Users/admin/postgres-data:/var/lib/postgresql/data" \
  --label "tier=database"

# Deploy monitoring on third host
anvyl container create "monitoring" "grafana/grafana:latest" \
  --host-id "macbook-pro-003" \
  --port "3000:3000" \
  --label "tier=monitoring"
```

### Development Workflow
```bash
# Check system status
anvyl status

# Create development container
anvyl container create "dev-env" "node:18-alpine" \
  --port "3000:3000" \
  --volume "/Users/me/project:/app" \
  --env "NODE_ENV=development" \
  --label "env=development"

# Follow development logs
anvyl container logs "dev-container-id" --follow

# Execute commands for debugging
anvyl container exec "dev-container-id" npm install
anvyl container exec "dev-container-id" npm test
```

### Production Monitoring
```bash
# Regular status check
anvyl status

# Check all containers
anvyl container list

# Get metrics for production hosts
for host in $(anvyl host list --output json | jq -r '.[].id'); do
  echo "=== Metrics for $host ==="
  anvyl host metrics "$host"
done

# Check logs for errors
anvyl container logs "prod-web-app" --tail 100 | grep ERROR
```

### Automation with JSON Output
```bash
# Script to restart failed containers
#!/bin/bash
anvyl container list --output json | \
  jq -r '.[] | select(.status == "exited") | .id' | \
  while read container_id; do
    echo "Restarting container: $container_id"
    # Note: restart functionality would need to be added to the API
    # anvyl container restart "$container_id"
  done

# Export system state
anvyl host list --output json > hosts.json
anvyl container list --output json > containers.json
anvyl agent list --output json > agents.json
```

## Environment Variables

You can set default connection parameters using environment variables:

```bash
export ANVYL_HOST="192.168.1.100"
export ANVYL_PORT="50051"

# Now these commands will use the default connection
anvyl status
anvyl host list
```

## Troubleshooting

### Connection Issues
```bash
# Test basic connectivity
anvyl status

# Try connecting to specific host
anvyl status --host 192.168.1.100 --port 50051

# Check if gRPC server is running
python anvyl_grpc_server.py
```

### Debug Mode
```bash
# Enable verbose logging (if implemented)
export ANVYL_DEBUG=1
anvyl status
```

### Common Error Messages

**"Error connecting to Anvyl server"**
- Ensure the gRPC server is running: `python anvyl_grpc_server.py`
- Check the host and port parameters
- Verify network connectivity

**"No hosts/containers/agents found"**
- This is normal for a fresh installation
- Add hosts first, then containers

**"Failed to create container"**
- Check if the specified host exists
- Verify the Docker image is available
- Check for port conflicts

## Tips and Best Practices

1. **Use JSON output for scripting**: `--output json`
2. **Always specify host-id for containers** in multi-host setups
3. **Use labels consistently** for easier management
4. **Follow container logs** during development: `--follow`
5. **Set up aliases** for common commands:
   ```bash
   alias ans="anvyl status"
   alias anl="anvyl container list"
   alias anh="anvyl host list"
   ```

6. **Use environment variables** for default connection settings
7. **Regular monitoring** with status checks and log reviews
8. **Backup important data** before major operations