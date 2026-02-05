# Global Knowledge & Retrieval Agents

This system implements intelligent retrieval agents that fetch information from AutoMem without using LLMs. This provides two key capabilities:

1. **Company-wide Knowledge** - Policies, procedures, documentation accessible to all users
2. **User Memory** - Personal conversation history and context

## Architecture

### Retrieval Agents (No LLM)

**Knowledge Agent** (`app/agentic/agents/knowledge_agent.py`)
- Retrieves company policies, HR documentation, procedures
- Uses semantic search via AutoMem vector database
- Tagged with `global_knowledge` + category tags
- Accessible to all users (not user-specific)

**Memory Agent** (`app/agentic/agents/memory_agent.py`)
- Retrieves user's conversation history
- 3-tier retrieval:
  - Recent chronological (last 5 messages)
  - Short-term semantic (current conversation)
  - Long-term semantic (across all conversations)
- User-scoped with `user_{id}` tags

### Processing Agents (LLM-based)

These agents generate responses using LLMs:
- `general` - Casual conversation, simple queries
- `research` - Factual information, analysis
- `writing` - Content creation, articles
- `code` - Implementation, debugging

## Workflow

```
User Query
    ↓
Orchestrator (analyzes intent)
    ↓
Routes to retrieval + processing agents:
    ├─ knowledge (if asking about policies)
    ├─ memory (if referencing past conversations)
    ├─ general/research/writing/code (for responses)
    ↓
Aggregator (combines context + responses)
    ↓
Final Response
```

## Storage: Global Knowledge

### AutoMem Tags

All company knowledge uses:
- `global_knowledge` - Marks as company-wide (not user-specific)
- `category_{type}` - Categorizes content (e.g., `category_leave_policy`)

### Categories

- `leave_policy` - Sick leave, vacation, personal leave
- `work_policy` - Remote work, work hours, flexibility
- `performance_policy` - Reviews, evaluations
- `benefits_policy` - Health insurance, retirement, wellness
- `training_policy` - Onboarding, development, certifications
- `travel_policy` - Business travel, expenses
- `equipment_policy` - Laptops, software, home office
- `code_of_conduct` - Professional behavior, ethics
- `parental_leave` - Maternity/paternity leave
- `company_info` - Company overview, locations, teams

## Setup

### 1. Load Company Knowledge

```bash
# Activate virtual environment
source venv/bin/activate

# Load sample HR policies and company info
python scripts/load_company_knowledge.py
```

This populates AutoMem with 13 sample documents (10 HR policies + 3 company info docs).

### 2. Query Examples

**Policy Questions** → Routes to `knowledge` + `general`:
- "How many sick leaves do I have?"
- "What's the remote work policy?"
- "Can I work from home 4 days a week?"

**Memory Questions** → Routes to `memory` + `general`:
- "What did we discuss last time?"
- "Can you remind me about our Python conversation?"
- "What projects did I mention before?"

**Mixed Questions** → Routes to multiple agents:
- "Based on the leave policy and what we discussed yesterday, can I take time off?" 
  → `knowledge`, `memory`, `general`

## API Methods

### Store Global Knowledge

```python
from app.services.automem_client import get_default_client

automem = get_default_client()

automem.store_global_knowledge(
    content="Your policy text here...",
    category="leave_policy",
    metadata={
        "title": "Leave Policy",
        "doc_id": "HR-POL-001",
        "version": "2.0"
    }
)
```

### Retrieve Global Knowledge

```python
# Semantic search across all company knowledge
results = automem.recall_global_knowledge(
    query="How many vacation days?",
    top_k=5,
    categories=["leave_policy"]  # Optional filter
)
```

### Store User Memory

```python
# Automatically handled by chat service
automem.store_message(
    user_id=123,
    conversation_id=456,
    role="user",
    content="I need help with Python",
    scope="conversation"
)
```

### Retrieve User Memory

```python
# Get user's conversation history
memories = automem.recall(
    user_id=123,
    conversation_id=456,  # or None for all conversations
    query="Python help",  # or None for chronological
    top_k=5,
    use_vector=True  # False for tag-only (chronological)
)
```

## Benefits

### Semantic Search
- No hardcoded keyword matching
- Handles multi-topic queries naturally
- "What's the leave policy AND remote work rules?" → Finds both automatically

### Intelligent Routing
- Orchestrator decides when to fetch knowledge/memory
- Skips retrieval for simple queries like greetings
- Only fetches what's needed based on user intent

### Separation of Concerns
- Retrieval agents = pure data fetching (no LLM cost)
- Processing agents = response generation (LLM-based)
- Aggregator = synthesis and coherence

### Scalability
- Add new categories without code changes
- Just store with appropriate tags
- Retrieval agents automatically find relevant content

## Testing

### Test Knowledge Retrieval

```bash
# Start servers
python server.py  # FastAPI backend (port 8000)
# AutoMem should be running on port 8001

# Test queries via API or UI
POST /api/chat
{
  "message": "How many sick leaves do I have?",
  "conversation_id": 1
}
```

Expected flow:
1. Orchestrator → routes to `["knowledge", "general"]`
2. Knowledge agent → retrieves HR-POL-001 (Leave Policy)
3. General agent → generates friendly response
4. Aggregator → combines: "According to company policy, you have 12 sick days..."

### Test Memory Retrieval

```bash
# Have a conversation first
POST /api/chat {"message": "I'm working on a Python ML project"}

# Later, reference it
POST /api/chat {"message": "What was I working on yesterday?"}
```

Expected flow:
1. Orchestrator → routes to `["memory", "general"]`
2. Memory agent → retrieves past conversation about Python ML
3. General agent → generates contextual response
4. Aggregator → combines: "You mentioned working on a Python ML project..."

## File Structure

```
app/
├── agentic/
│   ├── agents/
│   │   ├── knowledge_agent.py    # Global knowledge retrieval
│   │   ├── memory_agent.py       # User memory retrieval
│   │   ├── general_agent.py      # LLM: General responses
│   │   ├── research_agent.py     # LLM: Research/analysis
│   │   ├── writing_agent.py      # LLM: Content creation
│   │   └── code_agent.py         # LLM: Code generation
│   ├── state.py                  # Shared state (added knowledge_output, memory_output)
│   ├── graph.py                  # Workflow (registered new agents)
│   ├── orchestrator.py           # Routing logic
│   └── aggregator.py             # Synthesis (handles retrieval + LLM outputs)
├── services/
│   └── automem_client.py         # Added global knowledge methods
└── ...

scripts/
└── load_company_knowledge.py     # Populate sample data
```

## Next Steps

### Add More Knowledge
Edit `scripts/load_company_knowledge.py` to add:
- More HR policies
- Technical documentation
- Process guides
- FAQs
- Product documentation

### Custom Categories
Create new categories as needed:
- `engineering_docs`
- `product_specs`
- `customer_faqs`
- `security_policies`

Just use the same tag pattern: `category_{your_category}`

### Update Orchestrator (Optional)
If you want more explicit routing rules, update `prompts/orchestrator.md`:
```markdown
- Use "knowledge" for: policies, procedures, documentation, company info
- Use "memory" for: references to past conversations, "last time", "we discussed"
```

Currently the orchestrator learns implicitly from examples.
