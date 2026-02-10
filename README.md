# Multi-Agent AI System with LangGraph

A production-ready agentic AI system using **LangGraph** with clean layered architecture, where an **Orchestrator (Router) Agent** delegates tasks to specialized agents.

**🎨 Now with a beautiful web UI!** Chat interface built with FastAPI + React.

## 🏗️ Architecture

### Agent Flow
```
User Input (Web UI / CLI)
   ↓
Orchestrator Agent (Router)
   ↓ (conditional routing)
┌───────────────┬───────────────┬───────────────┐
│ ResearchAgent │ WritingAgent  │ CodeAgent     │
└───────────────┴───────────────┴───────────────┘
   ↓ (fan-in)
Aggregator Agent
   ↓
Final Response (Web UI / CLI)
```

### API Request Flow (Production)
```
server.py (FastAPI with OAuth + DB)
    ↓
app/api/routes.py (/api/query endpoint)
    ↓
app/services/chat_service.py
    ↓
app/orchestrator.py → agents → aggregator
```

See [API_ARCHITECTURE.md](API_ARCHITECTURE.md) for detailed documentation.

### Key Principles

- **Orchestrator Agent never answers directly** - Only routes to specialists
- **Specialized agents don't communicate** - Clean separation of concerns
- **Orchestrator controls flow** - Orchestrates everything
- **State is explicit** - Shared state passed between nodes

## 🎯 Features

- **🌐 Web Interface**: Beautiful chat UI with markdown rendering and syntax highlighting
- **💻 CLI Interface**: Interactive command-line interface
- **📊 LangSmith Tracing**: Complete observability and monitoring of all agent operations
- **🤖 Three Specialized Agents**:
  - **Research Agent**: Provides factual information, comparisons, and analysis
  - **Writing Agent**: Creates well-structured, human-friendly content
  - **Code Agent**: Generates production-quality code
- **🎨 Markdown Support**: Full markdown rendering with syntax-highlighted code blocks
- **🔀 Smart Routing**: Orchestrator agent determines which agents to invoke
- **🔄 Intelligent Aggregation**: Synthesizes multiple agent outputs
- **⚡ REST API**: FastAPI backend for easy integration
- **🔍 Performance Monitoring**: Track latency, costs, and success rates

## 📋 Prerequisites

- Python 3.10+
- Node.js 16+ (for web UI)
- **OpenAI API key** (Required - Get one at https://platform.openai.com/api-keys)

## 🎯 Quick Reference Commands

### Running the System
```bash
# Start production server
python server.py

# Start with auto-reload (development)
uvicorn server:app --reload --port 8000

# Run tests
pytest                    # All tests
pytest -m api            # API tests only
pytest -m unit           # Unit tests only
make test                # Using Makefile
make test-coverage       # With coverage report
```

### Agent Routing Examples

| User Query | Selected Agents | Reason |
|------------|----------------|--------|
| "What is Docker?" | research | Factual question |
| "Explain machine learning" | research + writing | Needs explanation |
| "Build a REST API" | code | Implementation needed |
| "Compare React vs Vue, show code" | research + code | Analysis + implementation |
| "Write tutorial on Python" | research + writing | Educational content |

## 🚀 Quick Start

### Option 1: Web Interface (Recommended)

#### Step 1: Setup Backend

```bash
# Clone/navigate to project
cd langgraph-multi-agent-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (REQUIRED)
# Get your key from: https://platform.openai.com/api-keys

# Optional: Add LangSmith for tracing (Recommended for production)
# Get your key from: https://smith.langchain.com/
# Add to .env:
#   LANGCHAIN_TRACING_V2=true
#   LANGCHAIN_API_KEY=your_langsmith_key_here
#   LANGCHAIN_PROJECT=multi-agent-ai-system

# Optional: Configure memory driver (default: automem)
# Options: automem (external service) or pgvector (PostgreSQL)
#   MEMORY_DRIVER=pgvector
# If using pgvector, ensure PostgreSQL is configured:
#   DB_HOST=localhost
#   DB_PORT=5432
#   DB_DATABASE=multiagent_ai
#   DB_USERNAME=postgres
#   DB_PASSWORD=your_password
```

#### Step 2: Run Database Migrations (If Using PGVector)

```bash
# Run migrations to create tables (users, conversations, memories, etc.)
python migrate.py upgrade

# Or create all tables from scratch
python migrate.py fresh
# ⚠️  Warning: 'fresh' drops all existing tables and data!
```

#### Step 3: Start Production API Server

```bash
# Start production server (with OAuth, Database, Rate Limiting)
python server.py

# Or use the helper script
./start.sh
```

Backend will be available at: **http://localhost:8000**  
API Documentation: **http://localhost:8000/docs**

**Production API Endpoints:**
- `POST /api/query` - Process queries through agent system (requires auth)
- `GET /api/conversations` - Get conversation history (requires auth)
- `POST /api/feedback` - Submit feedback (requires auth)
- `GET /api/user/profile` - Get user profile (requires auth)
- `GET /auth/google/login` - OAuth login
- `GET /health` - Health check

**Note:** Most endpoints require Google OAuth authentication. See server documentation for details.

#### Step 4: Setup Frontend

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

#### Step 5: Start Chatting! 🎉

Open your browser and go to **http://localhost:3000**

Try asking:
- "What is Docker?"
- "Write a tutorial on Python basics"
- "Create a REST API in FastAPI"
- "Compare React and Vue, then show example code"

### Option 2: CLI Interface (No Auth Required)

```bash
# Activate virtual environment
source venv/bin/activate

# Run interactive CLI (direct agent access, no authentication)
python -m app.main

# Or use the helper script
./start.sh
# Then select option 2 for CLI mode

# Or use in Python code
python
>>> from app import run_agent_system
>>> response = run_agent_system("What is LangGraph?")
>>> print(response)
```

## 📁 Project Structure

```
multi-agent/
├── server.py                # Production FastAPI server (OAuth, DB)
├── start.sh                 # Helper startup script
│
├── app/                     # Core application
│   ├── main.py              # CLI entry point
│   ├── graph.py             # LangGraph workflow
│   ├── state.py             # Shared state schema
│   ├── orchestrator.py      # Router agent logic
│   ├── aggregator.py        # Response synthesis
│   │
│   ├── agents/              # Specialized AI agents
│   │   ├── research.py
│   │   ├── writing.py
│   │   └── code.py
│   │
│   ├── api/                 # API layer
│   │   ├── routes.py        # API endpoints (/api/query, etc.)
│   │   └── models.py        # Request/Response models
│   │
│   ├── services/            # Business logic
│   │   └── chat_service.py  # Calls orchestrator
│   │
│   ├── controllers/         # Request handlers
│   │   └── chat_controller.py
│   │
│   ├── requests/            # Request validation
│   │   └── chat_request.py
│   │
│   ├── responses/           # Response formatting
│   │   └── chat_response.py
│   │
│   ├── middlewares/         # CORS, errors
│   │   ├── cors_middleware.py
│   │   └── error_middleware.py
│   │
│   └── auth/                # OAuth authentication
│       ├── routes.py
│       ├── dependencies.py
│       └── security.py
│
├── database/                # Database models
│   ├── __init__.py
│   └── models.py
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
│   ├── orchestrator.md
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
# Orchestrator routes to: Research Agent
```

### Writing Task

```python
response = run_agent_system("Write an explanation of machine learning")
# Orchestrator routes to: Research Agent → Writing Agent
```

### Code Generation

```python
response = run_agent_system("Create a FastAPI endpoint for user authentication")
# Orchestrator routes to: Code Agent
```

### Complex Multi-Agent Task

```python
response = run_agent_system("Compare Python web frameworks and show example code for FastAPI")
# Orchestrator routes to: Research Agent → Code Agent → Aggregator
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
# Orchestrator routes to: Research Agent
```

### Example 2: Writing Task

```python
response = run_agent_system("Write an explanation of machine learning")
# Orchestrator routes to: Research Agent → Writing Agent
```

### Example 3: Code Generation

```python
response = run_agent_system("Create a FastAPI endpoint for user authentication")
# Orchestrator routes to: Code Agent
```

### Complex Multi-Agent Task

```python
response = run_agent_system("Compare Python web frameworks and show example code for FastAPI")
# Orchestrator routes to: Research Agent → Code Agent → Aggregator
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

## 🔧 Configuration

Edit `config/settings.py` or set environment variables in `.env`:

```bash
# Required - You MUST set this
OPENAI_API_KEY=your-api-key-here

# Optional: Model selection
ORCHESTRATOR_MODEL=gpt-4o-mini
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

# Memory Driver Configuration (Laravel-style)
MEMORY_DRIVER=automem  # Options: automem, pgvector

# AutoMem Configuration (if using automem driver)
AUTOMEM_URL=http://localhost:8001
AUTOMEM_API_TOKEN=your-token  # Optional

# PostgreSQL Configuration (if using pgvector driver)
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=multiagent_ai
DB_USERNAME=postgres
DB_PASSWORD=your_password
```

## 📡 API Reference

### Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/` | GET | No | API information |
| `/health` | GET | No | Health check & database status |
| `/api/query` | POST | Yes | Process query through agents |
| `/api/conversations` | GET | Yes | Get conversation history |
| `/api/feedback` | POST | Yes | Submit feedback |
| `/api/persona` | GET/PUT | Yes | User persona management |
| `/api/user/profile` | GET | Yes | Get user profile |
| `/auth/google/login` | GET | No | OAuth login |
| `/auth/logout` | POST | Yes | Logout |
| `/docs` | GET | No | Interactive API documentation |

### Example Request (with Authentication)

```bash
# First, get JWT token via OAuth login
# Visit: http://localhost:8000/auth/google/login

# Then use token in requests
POST /api/query
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "query": "What is Docker?",
  "context": {}
}
```

### Example Response

```json
{
  "conversation_id": 123,
  "query": "What is Docker?",
  "response": "Docker is a platform for developing...",
  "agents_used": ["research", "writing"],
  "agent_responses": [],
  "metadata": {},
  "created_at": "2024-01-29T12:00:00"
}
python -m app.main
> Compare React and Vue --verbose
```

## 🔧 Configuration

Edit `config/settings.py` or set environment variables in `.env`:

```bash
# Models
ORCHESTRATOR_MODEL=gpt-4
RESEARCH_MODEL=gpt-4
WRITING_MODEL=gpt-4
### Web Interface
1. Start backend and frontend
2. Open http://localhost:3000
3. Try example queries from the welcome screen

### API Testing
```bash
# Test health endpoint (no auth required)
curl http://localhost:8000/health

# For authenticated endpoints, first login via browser:
# http://localhost:8000/auth/google/login
# Get JWT token from callback

# Then test query endpoint (requires auth)
curl -X POST http://localhost:8000/api/query \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?", "context": {}}'
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

4. Update routing logic in orchestrator prompt

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
- **Monitoring**: LangSmith tracing for complete observability (see below)
- **Rate Limiting**: API call management
- **Caching**: Redis for repeated queries
- **Authentication**: Secure API endpoints
- **Cost Tracking**: Monitor LLM usage via LangSmith dashboard
- **CORS**: Configure allowed origins in production
- **Environment Variables**: Use secure secret management
- **Database**: PostgreSQL with connection pooling
- **Streaming**: Streaming responses in web UI
- **Persistence**: Chat history and user data

## 📊 LangSmith Tracing & Monitoring

This application includes comprehensive **LangSmith** integration for complete observability of your agentic AI system.

### What Gets Traced?

- ✅ **All LLM calls** with prompts, responses, and token usage
- ✅ **Agent routing decisions** by the orchestrator
- ✅ **Individual agent executions** (research, writing, code, etc.)
- ✅ **Knowledge and memory retrieval** operations
- ✅ **Final response aggregation**
- ✅ **Complete execution timeline** with latency metrics
- ✅ **Custom metadata** (user_id, conversation_id, intent, etc.)

### Quick Setup

1. **Sign up for LangSmith**: Visit [https://smith.langchain.com/](https://smith.langchain.com/)
2. **Get your API key**: Create an API key in the LangSmith dashboard
3. **Configure environment variables** in your `.env` file:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=multi-agent-ai-system
```

4. **Start your application**: Tracing is automatically enabled!

### View Traces

- Open your LangSmith dashboard at [https://smith.langchain.com/](https://smith.langchain.com/)
- Navigate to your project ("multi-agent-ai-system" by default)
- See real-time traces of all agent operations
- Filter by tags: `orchestrator`, `agent`, `research`, `writing`, `code`, `retrieval`, etc.

### Benefits

- 🔍 **Debug complex agent flows** - See exactly which agents ran and why
- ⚡ **Identify bottlenecks** - Track latency at each step
- 💰 **Monitor costs** - See token usage and costs per request
- 🐛 **Trace errors** - Quickly find the source of failures
- 📈 **Analyze patterns** - Understand how users interact with your system
- ✅ **Evaluate outputs** - Add feedback and ratings to traces

### Detailed Documentation

See [docs/LANGSMITH_SETUP.md](docs/LANGSMITH_SETUP.md) for:
- Complete setup instructions
- Advanced configuration options
- How to add custom metadata and tags
- Using the LangSmith dashboard
- Best practices for production monitoring
- Troubleshooting guide

## 🐛 Troubleshooting

### Common Issues

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
- **Slow responses**: Use faster models like `gpt-3.5-turbo`

## 📚 Documentation

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup instructions
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture and design
- [TESTING.md](TESTING.md) - Testing guide and best practices
- [INSTRUCTION.md](INSTRUCTION.md) - Implementation guide
- [LANGSMITH_SETUP.md](docs/LANGSMITH_SETUP.md) - **LangSmith tracing and monitoring guide**
- [FUTURE_IMPROVEMENTS_PLAN.md](FUTURE_IMPROVEMENTS_PLAN.md) - Roadmap and planned features

## 📝 Development Notes

- Each agent writes ONLY to its designated state field
- Orchestrator agent never generates content
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
 - LLM framework
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
- [LangGraph](https://github.com/langchain-ai/langgraph)
- OpenAI GPT-4

---

**Philosophy**: Agents should behave like microservices, not like humans chatting. Determinism, clarity, and control beat autonomy in real systems.
