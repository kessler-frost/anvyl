# Anvyl - AI-Powered Infrastructure Management

A modern, self-hosted infrastructure management platform that uses AI agents to manage infrastructure using natural language.

## 🚀 Features

- **AI Agent System**: Natural language infrastructure management
- **Container Orchestration**: Docker container management via API
- **CLI Interface**: Comprehensive command-line automation
- **MCP Server**: Integration with AI applications like Claude Desktop
- **Service Management**: Unified process management with PID files

## 🚀 Quick Start

### 1. Install Anvyl

```bash
git clone https://github.com/kessler-frost/anvyl.git
cd anvyl
pip install .
```

### 2. Start All Services

```bash
# Start all services (Agent, Infrastructure API, MCP Server)
anvyl up

# Or start individual services
anvyl agent up
anvyl infra up
anvyl mcp up

# Agent API at http://localhost:4202
# Infrastructure API at http://localhost:4200
# MCP Server at http://localhost:4201
```

### 3. Use the AI Agent

```bash
# Query the agent directly
anvyl agent "Show me all running containers"
anvyl agent "Create a new nginx container on port 8080"
anvyl agent "What's the CPU usage on this host?"

# Or use explicit query command
anvyl agent query "Show me all running containers"

# Manage remote hosts
anvyl agent add-host host-b 192.168.1.101
anvyl agent "List containers on host-b" --host-id host-b
```

### 4. Check Service Status and Use AI Agent

```bash
# Check status
anvyl status

# Query the AI agent
anvyl agent "Show me all running containers"
anvyl agent "Create a new nginx container on port 8080"

# View logs
anvyl agent logs
anvyl infra logs
```

## 🔌 MCP Server Integration

Integrate with Claude Desktop by adding this to your configuration:

```json
{
  "mcpServers": {
    "anvyl-infrastructure": {
      "command": "python",
      "args": ["-m", "anvyl.mcp.server"]
    }
  }
}
```

Then ask Claude to manage your infrastructure: "Show me all running containers", "Create an nginx server", etc.

## 📋 CLI Commands

```bash
# Service management
anvyl up                    # Start all services
anvyl down                  # Stop all services
anvyl status                # Show service status
anvyl restart               # Restart all services

# AI Agent
anvyl agent "Your query"    # Query the agent
anvyl agent up/down/logs    # Manage agent service
anvyl agent add-host <id> <ip>  # Add remote host

# Individual services
anvyl infra up/down/status/logs
anvyl mcp up/down/status/logs
```

## 🛠️ Development

**Prerequisites**: Python 3.10+, Docker Desktop, LM Studio (recommended)

```bash
git clone https://github.com/kessler-frost/anvyl.git
cd anvyl
pip install . -e
anvyl up
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
