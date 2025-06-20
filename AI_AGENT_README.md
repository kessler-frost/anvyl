# Anvyl AI Agent - Natural Language Infrastructure Management

This document describes the Anvyl AI Agent integration with LMStudio's `act()` function, providing natural language access to Anvyl's infrastructure management capabilities.

## Overview

The Anvyl AI Agent uses LMStudio's Python SDK to provide AI-powered natural language interaction with the Anvyl infrastructure orchestrator. Users can manage hosts, containers, agents, and monitor system status using conversational commands.

## Features

### 🤖 AI-Powered Management
- **Natural Language Commands**: Use conversational language to manage infrastructure
- **LMStudio Integration**: Leverages LMStudio's `act()` function for intelligent responses
- **Function Calling**: AI agent can call specific infrastructure functions based on user requests
- **Interactive Chat**: Full interactive session for complex management tasks

### 🏗️ Infrastructure Capabilities
- **Host Management**: List, add, and monitor hosts
- **Container Management**: Create, stop, view logs, and execute commands
- **Agent Management**: Launch and manage infrastructure agents
- **System Monitoring**: Get real-time status and metrics
- **UI Stack Management**: Monitor and manage the Anvyl UI components

## Prerequisites

1. **LMStudio**: Must be installed and running with MLX models
2. **Anvyl Infrastructure**: gRPC server must be running (`anvyl up`)
3. **Python Dependencies**: Anvyl package installed

## Installation

1. **Install Anvyl** (includes LMStudio dependency):
   ```bash
   pip install anvyl
   ```

2. **Start Anvyl Infrastructure**:
   ```bash
   anvyl up
   ```

3. **Ensure LMStudio is running** and has models available

## Quick Start

### 1. Start Anvyl Infrastructure

```bash
# Start the Anvyl stack (gRPC server + UI)
anvyl up

# Verify the server is running
anvyl status
```

### 2. Interactive AI Session

```bash
# Start an interactive chat session
anvyl agent interactive my-ai

# Example conversation:
# You: "Show me all hosts"
# AI: "I'll list all the hosts in your infrastructure..."
# You: "Create a nginx container"
# AI: "I'll create a nginx container for you..."
```

### 3. Single Commands

```bash
# Send a single command
anvyl agent chat my-ai "What's the system status?"

# Use a specific model
anvyl agent chat my-ai "List all containers" --model llama-3.2-3b-instruct-mlx
```

### 4. Demo Mode

```bash
# Run a demonstration of AI capabilities
anvyl agent demo my-ai
```

## CLI Usage

The AI agent is accessible through the `anvyl agent` command group:

### List Available Agents
Discover all agents across all connected hosts:
```bash
anvyl agent list
```

**Options:**
- `--host, -h`: Anvyl server host (default: localhost)
- `--port, -p`: Anvyl server port (default: 50051)
- `--output, -o`: Output format: table, json (default: table)

### Chat Mode
Send a single message to the AI agent:
```bash
anvyl agent chat <agent_name> "your message"
```

**Options:**
- `--model, -m`: LMStudio model to use (default: llama-3.2-1b-instruct-mlx)
- `--host, -h`: Anvyl server host (default: localhost)
- `--port, -p`: Anvyl server port (default: 50051)
- `--verbose, -v`: Enable verbose output

**Examples:**
```bash
# Basic usage
anvyl agent chat my-ai "Show me all hosts"

# With custom model
anvyl agent chat my-ai "Create a container" --model llama-3.2-7b-instruct-mlx

# Verbose mode
anvyl agent chat my-ai "List containers" --verbose

# List available agents first
anvyl agent list
anvyl agent chat my-ai "What's the status?"
```

### Interactive Mode
Start an interactive chat session:
```bash
anvyl agent interactive <agent_name>
```

**Options:**
- `--model, -m`: LMStudio model to use
- `--host, -h`: Anvyl server host
- `--port, -p`: Anvyl server port
- `--verbose, -v`: Enable verbose output

### Demo Mode
Run a demonstration of AI agent capabilities:
```bash
anvyl agent demo <agent_name>
```

**Options:**
- `--model, -m`: LMStudio model to use
- `--host, -h`: Anvyl server host
- `--port, -p`: Anvyl server port

## Example Conversations

### Host Management
```
You: "Show me all hosts"
AI: "I'll list all the hosts in your infrastructure. Let me check that for you..."

You: "Add a new host called 'prod-server' with IP 192.168.1.100"
AI: "I'll add a new host to your infrastructure. Creating host 'prod-server'..."

You: "What are the metrics for host 'prod-server'?"
AI: "I'll get the resource metrics for host 'prod-server'. Let me check that..."
```

### Container Management
```
You: "List all containers"
AI: "I'll show you all the containers in your infrastructure..."

You: "Create a nginx container named 'web-server' on port 8080"
AI: "I'll create a nginx container for you. Setting up 'web-server' with port mapping..."

You: "Stop the web-server container"
AI: "I'll stop the web-server container for you..."

You: "Show me the logs from the web-server container"
AI: "I'll get the logs from the web-server container. Here are the recent logs..."
```

### System Monitoring
```
You: "What's the current system status?"
AI: "I'll check the overall system status for you. Here's what I found..."

You: "How many containers are running?"
AI: "Let me check the container status. I found X running containers..."

You: "Show me the UI stack status"
AI: "I'll check the status of the Anvyl UI components..."
```

## Available Functions

The AI agent has access to the following infrastructure functions:

### Host Functions
- `list_hosts()`: List all registered hosts
- `add_host(name, ip, os, tags)`: Add a new host
- `get_host_metrics(host_id)`: Get host resource metrics

### Container Functions
- `list_containers(host_id)`: List all containers
- `create_container(name, image, host_id, ports, volumes, environment)`: Create a container
- `stop_container(container_id, timeout)`: Stop a container
- `get_container_logs(container_id, tail)`: Get container logs
- `exec_container_command(container_id, command)`: Execute command in container

### Agent Functions
- `list_agents(host_id)`: List all agents
- `launch_agent(name, host_id, entrypoint, use_container, environment)`: Launch an agent
- `stop_agent(agent_id)`: Stop an agent

### System Functions
- `get_system_status()`: Get overall system status
- `get_ui_status()`: Get UI stack status

## Python API

You can also use the AI agent programmatically:

```python
from anvyl.ai_agent import create_ai_agent

# Create an AI agent with default settings
agent = create_ai_agent(
    model_id="llama-3.2-1b-instruct-mlx",
    host="localhost",
    port=50051,
    verbose=True,
    agent_name="my-ai"
)

# Discover all available agents
discovery_result = agent._discover_agents()
if discovery_result["success"]:
    print(f"Found {discovery_result['total']} agents:")
    for agent_info in discovery_result["agents"]:
        print(f"  - {agent_info['name']} on {agent_info['host_name']} ({agent_info['host_ip']})")

# Send a message
response = agent.chat("Show me all hosts")
print(response)

# Start interactive session
agent.interactive_chat()
```

## Configuration

### Model Selection
Choose from available LMStudio models:
- `llama-3.2-1b-instruct-mlx` (default, fast)
- `llama-3.2-3b-instruct-mlx` (balanced)
- `llama-3.2-7b-instruct-mlx` (high quality)
- Any other MLX model available in LMStudio

### Agent Discovery
The AI agent system automatically discovers all agents across all connected hosts:

**CLI Usage:**
```bash
# List all available agents
anvyl agent list

# The system will automatically find and route to the specified agent
anvyl agent chat my-ai "hello"
```

**Python API:**
```python
# Discover all agents
discovery_result = agent._discover_agents()
for agent_info in discovery_result["agents"]:
    print(f"Agent: {agent_info['name']} on {agent_info['host_name']}")

# Route command to specific agent
routing_result = agent._route_to_agent("my-ai", "your command")
```

**Discovery Features:**
- Automatically scans all connected hosts
- Shows agent status, host, and location
- Routes commands to the correct agent
- Handles agent not found scenarios gracefully

## Troubleshooting

### Common Issues

1. **Model Not Found**
   ```
   Error: Model 'llama-3.2-1b-instruct-mlx' not available
   ```
   **Solution**: Download the model in LMStudio: `lms get llama-3.2-1b-instruct-mlx`

2. **Anvyl Server Not Running**
   ```
   Error: Failed to connect to Anvyl server at localhost:50051
   ```
   **Solution**: Start the Anvyl infrastructure: `anvyl up`

3. **Function Call Errors**
   ```
   Error: Function call failed
   ```
   **Solution**: Check that the gRPC server is running and accessible

4. **Agent Not Found**
   ```
   Error: Agent 'my-ai' not found
   ```
   **Solution**: Use `anvyl agent list` to see available agents, or launch the agent first

5. **Agent Discovery Issues**
   ```
   Error: Error discovering agents
   ```
   **Solution**: Check host connectivity and ensure agents are running on the hosts

### Debug Mode

Enable verbose output to see detailed function calls:

```bash
anvyl agent chat my-ai "your message" --verbose
```

### Logging

The AI agent uses Python logging. Set the log level for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Advanced Usage

### Custom Function Integration

You can extend the AI agent with custom functions:

```python
from anvyl.ai_agent import AnvylAIAgent

class CustomAIAgent(AnvylAIAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom functions to the functions list
        self.functions.append(self._custom_function)
    
    def _custom_function(self, param1: str, **kwargs):
        """Custom function description"""
        # Your custom logic here
        return {"success": True, "result": f"Processed: {param1}"}
```

### Batch Operations

Use the AI agent for batch infrastructure operations:

```python
agent = create_ai_agent()

# Batch container creation
commands = [
    "Create a nginx container named 'web1'",
    "Create a redis container named 'cache1'",
    "Create a postgres container named 'db1'"
]

for cmd in commands:
    response = agent.chat(cmd)
    print(f"Command: {cmd}")
    print(f"Response: {response}\n")
```

## Security Considerations

1. **Access Control**: The AI agent has full access to infrastructure management
2. **Model Security**: Use trusted LMStudio models only
3. **Network Security**: Ensure gRPC server is properly secured in production
4. **Function Validation**: AI agent validates function parameters before execution
5. **Agent Discovery Security**: Agent discovery reveals host information - secure your network

## Performance Tips

1. **Model Selection**: Use smaller models for faster responses
2. **Connection Pooling**: Reuse AI agent instances for multiple commands
3. **Batch Operations**: Group related commands for efficiency
4. **Caching**: Cache frequently requested information
5. **Agent Discovery**: Discovery is cached during session - restart for fresh discovery

## Future Enhancements

Planned features include:
- **Multi-Model Support**: Switch between different AI models dynamically
- **Context Memory**: Remember conversation context across sessions
- **Advanced Function Calling**: More sophisticated function selection
- **Integration APIs**: REST API for AI agent access
- **Custom Prompts**: User-defined system prompts
- **Workflow Automation**: Complex multi-step operations
- **Agent Discovery Enhancements**: Real-time agent status updates and health checks

## Support

For issues and questions:
- Check the troubleshooting section above
- Review LMStudio documentation
- Open issues on the Anvyl GitHub repository
- Check Anvyl logs: `anvyl logs`

## License

This AI agent functionality is part of the Anvyl project and is licensed under the MIT License.