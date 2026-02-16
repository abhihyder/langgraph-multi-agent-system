# Multi-Agent AI System Architecture

**Version**: 3.0.0  
**Last Updated**: February 16, 2026  
**Architecture Pattern**: LangGraph-Based Multi-Agent System

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Agent Architecture](#agent-architecture)
4. [Directory Structure](#directory-structure)
5. [Data Flow](#data-flow)
6. [Key Components](#key-components)
7. [Design Patterns](#design-patterns)
8. [Integration Architecture](#integration-architecture)
9. [Memory & Knowledge System](#memory--knowledge-system)
10. [API Architecture](#api-architecture)

---

## Overview

This is a production-ready multi-agent AI system built with **LangGraph**, featuring:

- **Graph-based agent architecture** with StateGraph pattern
- **Specialized agents** for different capabilities (code, research, writing, email, etc.)
- **Orchestrator-driven routing** for intelligent task delegation
- **Memory system** with pluggable drivers (AutoMem, PGVector)
- **Clean layered architecture** separating concerns
- **FastAPI backend** with OAuth2 authentication
- **React frontend** with beautiful UI

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│  ┌──────────────────────┐    ┌──────────────────────────────┐  │
│  │   Web UI (React)     │    │   CLI Interface              │  │
│  └──────────┬───────────┘    └──────────┬───────────────────┘  │
└─────────────┼────────────────────────────┼──────────────────────┘
              │                            │
              └────────────┬───────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                    FastAPI Server                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Gateway & Middleware                                │   │
│  │  - Authentication (OAuth2/JWT)                           │   │
│  │  - Rate Limiting                                          │   │
│  │  - CORS                                                   │   │
│  │  - Request Validation                                     │   │
│  └──────────────────┬───────────────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                 Service Layer                                    │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ ChatService │  │ AuthService  │  │ ConversationService │   │
│  └─────┬───────┘  └──────────────┘  └─────────────────────┘   │
└────────┼────────────────────────────────────────────────────────┘
         │
┌────────▼─────────────────────────────────────────────────────────┐
│              Agentic AI System (LangGraph)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 Orchestrator Graph                        │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  Intent Analysis → Agent Selection → Routing      │  │   │
│  │  └───────────────────┬────────────────────────────────┘  │   │
│  └────────────────────────┼───────────────────────────────────┘ │
│                           │                                      │
│  ┌────────────────────────▼──────────────────────────────────┐  │
│  │              Specialized Agent Graphs                     │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │Memory Graph  │  │Knowledge Graph│  │General Graph │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │Research Graph│  │Writing Graph │  │Code Graph    │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  │  ┌──────────────┐                                         │  │
│  │  │Email Graph   │                                         │  │
│  │  └──────────────┘                                         │  │
│  └────────────────────┬──────────────────────────────────────┘  │
│                       │                                          │
│  ┌────────────────────▼──────────────────────────────────────┐  │
│  │                Aggregator Node                            │  │
│  │  Synthesizes outputs from multiple agents                 │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│              External Services & Storage                         │
│  ┌────────────┐  ┌───────────┐  ┌─────────────┐  ┌──────────┐ │
│  │  OpenAI    │  │  AutoMem  │  │  Gmail API  │  │  SQLite  │ │
│  │    API     │  │  Memory   │  │             │  │    DB    │ │
│  └────────────┘  └───────────┘  └─────────────┘  └──────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Agent Architecture

### LangGraph StateGraph Pattern

Each agent is implemented as a **StateGraph** with nodes representing processing steps:

```
┌────────────────────────────────────────────────────────────────┐
│                    Agent Graph Structure                        │
│                                                                 │
│  START                                                          │
│    ↓                                                            │
│  ┌──────────────────┐                                          │
│  │  Validate Input  │  (Processing Node)                       │
│  └────────┬─────────┘                                          │
│           ↓                                                     │
│  ┌──────────────────┐                                          │
│  │   LLM Node       │  (AI Processing)                         │
│  └────────┬─────────┘                                          │
│           ↓                                                     │
│  ┌──────────────────┐                                          │
│  │  Router Node     │  (Conditional Logic)                     │
│  └────────┬─────────┘                                          │
│           ↓                                                     │
│  ┌──────────────────┐      ┌──────────────────┐              │
│  │  Tool Node       │  OR  │  Format Response │              │
│  └────────┬─────────┘      └────────┬─────────┘              │
│           ↓                          ↓                         │
│  ┌──────────────────┐      ┌──────────────────┐              │
│  │ Format Response  │      │    END           │              │
│  └────────┬─────────┘      └──────────────────┘              │
│           ↓                                                     │
│         END                                                     │
└────────────────────────────────────────────────────────────────┘
```

### Agent Types

1. **Orchestrator Graph** - Routes requests to appropriate agents
2. **Memory Graph** - Retrieves conversation history and context
3. **Knowledge Graph** - Fetches company docs and policies
4. **General Graph** - Handles general queries
5. **Research Graph** - Provides factual information and analysis
6. **Writing Graph** - Creates structured content
7. **Code Graph** - Generates production-quality code
8. **Email Graph** - Manages Gmail operations

---

## Directory Structure

```
multi-agent/
├── app/
│   ├── main.py                      # CLI entry point
│   ├── agentic/                     # Agentic AI system
│   │   ├── __init__.py              # Main orchestrator graph
│   │   ├── graphs/                  # Agent graph implementations
│   │   │   ├── base_graph.py        # BaseAgentGraph abstract class
│   │   │   ├── email_graph.py       # Email agent
│   │   │   ├── code_graph.py        # Code generation agent
│   │   │   ├── research_graph.py    # Research agent
│   │   │   ├── writing_graph.py     # Writing agent
│   │   │   ├── general_graph.py     # General query agent
│   │   │   ├── memory_graph.py      # Memory retrieval agent
│   │   │   └── knowledge_graph.py   # Knowledge retrieval agent
│   │   ├── nodes/                   # Reusable node implementations
│   │   │   ├── email_nodes.py       # Email-specific nodes
│   │   │   ├── code_nodes.py        # Code-specific nodes
│   │   │   ├── research_nodes.py    # Research-specific nodes
│   │   │   └── ...
│   │   ├── utils/                   # Node building blocks
│   │   │   ├── llm_node.py          # LLM node utilities
│   │   │   ├── tool_node.py         # Tool execution utilities
│   │   │   ├── processing_node.py   # Processing utilities
│   │   │   ├── router_node.py       # Routing logic
│   │   │   └── node_factories.py    # Factory functions
│   │   ├── states/                  # State definitions
│   │   │   ├── agent_state.py       # Main AgentState TypedDict
│   │   │   ├── base_state.py        # Base state class
│   │   │   └── email_state.py       # Email-specific state
│   │   └── prompts/                 # Agent prompts
│   │       ├── orchestrator.md      # Orchestrator prompts
│   │       ├── code.md              # Code agent prompts
│   │       ├── research.md          # Research agent prompts
│   │       ├── writing.md           # Writing agent prompts
│   │       ├── email.md             # Email agent prompts
│   │       └── general.md           # General agent prompts
│   ├── services/                    # Business logic layer
│   │   ├── chat_service.py          # Chat orchestration
│   │   ├── auth_service.py          # Authentication
│   │   ├── conversation_service.py  # Conversation management
│   │   ├── persona_service.py       # User persona
│   │   ├── feedback_service.py      # Feedback handling
│   │   └── voice/                   # Voice services
│   │       ├── stt_service.py       # Speech-to-text
│   │       └── tts_service.py       # Text-to-speech
│   ├── integrations/                # Third-party integrations
│   │   ├── base_integration.py      # Base integration class
│   │   └── email/                   # Email integrations
│   │       ├── gmail_service.py     # Gmail API service
│   │       └── email_composer.py    # AI email composition
│   ├── routes/                      # API endpoints
│   │   ├── api.py                   # Main API routes
│   │   ├── auth.py                  # Auth routes
│   │   ├── oauth.py                 # OAuth routes
│   │   ├── email.py                 # Email routes
│   │   └── voice.py                 # Voice routes
│   ├── controllers/                 # Request handlers
│   │   ├── auth_controller.py
│   │   ├── conversation_controller.py
│   │   ├── query_controller.py
│   │   ├── persona_controller.py
│   │   ├── feedback_controller.py
│   │   └── user_controller.py
│   ├── models/                      # Database models
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   └── feedback.py
│   ├── middlewares/                 # HTTP middlewares
│   │   ├── cors_middleware.py
│   │   └── error_middleware.py
│   ├── gateway/                     # API Gateway
│   │   ├── gateway.py               # Main gateway
│   │   ├── middleware.py            # Gateway middlewares
│   │   ├── rate_limiter.py          # Rate limiting
│   │   └── handlers/                # Request handlers
│   ├── core/                        # Core functionality
│   │   └── memory/                  # Memory system
│   │       ├── base.py              # Abstract driver interface
│   │       ├── manager.py           # Driver manager
│   │       ├── automem_driver.py    # AutoMem implementation
│   │       └── pgvector_driver.py   # PGVector implementation
│   ├── utils/                       # Utility functions
│   │   ├── helpers.py               # General helpers
│   │   ├── llm_factory.py           # LLM initialization
│   │   ├── tracing.py               # LangSmith tracing
│   │   └── email_utils.py           # Email utilities
│   ├── exceptions/                  # Custom exceptions
│   └── responses/                   # Response schemas
├── config/                          # Configuration
│   ├── settings.py                  # App settings
│   ├── llm_config.py               # LLM configuration
│   └── voice_config.py             # Voice settings
├── database/                        # Database
│   ├── connection.py               # DB connection
│   └── migrations/                 # Alembic migrations
├── docs/                            # Documentation
│   ├── MEMORY_DRIVER_SYSTEM.md     # Memory system docs
│   ├── MEMORY_DRIVER_IMPLEMENTATION.md
│   └── GLOBAL_KNOWLEDGE.md         # Global knowledge docs
├── tests/                           # Test suite
├── frontend/                        # React frontend
├── server.py                        # FastAPI server entry
└── README.md                        # Project readme
```

---

## Data Flow

### Request Flow

```
1. User Request
   ↓
2. FastAPI Server (server.py)
   ↓
3. API Gateway (auth, rate limit, validation)
   ↓
4. Route Handler (app/routes/)
   ↓
5. Controller (app/controllers/)
   ↓
6. Service Layer (app/services/)
   ↓
7. Orchestrator Graph (app/agentic/__init__.py)
   ↓
8. Agent Selection & Routing
   ↓
9. Specialized Agent Graphs (parallel execution)
   │
   ├── Memory Graph → AutoMem/PGVector
   ├── Knowledge Graph → Knowledge Base
   ├── Research/Writing/Code Graphs → OpenAI
   └── Email Graph → Gmail API
   ↓
10. Aggregator Node (synthesize results)
    ↓
11. Response Formatting
    ↓
12. Return to User
```

### State Management

```python
# AgentState - Main state passed through orchestrator
{
    "user_input": str,
    "conversation_id": Optional[str],
    "user_id": Optional[str],
    "intent": Optional[str],
    "knowledge_output": Optional[str],
    "memory_output": Optional[str],
    "general_output": Optional[str],
    "research_output": Optional[str],
    "writing_output": Optional[str],
    "code_output": Optional[str],
    "selected_agents": List[str],
    "executed_agents": List[str],
    "final_output": Optional[str]
}
```

---

## Key Components

### 1. BaseAgentGraph

Abstract base class for all agent graphs with:
- Decorator support (`@retry_on_failure`, `@log_node_execution`)
- Helper methods for LLM calls, tool execution
- Error handling and tracing
- State management utilities

### 2. Orchestrator Graph

Main coordination graph:
- **Intent Analysis**: Determines user intent
- **Memory Retrieval**: Fetches conversation history
- **Knowledge Retrieval**: Gets relevant docs
- **Agent Selection**: Routes to appropriate agents
- **Aggregation**: Synthesizes results

### 3. Memory Driver System

Pluggable memory backends:
- **AutoMem Driver**: Cloud-based memory service
- **PGVector Driver**: PostgreSQL with vector search
- **Interface**: Abstract `BaseMemoryDriver`

### 4. Integration System

Third-party service wrappers:
- **BaseIntegration**: Abstract base class
- **GmailService**: Gmail API integration
- **EmailComposer**: AI-powered email generation

---

## Design Patterns

### 1. Graph-Based Architecture (LangGraph)

- **StateGraph**: Each agent is a state machine
- **Nodes**: Processing steps (LLM, Tool, Processing, Router)
- **Edges**: Control flow between nodes
- **Conditional Edges**: Dynamic routing based on state

### 2. Abstract Base Classes

- `BaseAgentGraph`: Template for all agents
- `BaseMemoryDriver`: Memory system interface
- `BaseIntegration`: Third-party service interface

### 3. Dependency Injection

Services receive dependencies through constructors:
```python
class ChatService:
    def __init__(self, memory_driver, orchestrator_graph):
        self.memory = memory_driver
        self.orchestrator = orchestrator_graph
```

### 4. Factory Pattern

- `get_llm()`: Creates LLM instances
- `get_memory_driver()`: Creates memory driver instances
- Node factories for reusable components

### 5. Decorator Pattern

```python
@retry_on_failure(max_retries=3)
@log_node_execution
def my_node(state: AgentState) -> AgentState:
    # Node implementation
```

### 6. Strategy Pattern

Memory drivers implement common interface with different strategies

---

## Integration Architecture

### Gmail Integration

```
EmailGraph
   ↓
GmailService (wrapper)
   ↓
Gmail API (Google)
```

Features:
- OAuth2 authentication
- Send, read, search, reply
- Email composition with AI
- Attachment handling

### Memory Integration

```
ChatService
   ↓
MemoryDriverManager
   ↓
AutoMemDriver / PGVectorDriver
   ↓
AutoMem API / PostgreSQL
```

---

## Memory & Knowledge System

### Memory Types

1. **Short-term**: Recent conversation (last N messages)
2. **Long-term**: Historical context (vector search)
3. **Global Knowledge**: Company docs, policies

### Storage Strategy

- **User Memories**: Conversation-specific, per user
- **Global Knowledge**: Shared across all users, categorized
- **Vector Search**: Semantic similarity for retrieval

### Driver Selection

```bash
# Environment variable controls driver
MEMORY_DRIVER=automem  # or pgvector
```

---

## API Architecture

### Endpoints

```
POST   /api/query              # Submit query to AI
GET    /api/conversations      # List conversations
GET    /api/conversations/:id  # Get conversation
DELETE /api/conversations/:id  # Delete conversation
POST   /api/feedback           # Submit feedback
GET    /api/persona            # Get user persona
PUT    /api/persona            # Update persona
GET    /api/user/profile       # Get user profile
POST   /auth/google            # Google OAuth
POST   /auth/token             # Get JWT token
GET    /auth/gmail/login       # Gmail OAuth
GET    /auth/gmail/callback    # Gmail OAuth callback
POST   /email/send             # Send email
POST   /email/compose          # Compose email with AI
GET    /voice/transcribe       # Speech-to-text
POST   /voice/synthesize       # Text-to-speech
```

### Authentication

- **OAuth2**: Google authentication
- **JWT**: Token-based sessions
- **Scopes**: Gmail access for email features

---

## Performance & Monitoring

### LangSmith Tracing

All agent executions traced with:
- Input/output logging
- Timing metrics
- Error tracking
- Token usage

### Metrics Tracked

- Response latency
- Agent selection accuracy
- Memory retrieval performance
- API success rates
- Cost per request

---

## Testing Strategy

### Test Coverage

- **Unit Tests**: Individual components
- **Integration Tests**: API endpoints, agent graphs
- **Memory Tests**: Driver implementations
- **Gateway Tests**: Middleware, rate limiting

### Test Organization

```
tests/
├── core/memory/           # Memory system tests
├── test_api_endpoints.py  # API tests
├── test_handlers.py       # Handler tests
├── test_gateway.py        # Gateway tests
├── test_orchestrator.py   # Orchestrator tests
├── test_email_integration.py
└── test_chat_service.py
```

**Current Status**: 246 tests passing, 4 skipped

---

## Deployment Considerations

### Environment Variables

```bash
OPENAI_API_KEY=xxx
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
MEMORY_DRIVER=automem
AUTOMEM_API_KEY=xxx
DATABASE_URL=sqlite:///./test.db
LANGSMITH_API_KEY=xxx
```

### Production Setup

1. Set environment variables
2. Run database migrations: `python migrate.py`
3. Start server: `python server.py`
4. Build frontend: `cd frontend && npm run build`
5. Configure reverse proxy (nginx)

---

## Future Enhancements

See [FEATURES.md](FEATURES.md) for detailed roadmap.

---

**Last Updated**: February 16, 2026  
**Maintainer**: Development Team  
**Status**: Production Ready ✅
