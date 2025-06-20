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
2. **Anvyl Infrastructure**: gRPC server must be running
3. **Python Dependencies**: LMStudio SDK and Anvyl package installed

## Installation

The AI agent functionality is included with Anvyl:

```bash
# Install Anvyl with AI agent support
pip install anvyl

# Ensure LMStudio is running and has models available
# Download a model if needed: lms get llama-3.2-1b-instruct-mlx
```

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

## CLI Commands

### `anvyl agent chat <agent_name> <message>`
Send a natural language message to the AI agent.

**Options:**
- `--model, -m`: LMStudio model to use (default: llama-3.2-1b-instruct-mlx)
- `--host, -h`: Anvyl server host (default: localhost)
- `--port, -p`: Anvyl server port (default: 50051)
- `--verbose, -v`: Enable verbose output

**Examples:**
```bash
anvyl agent chat my-ai "Show me all hosts"
anvyl agent chat my-ai "Create a web server container" --model llama-3.2-3b-instruct-mlx
anvyl agent chat my-ai "What's the system status?" --verbose
```

### `anvyl agent interactive <agent_name>`
Start an interactive chat session with the AI agent.

**Options:**
- `--model, -m`: LMStudio model to use
- `--host, -h`: Anvyl server host
- `--port, -p`: Anvyl server port
- `--verbose, -v`: Enable verbose output

**Usage:**
```bash
anvyl agent interactive my-ai
# Then type your commands interactively
```

### `anvyl agent demo <agent_name>`
Run a demonstration of AI agent capabilities.

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

# Create an AI agent
agent = create_ai_agent(
    model_id="llama-3.2-1b-instruct-mlx",
    host="localhost",
    port=50051,
    verbose=True,
    agent_name="my-ai"
)

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

### Server Configuration
- **Host**: Default is `localhost`
- **Port**: Default is `50051` (Anvyl gRPC server)
- **Verbose Mode**: Enable detailed logging and function call visibility

## Troubleshooting

### Common Issues

1. **LMStudio Not Available**
   ```
   Error: LMStudio is not available. Please ensure LMStudio is running.
   ```
   **Solution**: Start LMStudio and ensure it's accessible

2. **Model Not Found**
   ```
   Error: Model 'llama-3.2-1b-instruct-mlx' not available
   ```
   **Solution**: Download the model in LMStudio: `lms get llama-3.2-1b-instruct-mlx`

3. **Anvyl Server Not Running**
   ```
   Error: Failed to connect to Anvyl server at localhost:50051
   ```
   **Solution**: Start the Anvyl infrastructure: `anvyl up`

4. **Function Call Errors**
   ```
   Error: Function call failed
   ```
   **Solution**: Check that the gRPC server is running and accessible

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
        
        # Add custom functions
        self.functions["custom_function"] = self._custom_function
        self.function_descriptions["custom_function"] = {
            "description": "Custom function description",
            "parameters": {
                "param1": {"type": "string", "description": "Parameter description"}
            }
        }
    
    def _custom_function(self, param1: str, **kwargs):
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

## Performance Tips

1. **Model Selection**: Use smaller models for faster responses
2. **Connection Pooling**: Reuse AI agent instances for multiple commands
3. **Batch Operations**: Group related commands for efficiency
4. **Caching**: Cache frequently requested information

## Future Enhancements

Planned features include:
- **Multi-Model Support**: Switch between different AI models dynamically
- **Context Memory**: Remember conversation context across sessions
- **Advanced Function Calling**: More sophisticated function selection
- **Integration APIs**: REST API for AI agent access
- **Custom Prompts**: User-defined system prompts
- **Workflow Automation**: Complex multi-step operations

## Support

For issues and questions:
- Check the troubleshooting section above
- Review LMStudio documentation
- Open issues on the Anvyl GitHub repository
- Check Anvyl logs: `anvyl logs`

## License

This AI agent functionality is part of the Anvyl project and is licensed under the MIT License. 