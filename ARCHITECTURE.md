# 🏗️ Architecture Documentation

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         USER INPUT                          │
│                    "What is Docker?"                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    BOSS AGENT (Router)                      │
│  • Analyzes intent                                          │
│  • Selects agents: ["research", "writing"]                 │
│  • NEVER generates content                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
│ RESEARCH AGENT  │ │ WRITING     │ │ CODE AGENT      │
│                 │ │ AGENT       │ │                 │
│ • Facts         │ │ • Content   │ │ • Implementation│
│ • Analysis      │ │ • Structure │ │ • Best practices│
│ • Comparisons   │ │ • Clarity   │ │ • Production    │
└────────┬────────┘ └──────┬──────┘ └────────┬────────┘
         │                 │                 │
         └────────────────┬┴─────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────┐
         │      AGGREGATOR AGENT              │
         │  • Synthesizes outputs             │
         │  • Removes duplication             │
         │  • Creates coherent response       │
         └────────────────┬───────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────┐
         │         FINAL OUTPUT               │
         │  Well-structured response to user  │
         └────────────────────────────────────┘
```

## Data Flow

### State Object Flow

```python
# Initial State
{
    "user_input": "What is Docker?",
    "intent": None,
    "selected_agents": [],
    "research_output": None,
    "writing_output": None,
    "code_output": None,
    "final_output": None
}

# After Boss Agent
{
    "user_input": "What is Docker?",
    "intent": "educational explanation about Docker",
    "selected_agents": ["research", "writing"],
    "research_output": None,
    "writing_output": None,
    "code_output": None,
    "final_output": None
}

# After Research Agent
{
    "user_input": "What is Docker?",
    "intent": "educational explanation about Docker",
    "selected_agents": ["research", "writing"],
    "research_output": "Docker is a containerization platform...",
    "writing_output": None,
    "code_output": None,
    "final_output": None
}

# After Writing Agent
{
    "user_input": "What is Docker?",
    "intent": "educational explanation about Docker",
    "selected_agents": ["research", "writing"],
    "research_output": "Docker is a containerization platform...",
    "writing_output": "## Understanding Docker\n\nDocker is...",
    "code_output": None,
    "final_output": None
}

# After Aggregator
{
    "user_input": "What is Docker?",
    "intent": "educational explanation about Docker",
    "selected_agents": ["research", "writing"],
    "research_output": "Docker is a containerization platform...",
    "writing_output": "## Understanding Docker\n\nDocker is...",
    "code_output": None,
    "final_output": "# Understanding Docker\n\nDocker is a..."
}
```

## Component Details

### 1. Boss Agent (Router)

**Location**: `app/router.py`

**Responsibilities**:
- Parse user intent from input
- Classify query type
- Select appropriate agent(s)
- Return routing decision as JSON

**Key Characteristics**:
- Temperature: 0 (deterministic)
- Model: GPT-4
- Output: Structured JSON
- Never generates content

**Decision Logic**:
```
Keywords/Intent → Agent Selection
─────────────────────────────────
"compare", "what is" → research
"write", "explain" → research + writing
"code", "implement" → code
"compare + code" → research + code
```

### 2. Research Agent

**Location**: `app/agents/research.py`

**Responsibilities**:
- Provide factual information
- Compare options
- Analyze trade-offs
- Give comprehensive context

**Key Characteristics**:
- Temperature: 0.3 (slightly creative)
- Model: GPT-4
- Output: Factual, structured
- Input: User query + intent

**Output Format**:
- Bullet points
- Comparisons
- Structured data
- Citations/reasoning

### 3. Writing Agent

**Location**: `app/agents/writing.py`

**Responsibilities**:
- Transform research into readable content
- Structure information logically
- Ensure clarity and flow
- Format for readability

**Key Characteristics**:
- Temperature: 0.7 (more creative)
- Model: GPT-4
- Output: Well-structured prose
- Input: User query + research context

**Output Format**:
- Headings and sections
- Paragraphs
- Lists
- Emphasis

### 4. Code Agent

**Location**: `app/agents/code.py`

**Responsibilities**:
- Generate production-quality code
- Follow best practices
- Include error handling
- Provide usage examples

**Key Characteristics**:
- Temperature: 0.2 (deterministic)
- Model: GPT-4
- Output: Runnable code
- Input: User requirements

**Output Format**:
- Complete, functional code
- Comments
- Type hints
- Examples

### 5. Aggregator Agent

**Location**: `app/aggregator.py`

**Responsibilities**:
- Synthesize multiple outputs
- Remove duplication
- Ensure logical flow
- Create unified response

**Key Characteristics**:
- Temperature: 0.5 (balanced)
- Model: GPT-4
- Input: All agent outputs
- Output: Coherent final response

**Aggregation Strategy**:
1. Collect available outputs
2. If single output → use directly
3. If multiple → synthesize intelligently
4. Maintain quality from each agent
5. Create natural flow

## LangGraph Workflow

### Node Definitions

```python
workflow = StateGraph(AgentState)

# Nodes
workflow.add_node("boss", boss_router)
workflow.add_node("research", research_agent)
workflow.add_node("writing", writing_agent)
workflow.add_node("code", code_agent)
workflow.add_node("aggregator", aggregator)
```

### Edge Definitions

```python
# Entry point
workflow.set_entry_point("boss")

# Conditional routing
workflow.add_conditional_edges(
    "boss",
    route_to_agents,
    {
        "research": "research",
        "writing": "writing",
        "code": "code",
        "aggregator": "aggregator"
    }
)

# Fan-in to aggregator
workflow.add_edge("research", "aggregator")
workflow.add_edge("writing", "aggregator")
workflow.add_edge("code", "aggregator")

# End
workflow.add_edge("aggregator", END)
```

### Execution Flow Examples

**Example 1: Research Only**
```
User → Boss → Research → Aggregator → Output
```

**Example 2: Research + Writing**
```
User → Boss → [Research, Writing] → Aggregator → Output
                     ↓           ↓
                     └───────────┘ (parallel)
```

**Example 3: All Agents**
```
User → Boss → [Research, Writing, Code] → Aggregator → Output
                     ↓        ↓       ↓
                     └────────┴───────┘ (parallel)
```

## Design Principles

### 1. Separation of Concerns
- Each agent has ONE job
- No overlapping responsibilities
- Clear boundaries

### 2. Explicit State
- State is TypedDict
- Each agent writes to its field only
- No hidden state or memory

### 3. Deterministic Routing
- Boss agent uses rules (can upgrade to LLM)
- Predictable behavior
- Easy to debug

### 4. Isolation
- Agents don't communicate
- No shared context except state
- Independent execution

### 5. Composability
- Easy to add new agents
- Simple to modify routing
- Flexible aggregation

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
- Use faster models for boss
- Parallel agent execution
- Async/await for I/O

### Production Enhancements

```
                    ┌─────────────┐
                    │   FastAPI   │
                    │   Gateway   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Auth &     │
                    │  Rate Limit │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
    │  Redis  │      │ LangGraph│      │LangSmith│
    │  Cache  │      │  System  │      │   Logs  │
    └─────────┘      └──────────┘      └─────────┘
```

## Performance Characteristics

### Latency Breakdown

| Component | Typical Time | Notes |
|-----------|-------------|-------|
| Boss Agent | 1-2s | Fast, low temperature |
| Research Agent | 3-5s | Comprehensive |
| Writing Agent | 4-6s | Creative |
| Code Agent | 3-7s | Depends on complexity |
| Aggregator | 2-4s | Synthesis |
| **Total** | **5-15s** | Single agent: 5-8s |

### Cost Estimation (GPT-4)

| Query Type | Tokens | Cost |
|-----------|--------|------|
| Simple (1 agent) | ~2K | $0.02 |
| Medium (2 agents) | ~4K | $0.04 |
| Complex (3 agents) | ~6K | $0.06 |

## Error Handling

### Current Implementation
- Basic try/catch in boss router
- Fallback to writing agent on error
- Error messages returned to user

### Production Improvements
```python
# Retry with exponential backoff
@retry(max_attempts=3, backoff=2)
def call_agent(state):
    ...

# Circuit breaker
if failure_rate > 0.5:
    use_fallback_agent()

# Timeout handling
with timeout(30):
    result = agent.invoke(state)
```

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

### Key Metrics
- Agent selection frequency
- Response times per agent
- Token usage
- Error rates
- User satisfaction

### Logging Strategy
```python
logger.info("Boss selected agents", agents=selected_agents)
logger.info("Research completed", tokens=usage)
logger.error("Aggregation failed", error=e)
```

### Tracing
- Request ID per query
- Agent execution trace
- State snapshots
- Performance profiling

---

## Summary

This architecture provides:
- ✅ **Modularity**: Easy to extend
- ✅ **Clarity**: Explicit state flow
- ✅ **Control**: Deterministic routing
- ✅ **Scalability**: Production-ready
- ✅ **Maintainability**: Clean separation

**Philosophy**: Treat agents as microservices, not as chatting humans.
