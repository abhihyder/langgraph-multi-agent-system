# 🏗️ Architecture Documentation

## System Architecture

### High-Level Overview

```
           ┌──────────────────────────────────────────┐
           │           USER INPUT                     │
           │      "What is Docker?"                   │
           └─────────────────┬────────────────────────┘
                             │
                             ▼
           ┌──────────────────────────────────────────┐
           │    ORCHESTRATOR AGENT (Router)           │
           │  • Analyzes intent                       │
           │  • Selects agents                        │
           │  • Multi-provider LLM support            │
           └─────────────────┬────────────────────────┘
                             │
        ┌────────┬───────────┼───────────┬────────┬──────────┐
        │        │           │           │        │          │
        ▼        ▼           ▼           ▼        ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │RESEARCH│ │WRITING │ │  CODE  │ │GENERAL │ │KNOWLEDGE││ MEMORY │
    │ AGENT  │ │ AGENT  │ │ AGENT  │ │ AGENT  │ │ AGENT  │ │ AGENT  │
    │        │ │        │ │        │ │        │ │        │ │        │
    │ Facts  │ │Content │ │  Code  │ │  Chat  │ │  Docs  │ │History │
    │Analyze │ │ Style  │ │Practice│ │ Quick  │ │ Policy │ │Context │
    │Compare │ │Clarity │ │  Best  │ │Answers │ │  RAG   │ │  RAG   │
    └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
        │          │          │          │          │          │
        └──────────┴──────────┴──────────┴──────────┴──────────┘
                                │
                                ▼
               ┌──────────────────────────────────┐
               │    AGGREGATOR AGENT              │
               │  • Synthesizes outputs           │
               │  • Removes duplication           │
               │  • Creates coherent response     │
               └────────────────┬─────────────────┘
                                │
                                ▼
               ┌──────────────────────────────────┐
               │       FINAL OUTPUT               │
               │  Well-structured response        │
               └──────────────────────────────────┘
```

## Memory Driver System

### Architecture Pattern

**Inspiration**: Laravel's database driver pattern - seamless backend switching via configuration

**Location**: `app/core/memory/`

**Components**:
1. **BaseMemoryDriver** (`base.py`): Abstract interface defining memory operations
2. **AutoMemDriver** (`automem_driver.py`): Wraps external AutoMem HTTP service
3. **PGVectorDriver** (`pgvector_driver.py`): PostgreSQL with pgvector extension
4. **MemoryDriverManager** (`manager.py`): Factory for driver instantiation

### Driver Selection

**Configuration**: Set `MEMORY_DRIVER` environment variable
```bash
# Use external AutoMem service (default)
MEMORY_DRIVER=automem

# Use PostgreSQL with pgvector
MEMORY_DRIVER=pgvector
```

**Automatic Switching**: All agents use `get_memory_driver()` which returns the configured driver

### Driver Comparison

| Feature | AutoMem | PGVector |
|---------|---------|----------|
| **Type** | External HTTP service | PostgreSQL extension |
| **Setup** | Requires AutoMem server | Requires PostgreSQL + pgvector |
| **Vector Search** | Built-in | pgvector extension |
| **Scalability** | Horizontal (microservice) | Vertical (database) |
| **Latency** | Network overhead | Direct database |
| **Use Case** | Distributed systems | Monolithic applications |

### PGVector Schema

**Tables**:
1. **memories**: User conversation history
   - `user_id`, `conversation_id`, `content`, `tags`, `metadata`
   - `embedding` (vector(384)): Sentence embeddings for semantic search
   - Foreign keys to `users` and `conversations` tables

2. **global_knowledge**: Company policies and documentation
   - `content`, `category`, `title`, `doc_id`, `tags`, `metadata`
   - `embedding` (vector(384)): Sentence embeddings for semantic search

**Migrations**: Located in `database/migrations/versions/005_create_pgvector_tables.py`

**Vector Indexes**: IVFFlat indexes for fast similarity search (created manually after data insertion)

### API Interface

**All drivers implement**:
```python
class BaseMemoryDriver(ABC):
    def recall(user_id, conversation_id, query, top_k, use_vector) -> List[Dict]
    def recall_global_knowledge(query, top_k, category) -> List[Dict]
    def store(user_id, content, conversation_id, tags, metadata) -> Dict
    def store_global_knowledge(content, category, title, doc_id, metadata) -> Dict
    def delete(memory_id) -> bool
```

**Seamless Integration**: Agents call `get_memory_driver()` and use the same API regardless of backend

## Data Flow

### State Object Flow

State progresses through the system as a TypedDict:

1. **Initial**: Contains `user_input`, `user_id`, `conversation_id`, `executed_agents` (empty list), all outputs set to `None`
2. **After Orchestrator**: Adds `intent` and `selected_agents` list
3. **After Retrieval Agents** (parallel): Populates `knowledge_output` (company docs/policies) and `memory_output` (user history)
4. **After Specialized Agents** (parallel): Populates respective output fields (`research_output`, `writing_output`, `code_output`, `general_output`), appends agent name to `executed_agents`
5. **After Aggregator**: Synthesizes all outputs into `final_output`

**Key Properties**: `user_input`, `user_id`, `conversation_id`, `intent`, `selected_agents`, `knowledge_output`, `memory_output`, `research_output`, `writing_output`, `code_output`, `general_output`, `final_output`, `executed_agents`

**Infinite Loop Prevention**: The `executed_agents` field tracks which agents have run, preventing duplicate execution in routing logic

## Component Details

### 0. LLM Configuration System

**Location**: `config/llm_config.py`, `app/utils/llm_factory.py`

**Purpose**: Centralized configuration enabling multi-provider LLM support with agent-specific model selection

**Supported Providers**:
- **OpenAI**: gpt-4o, gpt-4o-mini (default), gpt-4-turbo, gpt-4, gpt-3.5-turbo
- **Anthropic**: claude-3-5-sonnet-20241022 (default), claude-3-5-haiku-20241022, claude-3-opus-20240229
- **Google**: gemini-1.5-pro, gemini-2.5-flash (default), gemini-1.5-flash, gemini-1.0-pro

**Configuration**: Each agent can use different providers/models via environment variables (format: `provider:model`)

**Factory Pattern**: Centralized LLM instance creation with validation and fallback support

### 1. Orchestrator Agent (Router)

**Location**: `app/agentic/orchestrator.py`

**Responsibilities**:
- Parse user intent from input
- Classify query type
- Select appropriate agent(s)
- Return routing decision as JSON

**Key Characteristics**:
- Temperature: 0 (deterministic)
- Model: Configurable via `ORCHESTRATOR_LLM` (default: openai:gpt-4o-mini)
- Output: Structured JSON with intent analysis and agent selection
- Never generates content - routing only

### 2. Research Agent

**Location**: `app/agentic/agents/research.py`

**Responsibilities**:
- Provide factual information
- Compare options
- Analyze trade-offs
- Give comprehensive context

**Key Characteristics**:
- Temperature: 0.3 (slightly creative, configurable via `RESEARCH_TEMPERATURE`)
- Model: Configurable via `RESEARCH_LLM` (default: openai:gpt-4o-mini)
- Output: Factual, structured information with comparisons and analysis

### 3. Writing Agent

**Location**: `app/agentic/agents/writing.py`

**Responsibilities**:
- Transform research into readable content
- Structure information logically
- Ensure clarity and flow
- Format for readability

**Key Characteristics**:
- Temperature: 0.7 (more creative, configurable via `WRITING_TEMPERATURE`)
- Model: Configurable via `WRITING_LLM` (default: openai:gpt-4o-mini)
- Output: Well-structured, readable content with clear narrative flow

### 4. Code Agent

**Location**: `app/agentic/agents/code.py`

**Responsibilities**:
- Generate production-quality code
- Follow best practices
- Include error handling
- Provide usage examples

**Key Characteristics**:
- Temperature: 0.2 (deterministic, configurable via `CODE_TEMPERATURE`)
- Model: Configurable via `CODE_LLM` (default: openai:gpt-4o-mini)
- Output: Production-ready code with best practices, error handling, and documentation

### 5. General Agent

**Location**: `app/agentic/agents/general.py`

**Responsibilities**:
- Handle general conversational queries
- Provide quick responses for simple questions
- Serve as fallback for uncategorized requests
- Direct user assistance

**Key Characteristics**:
- Temperature: 0.7 (balanced creativity)
- Model: Configurable via `GENERAL_LLM` (default: openai:gpt-4o-mini)
- Output: Conversational responses for quick answers and general assistance

### 6. Knowledge Agent (RAG)

**Location**: `app/agentic/agents/knowledge.py`

**Responsibilities**:
- Retrieve company policies and documentation
- Semantic search across global knowledge base
- Provide authoritative grounding for answers
- RAG (Retrieval-Augmented Generation) for company-specific info

**Key Characteristics**:
- Type: **Retrieval-only** (no LLM, no generation)
- Backend: Configurable memory driver (AutoMem or PGVector)
- Configuration: Set via `MEMORY_DRIVER` environment variable
- Operation: Semantic search with top-k retrieval (k=5)
- Output: Retrieved documents with metadata (category, doc_id, title)

**Integration**: Knowledge context is injected into other agents' prompts for grounded responses

### 7. Memory Agent (RAG)

**Location**: `app/agentic/agents/memory.py`

**Responsibilities**:
- Retrieve user conversation history
- Provide personalized context from past interactions
- Enable continuity across conversations
- Multi-level memory retrieval

**Key Characteristics**:
- Type: **Retrieval-only** (no LLM, no generation)
- Backend: Configurable memory driver (AutoMem or PGVector)
- Configuration: Set via `MEMORY_DRIVER` environment variable
- Operation: Three-tier retrieval strategy:
  - Recent chronological (last 5 messages)
  - Short-term semantic (current conversation)
  - Long-term semantic (across all conversations)
- Output: Formatted conversation history with context

**Integration**: Memory context is injected into other agents' prompts for personalized responses

### 8. Aggregator Agent

**Location**: `app/agentic/aggregator.py`

**Responsibilities**:
- Synthesize multiple outputs
- Remove duplication
- Ensure logical flow
- Create unified response

**Key Characteristics**:
- Temperature: 0.5 (balanced, configurable via `AGGREGATOR_TEMPERATURE`)
- Model: Configurable via `AGGREGATOR_LLM` (default: openai:gpt-4o-mini)
- Input: All agent outputs
- Output: Coherent final response

**Aggregation Strategy**:
1. Collect available outputs
2. If single output → use directly
3. If multiple → synthesize intelligently
4. Maintain quality from each agent
5. Create natural flow

## LangGraph Workflow

**Graph Structure**: StateGraph with 8 nodes:
- **Router**: orchestrator
- **Retrieval Agents**: knowledge, memory (RAG, no LLM)
- **Generative Agents**: research, writing, code, general (LLM-powered)
- **Synthesis**: aggregator

**Entry Point**: Orchestrator receives user input

**Routing**: Conditional edges from orchestrator to selected agents based on intent analysis

**Parallel Execution**:
- Retrieval agents (knowledge, memory) execute first in parallel
- Generative agents execute in parallel with retrieval context
- All agents converge to aggregator (fan-in pattern)

**Termination**: Aggregator produces final output and ends workflow

**Memory Backend**: Configurable via `MEMORY_DRIVER` (automem or pgvector) - uses driver abstraction, not LangGraph checkpointing

### Execution Flow Patterns

- **Retrieval First**: Knowledge and memory agents always execute first (when selected)
- **Parallel Generative**: Research, writing, code, general agents execute concurrently
- **Context Injection**: Retrieval outputs injected into generative agent prompts
- **Agent Selection**: Dynamic based on user intent (1-6 agents per query)
- **Fan-in Aggregation**: All agent outputs synthesize at aggregator

**Typical Flow**: Orchestrator → [Knowledge, Memory] → [Research, Writing, ...] → Aggregator → Output

## Design Principles

### 1. Separation of Concerns
- Each agent has ONE job
- Retrieval agents: No LLM, just vector search
- Generative agents: LLM-powered with injected context
- Clear boundaries between retrieval and generation

### 2. Explicit State
- State is TypedDict
- Each agent writes to its field only
- No hidden state or memory
- Retrieval context explicitly passed

### 3. RAG Architecture
- Knowledge agent: Company-specific grounding (RAG)
- Memory agent: User-specific personalization (RAG)
- Context injection: Retrieval → Generation
- Authoritative sources prioritized

### 4. Deterministic Routing
- Orchestrator uses intent analysis
- Predictable behavior
- Easy to debug

### 5. Isolation
- Agents don't communicate directly
- No shared context except state
- Independent execution
- Parallel processing

### 6. Composability
- Easy to add new agents
- Simple to modify routing
- Flexible aggregation
- Modular RAG integration

## Multi-Provider LLM Strategy

**Configuration Approach**: Environment-based with format `provider:model` per agent

**Flexibility**: Each agent can use different providers/models optimized for their task

**Temperature Control**: Configurable per agent (0.0 for routing, 0.7 for creative tasks)

**Benefits**:
- **Cost Optimization**: Mix premium and economical models by task complexity
- **Performance Tuning**: Select fastest providers for time-sensitive operations
- **Reliability**: Multi-provider fallback capability
- **Quality**: Best-in-class model selection per use case
- **Vendor Independence**: No single-provider lock-in

## Scalability Considerations

### Horizontal Scaling
```
         ┌─────────────┐
         │ Load        │
         │ Balancer    │
         └──────┬──────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌────────┐  ┌────────┐  ┌────────┐
│Instance│  │Instance│  │Instance│
│   1    │  │   2    │  │   3    │
└────────┘  └────────┘  └────────┘
```

### Vertical Scaling
- Cache LLM responses
- Use faster models for orchestrator
- Parallel agent execution
- Async/await for I/O

### Production Enhancements

```
                    ┌─────────────┐
                    │   FastAPI   │
                    │   Gateway   │
                    └──────┬──────┘
                           │
                    ┌─────────────┐
                    │  Auth &     │
                    │  Rate Limit │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌─────────┐      ┌──────────┐      ┌─────────┐
    │  Redis  │      │ LangGraph│      │LangSmith│
    │  Cache  │      │  System  │      │   Logs  │
    └─────────┘      └──────────┘      └─────────┘
```

## Performance Characteristics

### Latency Breakdown

| Component | Typical Time | Notes |
|-----------|-------------|-------|
| Orchestrator Agent | 1-2s | Fast, low temperature |
| Knowledge Agent (RAG) | 0.1-0.3s | Vector search only |
| Memory Agent (RAG) | 0.2-0.5s | Multi-tier retrieval |
| Research Agent | 3-5s | Comprehensive |
| Writing Agent | 4-6s | Creative |
| Code Agent | 3-7s | Depends on complexity |
| General Agent | 2-4s | Quick responses |
| Aggregator | 2-4s | Synthesis |
| **Total** | **5-15s** | Single agent: 5-8s |

**Note**: 
- Latency varies by provider (OpenAI: fast, Anthropic: quality, Google: economical)
- Retrieval agents add minimal latency (~0.3-0.5s total)
- Parallel execution optimizes overall response time

### Cost Estimation

**OpenAI (GPT-4o-mini)**:
| Query Type | Tokens | Cost |
|-----------|--------|------|
| Simple (1 agent) | ~2K | $0.003 |
| Medium (2 agents) | ~4K | $0.006 |
| Complex (3 agents) | ~6K | $0.009 |

**Anthropic (Claude-3.5-Sonnet)**:
| Query Type | Tokens | Cost |
|-----------|--------|------|
| Simple (1 agent) | ~2K | $0.006 |
| Medium (2 agents) | ~4K | $0.012 |
| Complex (3 agents) | ~6K | $0.018 |

**Google (Gemini-2.5-Flash)**:
| Query Type | Tokens | Cost |
|-----------|--------|------|
| Simple (1 agent) | ~2K | $0.001 |
| Medium (2 agents) | ~4K | $0.002 |
| Complex (3 agents) | ~6K | $0.003 |

**Cost Optimization Strategy**:
- Use faster, cheaper models (GPT-4o-mini, Gemini-Flash) for routing and simple tasks
- Reserve premium models (Claude-3.5-Sonnet, GPT-4o) for complex reasoning
- Mix providers: Gemini for research, Claude for writing, GPT for code

## Error Handling

**Current**: Try/catch blocks with fallback routing and user-facing error messages

**Production Enhancements**: Retry with exponential backoff, circuit breakers, timeout handling, graceful degradation

## Security Considerations

### Input Validation
- Sanitize user input
- Limit input length
- Rate limiting per user

### Output Safety
- Content filtering
- PII detection
- Injection prevention

### API Security
- Authentication required
- API key rotation
- Request signing

## Monitoring & Observability

**Key Metrics**: Agent selection frequency, response times, token usage, error rates, user satisfaction

**Logging**: Structured logging with request IDs, agent selection, execution traces, state snapshots

**Tracing**: End-to-end request tracking with performance profiling

---

## Summary

This architecture provides:
- ✅ **Modularity**: Easy to extend with new agents or providers
- ✅ **Clarity**: Explicit state flow through typed state objects
- ✅ **Control**: Deterministic routing with configurable LLMs
- ✅ **Scalability**: Production-ready with multi-provider support
- ✅ **Maintainability**: Clean separation of concerns
- ✅ **Flexibility**: Support for OpenAI, Anthropic, and Google models
- ✅ **Cost Efficiency**: Mix and match models based on task requirements
- ✅ **Vendor Independence**: Not locked into single LLM provider
- ✅ **RAG Integration**: Knowledge and memory agents for grounded, personalized responses
- ✅ **Context Awareness**: Multi-tier memory retrieval (recent, short-term, long-term)

**Philosophy**: Treat agents as microservices, not as chatting humans.

**Key Innovations**: 
- Multi-provider LLM support with centralized configuration and factory pattern
- Dual RAG agents (knowledge + memory) for authoritative and personalized responses
- Retrieval-first architecture with context injection into generative agents
- AutoMem integration for persistent, semantic-searchable memory
