# Multi-Agent AI System Constitution

> **Purpose**: Core principles and decision framework for both agentic and traditional architectures. Defines WHEN to use each pattern and universal rules.

**Version**: 2.2.0 | **Updated**: February 5, 2026

---

## Architecture Decision Framework

This application uses **two distinct architectural patterns**:

### 1. Agentic Architecture (AI Features)
**Flow**: `Request → Orchestrator → [Agents] → Aggregator → Response`  
**Use for**: AI chat, query assistant, multi-agent orchestration  
**Key**: LangGraph, multiple specialized agents, context aggregation  
**📖 Details**: See [AGENTIC_ARCHITECTURE.md](AGENTIC_ARCHITECTURE.md)

### 2. Traditional Architecture (Standard Features)  
**Flow**: `Request → Route → Controller → Service → Model/3rd Party → Response`  
**Use for**: CRUD operations, business logic, integrations, standard APIs  
**Key**: Layered architecture, separation of concerns, reusable services  
**📖 Details**: See [TRADITIONAL_ARCHITECTURE.md](TRADITIONAL_ARCHITECTURE.md)

---

## Quick Decision Tree

```
New Feature Request?
  ↓
Is it AI-powered with multi-agent needs?
  ├─ YES → Use Agentic Architecture
  │         └─ Orchestrator → Agents → Aggregator
  │         └─ Read: AGENTIC_ARCHITECTURE.md
  │
  └─ NO → Use Traditional Architecture
            └─ Route → Controller → Service → Model
            └─ Read: TRADITIONAL_ARCHITECTURE.md
```

**Decision Criteria**:
- **Agentic**: Needs AI response generation, multiple specialized agents, orchestration, NLU
- **Traditional**: Standard CRUD, business logic, integrations, non-AI features

---

## Universal Principles (Both Architectures)

### 1. Configuration Management
**All config from environment variables**:
```python
class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    REDIS_URL: str = os.getenv("REDIS_URL")
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY")
```

**Red Flags**:
- ❌ Hardcoded API keys, URLs, secrets
- ❌ Production values in code

### 2. Error Handling
**Consistent error responses**:
```python
{
    "success": false,
    "error": {
        "code": "USER_NOT_FOUND",
        "message": "User with ID 123 not found"
    }
}
```

### 3. Logging
**Structured logging everywhere**:
```python
import logging

logger.info("User created", extra={
    "user_id": user.id,
    "action": "create_user"
})
```

### 4. Security
- [ ] Validate all inputs (Pydantic schemas)
- [ ] Sanitize user data
- [ ] Use parameterized queries (prevent SQL injection)
- [ ] Implement rate limiting
- [ ] Never log sensitive data

### 5. Testing Requirements
**All features (agentic + traditional)**:
- [ ] Unit tests for business logic
- [ ] Integration tests for workflows
- [ ] All tests pass before merge
- [ ] No skipped or ignored tests without justification

---

## Documentation Index

**For detailed implementation guides**:
- **AI Features**: Read [AGENTIC_ARCHITECTURE.md](AGENTIC_ARCHITECTURE.md) for orchestrator, agents, state management
- **Standard Features**: Read [TRADITIONAL_ARCHITECTURE.md](TRADITIONAL_ARCHITECTURE.md) for routes, controllers, services, models

**This file (CONSTITUTION.md)**: Universal principles, decision framework, when to use which architecture

---