# DuckDuckGo Search Tool Integration

This document explains the DuckDuckGo search functionality added to the Anvyl AI agent system.

## Overview

The Anvyl AI agent now includes web search capabilities using DuckDuckGo, allowing the agent to:

- 🔍 Search for current information and documentation
- 🛠️ Find troubleshooting guides and solutions  
- 📚 Research best practices and tutorials
- ⚡ Get up-to-date information about technologies and tools

## Installation

The DuckDuckGo search functionality is automatically included when you install Anvyl with the updated dependencies:

```bash
pip install -e .
```

Or if you're installing manually:

```bash
pip install "pydantic-ai-slim[duckduckgo]"
```

## Usage

### Via Agent Conversation

Once the agent is running, you can ask it to search for information:

```
User: "Search for Docker container security best practices"
Agent: [Uses DuckDuckGo search tool to find current information and provides summary]

User: "Find information about Kubernetes troubleshooting"
Agent: [Searches and provides relevant results]

User: "What are the latest updates for PostgreSQL?"
Agent: [Searches for current information about PostgreSQL]
```

### Available Search Capabilities

The agent can now help with:

1. **Documentation Lookup**: Finding official docs and guides
2. **Troubleshooting**: Searching for solutions to specific errors
3. **Best Practices**: Finding current recommendations and standards
4. **Technology Updates**: Getting information about latest versions and features
5. **Configuration Examples**: Finding sample configurations and setups

## Tool Details

The DuckDuckGo search tool (`duckduckgo_search`) is automatically added to the agent's toolkit and includes:

- **Name**: `duckduckgo_search`
- **Description**: "Searches DuckDuckGo for the given query and returns the results"
- **Input**: Search query string
- **Output**: Search results with titles, snippets, and URLs

## Examples

### Infrastructure Help
```
"Search for nginx reverse proxy configuration examples"
"Find Redis clustering best practices"
"Look up Docker Compose networking troubleshooting"
```

### Technology Research
```
"Search for Python asyncio performance optimization"
"Find information about FastAPI deployment strategies"
"Look up PostgreSQL backup and recovery procedures"
```

### Error Resolution
```
"Search for solutions to 'docker container exit code 125'"
"Find fixes for PostgreSQL connection refused errors"
"Look up nginx 502 bad gateway troubleshooting"
```

## Integration Details

### Code Changes Made

1. **Dependencies**: Updated `pyproject.toml` to include `pydantic-ai-slim[duckduckgo]`
2. **Tools**: Added DuckDuckGo search tool to `anvyl/agent/tools.py`
3. **Agent**: Updated system prompt in `anvyl/agent/host_agent.py` to mention search capability
4. **Error Handling**: Added graceful fallback if DuckDuckGo dependencies aren't available

### System Architecture

```
Anvyl Agent
├── Infrastructure Tools (containers, hosts, commands)
├── Communication Tools (inter-agent messaging)
└── Search Tools (DuckDuckGo web search)  ← NEW!
```

## Testing

Run the test script to verify the integration:

```bash
python test_duckduckgo_search.py
```

This will:
- ✅ Check if the DuckDuckGo search tool is available
- 🔍 Test a sample search query  
- 📊 Display results and confirm functionality

## Benefits

Adding web search capabilities to the Anvyl agent provides:

1. **Enhanced Problem Solving**: Agent can find solutions to unfamiliar issues
2. **Current Information**: Access to up-to-date documentation and guides
3. **Self-Service Support**: Reduced need for manual research and documentation
4. **Learning Capability**: Agent can discover new techniques and best practices
5. **Comprehensive Assistance**: Combines infrastructure management with web research

## Privacy and Usage

- DuckDuckGo doesn't track users or store personal information
- Search queries are made directly to DuckDuckGo's API
- No additional API keys or configuration required
- Search results are processed locally by the agent

## Troubleshooting

### Search Tool Not Available
If you see warnings about the DuckDuckGo search tool not being available:

```bash
# Reinstall with DuckDuckGo support
pip install "pydantic-ai-slim[duckduckgo]"

# Or update the project dependencies
pip install -e .
```

### Import Errors
If you encounter import errors:

1. Ensure you have the correct version of pydantic-ai-slim
2. Check that the duckduckgo optional dependency is installed
3. Try reinstalling: `pip uninstall pydantic-ai-slim && pip install "pydantic-ai-slim[duckduckgo]"`

### Search Not Working
If searches fail:

1. Check internet connectivity
2. Verify DuckDuckGo service is accessible
3. Check firewall/proxy settings
4. Review agent logs for specific error messages

## Future Enhancements

Potential improvements for the search functionality:

- 🎯 **Search Filters**: Add domain-specific search filters
- 📊 **Result Ranking**: Implement relevance scoring for results
- 💾 **Search Cache**: Cache frequent queries to improve performance
- 🔧 **Search Templates**: Pre-built searches for common infrastructure tasks
- 📈 **Search Analytics**: Track and improve search query effectiveness