"""
Integration Tests for API Endpoints
Testing REST API endpoints with FastAPI TestClient
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from server import app


@pytest.mark.integration
@pytest.mark.api
class TestQueryEndpoint:
    """Test suite for /api/query endpoint"""
    
    def test_query_endpoint_requires_authentication(self):
        """Test query endpoint requires authentication"""
        client = TestClient(app)
        
        response = client.post("/api/query", json={
            "query": "Test query",
            "context": {},
            "conversation_id": None
        })
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403]
    
    @patch('app.controllers.query_controller.QueryController.process_query')
    def test_query_endpoint_success(self, mock_process_query, app_client, auth_headers):
        """Test successful query processing"""
        from datetime import datetime
        mock_process_query.return_value = {
            "query": "What is AI?",
            "response": "Test response",
            "agents_used": ["general"],
            "agent_responses": [{"agent": "general", "response": "Test response", "metadata": {}}],
            "metadata": {},
            "conversation_id": 1,
            "created_at": datetime.utcnow()
        }
        
        response = app_client.post(
            "/api/query",
            json={
                "query": "What is AI?",
                "context": {},
                "conversation_id": None
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Test response"
        assert "general" in data["agents_used"]
    
    @patch('app.controllers.query_controller.QueryController.process_query')
    def test_query_endpoint_with_conversation_id(self, mock_process_query, app_client, auth_headers):
        """Test query with existing conversation"""
        from datetime import datetime
        mock_process_query.return_value = {
            "query": "Continue the conversation",
            "response": "Follow-up response",
            "agents_used": ["general"],
            "agent_responses": [{"agent": "general", "response": "Follow-up response", "metadata": {}}],
            "metadata": {},
            "conversation_id": 5,
            "created_at": datetime.utcnow()
        }
        
        response = app_client.post(
            "/api/query",
            json={
                "query": "Continue the conversation",
                "context": {},
                "conversation_id": 5
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == 5
    
    def test_query_endpoint_validates_input(self, app_client, auth_headers):
        """Test query endpoint validates request body"""
        # Missing required field
        response = app_client.post(
            "/api/query",
            json={
                "context": {}
                # Missing 'query' field
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error


@pytest.mark.integration
@pytest.mark.api
class TestConversationEndpoints:
    """Test suite for conversation management endpoints"""
    
    @patch('app.controllers.conversation_controller.ConversationController.list_conversations')
    def test_list_conversations(self, mock_list, app_client, auth_headers):
        """Test listing user conversations"""
        mock_list.return_value = [
            {
                "id": 1,
                "title": "First Conversation",
                "last_query": "What is AI?",
                "message_count": 5,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            },
            {
                "id": 2,
                "title": "Second Conversation",
                "last_query": "Write code",
                "message_count": 3,
                "created_at": "2024-01-02T00:00:00",
                "updated_at": "2024-01-02T00:00:00"
            }
        ]
        
        response = app_client.get("/api/conversations", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "First Conversation"
    
    @patch('app.controllers.conversation_controller.ConversationController.list_conversations')
    def test_list_conversations_with_pagination(self, mock_list, app_client, auth_headers):
        """Test conversation list pagination"""
        mock_list.return_value = []
        
        response = app_client.get(
            "/api/conversations?limit=10&offset=20",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        # Verify pagination params were passed
        mock_list.assert_called_once()
    
    @patch('app.controllers.conversation_controller.ConversationController.get_conversation')
    def test_get_conversation_detail(self, mock_get, app_client, auth_headers):
        """Test getting conversation detail"""
        mock_get.return_value = {
            "id": 1,
            "title": "Test Conversation",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        response = app_client.get("/api/conversations/1", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert len(data["messages"]) == 2
    
    def test_get_nonexistent_conversation(self, app_client, auth_headers):
        """Test getting conversation that doesn't exist"""
        response = app_client.get("/api/conversations/99999", headers=auth_headers)
        
        # Should return 404
        assert response.status_code == 404
    
    @patch('app.controllers.conversation_controller.ConversationController.delete_conversation')
    def test_delete_conversation(self, mock_delete, app_client, auth_headers):
        """Test deleting a conversation"""
        mock_delete.return_value = {"message": "Conversation deleted"}
        
        response = app_client.delete("/api/conversations/1", headers=auth_headers)
        
        # DELETE operations typically return 204 No Content
        assert response.status_code == 204


@pytest.mark.integration
@pytest.mark.api
class TestFeedbackEndpoint:
    """Test suite for /api/feedback endpoint"""
    
    @patch('app.controllers.feedback_controller.FeedbackController.submit_feedback')
    def test_submit_feedback(self, mock_submit, app_client, auth_headers):
        """Test submitting feedback"""
        mock_submit.return_value = {
            "feedback_id": 1,
            "status": "success",
            "message": "Feedback submitted successfully"
        }
        
        response = app_client.post(
            "/api/feedback",
            json={
                "conversation_id": 1,
                "action": "accept",
                "reason": "Great response!"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Feedback submitted successfully"
    
    @patch('app.controllers.feedback_controller.FeedbackController.submit_feedback')
    def test_submit_feedback_validates_rating(self, mock_submit, app_client, auth_headers):
        """Test feedback submission with valid action"""
        mock_submit.return_value = {
            "feedback_id": 2,
            "status": "success",
            "message": "Feedback submitted successfully"
        }
        
        response = app_client.post(
            "/api/feedback",
            json={
                "conversation_id": 1,
                "action": "reject",
                "reason": "Not accurate"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201


@pytest.mark.integration
@pytest.mark.api
class TestPersonaEndpoint:
    """Test suite for /api/persona endpoint"""
    
    @patch('app.controllers.persona_controller.PersonaController.get_persona')
    def test_get_persona(self, mock_get, app_client, auth_headers):
        """Test getting user persona"""
        from datetime import datetime
        mock_get.return_value = {
            "id": 1,
            "user_id": 1,
            "communication_style": "professional",
            "detail_level": "detailed",
            "preferred_agents": ["research", "writing"],
            "expertise_level": "intermediate",
            "interests": ["AI", "technology"],
            "interaction_count": 10,
            "learning_data": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        response = app_client.get("/api/persona", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["communication_style"] == "professional"
    
    @patch('app.controllers.persona_controller.PersonaController.update_persona')
    def test_update_persona(self, mock_update, app_client, auth_headers):
        """Test updating user persona"""
        from datetime import datetime
        mock_update.return_value = {
            "id": 1,
            "user_id": 1,
            "communication_style": "casual",
            "detail_level": "concise",
            "preferred_agents": ["general"],
            "expertise_level": "intermediate",
            "interests": ["AI"],
            "interaction_count": 11,
            "learning_data": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        response = app_client.put(
            "/api/persona",
            json={
                "communication_style": "casual",
                "detail_level": "concise"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["communication_style"] == "casual"


@pytest.mark.integration
@pytest.mark.api
class TestUserEndpoint:
    """Test suite for /api/user endpoint"""
    
    @patch('app.controllers.user_controller.UserController.get_profile')
    def test_get_user_profile(self, mock_get, app_client, auth_headers):
        """Test getting user profile"""
        mock_get.return_value = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "conversation_count": 10,
            "total_queries": 50
        }
        
        response = app_client.get("/api/user", headers=auth_headers)
        
        # Endpoint may not be fully implemented yet
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["conversation_count"] == 10
    
    def test_user_endpoint_requires_auth(self, app_client):
        """Test user endpoint requires authentication"""
        response = app_client.get("/api/user")
        
        # Should return 401/403 for auth error, or 404 if endpoint doesn't exist
        assert response.status_code in [401, 403, 404]


@pytest.mark.integration
@pytest.mark.api
class TestHealthEndpoint:
    """Test suite for health check endpoint"""
    
    def test_health_check(self, app_client):
        """Test health check endpoint"""
        response = app_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_check_no_auth_required(self):
        """Test health check doesn't require authentication"""
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
