"""
Logging Middleware for Gateway
"""

import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logging middleware for API Gateway.
    
    Logs all requests and responses with timing information.
    """
    
    def __init__(self, app=None):
        """Initialize logging middleware"""
        if app is not None:
            super().__init__(app)
        self.total_requests = 0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through logging middleware.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler
        """
        self.total_requests += 1
        
        # Start timer
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client = request.client.host if request.client else "unknown"
        
        # Log request
        logger.info(
            f"Request started: {method} {path} from {client}",
            extra={
                "method": method,
                "path": path,
                "client": client,
                "query_params": query_params,
            },
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Extract status code (handle both Response objects and dicts)
            status_code = getattr(response, 'status_code', 200) if hasattr(response, 'status_code') else 200
            
            # Log response
            logger.info(
                f"Request completed: {method} {path} - "
                f"Status: {status_code} - "
                f"Duration: {duration:.3f}s",
                extra={
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration": duration,
                    "client": client,
                },
            )
            
            # Add timing header if response has headers attribute
            if hasattr(response, 'headers'):
                response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {method} {path} - "
                f"Error: {str(e)} - "
                f"Duration: {duration:.3f}s",
                extra={
                    "method": method,
                    "path": path,
                    "error": str(e),
                    "duration": duration,
                    "client": client,
                },
                exc_info=True,
            )
            
            # Re-raise exception
            raise
    
    def get_metrics(self) -> dict:
        """
        Get logging metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "total_requests": self.total_requests
        }
