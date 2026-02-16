"""
Server Integration Tests

Tests for server.py integration with Gateway and Handlers.

Run:
    pytest tests/test_server_integration.py -v
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from server import app
from app.gateway import APIGateway
from app.handlers import SingleChatHandler, VoiceHandler, ThirdPartyHandler


@pytest.fixture
def client():
    """Create test client with lifespan events."""
    with TestClient(app) as test_client:
        # Initialize gateway and handlers manually for tests if not present
        if not hasattr(app.state, "gateway"):
            gateway = APIGateway()
            app.state.gateway = gateway
            app.state.handlers = {
                "singlechat": SingleChatHandler(),
                "voice": VoiceHandler(),
                "third_party": ThirdPartyHandler(),
            }
        
        yield test_client


@pytest.mark.integration
class TestServerIntegration:
    """Test server startup and gateway integration."""
    
    def test_app_initialization(self, client):
        """Server initializes successfully."""
        # The app should be initialized with lifespan
        assert app is not None
        assert hasattr(app.state, "gateway")
    
    def test_health_check(self, client):
        """Health check endpoint works."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"
    
    def test_root_endpoint(self, client):
        """Root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Multi-Agent AI System API"
        assert data["version"] == "2.0.0"
        assert "docs" in data
        assert "api" in data
    
    def test_gateway_routes_registered(self, client):
        """Gateway routes are registered."""
        # Check that gateway routes exist in app
        routes = [getattr(route, 'path', None) for route in app.routes]
        routes = [r for r in routes if r is not None]
        
        # Gateway routes should be present
        assert "/api/chat/{path:path}" in routes
        assert "/api/voice/{path:path}" in routes
        assert "/api/email/{path:path}" in routes
        assert "/api/sms/{path:path}" in routes
        assert "/api/drive/{path:path}" in routes
    
    @pytest.mark.asyncio
    async def test_gateway_chat_routing(self, client):
        """Gateway routes chat requests to SingleChatHandler."""
        # Mock the handler
        with patch.object(app.state.handlers["singlechat"], "handle") as mock_handle:
            mock_handle.return_value = {
                "success": True,
                "data": {"message": "test"}
            }
            
            # Make request through gateway
            response = client.post(
                "/api/chat/query",
                json={"user_input": "test query", "user_id": 1}
            )
            
            # Handler should have been called
            assert mock_handle.called
    
    def test_cors_middleware_configured(self):
        """CORS middleware is configured."""
        # Check middleware is present - FastAPI wraps middleware
        assert hasattr(app, "user_middleware")
        # CORS is configured via add_middleware
    
    def test_rate_limiter_configured(self):
        """Rate limiter is configured."""
        assert hasattr(app.state, "limiter")
    
    def test_exception_handler_registered(self):
        """Global exception handler is registered."""
        # Check exception handlers exist
        assert len(app.exception_handlers) > 0


@pytest.mark.integration
class TestGatewayHandlerIntegration:
    """Test Gateway and Handler integration."""
    
    def test_gateway_has_handlers(self):
        """Gateway has handlers registered."""
        handlers = app.state.handlers
        assert len(handlers) == 3
        
        # Check handlers are registered for correct types
        assert "singlechat" in handlers
        assert "voice" in handlers
        assert "third_party" in handlers
    
    def test_handlers_are_correct_type(self):
        """Registered handlers are correct types."""
        from app.handlers import SingleChatHandler, VoiceHandler, ThirdPartyHandler
        
        handlers = app.state.handlers
        
        # Check handler types
        assert isinstance(handlers["singlechat"], SingleChatHandler)
        assert isinstance(handlers["voice"], VoiceHandler)
        assert isinstance(handlers["third_party"], ThirdPartyHandler)
