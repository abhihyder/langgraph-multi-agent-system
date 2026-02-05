# Quick Test Reference Card

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Or use make
make test
```

## 📋 Common Commands

```bash
# Basic
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest -s                       # Show print statements
pytest -x                       # Stop on first failure

# By Marker
make test-unit                  # Unit tests only
make test-integration           # Integration tests
make test-service               # Service layer
make test-agent                 # Agent tests
make test-api                   # API tests
make test-auth                  # Auth tests

# Coverage
make test-coverage              # Terminal report
make test-html                  # HTML report → htmlcov/index.html

# Specific Tests
pytest tests/test_chat_service.py                    # File
pytest tests/test_chat_service.py::TestChatService  # Class
pytest tests/test_chat_service.py::test_function    # Function

# Using Runner
python run_tests.py all         # All tests
python run_tests.py unit        # Unit only
python run_tests.py coverage    # With coverage
```

## 📊 Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_automem_client.py   # Memory operations
├── test_chat_service.py     # Chat logic
├── test_orchestrator.py     # Routing
├── test_agents.py           # Agent behavior
├── test_api_endpoints.py    # REST APIs
└── test_auth_service.py     # Authentication
```

## 🏷️ Test Markers

```python
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.service       # Service layer
@pytest.mark.agent         # Agents
@pytest.mark.api           # API endpoints
@pytest.mark.auth          # Authentication
@pytest.mark.slow          # Slow tests
```

## 🔧 Fixtures (in conftest.py)

```python
mock_automem_client        # Mock AutoMem API
sample_user_data           # Test user
sample_conversation_data   # Test conversation
mock_llm_response          # Mock LLM
sample_agent_state         # Agent state
app_client                 # FastAPI client
auth_headers               # Auth headers
```

## ✍️ Writing Tests

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
@pytest.mark.service
class TestMyComponent:
    """Test suite description"""
    
    def test_my_function(self, mock_automem_client):
        """Test description"""
        # Arrange
        component = MyComponent()
        
        # Act
        result = component.function()
        
        # Assert
        assert result.status == "success"
```

## 🐛 Debugging

```bash
pytest --pdb               # Drop into debugger on failure
pytest -x --pdb            # Stop and debug first failure
pytest -s                  # Show print statements
pytest -vv                 # Very verbose
pytest --lf                # Run last failed
pytest --ff                # Failed first, then rest
```

## 📈 Current Status

```
✅ 50 Passing Tests
❌ 11 Need Minor Fixes
📊 82% Pass Rate
⏱️ 3.37s Execution Time
```

## 🔗 Quick Links

- Full Guide: [TESTING.md](TESTING.md)
- Summary: [TEST_SUITE_SUMMARY.md](TEST_SUITE_SUMMARY.md)
- Implementation: [TDD_IMPLEMENTATION_COMPLETE.md](TDD_IMPLEMENTATION_COMPLETE.md)

## 💡 Tips

1. **Run fast tests during development**: `make test-fast`
2. **Check coverage regularly**: `make test-html`
3. **Use markers to focus**: `pytest -m service`
4. **Debug with print**: `pytest -s`
5. **Clean artifacts**: `make clean-test`

## 🎯 Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Services  | 80%    | ✅      |
| Agents    | 70%    | ✅      |
| APIs      | 80%    | ✅      |
| Overall   | 70%    | 🎯      |

---

**Need Help?** Check [TESTING.md](TESTING.md) for detailed documentation.
