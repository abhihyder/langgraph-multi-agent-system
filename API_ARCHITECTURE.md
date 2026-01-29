# API Architecture Documentation

## Overview

This project follows a clean **layered architecture** for API request handling:

```
routes → controllers → services → orchestrator.py (+ agents)
```

## Directory Structure

```
app/
├── routes/              # API endpoint definitions
│   ├── __init__.py
│   └── chat_routes.py   # Chat endpoints
│
├── controllers/         # Request/Response handling
│   ├── __init__.py
│   └── chat_controller.py  # Chat controller
│
├── services/            # Business logic layer
│   ├── __init__.py
│   └── chat_service.py  # Chat service (calls orchestrator)
│
├── requests/            # Request validation models (Pydantic)
│   ├── __init__.py
│   └── chat_request.py
│
├── responses/           # Response models (Pydantic)
│   ├── __init__.py
│   └── chat_response.py
│
├── middlewares/         # Cross-cutting concerns
│   ├── __init__.py
│   ├── cors_middleware.py
│   └── error_middleware.py
│
├── models/              # Data models (for future CRUD)
│   └── __init__.py
│
├── orchestrator.py      # Core: Routes to agents
├── aggregator.py        # Core: Aggregates agent outputs
├── graph.py             # Core: LangGraph workflow
├── state.py             # Core: State management
├── agents/              # Core: Specialized agents
│   ├── research.py
│   ├── writing.py
│   └── code.py
│
├── server.py            # FastAPI app setup
└── main.py              # Entry point (CLI + Server)
```

## Request Flow

### Chat Request Flow

```
HTTP POST /api/chat
    ↓
[routes/chat_routes.py]
    ↓ calls
[controllers/chat_controller.py]
    ↓ validates request, calls
[services/chat_service.py]
    ↓ calls
[orchestrator.py] (via graph.py)
    ↓ analyzes intent, routes to
[agents/research.py | writing.py | code.py]
    ↓ processes task, returns to
[aggregator.py]
    ↓ synthesizes output, returns to
[services/chat_service.py]
    ↓ formats result, returns to
[controllers/chat_controller.py]
    ↓ creates response model
HTTP Response (JSON)
```

### Future CRUD Request Flow

```
HTTP POST /api/resource
    ↓
[routes/resource_routes.py]
    ↓
[controllers/resource_controller.py]
    ↓
[services/resource_service.py]
    ↓
[models/resource.py]
    ↓
Database/Storage
```

## Layer Responsibilities

### 1. Routes Layer (`routes/`)

**Purpose**: Define API endpoints and routing

**Responsibilities**:
- Define HTTP methods and paths
- Dependency injection
- OpenAPI documentation
- Route parameters

**Example**:
```python
@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, controller: ChatController = Depends(get_controller)):
    return controller.process_chat(request)
```

### 2. Controllers Layer (`controllers/`)

**Purpose**: Handle HTTP request/response lifecycle

**Responsibilities**:
- Validate incoming requests (Pydantic)
- Call appropriate service methods
- Map service results to response models
- Handle HTTP-specific errors
- Return proper HTTP status codes

**Example**:
```python
class ChatController:
    def process_chat(self, request: ChatRequest) -> ChatResponse:
        result = self.chat_service.process_chat(request.message, request.context)
        return ChatResponse(
            response=result["response"],
            intent=result["intent"],
            agents_used=result["agents_used"]
        )
```

### 3. Services Layer (`services/`)

**Purpose**: Business logic and orchestration

**Responsibilities**:
- Implement core business logic
- Coordinate between components
- Call orchestrator/agents for AI tasks
- Transform data between layers
- Handle business-level exceptions

**Example**:
```python
class ChatService:
    def process_chat(self, user_input: str, context: dict) -> dict:
        # Prepare state for agent system
        initial_state = {...}
        
        # Execute through orchestrator -> agents
        result = agent_graph.invoke(initial_state)
        
        # Return formatted result
        return {...}
```

### 4. Models Layer (`models/`)

**Purpose**: Data models for CRUD operations (future use)

**Responsibilities**:
- Define database models
- Data validation
- Business logic related to data
- ORM mappings (if using SQLAlchemy, etc.)

### 5. Requests Layer (`requests/`)

**Purpose**: Request validation schemas

**Responsibilities**:
- Define Pydantic models for incoming requests
- Field validation
- Type checking
- Default values

**Example**:
```python
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    context: Optional[Dict[str, Any]] = None
```

### 6. Responses Layer (`responses/`)

**Purpose**: Response formatting schemas

**Responsibilities**:
- Define Pydantic models for responses
- Consistent response structure
- OpenAPI documentation
- Type safety

**Example**:
```python
class ChatResponse(BaseModel):
    response: str
    intent: Optional[str]
    agents_used: List[str]
    metadata: Optional[Dict[str, Any]]
    timestamp: str
```

### 7. Middlewares Layer (`middlewares/`)

**Purpose**: Cross-cutting concerns

**Responsibilities**:
- CORS configuration
- Error handling
- Authentication (future)
- Logging (future)
- Rate limiting (future)

## Core Agent System

### Orchestrator (`orchestrator.py`)

The orchestrator analyzes user intent and routes to appropriate agents. It NEVER answers questions directly.

### Agents (`agents/`)

Specialized agents that handle specific tasks:
- **Research Agent**: Web search, fact-finding, MCP tools
- **Writing Agent**: Content creation, articles
- **Code Agent**: Code generation, explanations

### Graph (`graph.py`)

LangGraph workflow that connects orchestrator → agents → aggregator.

### Aggregator (`aggregator.py`)

Synthesizes outputs from multiple agents into a coherent response.

## Usage

### Starting the API Server

```bash
# Using Python module
python -m app.main server

# Or directly
python app/server.py

# Or using uvicorn
uvicorn app.server:app --reload
```

### CLI Mode (Direct Agent Access)

```bash
python -m app.main
```

### API Endpoints

#### POST /api/chat
Process a chat message through the agent system.

**Request**:
```json
{
  "message": "Explain quantum computing",
  "context": {}
}
```

**Response**:
```json
{
  "response": "Quantum computing is...",
  "intent": "research",
  "agents_used": ["research", "writing"],
  "metadata": {},
  "timestamp": "2024-01-29T12:00:00"
}
```

#### GET /api/chat/agents
Get information about available agents.

**Response**:
```json
{
  "agents": [
    {
      "name": "research",
      "description": "Performs research using web search",
      "capabilities": ["web_search", "fact_finding"]
    }
  ],
  "orchestrator": {
    "name": "orchestrator",
    "description": "Routes requests to agents",
    "role": "router"
  }
}
```

#### GET /health
Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "service": "multi-agent-ai-system"
}
```

## Testing

### Test with curl

```bash
# Start server
python -m app.main server

# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain quantum computing"}'

# Get agent information
curl http://localhost:8000/api/chat/agents
```

### Test with Python

```python
import requests

# Chat request
response = requests.post(
    "http://localhost:8000/api/chat",
    json={"message": "Explain quantum computing"}
)
print(response.json())
```

## Design Principles

### 1. Separation of Concerns
Each layer has a single, well-defined responsibility.

### 2. Dependency Injection
Controllers are injected as dependencies in routes for testability.

### 3. Type Safety
Pydantic models ensure type safety throughout the API.

### 4. Single Responsibility
Each module does one thing well.

### 5. Open/Closed Principle
Easy to extend with new routes/controllers without modifying existing code.

## Future Enhancements

### Adding New Endpoints

1. **Create request model** in `requests/`
2. **Create response model** in `responses/`
3. **Create service method** in appropriate service
4. **Create controller method** in appropriate controller
5. **Add route** in appropriate route file

### Adding CRUD Operations

1. **Define model** in `models/`
2. **Create service** with CRUD methods
3. **Create controller** to handle HTTP
4. **Add routes** for GET/POST/PUT/DELETE
5. **Follow flow**: `routes → controllers → services → models`

### Adding Authentication

1. **Create auth middleware** in `middlewares/`
2. **Add authentication service** in `services/`
3. **Use FastAPI dependencies** for protected routes

## Environment Variables

Required in `.env`:
```bash
OPENAI_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here

# Optional
MCP_SERVER_URL=http://localhost:8080
```

## Benefits of This Architecture

✅ **Clear separation** between API and core logic
✅ **Easy to test** each layer independently
✅ **Type-safe** with Pydantic models
✅ **Scalable** - easy to add new features
✅ **Maintainable** - changes isolated to specific layers
✅ **Standard pattern** - follows REST API best practices
✅ **Ready for CRUD** - structure supports future database operations

## Summary

- **Routes**: API endpoints
- **Controllers**: HTTP handling + validation
- **Services**: Business logic + orchestrator calls
- **Requests/Responses**: Type-safe models
- **Middlewares**: Cross-cutting concerns
- **Models**: Data layer (for future CRUD)
- **Core agents**: Remain as they are, called by services
