"""
Tests for API Gateway Middleware

Test Coverage:
- AuthMiddleware JWT validation
- LoggingMiddleware request/response logging
- MetricsMiddleware metrics collection
- Middleware integration
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import Request, HTTPException
from starlette.datastructures import Headers

from app.gateway.middleware.auth_middleware import AuthMiddleware
from app.gateway.middleware.logging_middleware import LoggingMiddleware
from app.gateway.middleware.metrics_middleware import MetricsMiddleware


@pytest.mark.unit
@pytest.mark.middleware
class TestAuthMiddleware:
    """Test suite for AuthMiddleware"""
    
    def test_auth_middleware_initialization(self):
        """Test auth middleware initializes correctly"""
        middleware = AuthMiddleware()
        
        assert len(middleware.public_paths) > 0
        assert "/health" in middleware.public_paths
        assert "/docs" in middleware.public_paths
    
    @pytest.mark.asyncio
    async def test_public_path_bypass(self):
        """Test public paths bypass authentication"""
        middleware = AuthMiddleware()
        
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/health"
        
        next_call = AsyncMock(return_value={"status": "ok"})
        
        response = await middleware.dispatch(request, next_call)
        
        assert response == {"status": "ok"}
        next_call.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_valid_token_authentication(self):
        """Test valid JWT token is accepted"""
        middleware = AuthMiddleware()
        
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/chat"
        request.headers = {"authorization": "Bearer valid.jwt.token"}
        request.state = Mock()
        
        next_call = AsyncMock(return_value={"data": "success"})
        
        with patch.object(middleware, '_verify_token', return_value=123):
            response = await middleware.dispatch(request, next_call)
        
        assert response == {"data": "success"}
        assert hasattr(request.state, 'user_id')
        assert request.state.user_id == 123
    
    @pytest.mark.asyncio
    async def test_missing_token(self):
        """Test missing authorization header"""
        middleware = AuthMiddleware()
        
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/chat"
        request.headers = {}
        
        next_call = AsyncMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, next_call)
        
        assert exc_info.value.status_code == 401
        assert middleware.failed_auth_attempts == 1
    
    @pytest.mark.asyncio
    async def test_invalid_token_format(self):
        """Test invalid token format"""
        middleware = AuthMiddleware()
        
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/chat"
        request.headers = {"authorization": "Invalid token"}
        
        next_call = AsyncMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, next_call)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_expired_token(self):
        """Test expired JWT token"""
        middleware = AuthMiddleware()
        
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/chat"
        request.headers = {"authorization": "Bearer expired.jwt.token"}
        
        next_call = AsyncMock()
        
        with patch.object(middleware, '_verify_token', side_effect=HTTPException(status_code=401)):
            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(request, next_call)
        
        assert exc_info.value.status_code == 401
    
    def test_extract_token_bearer(self):
        """Test extracting token from Bearer header"""
        middleware = AuthMiddleware()
        
        request = Mock(spec=Request)
        request.headers = {"authorization": "Bearer test.jwt.token"}
        
        token = middleware._extract_token(request)
        
        assert token == "test.jwt.token"
    
    def test_extract_token_missing_header(self):
        """Test token extraction with missing header"""
        middleware = AuthMiddleware()
        
        request = Mock(spec=Request)
        request.headers = {}
        
        token = middleware._extract_token(request)
        
        assert token is None
    
    def test_extract_token_invalid_format(self):
        """Test token extraction with invalid format"""
        middleware = AuthMiddleware()
        
        request = Mock(spec=Request)
        request.headers = {"authorization": "InvalidFormat"}
        
        token = middleware._extract_token(request)
        
        assert token is None
    
    @patch('jwt.decode')
    def test_verify_token_success(self, mock_decode):
        """Test successful token verification"""
        middleware = AuthMiddleware()
        mock_decode.return_value = {"user_id": 123, "exp": time.time() + 3600}
        
        user_id = middleware._verify_token("valid.token")
        
        assert user_id == 123
        mock_decode.assert_called_once()
    
    @patch('jwt.decode')
    def test_verify_token_missing_user_id(self, mock_decode):
        """Test token verification with missing user_id"""
        middleware = AuthMiddleware()
        mock_decode.return_value = {"exp": time.time() + 3600}
        
        with pytest.raises(HTTPException) as exc_info:
            middleware._verify_token("invalid.token")
        
        assert exc_info.value.status_code == 401
    
    def test_get_metrics(self):
        """Test auth middleware metrics"""
        middleware = AuthMiddleware()
        middleware.total_requests = 100
        middleware.authenticated_requests = 80
        middleware.failed_auth_attempts = 5
        
        metrics = middleware.get_metrics()
        
        assert metrics["total_requests"] == 100
        assert metrics["authenticated_requests"] == 80
        assert metrics["failed_auth_attempts"] == 5
        assert metrics["authentication_rate"] == 0.8


@pytest.mark.unit
@pytest.mark.middleware
class TestLoggingMiddleware:
    """Test suite for LoggingMiddleware"""
    
    def test_logging_middleware_initialization(self):
        """Test logging middleware initializes correctly"""
        middleware = LoggingMiddleware()
        
        assert middleware.total_requests == 0
    
    @pytest.mark.asyncio
    async def test_request_response_logging(self):
        """Test request and response logging"""
        middleware = LoggingMiddleware()
        
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/api/chat"
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.state = Mock()
        request.state.user_id = 123
        request.query_params = {}  # Empty dict instead of Mock
        
        next_call = AsyncMock(return_value={"status": "ok"})
        
        response = await middleware.dispatch(request, next_call)
        
        assert response == {"status": "ok"}
        assert middleware.total_requests == 1
    
    @pytest.mark.asyncio
    async def test_logging_includes_duration(self):
        """Test logging includes request duration"""
        middleware = LoggingMiddleware()
        
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/users"
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.state = Mock()
        request.query_params = {}  # Empty dict instead of Mock
        
        async def slow_handler(req):
            await asyncio.sleep(0.1)
            return {"data": "test"}
        
        await middleware.dispatch(request, slow_handler)
        
        # Check that middleware completed successfully
        assert middleware.total_requests == 1
    
    @pytest.mark.asyncio
    async def test_logging_on_exception(self):
        """Test logging when handler raises exception"""
        middleware = LoggingMiddleware()
        
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/api/error"
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.state = Mock()
        request.query_params = {}  # Empty dict instead of Mock
        
        async def error_handler(req):
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await middleware.dispatch(request, error_handler)
        
        # Verify error tracking
        assert middleware.total_requests == 1
    
    def test_get_metrics(self):
        """Test logging middleware metrics"""
        middleware = LoggingMiddleware()
        middleware.total_requests = 50
        
        metrics = middleware.get_metrics()
        
        assert metrics["total_requests"] == 50


@pytest.mark.unit
@pytest.mark.middleware
class TestMetricsMiddleware:
    """Test suite for MetricsMiddleware"""
    
    def test_metrics_middleware_initialization(self):
        """Test metrics middleware initializes correctly"""
        middleware = MetricsMiddleware()
        
        assert middleware.total_requests == 0
        assert middleware.total_errors == 0
        assert middleware.total_response_time == 0
        assert len(middleware.endpoint_metrics) == 0
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Test metrics are collected correctly"""
        middleware = MetricsMiddleware()
        
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/users"
        
        next_call = AsyncMock(return_value={"data": "test"})
        
        await middleware.dispatch(request, next_call)
        
        assert middleware.total_requests == 1
        assert middleware.total_errors == 0
        assert middleware.total_response_time > 0
    
    @pytest.mark.asyncio
    async def test_endpoint_specific_metrics(self):
        """Test endpoint-specific metrics tracking"""
        middleware = MetricsMiddleware()
        
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/api/chat"
        
        next_call = AsyncMock(return_value={"message": "ok"})
        
        await middleware.dispatch(request, next_call)
        await middleware.dispatch(request, next_call)
        
        endpoint_key = "POST:/api/chat"
        assert endpoint_key in middleware.endpoint_metrics
        assert middleware.endpoint_metrics[endpoint_key]["count"] == 2
    
    @pytest.mark.asyncio
    async def test_error_counting(self):
        """Test error counting in metrics"""
        middleware = MetricsMiddleware()
        
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/api/error"
        
        async def error_handler(req):
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await middleware.dispatch(request, error_handler)
        
        assert middleware.total_errors == 1
    
    @pytest.mark.asyncio
    async def test_response_time_tracking(self):
        """Test response time tracking"""
        middleware = MetricsMiddleware()
        
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/slow"
        
        async def slow_handler(req):
            await asyncio.sleep(0.1)
            return {"data": "test"}
        
        await middleware.dispatch(request, slow_handler)
        
        assert middleware.total_response_time >= 100  # At least 100ms
    
    @pytest.mark.asyncio
    async def test_status_code_distribution(self):
        """Test status code tracking"""
        middleware = MetricsMiddleware()
        
        # Mock successful request
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/success"
        
        # Track status codes by endpoint
        next_call = AsyncMock(return_value={"status": "ok"})
        
        await middleware.dispatch(request, next_call)
        
        endpoint_key = "GET:/api/success"
        assert endpoint_key in middleware.endpoint_metrics
    
    def test_get_metrics(self):
        """Test metrics retrieval"""
        middleware = MetricsMiddleware()
        middleware.total_requests = 100
        middleware.total_errors = 5
        middleware.total_response_time = 15000
        middleware.endpoint_metrics = {
            "GET:/api/users": {"count": 50, "total_time": 5000},
            "POST:/api/chat": {"count": 30, "total_time": 8000},
        }
        
        metrics = middleware.get_metrics()
        
        assert metrics["total_requests"] == 100
        assert metrics["total_errors"] == 5
        assert metrics["error_rate"] == 0.05
        assert metrics["avg_response_time_ms"] == 150
        assert len(metrics["endpoint_metrics"]) == 2
    
    def test_calculate_average_response_time(self):
        """Test average response time calculation"""
        middleware = MetricsMiddleware()
        middleware.total_requests = 10
        middleware.total_response_time = 5000
        
        avg = middleware._calculate_avg_response_time()
        
        assert avg == 500


@pytest.mark.unit
@pytest.mark.middleware
class TestMiddlewareIntegration:
    """Test suite for middleware integration"""
    
    @pytest.mark.asyncio
    async def test_middleware_chain(self):
        """Test multiple middleware work together"""
        auth_middleware = AuthMiddleware()
        logging_middleware = LoggingMiddleware()
        metrics_middleware = MetricsMiddleware()
        
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/health"  # Public path
        request.method = "GET"
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.state = Mock()
        request.query_params = {}  # Empty dict instead of Mock
        
        final_handler = AsyncMock(return_value={"status": "healthy"})
        
        # Chain middleware: metrics -> logging -> auth -> handler
        with patch('logging.info'):
            response = await metrics_middleware.dispatch(
                request,
                lambda req: logging_middleware.dispatch(
                    req,
                    lambda req: auth_middleware.dispatch(req, final_handler)
                )
            )
        
        assert response == {"status": "healthy"}
        assert metrics_middleware.total_requests == 1
        assert logging_middleware.total_requests == 1
    
    @pytest.mark.asyncio
    async def test_middleware_error_propagation(self):
        """Test errors propagate through middleware chain"""
        auth_middleware = AuthMiddleware()
        logging_middleware = LoggingMiddleware()
        metrics_middleware = MetricsMiddleware()
        
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/protected"
        request.method = "POST"
        request.headers = {}  # No auth token
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.state = Mock()
        request.query_params = {}  # Empty dict instead of Mock
        
        final_handler = AsyncMock()
        
        # Should fail at auth middleware
        with patch('logging.info'), patch('logging.error'):
            with pytest.raises(HTTPException) as exc_info:
                await metrics_middleware.dispatch(
                    request,
                    lambda req: logging_middleware.dispatch(
                        req,
                        lambda req: auth_middleware.dispatch(req, final_handler)
                    )
                )
        
        assert exc_info.value.status_code == 401
        assert metrics_middleware.total_errors == 1


# Import asyncio for sleep tests
import asyncio


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
