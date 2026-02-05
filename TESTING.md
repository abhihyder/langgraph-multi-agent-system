# Testing Guide

Comprehensive test suite for the Multi-Agent AI System using pytest.

## Overview

This project follows Test-Driven Development (TDD) principles with comprehensive test coverage across all layers:

- **Unit Tests**: Individual components (services, agents, utilities)
- **Integration Tests**: API endpoints, agent pipelines, database interactions
- **Mocked Dependencies**: External services (OpenAI, AutoMem, Google OAuth)

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures and configuration
├── test_automem_client.py      # AutoMem HTTP client tests
├── test_chat_service.py        # Chat service logic tests
├── test_orchestrator.py        # Orchestrator routing tests
├── test_agents.py              # Agent node tests (general, research, writing, code)
├── test_api_endpoints.py       # REST API endpoint tests
└── test_auth_service.py        # Authentication service tests
```

## Installation

Install test dependencies:

```bash
pip install -r requirements.txt
```

Required test packages:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Enhanced mocking
- `pytest-env` - Environment variable management
- `faker` - Test data generation

## Quick Reference

### Common Test Commands

```bash
# Basic
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest -s                       # Show print statements
pytest -x                       # Stop on first failure
pytest --tb=short               # Shorter traceback

# By Marker
pytest -m unit                  # Unit tests only
pytest -m integration           # Integration tests
pytest -m api                   # API endpoint tests
pytest -m auth                  # Authentication tests
pytest -m agent                 # Agent tests

# Coverage
pytest --cov=app --cov-report=html    # HTML report
pytest --cov=app --cov-report=term    # Terminal report
make test-coverage                     # Using Makefile

# Specific Tests
pytest tests/test_chat_service.py                    # Single file
pytest tests/test_chat_service.py::TestChatService  # Single class
pytest tests/test_api_endpoints.py::test_query      # Single test

# Using Test Runner
python run_tests.py all         # All tests
python run_tests.py unit        # Unit only
python run_tests.py coverage    # With coverage
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Service layer tests
pytest -m service

# Agent tests
pytest -m agent

# API tests
pytest -m api

# Auth tests
pytest -m auth
```

### Run Specific Test Files

```bash
# Test AutoMem client
pytest tests/test_automem_client.py

# Test chat service
pytest tests/test_chat_service.py

# Test API endpoints
pytest tests/test_api_endpoints.py
```

### Run Specific Test Functions

```bash
# Run single test
pytest tests/test_automem_client.py::TestAutoMemClient::test_recall_with_conversation_id

# Run all tests in a class
pytest tests/test_chat_service.py::TestChatService
```

### Verbose Output

```bash
# Show detailed output
pytest -v

# Show even more detail
pytest -vv

# Show print statements
pytest -s
```

## Coverage Reports

### Generate Coverage Report

```bash
# Terminal report
pytest --cov=app --cov-report=term-missing

# HTML report (detailed)
pytest --cov=app --cov-report=html

# View HTML report
open htmlcov/index.html  # Mac/Linux
# or
start htmlcov/index.html  # Windows
```

### Coverage Requirements

The test suite enforces minimum 70% code coverage (configured in `pytest.ini`).

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests across components
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.service` - Service layer tests
- `@pytest.mark.agent` - Agent-specific tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.auth` - Authentication tests

### List All Markers

```bash
pytest --markers
```

## Fixtures

Common fixtures available in `conftest.py`:

- `mock_automem_client` - Mock AutoMem client with predefined responses
- `sample_user_data` - Test user data
- `sample_conversation_data` - Test conversation data
- `mock_llm_response` - Mock LLM responses
- `sample_agent_state` - Sample agent state for testing
- `app_client` - FastAPI test client
- `auth_headers` - Authentication headers for API tests

## Writing Tests

### Example Unit Test

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
@pytest.mark.service
class TestMyService:
    """Test suite for MyService"""
    
    def test_my_function(self, mock_automem_client):
        """Test description"""
        # Arrange
        service = MyService()
        
        # Act
        result = service.my_function()
        
        # Assert
        assert result is not None
```

### Example Integration Test

```python
@pytest.mark.integration
@pytest.mark.api
def test_api_endpoint(app_client, auth_headers):
    """Test API endpoint integration"""
    response = app_client.post(
        "/api/query",
        json={"query": "test"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
```

## Continuous Integration

Tests run automatically on:
- Pull requests
- Merges to main branch
- Scheduled daily runs

### CI Configuration

The CI pipeline:
1. Installs dependencies
2. Runs linting (flake8)
3. Runs full test suite
4. Generates coverage report
5. Fails if coverage < 70%

## Best Practices

### 1. Test Naming

- Test files: `test_<module_name>.py`
- Test classes: `Test<ComponentName>`
- Test functions: `test_<behavior_being_tested>`

### 2. Test Structure (AAA Pattern)

```python
def test_example():
    # Arrange - Set up test data and mocks
    service = MyService()
    mock_data = {"key": "value"}
    
    # Act - Execute the code being tested
    result = service.process(mock_data)
    
    # Assert - Verify the results
    assert result["status"] == "success"
```

### 3. Mock External Dependencies

Always mock:
- OpenAI API calls
- AutoMem HTTP requests
- Database queries (use in-memory SQLite)
- Google OAuth flows

### 4. Isolation

- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order

### 5. Coverage Goals

- Aim for 80%+ coverage
- Focus on critical paths
- Test edge cases and error handling

## Debugging Tests

### Run with Debugger

```bash
# Use pytest debugger
pytest --pdb

# Drop into debugger on first failure
pytest -x --pdb
```

### Show Print Statements

```bash
pytest -s
```

### Increase Verbosity

```bash
pytest -vv
```

## Performance

### Run Tests in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run with 4 workers
pytest -n 4
```

### Skip Slow Tests

```bash
# Skip tests marked as slow
pytest -m "not slow"
```

## Test Data

Test data is generated using:
- **Fixtures** in `conftest.py`
- **Faker** library for realistic data
- **Predefined constants** for deterministic tests

## Troubleshooting

### Tests Fail Locally but Pass in CI

Check environment variables:
```bash
# View test environment
pytest --co -v
```

### Import Errors

Ensure you're running from project root:
```bash
cd /home/abhi/Projects/Portonics/AI-Based/multi-agent
pytest
```

### Database Errors

Tests use in-memory SQLite by default. If you see database errors:
```bash
# Clean test database
rm test.db
```

### Coverage Not Accurate

Regenerate coverage:
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

## Quick Reference

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific marker
pytest -m unit

# Run specific file
pytest tests/test_chat_service.py

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Generate HTML coverage report
pytest --cov=app --cov-report=html
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/mark.html)
- [Coverage.py](https://coverage.readthedocs.io/)
