# Anvyl Infrastructure Orchestrator

A self-hosted infrastructure management platform designed specifically for Apple Silicon, providing AI-powered automation and container orchestration capabilities.

## 🚀 Features

- **AI-Powered Infrastructure Management**: Natural language instructions for infrastructure operations
- **Container Orchestration**: Docker-based container management with isolation
- **Multi-Model AI Support**: LM Studio, Ollama, OpenAI, and Anthropic integration
- **Web UI**: Modern React-based interface for infrastructure monitoring
- **CLI Interface**: Comprehensive command-line tools for automation
- **Apple Silicon Optimized**: Designed and tested for M1/M2/M3 Macs

## 🏗️ Architecture

Anvyl uses a modular architecture with the following components:

- **Infrastructure Service**: Core service managing hosts, containers, and agents
- **AI Agents**: Containerized AI agents that execute infrastructure instructions
- **Web UI**: React frontend with FastAPI backend for monitoring and control
- **CLI**: Command-line interface for automation and scripting
- **Database**: SQLite-based storage for configuration and state

## 📦 Installation

### Prerequisites

- Python 3.12+
- Docker Desktop
- macOS (Apple Silicon recommended)

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/anvyl.git
   cd anvyl
   ```

2. **Run the setup script**:
   ```bash
   ./scripts/dev_setup.sh
   ```

3. **Start the infrastructure**:
   ```bash
   ./scripts/start_anvyl_ui.sh
   ```

4. **Create and use an AI agent**:
   ```bash
   # Create an agent
   anvyl agent create my-agent --provider lmstudio --auto-start

   # Execute instructions
   anvyl agent act my-agent "Show me all hosts"
   anvyl agent act my-agent "Create a nginx container"
   ```

## 🎯 Usage Examples

### Basic Infrastructure Management

```bash
# Check system status
anvyl status

# List all hosts
anvyl host list

# List containers
anvyl container list

# Create a container
anvyl container create my-app nginx:latest --port 8080:80
```

### AI Agent Operations

```bash
# Create an AI agent
anvyl agent create my-agent --provider lmstudio --model deepseek/deepseek-r1-0528-qwen3-8b

# Start the agent
anvyl agent start my-agent

# Execute natural language instructions
anvyl agent act my-agent "Show me all running containers"
anvyl agent act my-agent "Create a new web server container"
anvyl agent act my-agent "What's the current system status?"

# Interactive session
anvyl agent session my-agent

# View agent logs
anvyl agent logs my-agent --follow
```

### Advanced Agent Configuration

```bash
# Create agent with Ollama
anvyl agent create ollama-agent --provider ollama --model llama3.2:1b

# Create agent with OpenAI
anvyl agent create openai-agent --provider openai --model gpt-4o-mini --api-key YOUR_KEY

# Create agent with Anthropic
anvyl agent create claude-agent --provider anthropic --model claude-3-haiku-20240307 --api-key YOUR_KEY
```

## 🌐 Web Interface

Access the web interface at `http://localhost:3000` after starting the infrastructure.

Features:
- Real-time system monitoring
- Container management
- Agent status and control
- Infrastructure metrics

## 🔧 Development

### Setup Development Environment

```bash
# Run the development setup
./scripts/dev_setup.sh

# Activate virtual environment
source venv/bin/activate

# Run tests
python -m pytest

# Start development UI
./scripts/start_anvyl_ui.sh
```

### Project Structure

```
anvyl/
├── anvyl/                 # Core Python package
│   ├── infrastructure_service.py  # Main infrastructure service
│   ├── agent_manager.py   # AI agent management
│   ├── ai_agent.py        # AI agent implementation
│   ├── cli.py            # Command-line interface
│   └── model_providers.py # AI model providers
├── ui/                   # Web interface
│   ├── frontend/         # React frontend
│   └── backend/          # FastAPI backend
├── examples/             # Usage examples
├── scripts/              # Utility scripts
└── tests/                # Test suite
```

## 🤖 AI Model Providers

Anvyl supports multiple AI model providers:

### LM Studio (Default)
- **Local**: Runs on your machine
- **Models**: Any model supported by LM Studio
- **Setup**: Download and run LM Studio

### Ollama
- **Local**: Runs on your machine
- **Models**: llama3.2, codellama, mistral, etc.
- **Setup**: Install Ollama and pull models

### OpenAI
- **Cloud**: Uses OpenAI API
- **Models**: GPT-4, GPT-3.5, etc.
- **Setup**: API key required

### Anthropic
- **Cloud**: Uses Anthropic API
- **Models**: Claude-3, Claude-2, etc.
- **Setup**: API key required

## 📚 Documentation

- [CLI Usage Guide](docs/cli_usage.md)
- [Model Providers](MODEL_PROVIDERS.md)
- [AI Agent Guide](AI_AGENT_README.md)

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_models.py

# Run with coverage
python -m pytest --cov=anvyl
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/anvyl/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/anvyl/discussions)
- **Documentation**: [Wiki](https://github.com/your-org/anvyl/wiki)

## 🗺️ Roadmap

- [ ] Kubernetes integration
- [ ] Multi-host support
- [ ] Advanced monitoring and alerting
- [ ] Infrastructure as Code templates
- [ ] Plugin system for custom providers
- [ ] Mobile app for monitoring

## Agent Management

### Creating Agents
```bash
# Create a basic agent
anvyl agent create my-agent

# Create with specific provider and model
anvyl agent create my-agent --provider ollama --model llama2

# Create and auto-start
anvyl agent create my-agent --start
```

### Managing Agents
```bash
# List all agents
anvyl agent list

# Start an agent
anvyl agent start my-agent

# Stop an agent
anvyl agent stop my-agent

# Remove an agent
anvyl agent remove my-agent

# Clean up orphaned Docker resources
anvyl agent cleanup

# Clean up specific agent resources
anvyl agent cleanup my-agent
```

### Using Agents
```bash
# Execute a single action
anvyl agent act my-agent "Show me all running containers"

# Start an interactive session
anvyl agent session my-agent

# View agent logs
anvyl agent logs my-agent

# Get agent information
anvyl agent info my-agent
```

### Cleanup and Maintenance

The Anvyl agent system includes comprehensive cleanup functionality to prevent resource leaks:

- **Automatic cleanup on startup failure**: When an agent fails to start, all Docker containers, images, and temporary files are automatically cleaned up
- **Manual cleanup**: Use `anvyl agent cleanup` to remove orphaned Docker resources
- **Specific agent cleanup**: Use `anvyl agent cleanup <agent-name>` to clean up resources for a specific agent

This ensures that failed agent startups don't leave behind Docker containers, images, or temporary build directories that could consume disk space or cause conflicts.