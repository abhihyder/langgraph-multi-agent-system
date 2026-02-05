# 🚀 Setup Guide - Agentic AI System

## Web UI Setup

### Backend Server

```bash
# Install backend dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# Start the FastAPI server
python server.py
```

Backend will be available at: http://localhost:8000  
API Documentation: http://localhost:8000/docs

### Frontend Development Server

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:3000

### Usage

1. Start the backend server (Python)
2. Start the frontend development server (React)
3. Open http://localhost:3000 in your browser
4. Start chatting with the AI!

### API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `POST /api/query` - Process AI queries (requires auth)
- `GET /api/conversations` - List conversations
- `POST /auth/login` - Google OAuth login
- `GET /docs` - Interactive API documentation

---

## Prerequisites

Before you begin, ensure you have:
- Python 3.10 or higher
- pip (Python package manager)
- OpenAI API key (get one at https://platform.openai.com/api-keys)

## Step-by-Step Setup

### 1. Navigate to Project Directory

```bash
cd /home/abhi/Projects/Portonics/AI-Based/multi-agent
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- langchain (LLM framework)
- langgraph (Workflow orchestration)
- langchain-openai (OpenAI integration)
- pydantic (Data validation)
- python-dotenv (Environment management)
- fastapi & uvicorn (Optional API layer)

### 4. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file
nano .env  # or use your preferred editor
```

Add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 5. Verify Installation

```bash
python -c "import langchain; import langgraph; print('✅ All dependencies installed!')"
```

## 🎯 Running the System

### Option 1: Interactive CLI Mode (Recommended)

```bash
python -m app.main
```

This starts an interactive session where you can ask questions:

```
🤔 Your question: What is machine learning?
🤖 Processing your request...

[Response appears here]
```

### Option 2: Quick Test Script

```bash
python run_test.py
```

This runs predefined test cases to verify the system works.

### Option 3: Use as Python Module

```python
from app import run_agent_system

# Simple usage
response = run_agent_system("Explain quantum computing")
print(response)

# With verbose output
response = run_agent_system("Compare frameworks", verbose=True)
```

## 📝 Example Usage

### Research Query
```
Your question: What are the benefits of microservices?
```
→ Routes to **Research Agent**

### Writing Task
```
Your question: Write a tutorial on Docker basics
```
→ Routes to **Research Agent** + **Writing Agent**

### Code Generation
```
Your question: Create a FastAPI endpoint for user login
```
→ Routes to **Code Agent**

### Complex Multi-Agent
```
Your question: Compare React and Vue, then show example code
```
→ Routes to **Research Agent** + **Code Agent**

## 🔧 Advanced Configuration

### Using Different Models

Edit `.env` to customize models:

```bash
# Use GPT-3.5 for faster/cheaper responses
ORCHESTRATOR_MODEL=gpt-3.5-turbo
RESEARCH_MODEL=gpt-3.5-turbo
WRITING_MODEL=gpt-4
CODE_MODEL=gpt-4

# Adjust creativity levels
WRITING_TEMPERATURE=0.8  # More creative
CODE_TEMPERATURE=0.1     # More deterministic
```

### Using Claude (Anthropic)

```bash
# In .env
ANTHROPIC_API_KEY=your-anthropic-key

# Modify app/router.py, app/agents/*.py to use:
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-3-sonnet-20240229")
```

## 🐛 Troubleshooting

### Issue: "Module not found"

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "API key not found"

**Solution:**
```bash
# Verify .env file exists
ls -la .env

# Check it contains your key
cat .env | grep OPENAI_API_KEY

# Ensure it's loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

### Issue: "Rate limit exceeded"

**Solution:**
- Wait a moment and try again
- Check your OpenAI account quota
- Reduce request frequency
- Consider upgrading OpenAI plan

### Issue: "Connection timeout"

**Solution:**
```bash
# Increase timeout in config/settings.py
TIMEOUT=300  # 5 minutes
```

## 📊 Project Structure Overview

```
multi-agent/
├── app/                    # Main application code
│   ├── main.py            # Entry point
│   ├── graph.py           # LangGraph workflow
│   ├── state.py           # Shared state
│   ├── router.py          # Orchestrator agent
│   ├── aggregator.py      # Output synthesis
│   └── agents/            # Specialized agents
│       ├── research.py
│       ├── writing.py
│       └── code.py
│
├── prompts/               # Agent prompts
├── config/                # Configuration
├── requirements.txt       # Dependencies
├── .env                   # Your API keys (create this)
└── README.md             # Documentation
```

## ✅ Verification Checklist

Before running, ensure:
- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip list` shows langchain, langgraph)
- [ ] .env file created with valid API key
- [ ] API key has sufficient quota
- [ ] Internet connection active

## 🎓 Next Steps

1. **Test the system**: Run `python run_test.py`
2. **Try interactive mode**: Run `python -m app.main`
3. **Explore verbose mode**: Add `--verbose` flag
4. **Read the code**: Start with `app/main.py` and `app/graph.py`
5. **Customize prompts**: Edit files in `prompts/` directory
6. **Add agents**: Create new agents in `app/agents/`

## 🤝 Getting Help

- Check [README.md](README.md) for detailed documentation
- Review [DEVELOPMENT_PROGRESS.md](DEVELOPMENT_PROGRESS.md) for architecture details
- Look at code comments for implementation details

## 📚 Additional Resources

- LangChain Docs: https://python.langchain.com/docs/
- LangGraph Docs: https://langchain-ai.github.io/langgraph/
- OpenAI API: https://platform.openai.com/docs

---

**Ready to go!** 🚀 Run `python -m app.main` to start!
