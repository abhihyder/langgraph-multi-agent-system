# Agentic Architecture Guide (AI Features)

> **Scope**: LangGraph StateGraph-based multi-agent system for AI-powered features (chat, query assistant)
> **Implementation**: Each agent is a StateGraph with nodes for processing steps

**Flow**: `Request → Orchestrator Graph → [Agent Graphs] → Aggregator → Response`

**See [ARCHITECTURE.md](ARCHITECTURE.md) for complete system architecture.**

---

## The Prime Directive

**Before ANY change, ask: "Does this preserve single-direction flow?"**

```
Input → Orchestrator → [Agents] → Aggregator → Output
```

If NO, stop. You're breaking the pattern.

---

## Mental Model: Assembly Line, Not Group Chat

- **Orchestra**: One conductor (orchestrator), specialized musicians (agents), no inter-musician communication
- **HTTP**: Request → Router → Handlers → Aggregator → Response  
- **Pipeline**: One-way data flow, each stage independent

---

## Core Principles

### 1. Graph-Based Architecture
**Implementation**: Each agent is a `StateGraph` with nodes representing processing steps.

**Structure**:
```python
class EmailAgentGraph(BaseAgentGraph):
    def build_graph(self) -> StateGraph:
        graph = StateGraph(EmailState)
        graph.add_node("validate_input", self.validate_input)
        graph.add_node("process_with_llm", self.process_with_llm)
        graph.add_conditional_edges("validate_input", self.route_decision)
        return graph.compile()
```

### 2. Single Responsibility
**Rule**: One job per agent graph. If you need "and" or "or" to describe it, split it.

### 3. State as Contract
**Rule**: Read what you need. Write only your field.

**Field Ownership**:
- Orchestrator → `intent`, `selected_agents`
- Retrieval agents → `{name}_output` (NO LLM)
- Processing agents → `{name}_output` (WITH LLM)
- Aggregator → `final_output`
- All agents → Append to `executed_agents` (prevents infinite loops)

**Red Flags**:
- Modifying `user_input`? STOP - it's read-only
- Writing multiple `_output` fields? STOP - one agent, one field
- Not updating `executed_agents`? STOP - routing will break

### 3. No Coordination
**Rule**: Agents are blind to each other. Run independently.

**Isolation Test**: Remove all other agents - yours should still work for its task.

### Context Separation
**Two Agent Types**:
- **Retrieval**: Query database/service, return data, NO LLM (fast)
- **Processing**: Call LLM, generate content, USE retrieval context (slower)

**Never mix**: If it fetches AND generates, split into two agents.

**Memory Driver Abstraction**:
- Retrieval agents use `get_memory_driver()` for seamless backend switching
- Supports multiple backends: AutoMem (HTTP service) or PGVector (PostgreSQL)
- Configuration: Set `MEMORY_DRIVER` environment variable (automem | pgvector)
- Same API interface regardless of backend

**Aggregation Logic**:
- Retrieval agents (knowledge, memory) provide context only
- 1 processing agent → passthrough (skip aggregator)
- 0 or 2+ processing agents → aggregator (synthesize outputs)
- **Token savings**: ~40% reduction for single-agent queries

---

## Decision Frameworks

### Use Agentic Architecture?
Ask:
- Needs AI-powered response generation? ✓
- Requires multiple specialized agents (retrieval + processing)? ✓
- Benefits from orchestration and context aggregation? ✓
- Complex natural language understanding needed? ✓

All YES → Use agentic | Otherwise → Use traditional

**Examples**:
- AI chat, query assistant → Agentic
- User CRUD, analytics, file upload → Traditional
- Payment processing, notifications → Traditional

### Adding New Agent?
Ask:
1. Distinct job no existing agent handles? ✓
2. Describable in one sentence? ✓
3. Retrieval OR processing (not both)? ✓
4. Works independently? ✓

All YES → Add agent | Any NO → Reconsider

### Modifying State?
Only when:
- Adding new agent (needs `{name}_output` field)
- Adding input ALL agents need

Never for:
- Agent-specific intermediate data (use local variables)
- Temporary calculations
- Debugging info

### Using Retrieval vs Processing?
**Retrieval**: User asks about policies/docs, references history, needs facts, speed critical  
**Processing**: Needs generated content, creative response, explanations, can wait

### When Context Exists?
**ALWAYS use retrieval outputs** (`knowledge_output`, `memory_output`) when present in state.

---

## Behavioral Patterns

### Read-Transform-Write (Every Agent)
1. **Read**: state fields (user_input, intent, context)
2. **Transform**: query DB or call LLM
3. **Write**: ONLY `{your_name}_output`

### Context First (Processing Agents)
1. Check for retrieval context
2. Include in LLM prompt
3. Generate response using context

### Parallel Execution
- Orchestrator selects agents
- Agents run simultaneously (when possible)
- Aggregator waits for all, then synthesizes

---

## Four Questions (Before Any Change)

1. **Isolation**: Can this work without knowing about others? (YES = good)
2. **Flow**: Does data still flow Orchestrator → Agents → Aggregator? (YES = preserves)
3. **Responsibility**: Does this have exactly one job? (YES = single responsibility)
4. **State**: Reading needs, writing only owned field? (YES = respects contract)

All YES → Proceed | Any NO → Redesign

---

## Architecture Quick Reference

### Workflow Topology
```
Entry: orchestrator
Routes to: knowledge, memory, general, research, writing, code

Agents route to (conditionally):
├─ passthrough (1 processing agent) → END
└─ aggregator (0 or 2+ processing agents) → END

Optimization: Skips aggregator when only 1 processing agent runs,
even if retrieval agents (knowledge, memory) provided context.
```

### Memory System
- **Configurable Driver**: AutoMem (external HTTP service) or PGVector (PostgreSQL) - NOT LangGraph checkpointing
- **Selection**: Set `MEMORY_DRIVER` environment variable (automem | pgvector)
- **Global knowledge**: `tag:global_knowledge` + `category_{type}`
- **User memory**: `tag:user_{id}` + `conversation_{id}`
- Retrieval agents query via driver abstraction (`get_memory_driver()`)
- Processing agents consume via state
- Seamless switching: Same API, different backends

### Service Layer Flow
```
API Route → ChatService → LangGraph (Orchestrator → Agents → Aggregator) → External (AutoMem, OpenAI)
```

---

## Extension Template

### Adding Processing Agent Graph

1. **Create** `app/agentic/graphs/{name}_graph.py`:
   ```python
   from .base_graph import BaseAgentGraph
   from langgraph.graph import StateGraph
   
   class MyAgentGraph(BaseAgentGraph):
       def build_graph(self) -> StateGraph:
           graph = StateGraph(AgentState)
           graph.add_node("process", self.process_node)
           graph.set_entry_point("process")
           graph.add_edge("process", END)
           return graph.compile()
   ```

2. **Update** `app/agentic/states/agent_state.py`: Add `{name}_output: Optional[str]`
3. **Register** in `app/agentic/__init__.py`: Add to orchestrator routing
4. **Update** `app/agentic/prompts/orchestrator.md`: Document when to use
5. **Update aggregator** in orchestrator: Handle new output
6. **Create** `app/agentic/prompts/{name}.md`: Agent instructions
7. **Ensure** nodes append to `executed_agents` list
8. **Write tests** in `tests/test_{name}_integration.py`
9. **Run tests**: All tests must pass before merging (`pytest`)

### Adding Retrieval Agent
Same steps, but:
- NO LLM calls
- Use `get_memory_driver()` for memory/knowledge access
- Query data source directly
- Fast execution (< 200ms)
- Append to `executed_agents` list
- All tests must pass

---

## Anti-Patterns

| ❌ Never | ✅ Instead |
|---------|----------|
| Agent calls another agent | Use orchestrator routing |
| Orchestrator generates content | Delegate to agents |
| Processing agent fetches memory | Use memory_agent |
| Hardcoded prompts | Load from `prompts/*.md` |
| Circular imports at top | Lazy load in `__init__` |
| Agent writes multiple fields | One agent, one field |

---

## Self-Check Checklist

**Agent Graph Code**:
- [ ] Extends `BaseAgentGraph` abstract class
- [ ] Implements `build_graph()` method
- [ ] Uses `StateGraph` with proper state TypedDict
- [ ] Nodes read from state, write ONE output field
- [ ] Nodes append agent name to `executed_agents` list
- [ ] No references to other agents' outputs
- [ ] Processing agents use retrieval context
- [ ] Retrieval agents don't call LLM
- [ ] Retrieval agents use `get_memory_driver()`
- [ ] Prompts loaded from `app/agentic/prompts/` files
- [ ] Uses decorators (`@retry_on_failure`, `@log_node_execution`)
- [ ] All tests pass (`pytest` runs successfully)

**Orchestrator**:
- [ ] Only routes, doesn't generate
- [ ] Returns `intent` + `selected_agents`

**Aggregator**:
- [ ] Collects all outputs
- [ ] Synthesizes coherently
- [ ] Handles missing outputs

**State**:
- [ ] Each agent has ONE output field
- [ ] No field ownership overlap
- [ ] Input fields read-only
- [ ] Agent appends to `executed_agents` list

**Testing**:
- [ ] New/modified functions have test coverage
- [ ] All existing tests still pass
- [ ] No test failures or warnings

---

**Related**: 
- [CONSTITUTION.md](CONSTITUTION.md) - Universal principles and decision framework
- [ARCHITECTURE.md](ARCHITECTURE.md) - Complete system architecture
- [FEATURES.md](FEATURES.md) - Feature list and roadmap
