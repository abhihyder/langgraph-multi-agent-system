# LangSmith Tracing Setup Guide

This document explains how to set up and use LangSmith for tracing and monitoring your multi-agent AI system.

## Table of Contents

1. [What is LangSmith?](#what-is-langsmith)
2. [Why Use LangSmith?](#why-use-langsmith)
3. [Setup Instructions](#setup-instructions)
4. [Configuration](#configuration)
5. [What Gets Traced?](#what-gets-traced)
6. [Using the LangSmith Dashboard](#using-the-langsmith-dashboard)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)

## What is LangSmith?

LangSmith is a comprehensive platform for debugging, testing, and monitoring LLM applications. It provides:

- **Tracing**: See every step of your agent's execution
- **Monitoring**: Track performance metrics and costs
- **Debugging**: Identify and fix issues quickly
- **Analytics**: Understand usage patterns and bottlenecks
- **Testing**: Create test suites and evaluate outputs

## Why Use LangSmith?

For agentic AI systems like ours with multiple specialized agents, LangSmith provides critical visibility:

1. **Track Agent Flow**: See which agents are invoked and in what order
2. **Monitor LLM Calls**: View all prompts, responses, and token usage
3. **Identify Bottlenecks**: Find slow agents or inefficient routing
4. **Debug Issues**: Trace errors back to their source
5. **Cost Management**: Monitor API usage and costs across providers
6. **Performance Optimization**: Analyze latency and optimize accordingly

## Setup Instructions

### Step 1: Sign Up for LangSmith

1. Visit [https://smith.langchain.com/](https://smith.langchain.com/)
2. Sign up for a free account (or log in if you have one)
3. The free tier includes generous limits for development

### Step 2: Create API Key

1. In the LangSmith dashboard, navigate to **Settings** → **API Keys**
2. Click **Create API Key**
3. Give it a descriptive name (e.g., "Multi-Agent AI Dev")
4. Copy the API key (you won't see it again!)

### Step 3: Configure Environment Variables

Add the following to your `.env` file:

```bash
# LangSmith Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls_xxx_your_api_key_here
LANGCHAIN_PROJECT=multi-agent-ai-system
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

### Step 4: Install Dependencies

The LangSmith SDK is already included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Step 5: Start Your Application

```bash
# Start the server
python server.py

# Or run CLI mode
python -m app.main
```

LangSmith tracing is now active! All traces will appear in your dashboard.

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LANGCHAIN_TRACING_V2` | No | `true` | Enable/disable tracing |
| `LANGCHAIN_API_KEY` | Yes* | None | Your LangSmith API key |
| `LANGCHAIN_PROJECT` | No | `multi-agent-ai-system` | Project name in dashboard |
| `LANGCHAIN_ENDPOINT` | No | `https://api.smith.langchain.com` | LangSmith API endpoint |

*Required only if tracing is enabled

### Disabling Tracing

To disable tracing (e.g., in production):

```bash
LANGCHAIN_TRACING_V2=false
```

Or simply remove/comment out the LangSmith variables.

## What Gets Traced?

Our implementation traces the following:

### 1. **Chat Service**
- Full chat processing flow
- User input metadata (user_id, conversation_id)
- Response metadata (intent, agents used, length)

### 2. **LangGraph Execution**
- Complete graph execution flow
- Agent routing decisions
- State transitions

### 3. **All Agents**
- **Orchestrator**: Intent classification and routing
- **Knowledge Agent**: Global knowledge retrieval
- **Memory Agent**: User conversation history retrieval
- **General Agent**: Generic query handling
- **Research Agent**: Research operations
- **Writing Agent**: Content generation
- **Code Agent**: Code generation
- **Aggregator**: Final response synthesis

### 4. **LLM Calls**
- All prompts sent to LLMs
- Model responses
- Token usage and costs
- Latency metrics
- Provider and model information

### 5. **Custom Metadata**
Each trace includes rich metadata:
- User and conversation identifiers
- Agent selection and routing
- Context availability
- Response characteristics

## Using the LangSmith Dashboard

### Viewing Traces

1. Navigate to your project in the LangSmith dashboard
2. You'll see a list of all traces (runs)
3. Click on any trace to see detailed execution flow

### Understanding the Trace View

Each trace shows:
- **Timeline**: Visual representation of execution flow
- **Tree View**: Hierarchical view of all operations
- **Inputs/Outputs**: Data at each step
- **Metadata**: Custom tags and information
- **Costs**: Token usage and estimated costs
- **Latency**: Time spent at each step

### Filtering Traces

Use tags to filter traces:
- `agent`: All agent executions
- `orchestrator`: Routing decisions
- `research`, `writing`, `code`: Specific agents
- `retrieval`: Knowledge and memory retrieval
- `service`: Service layer operations
- `graph`: LangGraph execution
- `multi-agent`: Multi-agent orchestration

### Monitoring Metrics

The dashboard provides:
- **Success Rate**: Percentage of successful runs
- **Latency Distribution**: P50, P95, P99 latencies
- **Token Usage**: Total tokens by model
- **Cost Analysis**: Spending by provider
- **Error Rates**: Failures over time

## Advanced Features

### Adding Custom Metadata

Use the tracing utilities to add custom metadata:

```python
from app.utils.tracing import add_trace_metadata, add_trace_tags

# Add metadata to current trace
add_trace_metadata({
    "custom_field": "value",
    "user_tier": "premium",
    "feature_flag": "enabled"
})

# Add tags for filtering
add_trace_tags(["high-priority", "complex-query"])
```

### Creating Custom Traces

Wrap your code in trace contexts:

```python
from app.utils.tracing import trace_context

with trace_context(
    name="custom_operation",
    run_type="chain",
    metadata={"operation_id": 123},
    tags=["custom", "important"]
):
    # Your code here
    result = perform_operation()
```

### Logging Feedback

Capture user feedback on responses:

```python
from app.utils.tracing import log_trace_feedback

log_trace_feedback(
    run_id="abc-123-def-456",
    score=0.9,
    feedback_type="user_rating",
    comment="Great response!"
)
```

### Using Decorators

Our custom decorators automatically trace functions:

```python
from app.utils.tracing import trace_agent, trace_service

@trace_agent("my_agent", tags=["custom"])
def my_agent_function(state):
    # Agent logic
    return result

@trace_service("my_service", operation="process")
def my_service_method(self, data):
    # Service logic
    return result
```

## Troubleshooting

### Traces Not Appearing

1. **Check API Key**: Ensure `LANGCHAIN_API_KEY` is set correctly
2. **Verify Tracing Enabled**: `LANGCHAIN_TRACING_V2=true`
3. **Check Console**: Look for "[LangSmith] Tracing enabled" message
4. **Network Issues**: Ensure you can reach `api.smith.langchain.com`
5. **Restart Application**: Restart after changing environment variables

### High Latency

LangSmith adds minimal overhead (~10-50ms per trace). If you experience issues:

1. Use async tracing (enabled by default)
2. Reduce metadata size
3. Consider sampling (trace only percentage of requests)

### API Rate Limits

Free tier has limits:
- Check your usage in the dashboard
- Consider upgrading for production
- Implement sampling for high-volume applications

### Missing Metadata

If custom metadata doesn't appear:

1. Ensure you're within a traced context
2. Check that `LANGCHAIN_TRACING_V2=true`
3. Verify the trace completed successfully

## Best Practices

1. **Use Descriptive Project Names**: Makes traces easier to find
2. **Add Meaningful Tags**: Enables powerful filtering
3. **Include Business Context**: Add user_id, session_id, etc.
4. **Monitor Regularly**: Set up alerts for errors and latency
5. **Archive Old Projects**: Keep dashboard organized
6. **Document Trace Patterns**: Help team understand common flows
7. **Use Feedback**: Capture user ratings for model evaluation

## Integration with Development Workflow

### Local Development
- Keep tracing enabled to catch issues early
- Use separate project names for dev/staging/prod

### Testing
- Traces help debug failing tests
- Compare test runs over time

### Production
- Monitor performance and costs
- Set up alerts for anomalies
- Use for incident investigation

## Resources

- **LangSmith Docs**: https://docs.smith.langchain.com/
- **LangSmith Dashboard**: https://smith.langchain.com/
- **LangChain Discord**: Community support
- **API Reference**: https://api.python.langchain.com/

## Support

For issues specific to our implementation:
1. Check this documentation
2. Review code in `app/utils/tracing.py`
3. Check environment variable configuration
4. Consult LangSmith official documentation

---

**Happy Tracing! 🚀**

With LangSmith, you now have complete visibility into your multi-agent system's behavior, making debugging and optimization significantly easier.
