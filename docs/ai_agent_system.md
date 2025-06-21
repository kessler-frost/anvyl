# Anvyl AI Agent System

The Anvyl AI Agent System provides distributed AI agents that can manage infrastructure across multiple hosts using Pydantic AI and tool-use capabilities.

## Overview

Each host running Anvyl can have an AI agent that:
- Manages local infrastructure using Docker primitives
- Communicates with agents on other hosts
- Provides natural language interface for infrastructure management
- Uses Pydantic AI for intelligent tool selection and execution
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
│ │ • Model     │ │    │ │ • Model     │ │    │ │ • Model     │ │
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

### Dependencies
The AI agent system requires the following Python packages:
- `pydantic-ai>=0.1.0` - Core AI framework
- `aiohttp>=3.9.0` - Async HTTP client for agent communication
- `requests>=2.31.0` - HTTP client for model queries

## Usage

### Starting an Agent

```python
from anvyl.agent import create_agent_manager

# Create and start an agent
agent_manager = create_agent_manager(
    lmstudio_url="http://localhost:1234/v1",
    lmstudio_model="llama-3.2-3b-instruct",
    port=4200
)

# Start the agent server
await agent_manager.start()
```

### Using the CLI

```bash
# Start an agent
anvyl agent start --port 4200

# Process a query
anvyl agent process "List all containers"

# Query a remote host
anvyl agent query-remote host-123 "Get host resources"
```

### API Endpoints

The agent provides a REST API for communication:

- `GET /agent/info` - Get agent information
- `POST /agent/process` - Process a local query
- `POST /agent/remote-query` - Query a remote host
- `GET /agent/hosts` - List known hosts
- `POST /agent/hosts` - Add a known host
- `DELETE /agent/hosts/{host_id}` - Remove a known host
- `POST /agent/broadcast` - Broadcast a message to all hosts

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
- `ANVYL_AGENT_PORT`: Default port for agent API (default: 4201)
- `ANVYL_INFRA_API_PORT`: Default port for infrastructure API (default: 4200)
- `ANVYL_AGENT_HOST`: Host to bind agent API to (default: 0.0.0.0)

### Agent Settings
- **LMStudio URL**: http://localhost:1234/v1 (configurable)
- **Model**: Any model loaded in LMStudio (configurable)
- **Infra API Port**: 4200 (default)
- **Agent Port**: 4201 (default)
- **Temperature**: 0 (deterministic responses)
- **Timeout**: 30 seconds for remote queries
- **Agent Type**: Pydantic AI Agent with tool calling

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
- Agents communicate over HTTP/JSON
- No built-in encryption (use HTTPS in production)
- Host discovery is manual (no automatic scanning)
- API endpoints are unauthenticated (add auth in production)

### Model Security
- Local models provide privacy
- No data sent to external services
- Model outputs are not validated
- Use trusted models only

### Infrastructure Access
- Agents have full access to infrastructure management
- Tools can execute commands on the host
- Container operations are unrestricted
- Add access controls in production

## Development

### Adding New Tools

1. Create a new tool function in `anvyl/agent/tools.py`
2. Use the `@tool` decorator from Pydantic AI
3. Add proper type hints and docstrings
4. Add to the tools list in `InfrastructureTools.get_tools()`

Example:
```python
@tool
def my_new_tool(param1: str, param2: Optional[int] = None) -> str:
    """Description of what this tool does."""
    # Implementation here
    return "Result"
```

### Extending Communication

1. Add new message types in `anvyl/agent/communication.py`
2. Implement handlers in `HostAgent`
3. Add API endpoints in `AgentManager`

### Testing

```python
import pytest
from anvyl.agent import HostAgent, InfrastructureTools
from anvyl.infrastructure_client import InfrastructureClient

def test_agent_creation():
    client = InfrastructureClient()
    tools = InfrastructureTools(client)
    agent = HostAgent(
        communication=mock_communication,
        tools=tools.get_tools(),
        host_id="test-host"
    )
    assert agent.host_id == "test-host"
```

## Troubleshooting

### Common Issues

1. **LMStudio Not Available**:
   - Check if LMStudio is running
   - Verify the API URL is correct
   - Check if a model is loaded

2. **Tool Execution Errors**:
   - Check infrastructure client connection
   - Verify Docker is running
   - Check permissions for command execution

3. **Communication Errors**:
   - Verify network connectivity
   - Check if remote agents are running
   - Verify host IP addresses are correct

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

Check agent health:
```bash
curl http://localhost:4200/health
```

## Examples

### Basic Usage

```python
from anvyl.agent import create_agent_manager

# Create agent manager
manager = create_agent_manager(
    lmstudio_url="http://localhost:1234/v1",
    lmstudio_model="llama-3.2-3b-instruct"
)

# Start the agent
await manager.start()
```

### Processing Queries

```python
# Process a local query
result = await agent.process_query("List all containers")
print(result)

# Query a remote host
result = await agent.query_remote_host("host-123", "Get host resources")
print(result)
```

### Adding Hosts

```python
# Add a known host
agent.add_known_host("host-123", "192.168.1.100")

# List known hosts
hosts = agent.get_known_hosts()
print(hosts)
```

### Broadcasting Messages

```python
# Broadcast to all hosts
results = await agent.broadcast_to_all_hosts("System health check")
for result in results:
    print(f"Host {result['host_id']}: {result['result']}")
```

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

## New Infra Package

- `anvyl/infra/` - Infrastructure API, client, and service modules