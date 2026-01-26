# MCP Integration Guide

## Overview

The multi-agent system supports optional Model Context Protocol (MCP) integration, allowing the research agent to access external tools and data sources when needed.

## What is MCP?

Model Context Protocol (MCP) is an open protocol that enables AI models to securely connect to external tools, APIs, and data sources. When enabled, your research agent can:

- 🔍 Perform web searches for current information
- 📁 Access local file systems
- 🗄️ Query databases
- 🔧 Use custom tools and APIs

## Setup

### 1. Install MCP Library (Optional)

```bash
pip install mcp
```

The system works fully without MCP. Install only if you need external tools.

### 2. Configure MCP Server

Add MCP configuration to your `.env` file:

```bash
# Example: Enable Brave Search for web research
MCP_SERVER_COMMAND=npx
MCP_SERVER_ARGS=-y @modelcontextprotocol/server-brave-search
```

### 3. Set Environment Variables (If Using Brave Search)

```bash
# Required for Brave Search MCP server
export BRAVE_API_KEY=your-brave-api-key
```

Get a free Brave Search API key: https://brave.com/search/api/

## Available MCP Servers

### 1. Brave Search (Recommended for Research)

```bash
MCP_SERVER_COMMAND=npx
MCP_SERVER_ARGS=-y @modelcontextprotocol/server-brave-search
```

**Capabilities:**
- Web search
- Current information lookup
- News and recent events
- Fact verification

**Setup:**
1. Get API key from https://brave.com/search/api/
2. Set `BRAVE_API_KEY` in your environment
3. Configure MCP as shown above

### 2. File System Access

```bash
MCP_SERVER_COMMAND=npx
MCP_SERVER_ARGS=-y @modelcontextprotocol/server-filesystem /path/to/directory
```

**Capabilities:**
- Read local files
- Search file contents
- List directory structures

**Use Cases:**
- Research from local documents
- Code analysis from repositories
- Data extraction from files

### 3. Custom MCP Server

```bash
MCP_SERVER_COMMAND=python
MCP_SERVER_ARGS=/path/to/your_mcp_server.py
```

Build your own MCP server for custom tools and integrations.

## How It Works

### Without MCP (Default)

```
User Question → Research Agent → LLM Knowledge → Response
```

The research agent uses the LLM's training data to answer questions.

### With MCP Enabled

```
User Question → Research Agent → LLM Analysis
                                    ↓
                        "Need external data?" 
                                    ↓
                        MCP Tools → External Data → Enhanced Response
```

The research agent can request external tools when needed for:
- Current events and recent information
- Specific data lookups
- File access
- API calls

## Agent Behavior

### Automatic Detection

The research agent automatically detects if MCP is configured:

```python
# Without MCP
🤖 Research Mode: 📚 Using LLM knowledge only

# With MCP
🤖 Research Mode: ✅ MCP tools available
```

### Smart Tool Usage

The agent decides when to use external tools based on:
- Need for current information
- Requirement for specific data sources
- Benefit of external verification

### Fallback Support

If MCP is unavailable or fails:
- Agent continues with LLM knowledge
- No errors or interruptions
- Graceful degradation

## Testing MCP Integration

### 1. Test Without MCP

```bash
# Don't configure MCP in .env
python -m app.main
```

Ask: "What is machine learning?"
- Expected: Uses LLM knowledge

### 2. Test With MCP

```bash
# Configure MCP in .env
MCP_SERVER_COMMAND=npx
MCP_SERVER_ARGS=-y @modelcontextprotocol/server-brave-search

python -m app.main
```

Ask: "What are today's top tech news?"
- Expected: Uses web search for current information

## Configuration Examples

### Development Setup (No MCP)

```bash
# .env
OPENAI_API_KEY=sk-...
# No MCP configuration
```

Simple setup for testing and development.

### Production Setup (With MCP)

```bash
# .env
OPENAI_API_KEY=sk-...

# Enable web search
MCP_SERVER_COMMAND=npx
MCP_SERVER_ARGS=-y @modelcontextprotocol/server-brave-search

# Brave API key
export BRAVE_API_KEY=your-brave-api-key
```

Full capabilities with external tool access.

## Troubleshooting

### Issue: "MCP library not installed"

**Solution:**
```bash
pip install mcp
```

Or continue without MCP - system works fully without it.

### Issue: "Could not connect to MCP server"

**Possible causes:**
1. Server command not found (e.g., `npx` not installed)
2. Server package not available
3. API keys not configured

**Solution:**
- Verify Node.js installed: `node --version`
- Check API keys are set
- Test server manually: `npx -y @modelcontextprotocol/server-brave-search`

### Issue: Tools not being used

**Explanation:**
The LLM decides when tools are needed. Not all queries require external tools.

**Example:**
- "What is Python?" → Uses LLM knowledge (no tool needed)
- "Latest Python release date?" → May use web search

## Best Practices

### 1. Choose Appropriate MCP Servers

- **Research tasks** → Brave Search
- **Code analysis** → File System
- **Custom needs** → Build your own

### 2. API Key Security

```bash
# Use environment variables
export BRAVE_API_KEY=xxx

# Don't commit .env to git
echo ".env" >> .gitignore
```

### 3. Test Both Modes

Verify your system works:
- Without MCP (baseline)
- With MCP (enhanced)

### 4. Monitor Usage

MCP responses include a note:

```
---
*Note: This response was generated with access to external research tools.*
```

## Advanced: Building Custom MCP Servers

Create your own MCP server for custom integrations:

```python
# custom_mcp_server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("my-custom-server")

@app.list_tools()
async def list_tools():
    return [{
        "name": "custom_lookup",
        "description": "Look up custom data",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            }
        }
    }]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "custom_lookup":
        # Your custom logic here
        return {"result": "data"}

if __name__ == "__main__":
    stdio_server(app)
```

Then configure:
```bash
MCP_SERVER_COMMAND=python
MCP_SERVER_ARGS=/path/to/custom_mcp_server.py
```

## Resources

- MCP Specification: https://modelcontextprotocol.io/
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Official MCP Servers: https://github.com/modelcontextprotocol/servers
- Brave Search API: https://brave.com/search/api/

## Summary

✅ **MCP is optional** - System works fully without it
✅ **Easy to enable** - Just configure environment variables
✅ **Automatic fallback** - Graceful degradation if unavailable
✅ **Flexible** - Use existing servers or build custom ones
✅ **Secure** - Agent decides when to use tools

Start without MCP, enable when you need external tool capabilities!
