# Anvyl - AI-Powered Infrastructure Management

A modern, self-hosted infrastructure management platform that uses AI agents to manage infrastructure across multiple hosts.

Note: Alpha Stage

## 🚀 Features

- **AI Agent System**: Intelligent agents that can manage infrastructure using natural language
- **Local Host Management**: Automatic registration and monitoring of the local host
- **Container Orchestration**: Create, manage, and monitor Docker containers via API
- **CLI Interface**: Comprehensive command-line interface for automation
- **Distributed Management**: Manage infrastructure across multiple hosts (planned)
- **Real-time Monitoring**: Live resource monitoring and status updates
- **Unified Service Management**: Simple, reliable service management with PID files
- **System Monitoring**: `system_status`

## 🏗️ Architecture

Anvyl consists of several key components:

- **AI Agents**: Intelligent agents that can understand and execute infrastructure tasks
- **Infrastructure Service**: Core service managing local host and containers
- **CLI**: Command-line interface for automation and scripting
- **Database**: SQLite-based storage for host and container data
- **Simple Service Manager**: Reliable process management using subprocess and PID files

## 🚀 Quick Start

### 1. Install Anvyl

```bash
pip install anvyl
```

### 2. Start All Services

```bash
# Start all services (Infrastructure API, Agent, MCP Server)
anvyl start

# Or start individual services
anvyl infra up --background
anvyl agent up --background
anvyl mcp up --background

# Infrastructure API at http://localhost:4200
# Agent API at http://localhost:4202
# MCP Server at http://localhost:4201
```

### 3. Check Service Status

```bash
# View all service status
anvyl status

# View service logs
anvyl infra logs
anvyl agent logs
anvyl mcp logs

# Follow logs in real-time
anvyl infra logs --follow
anvyl agent logs --follow
anvyl mcp logs --follow
```

### 4. Use the CLI

```bash
# Show system status
anvyl status

# List hosts
anvyl host list

# List containers
anvyl container list
```

## 🔧 Service Management

Anvyl uses a simple, reliable service manager for unified process management:

### Start/Stop All Services
```bash
# Start all services
anvyl start

# Stop all services
anvyl down

# Restart all services
anvyl restart
```

### Individual Service Management
```bash
# Infrastructure API
anvyl infra up --background --port 4200
anvyl infra down
anvyl infra status
anvyl infra logs --follow

# AI Agent
anvyl agent up --background --port 4202 --model-provider-url http://localhost:11434/v1
anvyl agent down
anvyl agent status
anvyl agent logs --follow

# MCP Server
anvyl mcp up --background --port 4201
anvyl mcp down
anvyl mcp status
anvyl mcp logs --follow
```

### Service Monitoring
```bash
# View all service status
anvyl status

# View specific service logs
anvyl infra logs
anvyl agent logs
anvyl mcp logs

# Follow logs in real-time
anvyl infra logs --follow
anvyl agent logs --follow
anvyl mcp logs --follow
```

For detailed service management documentation, see the service manager implementation in the codebase.

## 🤖 AI Agent System

Anvyl's AI agents can understand natural language commands and execute infrastructure tasks:

```bash
# Start an agent
anvyl agent up --model-provider-url http://localhost:11434/v1 --model llama-3.2-3b-instruct --mcp-server-url http://localhost:4201/mcp

# Query the agent
anvyl agent query "Show me all running containers"
anvyl agent query "Create a new nginx container on port 8080"
anvyl agent query "What's the CPU usage on this host?"

# Manage remote hosts
anvyl agent add-host host-b 192.168.1.101
anvyl agent query "List containers on host-b"
```

## 🔌 MCP Server Integration

Anvyl provides an MCP (Model Context Protocol) server that allows AI applications like Claude Desktop to directly manage your infrastructure:

### Quick Start

```bash
# Start the MCP server
anvyl mcp up

# Check server status
anvyl mcp status

# Stop the server
anvyl mcp down
```

### Claude Desktop Integration

Add this to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "anvyl-infrastructure": {
      "command": "python",
      "args": ["-m", "anvyl.mcp.server"],
      "env": {
        "ANVYL_MCP_SERVER": "true"
      }
    }
  }
}
```

### Available Tools

The MCP server provides these tools for AI applications:

- **Host Management**: `list_hosts`, `add_host`, `get_host_metrics`
- **Container Management**: `list_containers`, `create_container`, `remove_container`, `get_container_logs`, `exec_container_command`

### Example AI Interactions

Once integrated, you can ask Claude to:

- "Show me all running containers"
- "Create a new nginx web server on port 8080"
- "What's the system status?"
- "Get logs from the postgres container"
- "Execute 'ls -la' in the web container"

For detailed MCP server information, see the MCP server implementation in the codebase.

## 📋 CLI Commands

### Infrastructure Management

```bash
# Start the infrastructure stack
anvyl start

# Stop the infrastructure stack
anvyl down

# Show infrastructure status
anvyl status

# Show system logs
anvyl infra logs

# Show overall system status
anvyl status
```

### Host Operations

```bash
# List all hosts (not implemented yet)
anvyl host list

# Add a new host (not implemented yet)
anvyl host add my-host 192.168.1.100 --os "Linux" --tag "web-server"

# Get host metrics (not implemented yet)
anvyl host metrics <host-id>
```

**Note**: Host management is not implemented yet. Only the local host is automatically registered. This feature is planned for future releases.

### Container Operations

```bash
# List containers (not implemented yet)
anvyl container list

# Create a container (not implemented yet)
anvyl container create my-app nginx:latest --port 8080:80

# Stop a container (not implemented yet)
anvyl container stop <container-id>

# Get container logs (not implemented yet)
anvyl container logs <container-id> --follow

# Execute command in container (not implemented yet)
anvyl container exec <container-id> ls -la
```

**Note**: Container management is not implemented yet. Containers are managed through the infrastructure API. This feature is planned for future releases.

### Agent Operations

```bash
# Start an AI agent
anvyl agent up

# Stop the agent
anvyl agent down

# Query the agent
anvyl agent query "Your question here"

# List agent hosts
anvyl agent hosts

# Add a remote host to the agent
anvyl agent add-host <host-id> <host-ip>
```

### MCP Server Operations

```bash
# Start the MCP server
anvyl mcp up

# Check MCP server status
anvyl mcp status

# View MCP server logs
anvyl mcp logs

# Stop the MCP server
anvyl mcp down

# Run MCP server in foreground
anvyl mcp up --foreground
```

## 🏗️ Project Structure

```
anvyl/
├── anvyl/                    # Core package
│   ├── agent/               # AI agent system
│   │   ├── communication.py # Agent communication
│   │   ├── core.py          # Core agent functionality
│   │   └── server.py        # Agent server
│   ├── cli.py               # Command-line interface
│   ├── infra/               # Infrastructure management
│   │   ├── service.py       # Infrastructure service
│   │   ├── api.py           # Infrastructure API
│   │   └── client.py        # Infrastructure client
│   ├── mcp/                 # MCP server
│   │   ├── server.py        # MCP server implementation
│   │   └── config.json      # MCP configuration
│   └── database/
│       └── models.py        # Database models
├── examples/                # Usage examples
└── tests/                   # Test suite
```

## 🛠️ Development

### Prerequisites

- Python 3.10+
- Docker Desktop
- Unix-like operating system (Linux, macOS, BSD)
- Model provider (for AI agent functionality)

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kessler-frost/anvyl.git
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
   anvyl start
   ```

### AI Agent Development

To use the AI agent features, you'll need a model provider running locally:

1. **Install a model provider**: Options include LMStudio, Ollama, or other OpenAI-compatible providers
2. **Load a model**: Download and load a model like `llama-3.2-3b-instruct`
3. **Start the API server**: Enable the local server in your model provider
4. **Start Anvyl agent**: `anvyl agent up --model-provider-url http://localhost:11434/v1 --model llama-3.2-3b-instruct --mcp-server-url http://localhost:4201/mcp`

## 📚 Examples

See the `examples/` directory for usage examples:

- `mcp_agent_demo.py`: AI agent demonstration
- Various CLI usage patterns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🆘 Support

- Issues: [GitHub Issues](https://github.com/kessler-frost/anvyl/issues)
- Discussions: [GitHub Discussions](https://github.com/kessler-frost/anvyl/discussions)