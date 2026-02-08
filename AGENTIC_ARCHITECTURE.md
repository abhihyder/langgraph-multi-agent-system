# Agentic Architecture Guide (AI Features)

> **Scope**: Multi-agent orchestration using LangGraph for AI-powered features (chat, query assistant)

**Flow**: `Request → Orchestrator → [Agents] → Aggregator → Response`

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

### 1. Single Responsibility
**Rule**: One job per agent. If you need "and" or "or" to describe it, split it.

### 2. State as Contract
**Rule**: Read what you need. Write only your field.

**Field Ownership**:
- Orchestrator → `intent`, `selected_agents`
- Retrieval agents → `{name}_output` (NO LLM)
- Processing agents → `{name}_output` (WITH LLM)
- Aggregator → `final_output`

**Red Flags**:
- Modifying `user_input`? STOP - it's read-only
- Writing multiple `_output` fields? STOP - one agent, one field

### 3. No Coordination
**Rule**: Agents are blind to each other. Run independently.

**Isolation Test**: Remove all other agents - yours should still work for its task.

### Context Separation
**Two Agent Types**:
- **Retrieval**: Query database/service, return data, NO LLM (fast)
- **Processing**: Call LLM, generate content, USE retrieval context (slower)

**Never mix**: If it fetches AND generates, split into two agents.

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
- **AutoMem** (external HTTP service) - NOT LangGraph checkpointing
- **Global knowledge**: `tag:global_knowledge` + `category_{type}`
- **User memory**: `tag:user_{id}` + `conversation_{id}`
- Retrieval agents query AutoMem
- Processing agents consume via state

### Service Layer Flow
```
API Route → ChatService → LangGraph (Orchestrator → Agents → Aggregator) → External (AutoMem, OpenAI)
```

---

## Extension Template

### Adding Processing Agent

1. **Create** `app/agentic/agents/{name}.py`
2. **Update** `app/agentic/state.py`: Add `{name}_output: Optional[str]`
3. **Register** in `app/agentic/graph.py`: Add node, edges, routing
4. **Update** `prompts/orchestrator.md`: Document when to use
5. **Update** `app/agentic/aggregator.py`: Handle new output
6. **Create** `prompts/{name}.md`: Agent instructions
7. **Write tests** in `tests/test_agents.py`
8. **Run tests**: All tests must pass before merging (`pytest`)

### Adding Retrieval Agent
Same steps, but:
- NO LLM calls
- Query data source directly
- Fast execution (< 200ms)
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

**Agent Code**:
- [ ] One clear job (one sentence description)
- [ ] Reads from state, writes ONE field
- [ ] No references to other agents' outputs
- [ ] Processing agents use retrieval context
- [ ] Retrieval agents don't call LLM
- [ ] Prompts from files, not hardcoded
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

**Testing**:
- [ ] New/modified functions have test coverage
- [ ] All existing tests still pass
- [ ] No test failures or warnings

---

**Related**: See [CONSTITUTION.md](CONSTITUTION.md) for universal principles and [TRADITIONAL_ARCHITECTURE.md](TRADITIONAL_ARCHITECTURE.md) for non-agentic features.
