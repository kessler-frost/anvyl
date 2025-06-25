# Anvyl - Simple Container Management with AI

DISCLAIMER: This is my first attempt at "vibe coding" a simple tool over a weekend.

> **Simplicity is key.** Manage your containers with plain English, not complex commands.

Anvyl makes container management effortless. Just tell it what you want in natural language, and it handles the complexity for you.

## Why Simple?

Container management shouldn't be complicated. Anvyl strips away the complexity:

- **One command to start everything**: `anvyl up`
- **Plain English queries**: "Show me running containers"
- **Zero configuration**: Works out of the box
- **Single installation**: `pip install .`

## Quick Start (3 steps)

### 1. Install
```bash
git clone https://github.com/kessler-frost/anvyl.git
cd anvyl
pip install .
```

### 2. Start Your AI Model
You need either:
- **LM Studio** running on `http://localhost:1234` (recommended)
- **Ollama** running on `http://localhost:11434` (update port in config if needed)

### 3. Start Anvyl
```bash
anvyl up
```

### 3. Ask
```bash
anvyl agent "Show me all running containers"
anvyl agent "Create an nginx container on port 8080"
anvyl agent "What's the CPU usage?"
```

That's it. No complex configuration files, no learning curve.

## What You Can Do

**Container Management**
```bash
anvyl agent "List all containers"
anvyl agent "Start a Redis container"
anvyl agent "Stop the nginx container"
```

**System Monitoring**
```bash
anvyl agent "Show CPU usage"
anvyl agent "Check disk space"
anvyl agent "What services are running?"
```

**Remote Management**
```bash
anvyl agent add-host server1 192.168.1.100
anvyl agent "List containers on server1" --host-id server1
```

## Connect to Claude Desktop

Add this simple configuration:

```json
{
  "mcpServers": {
    "anvyl-containers": {
      "command": "python",
      "args": ["-m", "anvyl.mcp.server"]
    }
  }
}
```

Now ask Claude directly: "Show me my containers", "Deploy nginx", etc.

## Simple Commands

```bash
anvyl up           # Start everything
anvyl down         # Stop everything  
anvyl status       # Check status
anvyl restart      # Restart all

# That's all you need to remember
```

## Advanced Usage

For power users who need direct API access or integration:

**REST APIs Available**
- **Agent API**: `http://localhost:4202` - Direct agent management and queries
- **Infrastructure API**: `http://localhost:4200` - Low-level container and system operations
- **MCP Server**: `http://localhost:4201` - Integration with AI applications

**Individual Service Management**
```bash
# Start services individually
anvyl agent up
anvyl infra up  
anvyl mcp up

# Check individual service logs
anvyl agent logs
anvyl infra logs
```

**API Examples**
```bash
# Query agent via REST API
curl -X POST http://localhost:4202/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all containers"}'

# Direct container API calls
curl http://localhost:4200/containers
```

Still simple, just more control when you need it.

## For Developers

**Requirements**: Python 3.10+, Docker, LM Studio or Ollama

```bash
git clone https://github.com/kessler-frost/anvyl.git
cd anvyl
pip install -e .

# Make sure LM Studio is running on localhost:1234
# OR Ollama is running on localhost:11434
anvyl up
```

Simple as that.

---

**Remember**: If it feels complicated, we've failed. Container management should be simple.

## License

MIT License - see [LICENSE](LICENSE) for details.
