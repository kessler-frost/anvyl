# Anvyl AI Agent System

The Anvyl AI Agent System provides distributed AI agents that can manage infrastructure across multiple hosts using LangChain and tool-use capabilities.

## Overview

Each host running Anvyl can have an AI agent that:
- Manages local infrastructure using Docker primitives
- Communicates with agents on other hosts
- Provides natural language interface for infrastructure management
- Uses LangChain for intelligent tool selection and execution
- Runs on local LLMs via LMStudio for privacy and cost control

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Host A        │    │   Host B        │    │   Host C        │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ AI Agent    │ │    │ │ AI Agent    │ │    │ │ AI Agent    │ │
│ │             │ │    │ │             │ │    │ │             │ │
│ │ • Tools     │ │    │ │ • Tools     │ │    │ │ • Tools     │ │
│ │ • LLM       │ │    │ │ • LLM       │ │    │ │ • LLM       │ │
│ │ • API       │ │    │ │ • API       │ │    │ │ • API       │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Docker      │ │    │ │ Docker      │ │    │ │ Docker      │ │
│ │ Containers  │ │    │ │ Containers  │ │    │ │ Containers  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    HTTP/JSON Communication
```

## Features

### Local Infrastructure Management
- **Container Operations**: List, start, stop, create containers
- **Host Monitoring**: CPU, memory, disk usage
- **Command Execution**: Run commands on the host
- **Resource Management**: Monitor and manage system resources

### Distributed Communication
- **Agent-to-Agent Queries**: Ask questions to agents on other hosts
- **Host Discovery**: Manually add and register hosts
- **Fault Tolerance**: Handle network failures gracefully

### Natural Language Interface
- **Intelligent Queries**: Ask questions in natural language
- **Tool Selection**: AI automatically selects appropriate tools
- **Context Awareness**: Agents understand infrastructure context
- **Multi-step Reasoning**: Complex operations broken down automatically

### Local LLM Support
- **LMStudio Integration**: Use local models for privacy and cost control
- **OpenAI-Compatible API**: Works with any model served by LMStudio
- **Fallback Mode**: Graceful degradation when LLM is unavailable

## Installation

### Prerequisites
- Python 3.10+
- Docker
- LMStudio (for local LLM capabilities)
- `openai` Python package (for LMStudio integration)

### Setup
1. Install Anvyl with agent dependencies:
```bash
pip install anvyl[agent]
pip install openai
```

2. Install and configure LMStudio:
   - Download from [https://lmstudio.ai/](https://lmstudio.ai/)
   - Install and start LMStudio
   - Load a model (e.g., Llama 2, Mistral, etc.)
   - Enable the local server (Settings → Local Server → Start Server)

## Usage

### Starting an Agent

Start an AI agent on a host:

```bash
# Start with default LMStudio URL
anvyl agent start

# Start with custom LMStudio URL
anvyl agent start --lmstudio-url "http://localhost:1234/v1"

# Start with specific model
anvyl agent start --model "default"

# Start on custom port
anvyl agent start --port 8081
```

### Querying Agents

#### Local Queries
```bash
# Ask about local containers
anvyl agent query "How many containers are running?"

# Get host resources
anvyl agent query "What's the current CPU usage?"

# List all containers
anvyl agent query "Show me all containers with their status"
```

#### Remote Queries
```bash
# Query a specific remote host
anvyl agent query "How many containers are running?" --host-id "host-b-id"

# Get containers from remote host
anvyl agent query "List all containers" --host-id "host-b-id"

# Get remote host resources
anvyl agent query "What's the memory usage?" --host-id "host-b-id"
```

### Managing Known Hosts

```bash
# List known hosts
anvyl agent hosts

# Add a remote host
anvyl agent add-host "host-b-id" "192.168.1.100"

# Get agent information
anvyl agent info
```

### API Endpoints

The agent provides a REST API for programmatic access:

```bash
# Get agent info
curl http://localhost:8080/agent/info

# Process a local query
curl -X POST http://localhost:8080/agent/process \
  -H "Content-Type: application/json" \
  -d '{"query": "List all containers"}'

# Query a remote host
curl -X POST http://localhost:8080/agent/remote-query \
  -H "Content-Type: application/json" \
  -d '{"host_id": "host-b-id", "query": "How many containers are running?"}'

# List known hosts
curl http://localhost:8080/agent/hosts

# Add a known host
curl -X POST http://localhost:8080/agent/hosts \
  -H "Content-Type: application/json" \
  -d '{"host_id": "host-b-id", "host_ip": "192.168.1.100"}'
```

## Example Scenarios

### Scenario 1: Multi-Host Container Management

1. Start agents on multiple hosts:
```bash
# On Host A
anvyl agent start --lmstudio-url http://localhost:1234/v1 --model default --port 8080

# On Host B
anvyl agent start --lmstudio-url http://localhost:1234/v1 --model default --port 8081

# On Host C
anvyl agent start --lmstudio-url http://localhost:1234/v1 --model default --port 8082
```

2. Add hosts to each other's known lists:
```bash
# From Host A, add Host B and C
anvyl agent add-host "host-b-id" "192.168.1.101"
anvyl agent add-host "host-c-id" "192.168.1.102"
```

3. Query across hosts:
```bash
# From Host A, ask about containers on Host B
anvyl agent query "How many containers are running on Host B?" --host-id "host-b-id"

# From Host A, get resource usage from Host C
anvyl agent query "What's the current CPU and memory usage?" --host-id "host-c-id"
```

### Scenario 2: Infrastructure Monitoring

```bash
# Get overview of all hosts
anvyl agent query "Give me a summary of all hosts in the network"

# Check for high resource usage
anvyl agent query "Which hosts have CPU usage above 80%?"

# Monitor container health
anvyl agent query "Are there any stopped containers that should be running?"
```

### Scenario 3: Automated Operations

```bash
# Scale up a service
anvyl agent query "Start 3 more instances of the web service container"

# Clean up resources
anvyl agent query "Stop and remove all stopped containers"

# Deploy new service
anvyl agent query "Deploy a new nginx container on the host with the most available memory"
```

## Tools Available

The AI agents have access to the following tools:

### Container Management
- `list_containers`: List all containers on a host
- `get_container_info`: Get detailed container information
- `start_container`: Start a stopped container
- `stop_container`: Stop a running container
- `create_container`: Create and start a new container

### Host Management
- `get_host_info`: Get host information
- `get_host_resources`: Get current resource usage
- `list_hosts`: List all hosts in the network
- `execute_command`: Execute commands on the host

### Remote Communication
Remote queries are handled through the agent's communication system, not as individual tools. The agent can query remote hosts using the `--host-id` parameter.

## Configuration

### Environment Variables
- `ANVYL_LMSTUDIO_URL`: Default LMStudio API URL (default: http://localhost:1234/v1)
- `ANVYL_LMSTUDIO_MODEL`: Default model name (default: default)
- `ANVYL_AGENT_PORT`: Default port for agent API (default: 8080)
- `ANVYL_AGENT_HOST`: Host to bind agent API to (default: 0.0.0.0)

### Agent Settings
- **LMStudio URL**: http://localhost:1234/v1 (configurable)
- **Model**: Any model loaded in LMStudio (configurable)
- **Temperature**: 0 (deterministic responses)
- **Timeout**: 30 seconds for remote queries
- **Agent Type**: structured-chat-zero-shot-react-description

### LMStudio Setup

1. **Install LMStudio**:
   - Download from [https://lmstudio.ai/](https://lmstudio.ai/)
   - Install and launch the application

2. **Load a Model**:
   - Go to the "Search" tab
   - Search for and download a model (e.g., "Llama 2 7B Chat")
   - Wait for download to complete

3. **Start Local Server**:
   - Go to Settings → Local Server
   - Click "Start Server"
   - Note the URL (usually http://localhost:1234/v1)

4. **Test Connection**:
   ```bash
   curl http://localhost:1234/v1/models
   ```

## Security Considerations

### Network Security
- Agents communicate over HTTP/JSON (consider HTTPS for production)
- No built-in authentication (implement for production use)
- CORS enabled for web access

### API Security
- Validate all incoming requests
- Rate limiting recommended
- Input sanitization for commands

### Docker Access
- Agents have full Docker access on local host
- Consider Docker socket permissions
- Container isolation recommended

### Local LLM Benefits
- **Privacy**: No data sent to external APIs
- **Cost Control**: No per-token charges
- **Offline Operation**: Works without internet
- **Custom Models**: Use any model supported by LMStudio

## Troubleshooting

### Common Issues

1. **Agent won't start**
   - Check if port is already in use
   - Verify Docker is running
   - Check if LMStudio is running and serving models

2. **Remote queries fail**
   - Verify host IP addresses are correct
   - Check network connectivity
   - Ensure remote agent is running

3. **Mock LLM responses**
   - Start LMStudio and load a model
   - Check LMStudio server URL
   - Verify model is loaded and accessible

4. **LMStudio connection issues**
   - Ensure LMStudio is running
   - Check if local server is started
   - Verify the API URL is correct
   - Test with curl: `curl http://localhost:1234/v1/models`

5. **Missing dependencies**
   - Install required packages: `pip install openai`
   - Ensure all agent dependencies are installed: `pip install anvyl[agent]`

### Debug Mode

Enable debug logging:
```bash
export ANVYL_LOG_LEVEL=DEBUG
anvyl agent start
```

### Health Checks

Check agent health:
```bash
curl http://localhost:8080/
curl http://localhost:8080/agent/info
```

Check LMStudio:
```bash
curl http://localhost:1234/v1/models
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "default", "messages": [{"role": "user", "content": "Hello"}]}'
```

## Development

### Running the Demo

```bash
# Run the interactive demo
python examples/agent_demo.py

# Or use the CLI
anvyl agent start
```

### Adding New Tools

1. Create a new tool class in `anvyl/agent/tools.py`
2. Inherit from `BaseTool`
3. Implement the `_run` method
4. Add to the tools list in `InfrastructureTools`

### Extending Communication

1. Add new message types in `anvyl/agent/communication.py`
2. Implement handlers in `HostAgent`
3. Add API endpoints in `AgentManager`

## Future Enhancements

- **Authentication**: JWT-based authentication
- **Encryption**: End-to-end encryption for agent communication
- **Service Discovery**: Automatic host discovery
- **Load Balancing**: Intelligent workload distribution
- **Monitoring**: Built-in metrics and alerting
- **Web UI**: Visual interface for agent management
- **Plugin System**: Extensible tool system
- **Multi-Model Support**: Support for other local LLM providers (Ollama, etc.)
- **Model Switching**: Dynamic model selection based on task requirements
- **Remote Tool Integration**: Direct tool access on remote hosts
- **Broadcast Messages**: Send messages to all known hosts