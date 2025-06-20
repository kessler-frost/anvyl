# Anvyl AI Agent Workflow Guide

This guide demonstrates the new agent workflow where **configuration is separated from action execution**. You create and configure agents once, then use them by name to execute actions.

## Overview

The Anvyl AI Agent system now follows a **two-phase approach**:

1. **🔧 Configuration Phase**: Create and configure agents with model providers, settings, etc.
2. **⚡ Execution Phase**: Use agents by name to execute instructions (no configuration needed)

## Benefits

- **Cleaner Commands**: Action execution is simple and focused
- **Persistent Configuration**: Agent settings are saved and reused
- **Multiple Agents**: Create different agents for different purposes
- **Easy Switching**: Switch between providers without complex commands

## Complete Workflow

### Phase 1: Agent Configuration

#### 1. Create Agents with Different Providers

```bash
# Create an LM Studio agent (default, fast local inference)
anvyl agent create my-local-agent \
  --provider lmstudio \
  --model deepseek/deepseek-r1-0528-qwen3-8b \
  --start

# Create an Ollama agent (local open-source models)
anvyl agent create my-ollama-agent \
  --provider ollama \
  --model deepseek/deepseek-r1-0528-qwen3-8b \
  --ollama-host localhost \
  --ollama-port 11434

# Create an OpenAI agent (cloud-based, high quality)
anvyl agent create my-openai-agent \
  --provider openai \
  --model deepseek/deepseek-r1-0528-qwen3-8b \
  --api-key YOUR_OPENAI_KEY

# Create an Anthropic agent (cloud-based, detailed responses)
anvyl agent create my-anthropic-agent \
  --provider anthropic \
  --model claude-3-haiku-20240307 \
  --api-key YOUR_ANTHROPIC_KEY
```

#### 2. Environment Variables for API Keys

```bash
# Set environment variables to avoid passing keys every time
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"

# Now create agents without --api-key
anvyl agent create my-openai-agent --provider openai --model deepseek/deepseek-r1-0528-qwen3-8b
anvyl agent create my-anthropic-agent --provider anthropic --model claude-3-haiku-20240307
```

#### 3. List and Manage Agents

```bash
# List all configured agents
anvyl agent list

# Output:
# ┌────────────────────┬──────────────┬──────────┬─────────────────────────────┬─────────────────┬────────────┐
# │ Name               │ Status       │ Provider │ Model                       │ Host            │ Created    │
# ├────────────────────┼──────────────┼──────────┼─────────────────────────────┼─────────────────┼────────────┤
# │ my-local-agent     │ 🟢 Running   │ lmstudio │ deepseek/deepseek-r1-0528-qwen3-8b  │ localhost:50051 │ 2024-01-15 │
# │ my-ollama-agent    │ 🔴 Stopped   │ ollama   │ deepseek/deepseek-r1-0528-qwen3-8b                   │ localhost:50051 │ 2024-01-15 │
# │ my-openai-agent    │ 🔴 Stopped   │ openai   │ deepseek/deepseek-r1-0528-qwen3-8b                │ localhost:50051 │ 2024-01-15 │
# │ my-anthropic-agent │ 🔴 Stopped   │ anthropic│ claude-3-haiku-20240307    │ localhost:50051 │ 2024-01-15 │
# └────────────────────┴──────────────┴──────────┴─────────────────────────────┴─────────────────┴────────────┘

# Show only running agents
anvyl agent list --running

# Get detailed info about an agent
anvyl agent info my-local-agent
```

#### 4. Start/Stop Agents

```bash
# Start an agent
anvyl agent start my-ollama-agent

# Stop an agent
anvyl agent stop my-local-agent

# Remove an agent configuration
anvyl agent remove my-old-agent
```

### Phase 2: Action Execution

#### 1. Simple Action Execution

```bash
# Execute actions using just agent name + instruction
anvyl agent act my-local-agent "Show me all hosts"
anvyl agent act my-ollama-agent "List all containers"
anvyl agent act my-openai-agent "What's the system status?"
anvyl agent act my-anthropic-agent "Create a nginx container"

# Alias command
anvyl agent execute my-local-agent "Get host metrics"
```

#### 2. Interactive Sessions

```bash
# Start interactive session with any configured agent
anvyl agent session my-local-agent

# Example interactive session:
# 🚀 Interactive Action Session Started
#
# Agent: my-local-agent
# Provider: LMStudioProvider
# Model: deepseek/deepseek-r1-0528-qwen3-8b
#
# Give me instructions to execute on your infrastructure.
# Type 'help' for available actions, 'quit' to exit.
#
# Instruction: show all hosts
# 🔄 Executing: show all hosts
# ⏳ Processing...
# ✅ Result: Found 3 hosts: web-server (192.168.1.10), db-server (192.168.1.11), cache-server (192.168.1.12)
#
# Instruction: create nginx container on web-server
# 🔄 Executing: create nginx container on web-server
# ⏳ Processing...
# ✅ Result: Created nginx container 'nginx-web' on web-server (ID: abc123)
#
# Instruction: help
# 🔧 Available Commands:
# • Type any natural language instruction
# • 'help' or 'h' - Show this help
# • 'actions' or 'a' - Show available actions
# • 'quit' or 'q' - Exit session
#
# Instruction: quit
# Ending interactive session. Goodbye!
```

#### 3. Action Discovery

```bash
# See what actions are available for an agent
anvyl agent actions my-local-agent

# Output:
# ┌─────────────────────┬─────────────────────────────────────┐
# │ Action              │ Description                         │
# ├─────────────────────┼─────────────────────────────────────┤
# │ List Hosts          │ List all hosts                     │
# │ Add Host            │ Add a new host                      │
# │ Get Host Metrics    │ Get current host metrics            │
# │ List Containers     │ List containers                     │
# │ Create Container    │ Create a new container              │
# │ Stop Container      │ Stop a container                    │
# │ List Agents         │ List agents                         │
# │ Launch Agent        │ Launch an agent                     │
# │ Stop Agent          │ Stop an agent                       │
# │ Get System Status   │ Get overall system status          │
# └─────────────────────┴─────────────────────────────────────┘
#
# 💡 Usage: anvyl agent act my-local-agent "<your instruction>"
```

#### 4. Demo Mode

```bash
# Run a demonstration with any agent
anvyl agent demo my-local-agent
```

## Common Workflows

### 1. Quick Start Workflow

```bash
# 1. Create and start an agent in one command
anvyl agent create my-agent --provider lmstudio --start

# 2. Use the agent immediately
anvyl agent act my-agent "show all hosts"
anvyl agent act my-agent "list containers"

# 3. Start interactive session
anvyl agent session my-agent
```

### 2. Multi-Provider Workflow

```bash
# 1. Create agents for different use cases
anvyl agent create fast-local --provider lmstudio --model deepseek/deepseek-r1-0528-qwen3-8b --start
anvyl agent create smart-cloud --provider openai --model deepseek/deepseek-r1-0528-qwen3-8b
anvyl agent create detailed-cloud --provider anthropic --model claude-3-sonnet-20240229

# 2. Use different agents for different tasks
anvyl agent act fast-local "quick system check"        # Fast local inference
anvyl agent act smart-cloud "analyze this error log"   # Smart cloud reasoning
anvyl agent act detailed-cloud "write deployment docs" # Detailed analysis

# 3. Compare responses across providers
anvyl agent act fast-local "explain kubernetes"
anvyl agent act smart-cloud "explain kubernetes"
anvyl agent act detailed-cloud "explain kubernetes"
```

### 3. Development Workflow

```bash
# 1. Create a development agent
anvyl agent create dev-agent --provider ollama --model codellama --start

# 2. Use for development tasks
anvyl agent act dev-agent "list all containers"
anvyl agent act dev-agent "show logs for app-container"
anvyl agent act dev-agent "restart the database service"

# 3. Interactive debugging session
anvyl agent session dev-agent
# Then type things like:
# "check if redis is running"
# "show me the nginx configuration"
# "create a test container"
```

### 4. Production Workflow

```bash
# 1. Create production-ready agents
anvyl agent create prod-monitor \
  --provider openai \
  --model deepseek/deepseek-r1-0528-qwen3-8b \
  --host prod-server.company.com \
  --port 50051

# 2. Use for production monitoring
anvyl agent act prod-monitor "system health check"
anvyl agent act prod-monitor "show resource usage"
anvyl agent act prod-monitor "check for failed containers"

# 3. Alert response
anvyl agent act prod-monitor "investigate high CPU on web-server-01"
```

## Key Differences from Previous Approach

### ❌ Old Way (Configuration + Execution Together)
```bash
# Had to specify provider/model/config every time
anvyl agent chat my-agent "show hosts" \
  --provider ollama \
  --model deepseek/deepseek-r1-0528-qwen3-8b \
  --ollama-host localhost \
  --ollama-port 11434 \
  --api-key "key-here"
```

### ✅ New Way (Separated Configuration)
```bash
# Configure once
anvyl agent create my-agent \
  --provider ollama \
  --model deepseek/deepseek-r1-0528-qwen3-8b \
  --ollama-host localhost \
  --ollama-port 11434

# Use many times (simple!)
anvyl agent act my-agent "show hosts"
anvyl agent act my-agent "list containers"
anvyl agent act my-agent "create nginx"
```

## Advanced Usage

### 1. Agent Configurations

```bash
# Create agents for different infrastructure environments
anvyl agent create staging-agent --host staging.company.com --port 50051 --provider lmstudio
anvyl agent create prod-agent --host prod.company.com --port 50051 --provider openai
anvyl agent create dev-agent --host localhost --port 50051 --provider ollama

# Use environment-specific agents
anvyl agent act staging-agent "deploy to staging"
anvyl agent act prod-agent "check production health"
anvyl agent act dev-agent "run local tests"
```

### 2. Specialized Agents

```bash
# Create task-specific agents
anvyl agent create monitoring-agent --provider openai --model deepseek/deepseek-r1-0528-qwen3-8b
anvyl agent create deployment-agent --provider anthropic --model claude-3-sonnet-20240229
anvyl agent create debug-agent --provider ollama --model codellama

# Use for specialized tasks
anvyl agent act monitoring-agent "check system health"
anvyl agent act deployment-agent "prepare deployment plan"
anvyl agent act debug-agent "analyze error logs"
```

### 3. Auto-starting Agents

```bash
# Agents start automatically when first used
anvyl agent act my-stopped-agent "show hosts"
# 🚀 Agent 'my-stopped-agent' not running. Starting...
# ✅ Agent 'my-stopped-agent' started!
# 🔄 Executing: show hosts
# ✅ Result: ...
```

## Python API

The same separation applies to the Python API:

```python
from anvyl.agent_manager import get_agent_manager

# Configuration phase
manager = get_agent_manager()

# Create agents
manager.create_agent("my-local", provider="lmstudio", model_id="deepseek/deepseek-r1-0528-qwen3-8b")
manager.create_agent("my-cloud", provider="openai", model_id="deepseek/deepseek-r1-0528-qwen3-8b", api_key="key")

# Start agents
local_agent = manager.start_agent("my-local")
cloud_agent = manager.start_agent("my-cloud")

# Execution phase - simple!
result1 = local_agent.act("show all hosts")
result2 = cloud_agent.act("analyze system performance")

# Or get agents by name
agent = manager.get_agent("my-local")
result = agent.act("create nginx container")
```

## Troubleshooting

### Agent Not Found
```bash
anvyl agent act non-existent-agent "test"
# Error: Agent 'non-existent-agent' not found. Use 'anvyl agent create' first.
# Create the agent first: anvyl agent create non-existent-agent
# List available agents: anvyl agent list
```

### Agent Configuration Issues
```bash
# Check agent details
anvyl agent info my-agent

# Remove and recreate if needed
anvyl agent remove my-agent
anvyl agent create my-agent --provider ollama --model deepseek/deepseek-r1-0528-qwen3-8b
```

### Provider Issues
```bash
# Different agents can use different providers
anvyl agent act local-agent "test"    # Uses LM Studio
anvyl agent act cloud-agent "test"    # Uses OpenAI
anvyl agent act ollama-agent "test"   # Uses Ollama
```

## Migration from Old Approach

### For Existing Scripts
```bash
# Old way - configuration every time
anvyl agent chat my-agent "show hosts" --provider ollama --model deepseek/deepseek-r1-0528-qwen3-8b

# New way - configure once, use many times
anvyl agent create my-agent --provider ollama --model deepseek/deepseek-r1-0528-qwen3-8b --start
anvyl agent act my-agent "show hosts"
```

### Backward Compatibility
```bash
# Old commands still work but show deprecation warnings
anvyl agent chat my-agent "test"
# ⚠️  The 'chat' command is deprecated. Use 'anvyl agent act' instead.
# 💡 Try: anvyl agent act my-agent "test"
```

## Summary

The new workflow provides:

✅ **Cleaner commands** - No configuration clutter in action execution
✅ **Persistent agents** - Configure once, use many times
✅ **Multi-provider support** - Easy switching between LM Studio, Ollama, OpenAI, Anthropic
✅ **Environment separation** - Different agents for dev/staging/prod
✅ **Specialized agents** - Task-specific configurations
✅ **Simplified usage** - Just agent name + instruction

The result is a much cleaner and more intuitive workflow for infrastructure automation through natural language!