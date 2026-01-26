# Multi-Agent AI System with LangGraph

A production-ready agentic AI system using **LangGraph** with NGINX-style architecture, where a **Boss (Router) Agent** delegates tasks to specialized agents.

## 🏗️ Architecture

```
User Input
   ↓
Boss Agent (Router)
   ↓ (conditional routing)
┌───────────────┬───────────────┬───────────────┐
│ ResearchAgent │ WritingAgent  │ CodeAgent     │
└───────────────┴───────────────┴───────────────┘
   ↓ (fan-in)
Aggregator Agent
   ↓
Final Response to User
```

### Key Principles

- **Boss Agent never answers directly** - Only routes to specialists
- **Specialized agents don't communicate** - Clean separation of concerns
- **Boss controls flow** - Orchestrates everything
- **State is explicit** - Shared state passed between nodes

## 🎯 Features

- **Research Agent**: Provides factual information, comparisons, and analysis
- **Writing Agent**: Creates well-structured, human-friendly content
- **Code Agent**: Generates production-quality code
- **Smart Routing**: Boss agent determines which agents to invoke
- **Intelligent Aggregation**: Synthesizes multiple agent outputs

## 📋 Prerequisites

- Python 3.10+
- OpenAI API key (or Anthropic for Claude)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd multi-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Run the System

```bash
# Interactive CLI mode
python -m app.main

# Or import in your code
python
>>> from app import run_agent_system
>>> response = run_agent_system("What is LangGraph?")
>>> print(response)
```

## 📁 Project Structure

```
multi-agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point & CLI
│   ├── graph.py             # LangGraph workflow definition
│   ├── state.py             # Shared state schema
│   ├── router.py            # Boss agent logic
│   ├── aggregator.py        # Response synthesis
│   └── agents/
│       ├── __init__.py
│       ├── research.py      # Research agent
│       ├── writing.py       # Writing agent
│       └── code.py          # Code agent
│
├── prompts/                 # Agent prompt templates
│   ├── boss.md
│   ├── research.md
│   ├── writing.md
│   └── code.md
│
├── config/
│   └── settings.py          # Configuration management
│
├── requirements.txt
├── .env.example
└── README.md
```

## 💡 Usage Examples

### Example 1: Research Query

```python
from app import run_agent_system

response = run_agent_system("Compare SQL and NoSQL databases")
# Boss routes to: Research Agent
```

### Example 2: Writing Task

```python
response = run_agent_system("Write an explanation of machine learning")
# Boss routes to: Research Agent → Writing Agent
```

### Example 3: Code Generation

```python
response = run_agent_system("Create a FastAPI endpoint for user authentication")
# Boss routes to: Code Agent
```

### Example 4: Complex Multi-Agent Task

```python
response = run_agent_system("Compare Python web frameworks and show example code for FastAPI")
# Boss routes to: Research Agent → Code Agent → Aggregator
```

### Verbose Mode

Add `--verbose` flag to see intermediate steps:

```bash
python -m app.main
> Compare React and Vue --verbose
```

## 🔧 Configuration

Edit `config/settings.py` or set environment variables in `.env`:

```bash
# Models
BOSS_MODEL=gpt-4
RESEARCH_MODEL=gpt-4
WRITING_MODEL=gpt-4
CODE_MODEL=gpt-4

# Temperature settings
RESEARCH_TEMPERATURE=0.3
WRITING_TEMPERATURE=0.7
CODE_TEMPERATURE=0.2

# System
MAX_RETRIES=3
TIMEOUT=120
```

## 🎨 Customization

### Adding a New Agent

1. Create agent file in `app/agents/`:

```python
# app/agents/custom.py
def custom_agent(state: AgentState) -> Dict[str, Any]:
    # Your agent logic
    return {"custom_output": result}
```

2. Add prompt in `prompts/custom.md`

3. Register in `app/graph.py`:

```python
workflow.add_node("custom", custom_agent)
```

4. Update routing logic in boss prompt

## 🧪 Testing

```bash
# Run basic test
python -m app.main
> What is Python?

# Test different agent combinations
> Compare frameworks  # Research
> Write a tutorial    # Research + Writing
> Build an API        # Code
> Explain and show code  # Research + Writing + Code
```

## 📊 State Flow

The `AgentState` TypedDict flows through the system:

```python
{
    "user_input": str,           # Original query
    "intent": str,               # Boss interpretation
    "selected_agents": List[str], # Agents to invoke
    "research_output": str,      # Research agent result
    "writing_output": str,       # Writing agent result
    "code_output": str,          # Code agent result
    "final_output": str          # Aggregated response
}
```

## 🚧 Production Considerations

For production deployment, consider adding:

- **Error Handling**: Retry logic and fallbacks
- **Monitoring**: LangSmith or OpenTelemetry integration
- **Rate Limiting**: API call management
- **Caching**: Redis for repeated queries
- **API Layer**: FastAPI wrapper for HTTP access
- **Authentication**: Secure API endpoints
- **Cost Tracking**: Monitor LLM usage

## 📝 Development Notes

- Each agent writes ONLY to its designated state field
- Boss agent never generates content
- Aggregator runs after all agents complete
- Parallel execution supported for multiple agents
- State is immutable per node (updates merged)

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Additional specialized agents (SQL, Data Analysis, etc.)
- LLM-based routing instead of rules
- Tool-using agents (web search, database access)
- Memory and conversation history
- Human-in-the-loop workflows

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Built with:
- [LangChain](https://github.com/langchain-ai/langchain)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- OpenAI GPT-4

---

**Philosophy**: Agents should behave like microservices, not like humans chatting. Determinism, clarity, and control beat autonomy in real systems.
