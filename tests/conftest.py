"""
Pytest Configuration and Shared Fixtures
"""

import os
import pytest
from typing import Generator, Dict, Any
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient

# Set testing environment
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["AUTOMEM_URL"] = "http://localhost:8001"


@pytest.fixture
def mock_automem_client():
    """Mock AutoMem client for testing."""
    client = Mock()
    
    # Mock recall method
    client.recall.return_value = [
        {
            "id": "mem1",
            "memory": {
                "content": "User works at Portonics",
                "tags": ["user_1", "conversation_1"],
            },
            "relations": []
        },
        {
            "id": "mem2",
            "memory": {
                "content": "User is a software engineer",
                "tags": ["user_1", "conversation_1"],
            },
            "relations": []
        }
    ]
    
    # Mock store_message method
    client.store_message.return_value = {"id": "stored_mem_id", "status": "success"}
    
    # Mock associate method
    client.associate.return_value = {"status": "associated"}
    
    return client


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "is_active": True,
    }


@pytest.fixture
def sample_conversation_data() -> Dict[str, Any]:
    """Sample conversation data for testing."""
    return {
        "id": 1,
        "user_id": 1,
        "title": "Test Conversation",
        "created_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing agents."""
    mock = Mock()
    mock.content = "This is a test response from the LLM"
    return mock


@pytest.fixture
def mock_orchestrator_response():
    """Mock orchestrator JSON response."""
    return {
        "intent": "Test user needs help with coding",
        "selected_agents": ["code"]
    }


@pytest.fixture
def sample_agent_state() -> Dict[str, Any]:
    """Sample agent state for testing."""
    from langchain_core.messages import HumanMessage
    
    return {
        "user_input": "Help me write a Python function",
        "messages": [HumanMessage(content="Help me write a Python function")],
        "conversation_id": 1,
        "user_id": 1,
        "intent": None,
        "general_output": None,
        "research_output": None,
        "writing_output": None,
        "code_output": None,
        "selected_agents": [],
        "final_output": None
    }


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for AutoMem API calls."""
    client = Mock()
    
    # Mock successful GET response
    get_response = Mock()
    get_response.status_code = 200
    get_response.json.return_value = {
        "results": [
            {
                "id": "mem1",
                "memory": {"content": "test memory", "tags": ["user_1"]},
                "relations": []
            }
        ],
        "vector_search": {"matched": True}
    }
    client.get.return_value = get_response
    
    # Mock successful POST response
    post_response = Mock()
    post_response.status_code = 200
    post_response.json.return_value = {"id": "new_mem_id", "status": "stored"}
    client.post.return_value = post_response
    
    return client


@pytest.fixture
def app_client() -> Generator:
    """Test client for FastAPI app."""
    from server import app
    
    with TestClient(app) as client:
        yield client


@pytest.fixture
def test_user(sample_user_data):
    """Create a test user in the database."""
    from database import SessionLocal, User
    
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == sample_user_data["email"]).first()
        
        if not user:
            # Create new user
            user = User(
                email=sample_user_data["email"],
                name="Test User",
                google_id="test_google_id_123",
                picture="https://example.com/pic.jpg"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        yield user
        
        # Cleanup after test
        db.query(User).filter(User.email == sample_user_data["email"]).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def auth_headers(test_user) -> Dict[str, str]:
    """Generate auth headers with JWT token for test user."""
    from app.utils.auth.security import create_access_token
    
    token = create_access_token(data={"sub": str(test_user.id), "email": test_user.email})
    
    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)
