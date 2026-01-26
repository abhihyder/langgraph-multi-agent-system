# 📚 Quick Reference Guide

## Essential Commands

### Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add OPENAI_API_KEY
```

### Running the System
```bash
# Interactive CLI
python -m app.main

# Quick test
python run_test.py

# Python API
python
>>> from app import run_agent_system
>>> run_agent_system("Your question here")
```

## File Structure Quick Ref

```
multi-agent/
├── app/
│   ├── main.py          # Entry point - START HERE
│   ├── graph.py         # LangGraph workflow
│   ├── state.py         # State schema
│   ├── router.py        # Orchestrator agent
│   ├── aggregator.py    # Output synthesis
│   └── agents/
│       ├── research.py  # Facts & analysis
│       ├── writing.py   # Content creation
│       └── code.py      # Code generation
├── prompts/             # Agent instructions
├── config/              # Settings
└── requirements.txt     # Dependencies
```

## Agent Routing Examples

| User Query | Selected Agents | Reason |
|------------|----------------|--------|
| "What is Docker?" | research | Factual question |
| "Explain machine learning" | research + writing | Needs explanation |
| "Build a REST API" | code | Implementation needed |
| "Compare React vs Vue, show code" | research + code | Analysis + implementation |
| "Write tutorial on Python" | research + writing | Educational content |

## Code Snippets

### Basic Usage
```python
from app import run_agent_system

# Simple query
response = run_agent_system("What is Python?")
print(response)
```

### With Verbose Output
```python
response = run_agent_system(
    "Compare databases", 
    verbose=True
)
# Shows intermediate agent outputs
```

### Access the Graph Directly
```python
from app.graph import app
from app.state import AgentState

state = {
    "user_input": "Your question",
    "intent": None,
    "research_output": None,
    "writing_output": None,
    "code_output": None,
    "selected_agents": [],
    "final_output": None
}

result = app.invoke(state)
print(result["final_output"])
```

## Configuration Options

### Environment Variables (.env)
```bash
# Required
OPENAI_API_KEY=sk-...

# Optional model selection
ORCHESTRATOR_MODEL=gpt-4
RESEARCH_MODEL=gpt-4
WRITING_MODEL=gpt-4
CODE_MODEL=gpt-4

# Optional temperature tuning
ORCHESTRATOR_TEMPERATURE=0      # Deterministic
RESEARCH_TEMPERATURE=0.3
WRITING_TEMPERATURE=0.7  # More creative
CODE_TEMPERATURE=0.2
AGGREGATOR_TEMPERATURE=0.5

# System settings
MAX_RETRIES=3
TIMEOUT=120
VERBOSE=false
```

## Prompt Customization

### Edit Agent Prompts
```bash
# Research Agent
nano prompts/research.md

# Writing Agent
nano prompts/writing.md

# Code Agent
nano prompts/code.md

# Orchestrator Agent
nano prompts/orchestrator.md
```

## Adding a New Agent

### 1. Create Agent File
```python
# app/agents/new_agent.py
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from ..state import AgentState

def new_agent(state: AgentState) -> Dict[str, Any]:
    llm = ChatOpenAI(model="gpt-4", temperature=0.5)
    result = llm.invoke(state["user_input"])
    return {"new_output": result.content}
```

### 2. Update State Schema
```python
# app/state.py
class AgentState(TypedDict):
    # ... existing fields ...
    new_output: Optional[str]
```

### 3. Add to Graph
```python
# app/graph.py
from .agents import new_agent

workflow.add_node("new", new_agent)
workflow.add_edge("new", "aggregator")
```

### 4. Update Router
```python
# prompts/orchestrator.md
# Add new agent to available agents list
```

## Common Issues & Solutions

### Issue: Import Error
```bash
# Solution
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: API Key Error
```bash
# Solution
echo $OPENAI_API_KEY  # Check if set
# Or check .env file exists
```

### Issue: Model Timeout
```python
# In config/settings.py
TIMEOUT=300  # Increase to 5 minutes
```

### Issue: Slow Responses
```python
# Use faster models
ORCHESTRATOR_MODEL=gpt-3.5-turbo
RESEARCH_MODEL=gpt-3.5-turbo
```

## Testing Queries

### Test Research Agent
```
Your question: What are the benefits of Kubernetes?
Your question: Compare SQL vs NoSQL databases
Your question: What is the latest in AI research?
```

### Test Writing Agent
```
Your question: Write a tutorial on Git basics
Your question: Explain how the internet works
Your question: Create a guide to Python decorators
```

### Test Code Agent
```
Your question: Create a Python function for binary search
Your question: Build a REST API endpoint in FastAPI
Your question: Implement a React component for user login
```

### Test Multi-Agent
```
Your question: Compare Python frameworks and show FastAPI example
Your question: Explain microservices and provide sample code
Your question: What is Docker and how do I use it?
```

## Performance Tips

### Speed Up Responses
1. Use GPT-3.5-turbo for non-critical agents
2. Reduce temperature for faster generation
3. Cache frequent queries
4. Use smaller prompts

### Reduce Costs
1. Use cheaper models where possible
2. Implement response caching
3. Optimize prompts to be shorter
4. Limit max_tokens in LLM calls

### Improve Quality
1. Use GPT-4 for all agents
2. Increase temperature for writing
3. Add more context in prompts
4. Implement self-critique loops

## Debugging

### Enable Verbose Mode
```bash
python -m app.main
> Your question --verbose
```

### Check State at Each Step
```python
from app.graph import app
result = app.invoke(state)

print("Intent:", result["intent"])
print("Selected:", result["selected_agents"])
print("Research:", result.get("research_output", "None"))
print("Writing:", result.get("writing_output", "None"))
print("Code:", result.get("code_output", "None"))
```

### Add Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Useful Documentation Links

- **LangChain**: https://python.langchain.com/docs/
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **OpenAI API**: https://platform.openai.com/docs
- **Pydantic**: https://docs.pydantic.dev/

## Project Documentation

- [README.md](README.md) - Overview & features
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [DEVELOPMENT_PROGRESS.md](DEVELOPMENT_PROGRESS.md) - Implementation details
- [INSTRUCTION.md](INSTRUCTION.md) - Original requirements

## Quick Troubleshooting Checklist

- [ ] Virtual environment activated?
- [ ] Dependencies installed?
- [ ] .env file exists?
- [ ] OPENAI_API_KEY set?
- [ ] API key has quota?
- [ ] Internet connection working?
- [ ] Python version 3.10+?

---

**Need help?** Check the detailed guides in the documentation folder!
