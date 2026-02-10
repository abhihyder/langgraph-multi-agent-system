# Memory Driver System

## Overview

A Laravel-inspired configurable memory layer that enables seamless switching between different memory backends (AutoMem, PGVector, etc.) via environment configuration. This provides flexibility in choosing the right memory solution for your deployment while maintaining a consistent API.

## Architecture

```
┌─────────────────────────────────────┐
│         Memory Agents               │
│  (knowledge_agent, memory_agent)    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    get_memory_driver()              │
│    (Factory Function)                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    MemoryDriverManager              │
│    (Driver Selection & Caching)     │
└──────────────┬──────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
┌─────────────┐  ┌─────────────┐
│  AutoMem    │  │  PGVector   │
│  Driver     │  │  Driver     │
└─────────────┘  └─────────────┘
```

## Features

- **Seamless Switching**: Change memory backends via environment variable
- **Consistent API**: All drivers implement the same `BaseMemoryDriver` interface
- **Lazy Loading**: Drivers are instantiated only when needed
- **Caching**: Driver instances are cached for performance
- **Extensible**: Easy to add new custom drivers

## Available Drivers

### 1. AutoMem Driver (Default)
- **Backend**: AutoMem API service
- **Use Case**: Production deployments with AutoMem infrastructure
- **Configuration**: `MEMORY_DRIVER=automem`

### 2. PGVector Driver
- **Backend**: PostgreSQL with pgvector extension
- **Use Case**: Self-hosted deployments, full control over data
- **Configuration**: `MEMORY_DRIVER=pgvector`
- **Requirements**: PostgreSQL with pgvector, sentence-transformers

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Memory driver selection (automem | pgvector)
MEMORY_DRIVER=automem

# Database URL (required for pgvector)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### Settings

The memory driver is configured in `config/settings.py`:

```python
class Settings:
    MEMORY_DRIVER: str = os.getenv("MEMORY_DRIVER", "automem").lower()
```

## Usage

### In Application Code

```python
from app.core.memory import get_memory_driver

# Get the configured driver (singleton)
driver = get_memory_driver()

# Recall user memories
memories = driver.recall(
    user_id="user123",
    conversation_id="conv456",
    query="previous conversations",
    top_k=10,
    use_vector=True
)

# Recall global knowledge
knowledge = driver.recall_global_knowledge(
    query="company policies",
    top_k=5,
    category="policies"
)

# Store a memory
driver.store(
    user_id="user123",
    content="User said hello",
    conversation_id="conv456",
    tags=["user", "greeting"]
)

# Store global knowledge
driver.store_global_knowledge(
    content="Company policy document",
    category="policies",
    title="Remote Work Policy",
    doc_id="POL-001"
)

# Delete a memory
driver.delete(memory_id="mem123", user_id="user123")

# Health check
status = driver.health_check()
```

### Runtime Driver Switching

```python
from app.core.memory import set_memory_driver

# Explicitly switch to a different driver
driver = set_memory_driver("pgvector")
```

## Setup Instructions

### For AutoMem Driver

No additional setup required. Ensure AutoMem service is accessible.

### For PGVector Driver

1. **Install PostgreSQL with pgvector**:
   ```bash
   # PostgreSQL should already be installed
   # Install pgvector extension
   sudo apt-get install postgresql-14-pgvector
   ```

2. **Install Python dependencies**:
   ```bash
   pip install psycopg2-binary sentence-transformers
   ```

3. **Run migration** (Laravel-style):
   ```bash
   # Run all pending migrations (includes pgvector tables)
   python migrate.py
   
   # Or refresh database with all migrations
   python migrate.py fresh
   ```

4. **Set environment variable**:
   ```bash
   MEMORY_DRIVER=pgvector
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   ```

5. **Create vector indexes** (after inserting data):
   ```sql
   -- Only create these after you have some data in the tables
   CREATE INDEX idx_memories_embedding ON memories 
   USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);
   
   CREATE INDEX idx_knowledge_embedding ON global_knowledge 
   USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);
   ```

## BaseMemoryDriver Interface

All drivers must implement:

```python
class BaseMemoryDriver(ABC):
    
    @abstractmethod
    def recall(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        query: Optional[str] = None,
        top_k: int = 10,
        use_vector: bool = True,
        exclude_tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve user memories"""
        pass
    
    @abstractmethod
    def recall_global_knowledge(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve global knowledge/documentation"""
        pass
    
    @abstractmethod
    def store(
        self,
        user_id: str,
        content: str,
        conversation_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store a new memory"""
        pass
    
    @abstractmethod
    def store_global_knowledge(
        self,
        content: str,
        category: str,
        title: Optional[str] = None,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store global knowledge"""
        pass
    
    @abstractmethod
    def delete(
        self,
        memory_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Delete a specific memory"""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check driver health and connectivity"""
        pass
```

## Creating a Custom Driver

1. **Create driver class**:

```python
from app.core.memory.base import BaseMemoryDriver

class MyCustomDriver(BaseMemoryDriver):
    
    def __init__(self):
        # Initialize your backend connection
        pass
    
    def recall(self, user_id, **kwargs):
        # Implement memory retrieval
        pass
    
    def recall_global_knowledge(self, query, **kwargs):
        # Implement knowledge retrieval
        pass
    
    # ... implement other methods
```

2. **Register the driver**:

```python
from app.core.memory.manager import MemoryDriverManager
from .my_custom_driver import MyCustomDriver

MemoryDriverManager.register_driver("custom", MyCustomDriver)
```

3. **Use your driver**:

```bash
MEMORY_DRIVER=custom
```

## Testing

Run the comprehensive test suite:

```bash
# Run all memory driver tests
pytest tests/services/memory/ -v

# Run specific test files
pytest tests/services/memory/test_base.py -v
pytest tests/services/memory/test_automem_driver.py -v
pytest tests/services/memory/test_pgvector_driver.py -v
pytest tests/services/memory/test_manager.py -v
pytest tests/services/memory/test_integration.py -v

# Run with coverage
pytest tests/services/memory/ --cov=app/services/memory --cov-report=html
```

## Performance Considerations

### AutoMem Driver
- **Pros**: Optimized for distributed systems, managed infrastructure
- **Cons**: Network latency, external dependency

### PGVector Driver
- **Pros**: Local control, no external API calls, faster for self-hosted
- **Cons**: Requires PostgreSQL setup, embedding computation overhead

### Caching
- Driver instances are cached after first instantiation
- Use `MemoryDriverManager.reset_cache()` to clear cache (testing only)

## Migration Guide

### From Direct AutoMem Usage to Driver System

**Before**:
```python
from app.services.automem_client import get_default_client

automem = get_default_client()
memories = automem.recall(user_id="123", query="test")
```

**After**:
```python
from app.core.memory import get_memory_driver

driver = get_memory_driver()
memories = driver.recall(user_id="123", query="test")
```

## Troubleshooting

### Driver Not Found Error
```
ValueError: Memory driver 'xyz' not found
```
**Solution**: Check `MEMORY_DRIVER` value. Available: `automem`, `pgvector`

### PGVector Connection Failed
```
psycopg2.OperationalError: could not connect to server
```
**Solution**: Verify `DATABASE_URL` and PostgreSQL is running

### PGVector Extension Missing
```
UndefinedFunction: type "vector" does not exist
```
**Solution**: Install pgvector extension: `CREATE EXTENSION vector;`

### Embedding Model Download
```
Downloading sentence-transformers model...
```
**Note**: First-time PGVector use downloads the embedding model (~90MB). This is cached for future use.

## File Structure

```
app/services/memory/
├── __init__.py              # Public API exports
├── base.py                  # BaseMemoryDriver interface
├── automem_driver.py        # AutoMem implementation
├── pgvector_driver.py       # PGVector implementation
└── manager.py               # Driver factory and manager

tests/services/memory/
├── test_base.py             # Interface tests
├── test_automem_driver.py   # AutoMem driver tests
├── test_pgvector_driver.py  # PGVector driver tests
├── test_manager.py          # Manager/factory tests
└── test_integration.py      # End-to-end integration tests

database/migrations/
└── create_pgvector_tables.py  # PGVector schema migration
```

## Future Enhancements

- [ ] Redis driver for caching layer
- [ ] Pinecone driver for managed vector database
- [ ] Weaviate driver for advanced semantic search
- [ ] Hybrid driver (multiple backends with fallback)
- [ ] Memory replication across drivers
- [ ] Query result caching
- [ ] Batch operations for bulk inserts
- [ ] Migration tools between drivers

## Related Documentation

- [AGENTIC_ARCHITECTURE.md](../AGENTIC_ARCHITECTURE.md) - Agent system overview
- [CONSTITUTION.md](../CONSTITUTION.md) - Architecture decision framework
- [AutoMem Client](../app/services/automem_client.py) - Original AutoMem implementation
