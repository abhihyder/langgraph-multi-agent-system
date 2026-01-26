# Multi-Agent AI System with LangGraph

A production-ready agentic AI system using **LangGraph** with NGINX-style architecture, where a **Boss (Router) Agent** delegates tasks to specialized agents.

**🎨 Now with a beautiful web UI!** Chat interface built with FastAPI + React.

## 🏗️ Architecture

```
User Input (Web UI / CLI)
   ↓
Boss Agent (Router)
   ↓ (conditional routing)
┌───────────────┬───────────────┬───────────────┐
│ ResearchAgent │ WritingAgent  │ CodeAgent     │
└───────────────┴───────────────┴───────────────┘
   ↓ (fan-in)
Aggregator Agent
   ↓
Final Response (Web UI / CLI)
```

### Key Principles

- **Boss Agent never answers directly** - Only routes to specialists
- **Specialized agents don't communicate** - Clean separation of concerns
- **Boss controls flow** - Orchestrates everything
- **State is explicit** - Shared state passed between nodes

## 🎯 Features

- **🌐 Web Interface**: Beautiful chat UI with markdown rendering and syntax highlighting
- **💻 CLI Interface**: Interactive command-line interface
- **🤖 Three Specialized Agents**:
  - **Research Agent**: Provides factual information, comparisons, and analysis
  - **Writing Agent**: Creates well-structured, human-friendly content
  - **Code Agent**: Generates production-quality code
- **🎨 Markdown Support**: Full markdown rendering with syntax-highlighted code blocks
- **🔀 Smart Routing**: Boss agent determines which agents to invoke
- **🔄 Intelligent Aggregation**: Synthesizes multiple agent outputs
- **⚡ REST API**: FastAPI backend for easy integration

## 📋 Prerequisites

- Python 3.10+
- Node.js 16+ (for web UI)
- OpenAI API key

## 🚀 Quick Start

### Option 1: Web Interface (Recommended)

#### Step 1: Setup Backend

```bash
# Clone/navigate to project
cd multi-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

#### Step 2: Start FastAPI Server

```bash
# Run the backend server
python server.py
```

Backend will be available at: **http://localhost:8000**  
API Documentation: **http://localhost:8000/docs**

#### Step 3: Setup Frontend

Open a **new terminal**:

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:3000**

#### Step 4: Start Chatting! 🎉

Open your browser and go to **http://localhost:3000**

Try asking:
- "What is Docker?"
- "Write a tutorial on Python basics"
- "Create a REST API in FastAPI"
- "Compare React and Vue, then show example code"

### Option 2: CLI Interface

```bash
# Activate virtual environment
source venv/bin/activate

# Run interactive CLI
python -m app.main

# Or use in Python code
python
>>> from app import run_agent_system
>>> response = run_agent_system("What is LangGraph?")
>>> print(response)
```

## 📁 Project Structure

```
multi-agent/
├── app/                     # Core application
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── graph.py             # LangGraph workflow
│   ├── state.py             # Shared state schema
│   ├── router.py            # Boss agent logic
│   ├── aggregator.py        # Response synthesis
│   └── agents/              # Specialized agents
│       ├── research.py
│       ├── writing.py
│       └── code.py
│
├── frontend/                # React web UI
│   ├── src/
│   │   ├── App.jsx          # Main chat component
│   │   ├── App.css          # Styles
│   │   └── main.jsx         # React entry
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── prompts/                 # Agent instructions
│   ├── boss.md
│   ├── research.md
│   ├── writing.md
│   └── code.md
│
├── config/
│   └── settings.py          # Configuration
│CLI Examples

### Research Query

```python
from app import run_agent_system

response = run_agent_system("Compare SQL and NoSQL databases")
# Boss routes to: Research Agent
```

### Writing Task

```python
response = run_agent_system("Write an explanation of machine learning")
# Boss routes to: Research Agent → Writing Agent
```

### Code Generation

```python
response = run_agent_system("Create a FastAPI endpoint for user authentication")
# Boss routes to: Code Agent
```

### Complex Multi-Agent Task

```python
response = run_agent_system("Compare Python web frameworks and show example code for FastAPI")
# Boss routes to: Research Agent → Code Agent → Aggregator
```

## 🎨 Markdown & Code Rendering

The web UI supports full markdown rendering with syntax highlighting:

- **Headings**: H1, H2, H3 with custom styling
- **Text formatting**: Bold, italic, strikethrough
- **Lists**: Ordered and unordered
- **Code blocks**: Syntax highlighting for 50+ languages
- **Inline code**: `like this`
- **Tables**: Full table support
- **Blockquotes**: Styled quotes
- **Links**: Auto-opening in new tabs

Example AI response with code:

````markdown
## FastAPI Example

```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```
````

All rendered beautifully in the chat UI! ✨
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
``Required
OPENAI_API_KEY=your-api-key-here

# Optional: Model selection
BOSS_MODEL=gpt-4o-mini
RESEARCH_MODEL=gpt-4o-mini
WRITING_MODEL=gpt-4o-mini
CODE_MODEL=gpt-4o-mini

# Optional: Temperature settings
RESEARCH_TEMPERATURE=0.3
WRITING_TEMPERATURE=0.7
CODE_TEMPERATURE=0.2

# Optional: System settings
MAX_RETRIES=3
TIMEOUT=120
```

## 📡 API Reference

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check & API key status |
| `/api/chat` | POST | Send message to AI agents |
| `/api/agents` | GET | List available agents |
| `/docs` | GET | Interactive API documentation |

### Example Request

```bash
POST /api/chat
Content-Type: application/json

{
  "message": "What is Docker?",
  "verbose": false
}
```

### Example Response

```json
{
  "response": "Docker is a platform for developing...",
  "intent": null,
  "selected_agents": null
}
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
### Web Interface
1. Start backend and frontend
2. Open http://localhost:3000
3. Try example queries from the welcome screen

### API Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is Python?"}'
```

### CLI Testing
```bash
python -m app.main

# Test different agent combinations
> Compare frameworks        # Research
> Write a tutorial         # Research + Writing
> Build an API            # Code
> Explain and show code   # Multiple agents
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
Deployment

### Backend (FastAPI)

```bash
# Using Uvicorn
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4

# Using Gunicorn
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend (React)

```bash
cd frontend
npm run build
# Deploy the 'dist' folder to your hosting service
# (Vercel, Netlify, AWS S3, etc.)
```

### Production Considerations

- **Error Handling**: Retry logic and fallbacks
- **Monitoring**: LangSmith or OpenTelemetry integration
- **Rate Limiting**: API call management
- **Caching**: Redis for repeated queries
- **Authentication**: Secure API endpoints
- **Cost Tracking**: Monitor LLM usage
- **CORS**: Configure allowed origins in production
- **Environment Variables**: Use secure secret managemente agent result
    "final_output": str          # Aggregated response
}
```

## 🚧 Production Considerations

For production deployment, consider adding:

- **Error Handling**: Retry logic and fallbacks
- **Monitoring**: LangSmith or OpenTelemetry integration
- **Rate Limiting**: API call management
- **Caching**: Redis for repeated queries
- **API Layer**: FastAPI wrap
- Streaming responses in web UI
- User authentication
- Chat history persistence

## 📚 Documentation

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup instructions
- [CHAT_SETUP.md](CHAT_SETUP.md) - Web UI setup guide
- [MARKDOWN_SUPPORT.md](MARKDOWN_SUPPORT.md) - Markdown  - LLM framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - Workflow orchestration
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - Frontend UI library
- [Vite](https://vitejs.dev/) - Fast build tool
- [OpenAI GPT-4](https://openai.com/) - Language models

## ⭐ Star this Repository

If you find this project helpful, please give it a star! It helps others discover the project.

---

**Philosophy**: Agents should behave like microservices, not like humans chatting. Determinism, clarity, and control beat autonomy in real systems.

**Made with ❤️ using LangGraph**
- **Port 8000 in use**: Change port in `server.py`
- **API key error**: Check `.env` file has valid `OPENAI_API_KEY`
- **Import errors**: Ensure virtual environment is activated

### Frontend Issues
- **Cannot connect to backend**: Verify backend is running on port 8000
- **CORS errors**: Check CORS configuration in `server.py`
- **npm install fails**: Try `npm install --legacy-peer-deps`

### Model Issues
- **Model not found**: Update to `gpt-4o-mini` or check API key access
- **Rate limit**: Wait or upgrade OpenAI plan
- **Slow responses**: Use faster models like `gpt-3.5-turbo`per for HTTP access
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
