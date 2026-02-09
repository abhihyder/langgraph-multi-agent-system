# LangSmith Tracing - Quick Reference

## 🚀 Quick Setup (3 Steps)

1. **Get LangSmith API Key**
   - Sign up: https://smith.langchain.com/
   - Go to Settings → API Keys → Create API Key

2. **Add to `.env` file**
   ```bash
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your_api_key_here
   LANGCHAIN_PROJECT=multi-agent-ai-system
   ```

3. **Start your app** - Tracing is automatic! ✅

4. **View traces**: https://smith.langchain.com/

---

## 📊 What Gets Traced

✅ **All LLM calls** (prompts, responses, tokens, costs)  
✅ **Orchestrator routing** (intent classification, agent selection)  
✅ **All agent executions** (research, writing, code, general)  
✅ **Knowledge retrieval** (global knowledge searches)  
✅ **Memory retrieval** (user conversation history)  
✅ **Aggregator synthesis** (final response generation)  
✅ **Complete execution timeline** with latency  
✅ **Custom metadata** (user_id, conversation_id, etc.)

---

## 🏷️ Filtering Tags

Use these tags in LangSmith dashboard to filter traces:

| Tag | Description |
|-----|-------------|
| `orchestrator` | Routing and intent classification |
| `agent` | All agent operations |
| `research` | Research agent executions |
| `writing` | Writing agent executions |
| `code` | Code agent executions |
| `general` | General agent executions |
| `knowledge` | Knowledge retrieval |
| `memory` | Memory retrieval |
| `retrieval` | All retrieval operations |
| `aggregator` | Response synthesis |
| `service` | Service layer operations |
| `graph` | LangGraph execution |
| `multi-agent` | Multi-agent orchestration |

---

## 💡 Common Use Cases

### 1. Debug Wrong Agent Selection
**View**: Filter by `orchestrator` tag  
**Check**: Intent classification and routing decision  
**Fix**: Adjust orchestrator prompt or add examples

### 2. Find Slow Operations
**View**: Trace timeline in dashboard  
**Check**: Latency breakdown by component  
**Fix**: Optimize slow agent or use faster model

### 3. Monitor API Costs
**View**: Dashboard cost metrics  
**Check**: Token usage by model/provider  
**Fix**: Switch expensive agents to cheaper models

### 4. Track Errors
**View**: Filter traces by error status  
**Check**: Error patterns and stack traces  
**Fix**: Handle edge cases or add retries

---

## 🔧 Advanced Usage

### Add Custom Metadata
```python
from app.utils.tracing import add_trace_metadata

add_trace_metadata({
    "user_tier": "premium",
    "feature_flag": "enabled",
    "experiment_id": "exp_123"
})
```

### Add Custom Tags
```python
from app.utils.tracing import add_trace_tags

add_trace_tags(["high-priority", "complex-query"])
```

### Create Custom Trace
```python
from app.utils.tracing import trace_context

with trace_context(
    name="preprocessing",
    metadata={"step": "data_validation"}
):
    result = validate_data()
```

### Log User Feedback
```python
from app.utils.tracing import log_trace_feedback

log_trace_feedback(
    run_id="trace_id_here",
    score=0.9,
    feedback_type="user_rating",
    comment="Excellent response!"
)
```

---

## 🎯 Dashboard Features

### Traces View
- List of all traces with status, duration, cost
- Filter by tags, status, date range
- Search by metadata

### Trace Details
- **Timeline**: Visual execution flow
- **Tree View**: Hierarchical operation view
- **Inputs/Outputs**: Data at each step
- **Metadata**: Custom tags and info
- **Costs**: Token usage and estimated costs
- **Latency**: Time spent at each step

### Analytics
- **Success Rate**: % successful runs
- **Latency**: P50, P95, P99 percentiles
- **Token Usage**: By model and provider
- **Cost Analysis**: Spending trends
- **Error Rates**: Failures over time

---

## ⚙️ Configuration

### Environment Variables

```bash
# Enable/disable tracing
LANGCHAIN_TRACING_V2=true

# Your LangSmith API key
LANGCHAIN_API_KEY=ls_xxx_your_key

# Project name in dashboard
LANGCHAIN_PROJECT=multi-agent-ai-system

# API endpoint (usually default)
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

### Disable Tracing

Set `LANGCHAIN_TRACING_V2=false` or remove the variable.

---

## 🐛 Troubleshooting

### Traces Not Appearing?

1. ✅ Check `LANGCHAIN_TRACING_V2=true` in .env
2. ✅ Verify API key is correct
3. ✅ Look for "[LangSmith] Tracing enabled" in console
4. ✅ Check network access to api.smith.langchain.com
5. ✅ Restart application after .env changes

### Missing Metadata?

1. ✅ Ensure adding metadata within traced context
2. ✅ Check decorator applied to function
3. ✅ Verify trace completed successfully

### High Latency?

1. ✅ Tracing adds ~10-50ms overhead (minimal)
2. ✅ Check network latency to LangSmith
3. ✅ Async tracing enabled by default

---

## 📚 Resources

- **LangSmith Dashboard**: https://smith.langchain.com/
- **Setup Guide**: [LANGSMITH_SETUP.md](LANGSMITH_SETUP.md)
- **Implementation Details**: [LANGSMITH_IMPLEMENTATION.md](LANGSMITH_IMPLEMENTATION.md)
- **Official Docs**: https://docs.smith.langchain.com/

---

## ✅ Files Modified

All tracing implementation files:

1. [requirements.txt](../requirements.txt) - Added langsmith
2. [config/settings.py](../config/settings.py) - LangSmith config
3. [app/utils/tracing.py](../app/utils/tracing.py) - **NEW** Tracing utilities
4. [app/utils/llm_factory.py](../app/utils/llm_factory.py) - LLM tracing
5. [app/main.py](../app/main.py) - Initialize tracing
6. [app/services/chat_service.py](../app/services/chat_service.py) - Service tracing
7. [app/agentic/graph.py](../app/agentic/graph.py) - Graph tracing
8. [app/agentic/orchestrator.py](../app/agentic/orchestrator.py) - Orchestrator tracing
9. [app/agentic/aggregator.py](../app/agentic/aggregator.py) - Aggregator tracing
10. [app/agentic/agents/*.py](../app/agentic/agents/) - All agent tracing
11. [.env.example](../.env.example) - Configuration template
12. [README.md](../README.md) - Updated documentation

---

**That's it!** 🎉 

Your multi-agent AI system now has comprehensive tracing. Start your app and check https://smith.langchain.com/ to see your traces!
