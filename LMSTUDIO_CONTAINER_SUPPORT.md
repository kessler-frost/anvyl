# LMStudio Container Support for MLX Models

This document describes the new LMStudio container support feature in Anvyl, which allows you to run user-specified MLX models in containerized environments using LMStudio's Python SDK.

## Overview

The LMStudio container support feature provides:

- **MLX Model Containers**: Run Apple Silicon optimized MLX models in isolated Docker containers
- **LMStudio Integration**: Leverages LMStudio's Python SDK for model management
- **Container Orchestration**: Full integration with Anvyl's container management system
- **Health Monitoring**: Built-in health checks and monitoring for model containers
- **Memory Management**: Configurable memory limits for model containers

## Prerequisites

1. **LMStudio Installation**: LMStudio must be installed and running on your system
2. **MLX Models**: You need MLX-format models downloaded via LMStudio
3. **Docker**: Docker must be available for container management
4. **Anvyl Infrastructure**: Anvyl gRPC server must be running

## Installation

The LMStudio SDK is automatically included as a dependency in Anvyl:

```bash
# Install Anvyl with LMStudio support
pip install anvyl

# Or upgrade existing installation
pip install --upgrade anvyl
```

## CLI Commands

### List Available Models

```bash
# List downloaded and loaded MLX models
anvyl model list

# Output in JSON format
anvyl model list --output json
```

### Start a Model Container

```bash
# Start a model container with basic configuration
anvyl model start llama-3.2-1b-instruct-mlx

# Start with custom container name and port
anvyl model start llama-3.2-1b-instruct-mlx \
    --name my-llama-model \
    --port 8080

# Start with memory limit
anvyl model start llama-3.2-1b-instruct-mlx \
    --memory 8g \
    --port 8080

# Start on specific host
anvyl model start llama-3.2-1b-instruct-mlx \
    --host-id my-host-01 \
    --port 8080
```

### List Running Model Containers

```bash
# List all running MLX model containers
anvyl model ps

# Output in JSON format
anvyl model ps --output json
```

### Stop a Model Container

```bash
# Stop by model ID
anvyl model stop llama-3.2-1b-instruct-mlx

# Stop by container name
anvyl model stop my-llama-model

# Stop by container ID
anvyl model stop abc123def456
```

## Command Options

### `anvyl model start`

| Option | Description | Default |
|--------|-------------|---------|
| `model_id` | Model ID to start (must contain 'mlx') | Required |
| `--name, -n` | Container name | `model-<model_id>` |
| `--port, -p` | Port to expose LMStudio server | `1234` |
| `--host-id` | Target host ID | Current host |
| `--memory, -m` | Memory limit (e.g., 8g, 4096m) | No limit |
| `--anvyl-host` | Anvyl server host | `localhost` |
| `--anvyl-port` | Anvyl server port | `50051` |

### `anvyl model list`

| Option | Description | Default |
|--------|-------------|---------|
| `--output, -o` | Output format (table, json) | `table` |
| `--host, -h` | Anvyl server host | `localhost` |
| `--port, -p` | Anvyl server port | `50051` |

### `anvyl model ps`

| Option | Description | Default |
|--------|-------------|---------|
| `--output, -o` | Output format (table, json) | `table` |
| `--anvyl-host` | Anvyl server host | `localhost` |
| `--anvyl-port` | Anvyl server port | `50051` |

### `anvyl model stop`

| Option | Description | Default |
|--------|-------------|---------|
| `model_id` | Model ID, container name, or container ID | Required |
| `--anvyl-host` | Anvyl server host | `localhost` |
| `--anvyl-port` | Anvyl server port | `50051` |

## Container Features

### Model Server

Each model container runs:
- **LMStudio Server**: Accessible on port 1234 (mapped to host port)
- **Health Check Endpoint**: Available on port 8080/health
- **Model Loading**: Automatic model loading and initialization
- **Keep-Alive**: Continuous operation to serve the model

### Health Monitoring

Model containers include built-in health checks:
- **Health Endpoint**: `http://localhost:8080/health`
- **Check Interval**: Every 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3 attempts
- **Start Period**: 60 seconds for initial loading

### Container Labels

Model containers are labeled for easy identification:
- `anvyl.service=lmstudio-model`
- `anvyl.model.id=<model_id>`
- `anvyl.model.type=mlx`

## Usage Examples

### Basic Model Deployment

```bash
# 1. Check available models
anvyl model list

# 2. Start a model container
anvyl model start llama-3.2-1b-instruct-mlx --port 8080

# 3. Check container status
anvyl model ps

# 4. Test the model (using curl)
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.2-1b-instruct-mlx",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# 5. Stop the model
anvyl model stop llama-3.2-1b-instruct-mlx
```

### Multiple Model Deployment

```bash
# Start multiple models on different ports
anvyl model start llama-3.2-1b-instruct-mlx --name llama-small --port 8080
anvyl model start llama-3.2-3b-instruct-mlx --name llama-medium --port 8081

# Check all running models
anvyl model ps

# Stop specific models
anvyl model stop llama-small
anvyl model stop llama-medium
```

### Production Deployment

```bash
# Start with memory limit and custom name
anvyl model start llama-3.2-7b-instruct-mlx \
    --name production-llama \
    --port 8080 \
    --memory 16g \
    --host-id production-host-01

# Monitor logs
anvyl container logs production-llama --follow

# Check health
curl http://localhost:8080/health
```

## Integration with Anvyl

### Container Management

Model containers are fully integrated with Anvyl's container management:

```bash
# List all containers (including model containers)
anvyl container list

# Get container logs
anvyl container logs <container_id>

# Execute commands in container
anvyl container exec <container_id> ps aux

# Stop container directly
anvyl container stop <container_id>
```

### Host Management

Model containers can be deployed to specific hosts:

```bash
# List available hosts
anvyl host list

# Start model on specific host
anvyl model start llama-3.2-1b-instruct-mlx --host-id my-host-01
```

## Troubleshooting

### Common Issues

1. **Model Not Found**
   ```bash
   # Check available models
   anvyl model list
   
   # Download model if needed (using LMStudio CLI)
   lms get llama-3.2-1b-instruct-mlx
   ```

2. **Container Fails to Start**
   ```bash
   # Check container logs
   anvyl container logs <container_id>
   
   # Check available memory
   anvyl host metrics <host_id>
   ```

3. **Port Already in Use**
   ```bash
   # Use a different port
   anvyl model start llama-3.2-1b-instruct-mlx --port 8081
   ```

4. **LMStudio SDK Not Available**
   ```bash
   # Install LMStudio SDK
   pip install lmstudio
   
   # Or upgrade Anvyl
   pip install --upgrade anvyl
   ```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Set debug environment variable
export ANVYL_DEBUG=1

# Run commands with debug output
anvyl model start llama-3.2-1b-instruct-mlx --port 8080
```

### Health Checks

Monitor container health:

```bash
# Check health endpoint
curl http://localhost:8080/health

# Check container status
anvyl model ps

# View container logs
anvyl container logs <container_id> --tail 100
```

## Advanced Configuration

### Custom Docker Images

For advanced use cases, you can create custom Docker images:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install LMStudio SDK
RUN pip install lmstudio

# Add custom configuration
COPY model_config.json /app/config.json

# Set working directory
WORKDIR /app

# Expose ports
EXPOSE 1234 8080

# Custom entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
```

### Environment Variables

Model containers support environment variables:

- `MODEL_ID`: Model identifier
- `MEMORY_LIMIT`: Memory limit for container
- `PYTHONUNBUFFERED`: Unbuffered Python output
- `STARTUP_SCRIPT`: Custom startup script path

## Security Considerations

1. **Network Isolation**: Model containers run in isolated networks
2. **Resource Limits**: Configure appropriate memory and CPU limits
3. **Access Control**: Limit access to model endpoints
4. **Monitoring**: Enable logging and monitoring for production use

## Performance Optimization

1. **Memory Allocation**: Set appropriate memory limits based on model size
2. **CPU Affinity**: Use host-specific deployment for CPU optimization
3. **Storage**: Use fast storage for model loading
4. **Network**: Optimize network configuration for model serving

## Future Enhancements

Planned features include:
- **GPU Support**: NVIDIA and AMD GPU support for model inference
- **Model Scaling**: Automatic scaling based on demand
- **Load Balancing**: Distribute requests across multiple model instances
- **Model Caching**: Persistent model caching for faster startup
- **Monitoring Dashboard**: Web-based monitoring and management interface

## Support

For issues and questions:
- Check the troubleshooting section above
- Review container logs using `anvyl container logs`
- Open issues on the Anvyl GitHub repository
- Consult the LMStudio documentation for model-specific issues

## License

This feature is part of the Anvyl project and is licensed under the MIT License.