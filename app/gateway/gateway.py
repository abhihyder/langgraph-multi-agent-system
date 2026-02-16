"""
API Gateway - Main Router

Centralized entry point for all API requests.
Routes requests to appropriate handlers based on path and content.
"""

import logging
from typing import Callable, Dict, Optional, Pattern
import re
from fastapi import Request, Response
from fastapi.routing import APIRoute

from .rate_limiter import RateLimiter
from .request_validator import RequestValidator
from .response_transformer import ResponseTransformer

logger = logging.getLogger(__name__)


class APIGateway:
    """
    Central API Gateway for routing requests to appropriate handlers.
    
    Responsibilities:
    - Route requests based on path patterns
    - Apply rate limiting
    - Validate requests
    - Transform responses
    - Log all requests/responses
    """
    
    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        request_validator: Optional[RequestValidator] = None,
        response_transformer: Optional[ResponseTransformer] = None,
    ):
        """
        Initialize API Gateway.
        
        Args:
            rate_limiter: Rate limiting component
            request_validator: Request validation component
            response_transformer: Response transformation component
        """
        self.rate_limiter = rate_limiter or RateLimiter()
        self.request_validator = request_validator or RequestValidator()
        self.response_transformer = response_transformer or ResponseTransformer()
        
        # Route patterns mapped to handler types
        self.route_patterns: Dict[Pattern, str] = {}
        self._setup_default_routes()
        
        logger.info("API Gateway initialized")
    
    def _setup_default_routes(self) -> None:
        """Setup default route patterns."""
        self.route_patterns = {
            re.compile(r"^/api/chat.*"): "singlechat",
            re.compile(r"^/api/voice/.*"): "voice",
            re.compile(r"^/api/email/.*"): "third_party",
            re.compile(r"^/api/sms/.*"): "third_party",
            re.compile(r"^/api/drive/.*"): "third_party",
            re.compile(r"^/api/query.*"): "singlechat",
        }
    
    def register_route_pattern(self, pattern: str, handler_type: str) -> None:
        """
        Register a new route pattern.
        
        Args:
            pattern: Regex pattern for route matching
            handler_type: Type of handler to route to
        """
        self.route_patterns[re.compile(pattern)] = handler_type
        logger.info(f"Registered route pattern: {pattern} -> {handler_type}")
    
    def get_handler_type(self, path: str) -> str:
        """
        Determine handler type based on request path.
        
        Args:
            path: Request path
            
        Returns:
            Handler type (singlechat, voice, third_party)
        """
        for pattern, handler_type in self.route_patterns.items():
            if pattern.match(path):
                return handler_type
        
        # Default to singlechat for backward compatibility
        return "singlechat"
    
    async def process_request(
        self,
        request: Request,
        handler: Callable,
    ) -> Response:
        """
        Process incoming request through gateway pipeline.
        
        Pipeline:
        1. Rate limiting
        2. Request validation
        3. Handler execution
        4. Response transformation
        
        Args:
            request: FastAPI request
            handler: Handler function to execute
            
        Returns:
            Transformed response
            
        Raises:
            HTTPException: For rate limit, validation, or handler errors
        """
        # Step 1: Rate limiting
        await self.rate_limiter.check_rate_limit(request)
        
        # Step 2: Request validation
        await self.request_validator.validate(request)
        
        # Step 3: Determine handler type
        handler_type = self.get_handler_type(request.url.path)
        logger.info(f"Routing {request.method} {request.url.path} to {handler_type} handler")
        
        # Step 4: Execute handler
        try:
            response = await handler(request)
        except Exception as e:
            logger.error(f"Handler execution failed: {e}", exc_info=True)
            raise
        
        # Step 5: Transform response
        transformed_response = await self.response_transformer.transform(response)
        
        return transformed_response
    
    def get_metrics(self) -> Dict:
        """
        Get gateway metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "rate_limiter": self.rate_limiter.get_metrics(),
            "validator": self.request_validator.get_metrics(),
            "routes_registered": len(self.route_patterns),
        }
