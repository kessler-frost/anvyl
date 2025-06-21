# Anvyl - AI-Powered Infrastructure Management

A modern, self-hosted infrastructure management platform that uses AI agents to manage infrastructure across multiple hosts. Built specifically for Apple Silicon with container orchestration capabilities.

## 🚀 Features

- **AI Agent System**: Intelligent agents that can manage infrastructure using natural language
- **Host Management**: Register and monitor macOS hosts in your network
- **Container Orchestration**: Create, manage, and monitor Docker containers
- **Modern Web UI**: Beautiful, responsive interface for infrastructure management
- **CLI Interface**: Comprehensive command-line interface for automation
- **Distributed Management**: Manage infrastructure across multiple hosts
- **Real-time Monitoring**: Live resource monitoring and status updates

## 🏗️ Architecture

Anvyl consists of several key components:

- **AI Agents**: Intelligent agents that can understand and execute infrastructure tasks
- **Infrastructure Service**: Core service managing hosts and containers
- **Web UI**: Modern React-based interface with real-time updates
- **CLI**: Command-line interface for automation and scripting
- **Database**: SQLite-based storage for hosts, containers, and agent data

## 🚀 Quick Start

### 1. Install Anvyl

```bash
pip install anvyl
```

### 2. Start the Infrastructure Stack

```bash
# Start the web UI and backend services
anvyl up

# Access the web interface at http://localhost:3000
```

### 3. Start an AI Agent

```bash
# Start an AI agent (requires a model provider running locally)
anvyl agent up --model-provider-url http://localhost:1234/v1 --model llama-3.2-3b-instruct

# Query the agent
anvyl agent query "List all containers on this host"

# Get agent status
anvyl agent status

# Stop the agent
anvyl agent down
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

## 🤖 AI Agent System

Anvyl's AI agents can understand natural language commands and execute infrastructure tasks:

```bash
# Start an agent
anvyl agent up --model-provider-url http://localhost:1234/v1 --model llama-3.2-3b-instruct

# Query the agent
anvyl agent query "Show me all running containers"
anvyl agent query "Create a new nginx container on port 8080"
anvyl agent query "What's the CPU usage on this host?"

# Manage remote hosts
anvyl agent add-host host-b 192.168.1.101
anvyl agent query "List containers on host-b"
```

## 📋 CLI Commands

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

## 🎨 Web Interface

Anvyl includes a modern, responsive web interface with:

- **Dashboard**: Real-time system overview with beautiful charts
- **Host Management**: Visual host monitoring and management
- **Container Management**: Container lifecycle control and monitoring
- **Agent Management**: AI agent status and configuration
- **Settings**: System configuration and preferences

Access the web interface at `http://localhost:3000` after running `anvyl up`.

## 🏗️ Project Structure

```
anvyl/
├── anvyl/                    # Core package
│   ├── agent/               # AI agent system
│   │   ├── agent_manager.py # Agent orchestration
│   │   ├── host_agent.py    # Host-specific agents
│   │   └── tools.py         # Infrastructure tools
│   ├── cli.py               # Command-line interface
│   ├── infra/               # Infrastructure management
│   │   ├── infrastructure_service.py
│   │   └── infrastructure_client.py
│   └── database/
│       └── models.py        # Database models
├── ui/                      # Web interface
│   ├── frontend/            # React frontend
│   └── backend/             # FastAPI backend
├── examples/                # Usage examples
└── tests/                   # Test suite
```

## 🛠️ Development

### Prerequisites

- Python 3.10+
- Docker Desktop
- macOS (Apple Silicon recommended)
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
   anvyl up
   ```

### AI Agent Development

To use the AI agent features, you'll need a model provider running locally:

1. **Install a model provider**: Options include LMStudio, Ollama, or other OpenAI-compatible providers
2. **Load a model**: Download and load a model like `llama-3.2-3b-instruct`
3. **Start the API server**: Enable the local server in your model provider
4. **Start Anvyl agent**: `anvyl agent up --model-provider-url http://localhost:1234/v1 --model llama-3.2-3b-instruct`

## 📚 Examples

See the `examples/` directory for usage examples:

- `agent_demo.py`: AI agent demonstration
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

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/kessler-frost/anvyl/issues)
- Discussions: [GitHub Discussions](https://github.com/kessler-frost/anvyl/discussions)