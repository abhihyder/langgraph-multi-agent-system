# API Architecture Diagram

## Complete Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        HTTP CLIENT                              │
│                  (Browser / curl / Postman)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ POST /api/chat
                             │ {"message": "Question"}
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      ROUTES LAYER                               │
│                  (routes/chat_routes.py)                        │
│                                                                 │
│  @router.post("/", response_model=ChatResponse)                │
│  async def chat(request: ChatRequest):                         │
│      return controller.process_chat(request)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ ChatRequest
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   CONTROLLERS LAYER                             │
│              (controllers/chat_controller.py)                   │
│                                                                 │
│  class ChatController:                                         │
│      def process_chat(request):                                │
│          ✓ Validate request (Pydantic)                         │
│          ✓ Call service                                        │
│          ✓ Format response                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ user_input, context
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICES LAYER                               │
│               (services/chat_service.py)                        │
│                                                                 │
│  class ChatService:                                            │
│      def process_chat(user_input, context):                    │
│          ✓ Business logic                                      │
│          ✓ Prepare agent state                                 │
│          ✓ Call orchestrator via graph                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ AgentState
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                                │
│                    (graph.py)                                   │
│                                                                 │
│  LangGraph Workflow:                                           │
│      agent_graph.invoke(initial_state)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR                                  │
│                (orchestrator.py)                                │
│                                                                 │
│  orchestrator_router(state):                                   │
│      ✓ Analyze user intent                                     │
│      ✓ Decide which agent(s) to use                            │
│      ✓ Route to appropriate agent                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                 ┌───────────┴───────────┐
                 │                       │
                 ↓                       ↓
┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
│   RESEARCH AGENT     │   │   WRITING AGENT      │   │   CODE AGENT         │
│ (agents/research.py) │   │ (agents/writing.py)  │   │ (agents/code.py)     │
│                      │   │                      │   │                      │
│ • Web search         │   │ • Content creation   │   │ • Code generation    │
│ • Tavily API         │   │ • Article writing    │   │ • Code explanation   │
│ • MCP tools          │   │ • Summarization      │   │ • Best practices     │
└──────────┬───────────┘   └──────────┬───────────┘   └──────────┬───────────┘
           │                          │                          │
           └──────────────────────────┼──────────────────────────┘
                                      ↓
                        ┌──────────────────────────┐
                        │      AGGREGATOR          │
                        │   (aggregator.py)        │
                        │                          │
                        │  • Synthesize outputs    │
                        │  • Format final response │
                        └─────────┬────────────────┘
                                  │
                                  ↓
                        ┌──────────────────────────┐
                        │    Final State           │
                        │  {                       │
                        │    "final_output": "..." │
                        │    "intent": "..."       │
                        │    "selected_agents": [] │
                        │  }                       │
                        └─────────┬────────────────┘
                                  │
                                  ↓
                        Back through Services
                                  ↓
                        Back through Controllers
                                  ↓
                        Back through Routes
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      HTTP RESPONSE                              │
│                                                                 │
│  {                                                              │
│    "response": "Here is the answer...",                        │
│    "intent": "research",                                       │
│    "agents_used": ["research", "writing"],                     │
│    "metadata": {...},                                          │
│    "timestamp": "2024-01-29T12:00:00"                          │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### 🌐 Routes Layer
- **File**: `routes/chat_routes.py`
- **Purpose**: HTTP endpoint definitions
- **Handles**: URL routing, dependency injection

### 🎮 Controllers Layer
- **File**: `controllers/chat_controller.py`
- **Purpose**: Request/Response lifecycle
- **Handles**: Validation, error handling, response formatting

### 💼 Services Layer
- **File**: `services/chat_service.py`
- **Purpose**: Business logic
- **Handles**: State preparation, orchestrator coordination, data transformation

### 🧭 Orchestrator
- **File**: `orchestrator.py`
- **Purpose**: Intelligent routing
- **Handles**: Intent analysis, agent selection

### 🤖 Agents
- **Files**: `agents/research.py`, `agents/writing.py`, `agents/code.py`
- **Purpose**: Specialized task execution
- **Handles**: Actual AI work (research, writing, coding)

### 📊 Aggregator
- **File**: `aggregator.py`
- **Purpose**: Output synthesis
- **Handles**: Combining agent outputs into final response

## Data Models Flow

```
ChatRequest (Pydantic)
    ↓
Dict (Python)
    ↓
AgentState (TypedDict)
    ↓
AgentState (after processing)
    ↓
Dict (Python)
    ↓
ChatResponse (Pydantic)
```

## Directory Structure with Flow

```
app/
├── routes/              ← 1️⃣ Entry point
│   └── chat_routes.py
│
├── controllers/         ← 2️⃣ Validation
│   └── chat_controller.py
│
├── services/           ← 3️⃣ Business logic
│   └── chat_service.py
│
├── orchestrator.py     ← 4️⃣ Router
├── agents/             ← 5️⃣ Processing
│   ├── research.py
│   ├── writing.py
│   └── code.py
│
├── aggregator.py       ← 6️⃣ Synthesis
├── graph.py            ← LangGraph workflow
└── state.py            ← State management
```

## Request Example

### 1. Client Request
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain quantum computing"}'
```

### 2. Route Handler
```python
# routes/chat_routes.py
@router.post("/")
async def chat(request: ChatRequest):
    return controller.process_chat(request)
```

### 3. Controller
```python
# controllers/chat_controller.py
def process_chat(self, request: ChatRequest):
    result = self.chat_service.process_chat(
        user_input=request.message,
        context=request.context
    )
    return ChatResponse(response=result["response"], ...)
```

### 4. Service
```python
# services/chat_service.py
def process_chat(self, user_input: str, context: dict):
    initial_state = {
        "user_input": user_input,
        "intent": None,
        "research_output": None,
        ...
    }
    result = agent_graph.invoke(initial_state)
    return {...}
```

### 5. Orchestrator
```python
# orchestrator.py
def orchestrator_router(state: AgentState):
    # Analyze intent
    # Return routing decision
    return {"selected_agents": ["research", "writing"]}
```

### 6. Agents Execute
```python
# agents/research.py
def research_agent(state: AgentState):
    # Perform research
    return {"research_output": "..."}

# agents/writing.py
def writing_agent(state: AgentState):
    # Create content
    return {"writing_output": "..."}
```

### 7. Aggregator
```python
# aggregator.py
def aggregator(state: AgentState):
    # Combine outputs
    return {"final_output": "Complete answer..."}
```

### 8. Response
```json
{
  "response": "Quantum computing is a revolutionary...",
  "intent": "research",
  "agents_used": ["research", "writing"],
  "metadata": {...},
  "timestamp": "2024-01-29T12:00:00"
}
```

## Key Design Principles

### 1. Separation of Concerns
Each layer has a single, clear responsibility.

### 2. Dependency Flow
```
Routes → Controllers → Services → Orchestrator → Agents
```

### 3. Type Safety
Pydantic models at API boundaries ensure type safety.

### 4. Testability
Each layer can be tested independently.

### 5. Scalability
Easy to add new endpoints, services, or agents.

## Middleware Stack

```
HTTP Request
    ↓
[CORS Middleware] ← Allow cross-origin requests
    ↓
[Error Handling] ← Catch and format errors
    ↓
[Routes] ← Process request
    ↓
HTTP Response
```

## Future Extensions

### Adding CRUD Operations

```
routes → controllers → services → models → database
```

### Adding Authentication

```
routes → [Auth Middleware] → controllers → services
```

### Adding Caching

```
services → [Cache Layer] → orchestrator
```
