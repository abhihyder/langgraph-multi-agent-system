"""
Tests for API Gateway Components

Test Coverage:
- APIGateway routing logic
- RateLimiter functionality
- RequestValidator security checks
- ResponseTransformer formatting
- LoadBalancer strategies
- Middleware integration
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request, HTTPException, Response
from fastapi.responses import JSONResponse

from app.gateway.gateway import APIGateway
from app.gateway.rate_limiter import RateLimiter
from app.gateway.request_validator import RequestValidator
from app.gateway.response_transformer import ResponseTransformer
from app.gateway.load_balancer import LoadBalancer, Backend, LoadBalancingStrategy


@pytest.mark.unit
@pytest.mark.gateway
class TestAPIGateway:
    """Test suite for APIGateway"""
    
    def test_gateway_initialization(self):
        """Test gateway initializes with default components"""
        gateway = APIGateway()
        
        assert gateway.rate_limiter is not None
        assert gateway.request_validator is not None
        assert gateway.response_transformer is not None
        assert len(gateway.route_patterns) > 0
    
    def test_default_route_patterns(self):
        """Test default route patterns are set up correctly"""
        gateway = APIGateway()
        
        assert gateway.get_handler_type("/api/chat") == "singlechat"
        assert gateway.get_handler_type("/api/voice/transcribe") == "voice"
        assert gateway.get_handler_type("/api/email/send") == "third_party"
        assert gateway.get_handler_type("/api/sms/send") == "third_party"
        assert gateway.get_handler_type("/api/drive/upload") == "third_party"
    
    def test_register_custom_route_pattern(self):
        """Test registering custom route patterns"""
        gateway = APIGateway()
        
        gateway.register_route_pattern(r"^/api/custom/.*", "custom")
        
        assert gateway.get_handler_type("/api/custom/endpoint") == "custom"
    
    def test_get_handler_type_default(self):
        """Test default handler type for unknown routes"""
        gateway = APIGateway()
        
        # Unknown route should default to singlechat
        assert gateway.get_handler_type("/api/unknown") == "singlechat"
    
    @pytest.mark.asyncio
    async def test_process_request_success(self):
        """Test successful request processing through gateway"""
        gateway = APIGateway()
        
        # Mock request
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/chat"
        request.method = "POST"
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {"content-type": "application/json"}
        request.state = Mock()
        
        # Mock handler
        async def mock_handler(req):
            return {"message": "success"}
        
        # Process request
        response = await gateway.process_request(request, mock_handler)
        
        assert response is not None
        assert isinstance(response, Response)
    
    def test_get_metrics(self):
        """Test gateway metrics collection"""
        gateway = APIGateway()
        
        metrics = gateway.get_metrics()
        
        assert "rate_limiter" in metrics
        assert "validator" in metrics
        assert "routes_registered" in metrics
        assert metrics["routes_registered"] > 0


@pytest.mark.unit
@pytest.mark.gateway
class TestRateLimiter:
    """Test suite for RateLimiter"""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initializes correctly"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        
        assert limiter.requests_per_minute == 60
        assert limiter.burst_size == 10
        assert limiter.refill_rate == 1.0  # 60/60
    
    @pytest.mark.asyncio
    async def test_rate_limit_allows_initial_requests(self):
        """Test rate limiter allows requests within limit"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        
        # Mock request
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.state = Mock()
        
        # Should allow initial requests
        for _ in range(5):
            await limiter.check_rate_limit(request)
        
        assert limiter.total_requests == 5
        assert limiter.blocked_requests == 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_blocks_excessive_requests(self):
        """Test rate limiter blocks requests exceeding limit"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=3)
        
        # Mock request
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.state = Mock()
        
        # Consume all tokens
        for _ in range(3):
            await limiter.check_rate_limit(request)
        
        # Next request should be blocked
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check_rate_limit(request)
        
        assert exc_info.value.status_code == 429
        assert limiter.blocked_requests == 1
    
    @pytest.mark.asyncio
    async def test_rate_limit_bucket_refill(self):
        """Test token bucket refills over time"""
        limiter = RateLimiter(requests_per_minute=60, burst_size=2)
        
        # Mock request
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.state = Mock()
        
        # Consume all tokens
        await limiter.check_rate_limit(request)
        await limiter.check_rate_limit(request)
        
        # Should be blocked
        with pytest.raises(HTTPException):
            await limiter.check_rate_limit(request)
        
        # Wait for refill (1 token per second = 60 per minute)
        await asyncio.sleep(1.1)
        
        # Should now allow one more request
        await limiter.check_rate_limit(request)
    
    def test_get_bucket_key_with_user_id(self):
        """Test bucket key generation with authenticated user"""
        limiter = RateLimiter()
        
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = 123
        
        key = limiter._get_bucket_key(request)
        
        assert key == "user:123"
    
    def test_get_bucket_key_with_ip(self):
        """Test bucket key generation with IP address"""
        limiter = RateLimiter()
        
        request = Mock(spec=Request)
        request.state = Mock(spec=['user_id'])
        delattr(request.state, 'user_id')  # Remove user_id to test IP fallback
        request.client = Mock()
        request.client.host = "192.168.1.1"
        
        key = limiter._get_bucket_key(request)
        
        assert key == "ip:192.168.1.1"
    
    def test_get_metrics(self):
        """Test rate limiter metrics"""
        limiter = RateLimiter()
        limiter.total_requests = 100
        limiter.blocked_requests = 5
        
        metrics = limiter.get_metrics()
        
        assert metrics["total_requests"] == 100
        assert metrics["blocked_requests"] == 5
        assert metrics["block_rate"] == 0.05


@pytest.mark.unit
@pytest.mark.gateway
class TestRequestValidator:
    """Test suite for RequestValidator"""
    
    def test_validator_initialization(self):
        """Test validator initializes correctly"""
        validator = RequestValidator(max_content_length=1024)
        
        assert validator.max_content_length == 1024
        assert len(validator.allowed_content_types) > 0
    
    @pytest.mark.asyncio
    async def test_validate_successful_request(self):
        """Test validation passes for valid request"""
        validator = RequestValidator()
        
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/api/chat"
        request.headers = {
            "content-type": "application/json",
            "content-length": "100",
        }
        
        # Should not raise
        await validator.validate(request)
        
        assert validator.total_validations == 1
        assert validator.failed_validations == 0
    
    @pytest.mark.asyncio
    async def test_validate_content_length_exceeded(self):
        """Test validation fails for excessive content length"""
        validator = RequestValidator(max_content_length=1000)
        
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/api/chat"
        request.headers = {
            "content-type": "application/json",
            "content-length": "5000",
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await validator.validate(request)
        
        assert exc_info.value.status_code == 413
        assert validator.failed_validations == 1
    
    @pytest.mark.asyncio
    async def test_validate_invalid_content_type(self):
        """Test validation fails for invalid content type"""
        validator = RequestValidator()
        
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.url.path = "/api/chat"
        request.headers = {
            "content-type": "text/html",
            "content-length": "100",
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await validator.validate(request)
        
        assert exc_info.value.status_code == 415
    
    @pytest.mark.asyncio
    async def test_validate_path_traversal_attempt(self):
        """Test validation blocks path traversal attempts"""
        validator = RequestValidator()
        
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/../../etc/passwd"
        request.headers = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await validator.validate(request)
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_validate_sql_injection_attempt(self):
        """Test validation blocks SQL injection attempts"""
        validator = RequestValidator()
        
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/users?id=1 OR 1=1"
        request.headers = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await validator.validate(request)
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_validate_suspicious_headers(self):
        """Test validation blocks suspicious headers"""
        validator = RequestValidator()
        
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/chat"
        request.headers = {
            "X-Custom": "<script>alert('xss')</script>",
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await validator.validate(request)
        
        assert exc_info.value.status_code == 400


@pytest.mark.unit
@pytest.mark.gateway
class TestResponseTransformer:
    """Test suite for ResponseTransformer"""
    
    @pytest.mark.asyncio
    async def test_transform_dict_response(self):
        """Test transformation of dictionary response"""
        transformer = ResponseTransformer()
        
        response = await transformer.transform({"data": "test"})
        
        assert isinstance(response, JSONResponse)
        assert transformer.total_transformations == 1
    
    @pytest.mark.asyncio
    async def test_transform_adds_security_headers(self):
        """Test transformation adds security headers"""
        transformer = ResponseTransformer()
        
        response = await transformer.transform({"data": "test"})
        
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "X-API-Version" in response.headers
    
    @pytest.mark.asyncio
    async def test_transform_existing_response(self):
        """Test transformation of existing Response object"""
        transformer = ResponseTransformer()
        
        original_response = JSONResponse(content={"test": "data"})
        response = await transformer.transform(original_response)
        
        assert response is original_response
        assert "X-API-Version" in response.headers
    
    def test_standardize_response(self):
        """Test response standardization"""
        transformer = ResponseTransformer()
        
        # Test wrapping non-standard response
        result = transformer._standardize_response({"message": "hello"})
        assert result["success"] is True
        assert "data" in result
        
        # Test keeping standard response
        standard = {"success": False, "error": "test"}
        result = transformer._standardize_response(standard)
        assert result == standard


@pytest.mark.unit
@pytest.mark.gateway
class TestLoadBalancer:
    """Test suite for LoadBalancer"""
    
    def test_load_balancer_initialization(self):
        """Test load balancer initializes correctly"""
        backends = [
            Backend("localhost", 8001),
            Backend("localhost", 8002),
        ]
        lb = LoadBalancer(backends=backends)
        
        assert len(lb.backends) == 2
        assert lb.strategy == LoadBalancingStrategy.ROUND_ROBIN
    
    def test_add_backend(self):
        """Test adding backend to load balancer"""
        lb = LoadBalancer()
        backend = Backend("localhost", 8001)
        
        lb.add_backend(backend)
        
        assert len(lb.backends) == 1
        assert backend in lb.backends
    
    def test_remove_backend(self):
        """Test removing backend from load balancer"""
        backend = Backend("localhost", 8001)
        lb = LoadBalancer(backends=[backend])
        
        lb.remove_backend(backend)
        
        assert len(lb.backends) == 0
    
    def test_round_robin_strategy(self):
        """Test round-robin load balancing"""
        backends = [
            Backend("localhost", 8001),
            Backend("localhost", 8002),
            Backend("localhost", 8003),
        ]
        lb = LoadBalancer(backends=backends, strategy=LoadBalancingStrategy.ROUND_ROBIN)
        
        # Get backends in round-robin order
        b1 = lb.get_next_backend()
        b2 = lb.get_next_backend()
        b3 = lb.get_next_backend()
        b4 = lb.get_next_backend()  # Should wrap around
        
        assert b1 == backends[0]
        assert b2 == backends[1]
        assert b3 == backends[2]
        assert b4 == backends[0]
    
    def test_random_strategy(self):
        """Test random load balancing"""
        backends = [
            Backend("localhost", 8001),
            Backend("localhost", 8002),
        ]
        lb = LoadBalancer(backends=backends, strategy=LoadBalancingStrategy.RANDOM)
        
        backend = lb.get_next_backend()
        
        assert backend in backends
    
    def test_least_connections_strategy(self):
        """Test least connections load balancing"""
        backends = [
            Backend("localhost", 8001),
            Backend("localhost", 8002),
            Backend("localhost", 8003),
        ]
        backends[0].active_connections = 5
        backends[1].active_connections = 2
        backends[2].active_connections = 8
        
        lb = LoadBalancer(
            backends=backends,
            strategy=LoadBalancingStrategy.LEAST_CONNECTIONS
        )
        
        backend = lb.get_next_backend()
        
        assert backend == backends[1]  # Has least connections
    
    def test_unhealthy_backend_skipped(self):
        """Test unhealthy backends are not selected"""
        backends = [
            Backend("localhost", 8001),
            Backend("localhost", 8002),
        ]
        backends[0].is_healthy = False
        
        lb = LoadBalancer(backends=backends)
        
        backend = lb.get_next_backend()
        
        assert backend == backends[1]
    
    def test_no_healthy_backends(self):
        """Test behavior when no healthy backends available"""
        backends = [
            Backend("localhost", 8001),
            Backend("localhost", 8002),
        ]
        for b in backends:
            b.is_healthy = False
        
        lb = LoadBalancer(backends=backends)
        
        backend = lb.get_next_backend()
        
        assert backend is None
    
    def test_mark_backend_health(self):
        """Test marking backend health status"""
        backend = Backend("localhost", 8001)
        lb = LoadBalancer(backends=[backend])
        
        lb.mark_backend_health(backend, False)
        
        assert backend.is_healthy is False
    
    def test_get_metrics(self):
        """Test load balancer metrics"""
        backends = [
            Backend("localhost", 8001),
            Backend("localhost", 8002),
        ]
        backends[0].total_requests = 100
        backends[1].total_requests = 50
        backends[0].failed_requests = 5
        
        lb = LoadBalancer(backends=backends)
        
        metrics = lb.get_metrics()
        
        assert metrics["total_backends"] == 2
        assert metrics["healthy_backends"] == 2
        assert metrics["total_requests"] == 150
        assert metrics["total_failures"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
