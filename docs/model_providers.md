# Anvyl AI Agent Model Providers

This document describes the multi-provider AI agent system in Anvyl, which supports various model providers for executing natural language instructions against infrastructure.

## Overview

Anvyl AI Agents now run in **Docker containers** for better isolation, persistence, and scalability. Each agent is configured with a specific model provider and can execute instructions against the Anvyl infrastructure via gRPC.

## Containerized Agent Architecture

### Key Features
- **Container Isolation**: Each agent runs in its own Docker container
- **Persistence**: Agents continue running even when the CLI is closed
- **Scalability**: Multiple agents can run simultaneously
- **Resource Management**: Easy monitoring and control of agent resources
- **Reliability**: Automatic container restart on failures

### Agent Lifecycle
1. **Create**: Define agent configuration (provider, model, settings)
2. **Start**: Build Docker image and start container
3. **Execute**: Send instructions via gRPC to running container
4. **Monitor**: View logs and status
5. **Stop**: Stop and remove container
6. **Remove**: Clean up configuration and resources

## Supported Model Providers

### 1. LM Studio (Default)
**Provider**: `lmstudio`

LM Studio provides local model inference with MLX models.

**Configuration**:
```bash
anvyl agent create my-agent \
  --provider lmstudio \
  --model deepseek/deepseek-r1-0528-qwen3-8b \
  --host localhost \
  --port 50051
```

**Requirements**:
- LM Studio installed and running
- MLX models available
- Anvyl gRPC server running

### 2. Ollama
**Provider**: `ollama`

Ollama provides local model inference with various open-source models.

**Configuration**:
```bash
anvyl agent create my-agent \
  --provider ollama \
  --model llama3.2:1b \
  --provider-host localhost \
  --provider-port 11434
```

**Requirements**:
- Ollama installed and running
- Models pulled (`ollama pull llama3.2:1b`)
- Anvyl gRPC server running

### 3. OpenAI
**Provider**: `openai`

OpenAI provides cloud-based model inference.

**Configuration**:
```bash
anvyl agent create my-agent \
  --provider openai \
  --model gpt-4o-mini \
  --api-key your-openai-api-key
```

**Requirements**:
- OpenAI API key
- Internet connection
- Anvyl gRPC server running

### 4. Anthropic
**Provider**: `anthropic`

Anthropic provides cloud-based model inference with Claude models.

**Configuration**:
```bash
anvyl agent create my-agent \
  --provider anthropic \
  --model claude-3-haiku-20240307 \
  --api-key your-anthropic-api-key
```

**Requirements**:
- Anthropic API key
- Internet connection
- Anvyl gRPC server running

## Agent Management Commands

### Flag Structure

The agent creation command uses generic flags that work across all providers:

- `--anvyl-host` / `--anvyl-port`: Anvyl gRPC server connection (default: localhost:50051)
- `--provider-host` / `--provider-port`: Model provider connection (varies by provider)
- `--api-key`: API key for cloud providers (OpenAI, Anthropic)

**Provider-specific defaults**:
- **LM Studio**: No additional host/port needed (runs locally)
- **Ollama**: Defaults to localhost:11434
- **OpenAI/Anthropic**: Cloud APIs, only need API key

### Creating Agents
```bash
# Basic agent creation
anvyl agent create my-agent --provider lmstudio

# With auto-start
anvyl agent create my-agent --provider lmstudio --auto-start

# Full configuration
anvyl agent create my-agent \
  --provider ollama \
  --model llama3.2:1b \
  --provider-host localhost \
  --provider-port 11434 \
  --verbose
```

**Provider-specific examples**:

```bash
# LM Studio (default - no additional flags needed)
anvyl agent create lm-agent --provider lmstudio --model deepseek/deepseek-r1-0528-qwen3-8b

# Ollama with custom server
anvyl agent create ollama-agent --provider ollama --model llama3.2:1b --provider-host remote-server --provider-port 11434

# OpenAI with API key
anvyl agent create openai-agent --provider openai --model gpt-4o-mini --api-key your-api-key

# Anthropic with environment variable
export ANTHROPIC_API_KEY="your-key"
anvyl agent create claude-agent --provider anthropic --model claude-3-haiku-20240307
```

### Starting/Stopping Agents
```bash
# Start agent in container
anvyl agent start my-agent

# Stop agent container
anvyl agent stop my-agent

# Check agent status
anvyl agent list
```

### Executing Instructions
```bash
# Execute single instruction
anvyl agent act my-agent "List all hosts"

# Execute complex instruction
anvyl agent act my-agent "Create a nginx container on port 8080"

# Alias command
anvyl agent execute my-agent "Show system status"
```

### Monitoring Agents
```bash
# View agent logs
anvyl agent logs my-agent

# Follow logs in real-time
anvyl agent logs my-agent --follow

# Show agent information
anvyl agent info my-agent

# List all agents
anvyl agent list --running
```

### Cleanup
```bash
# Remove agent and container
anvyl agent remove my-agent

# Force removal
anvyl agent remove my-agent --force
```

## Example Workflows

### 1. Basic Infrastructure Management
```bash
# Create and start agent
anvyl agent create infra-agent --provider lmstudio --auto-start

# Manage hosts
anvyl agent act infra-agent "Add a new host called 'prod-server' with IP 192.168.1.100"
anvyl agent act infra-agent "List all hosts and their status"

# Manage containers
anvyl agent act infra-agent "Create a web server container with nginx"
anvyl agent act infra-agent "Show me all running containers"

# Monitor system
anvyl agent act infra-agent "What's the current system status?"
anvyl agent act infra-agent "Show resource usage for all hosts"
```

### 2. Multi-Agent Setup
```bash
# Create different agents for different purposes
anvyl agent create monitoring-agent --provider openai --model gpt-4o-mini
anvyl agent create deployment-agent --provider ollama --model llama3.2:1b
anvyl agent create security-agent --provider anthropic --model claude-3-haiku-20240307

# Start all agents
anvyl agent start monitoring-agent
anvyl agent start deployment-agent
anvyl agent start security-agent

# Use specialized agents
anvyl agent act monitoring-agent "Analyze system performance and identify bottlenecks"
anvyl agent act deployment-agent "Deploy the latest version of the web application"
anvyl agent act security-agent "Check for security vulnerabilities in running containers"
```

### 3. Development Workflow
```