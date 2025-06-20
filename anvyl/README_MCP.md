# Anvyl MCP (Model Context Protocol) Implementation

This document describes the Anvyl implementation of AI agents using the Model Context Protocol (MCP).

## Overview

The Model Context Protocol (MCP) is an open standard for connecting AI assistants to data sources and tools. Anvyl provides a complete implementation including:

- **MCP Servers**: Expose tools, resources, and prompts to AI agents
- **MCP Clients**: Connect to servers and use their capabilities
- **CLI Interface**: Manage agents and servers through command-line
- **Example Implementations**: Working server and client examples

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Agent      │◄──►│   MCP Client    │◄──►│   MCP Server    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                      │
                                ▼                      ▼
                         ┌─────────────────┐    ┌─────────────────┐
                         │   Transport     │    │  Tools/Resources│
                         │  (stdio/HTTP)   │    │    & Prompts    │
                         └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Test the Basic Implementation

```bash
# Test the MCP implementation
python3 anvyl/examples/test_mcp.py
```

### 2. Start an MCP Server

```bash
# Terminal 1: Start the server
python3 anvyl/examples/simple_mcp_server.py
```

### 3. Connect with an MCP Client

```bash
# Terminal 2: Start the client
python3 anvyl/examples/simple_mcp_client.py python3 anvyl/examples/simple_mcp_server.py
```

### 4. Interactive MCP Session

Once connected, you can use commands like:

```
mcp> list-tools
mcp> call-tool echo "Hello MCP!"
mcp> call-tool add 5 3
mcp> list-resources
mcp> read-resource server://status
mcp> quit
```

## 📋 Available MCP Commands

The Anvyl CLI includes comprehensive MCP management:

```bash
# List available MCP servers
anvyl mcp list-servers

# Start an MCP server
anvyl mcp start-server example-server

# Test client connectivity
anvyl mcp test-client

# Create an AI agent
anvyl mcp create-agent my-agent --server example-server

# List configured agents
anvyl mcp list-agents

# Run an agent interactively
anvyl mcp run-agent my-agent --task "analyze system"
```

## 🔧 MCP Server Capabilities

### Tools
Functions that agents can call to perform actions:

- **echo**: Echo input text
- **add**: Add two numbers
- **get_time**: Get current timestamp
- **system_info**: Get system information

### Resources
Data sources that agents can read:

- **server://status**: Current server status
- **server://tools**: List of available tools
- **anvyl://server/capabilities**: Server capabilities

### Prompts
Templates for agent interactions:

- **greeting**: Generate personalized greetings
- **code_review**: Code review templates

## 🧪 Testing & Validation

### Manual Protocol Test

```bash
# Test server response to initialize request
echo '{"id": "test", "method": "initialize", "params": {"protocol_version": "2024-11-05"}}' | python3 anvyl/examples/simple_mcp_server.py
```

### Tool Call Test

```bash
# Test tool call functionality
echo '{"id": "test", "method": "tools/call", "params": {"name": "echo", "arguments": {"text": "Hello MCP!"}}}' | python3 anvyl/examples/simple_mcp_server.py
```

### Resource Read Test

```bash
# Test resource reading
echo '{"id": "test", "method": "resources/read", "params": {"uri": "server://status"}}' | python3 anvyl/examples/simple_mcp_server.py
```

## 📚 Implementation Details

### Protocol Compliance

- **Protocol Version**: 2024-11-05
- **Transport**: stdio (standard input/output)
- **Message Format**: JSON-RPC 2.0
- **Capabilities**: Tools, Resources, Prompts

### Message Types

1. **Requests**: Bidirectional messages expecting responses
2. **Responses**: Success/error responses to requests
3. **Notifications**: One-way messages requiring no response

### Key Features

- ✅ **Protocol Compliant**: Follows MCP specification
- ✅ **Client-Server Architecture**: Clean separation of concerns
- ✅ **Multiple Transports**: stdio and HTTP support
- ✅ **Type Safety**: Structured message handling
- ✅ **Error Handling**: Comprehensive error responses
- ✅ **Extensible**: Easy to add new tools and resources

## 🛠️ Development

### Adding New Tools

```python
# In your MCP server
@server.tool("my_tool", "Tool description", {
    "param1": {"type": "string", "description": "Parameter description"}
}, ["param1"])
def my_tool(param1: str) -> str:
    return f"Tool result: {param1}"
```

### Adding New Resources

```python
@server.resource("my://resource", "Resource Name", "Resource description")
def my_resource() -> str:
    return "Resource content"
```

### Adding New Prompts

```python
@server.prompt("my_prompt", "Prompt description", "Template: {param}")
def my_prompt(param: str = "default") -> str:
    return f"Prompt content with {param}"
```

## 🔍 Troubleshooting

### Common Issues

1. **Server Not Responding**
   - Check if server process is running
   - Verify JSON message format
   - Ensure proper line termination

2. **Client Connection Failed**
   - Verify server command and arguments
   - Check transport configuration
   - Review error messages

3. **Tool Call Errors**
   - Validate tool parameters
   - Check required arguments
   - Review tool implementation

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📖 Examples

### Complete Server Example

See `anvyl/examples/simple_mcp_server.py` for a full server implementation with:
- Multiple tools (echo, add, get_time)
- Multiple resources (status, tools list)
- Multiple prompts (greeting)
- Error handling
- Protocol compliance

### Complete Client Example

See `anvyl/examples/simple_mcp_client.py` for a full client implementation with:
- Server connection management
- Interactive command interface
- Error handling
- Protocol compliance

## 🎯 Next Steps

1. **Extend Server Capabilities**
   - Add domain-specific tools
   - Implement custom resources
   - Create specialized prompts

2. **Integrate with AI Models**
   - Connect to language models
   - Implement agent reasoning
   - Add memory management

3. **Production Deployment**
   - HTTP transport for remote servers
   - Authentication and security
   - Monitoring and logging

## 🔗 References

- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Anvyl Infrastructure Documentation](../README.md)

---

**Status**: ✅ Implementation Complete & Tested  
**Protocol Version**: 2024-11-05  
**Last Updated**: 2024-01-01