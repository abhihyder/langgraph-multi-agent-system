"""
Metrics Middleware for Gateway
"""

import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Metrics collection middleware for API Gateway.
    
    Collects metrics about requests, responses, and performance.
    """
    
    def __init__(self, app=None):
        """Initialize metrics middleware."""
        if app is not None:
            super().__init__(app)
        
        # Metrics storage
        self.total_requests = 0
        self.total_errors = 0
        self.total_response_time = 0.0  # milliseconds
        self.endpoint_metrics = {}  # {endpoint: {count, total_time}}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through metrics middleware.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler
        """
        # Start timer
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        endpoint_key = f"{method}:{path}"
        
        # Increment total request count
        self.total_requests += 1
        
        # Initialize endpoint metrics if needed
        if endpoint_key not in self.endpoint_metrics:
            self.endpoint_metrics[endpoint_key] = {"count": 0, "total_time": 0.0}
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration in milliseconds
            duration_ms = (time.time() - start_time) * 1000
            
            # Update metrics
            self.total_response_time += duration_ms
            self.endpoint_metrics[endpoint_key]["count"] += 1
            self.endpoint_metrics[endpoint_key]["total_time"] += duration_ms
            
            return response
            
        except Exception as e:
            # Calculate duration in milliseconds
            duration_ms = (time.time() - start_time) * 1000
            
            # Update error metrics
            self.total_errors += 1
            self.total_response_time += duration_ms
            self.endpoint_metrics[endpoint_key]["count"] += 1
            self.endpoint_metrics[endpoint_key]["total_time"] += duration_ms
            
            logger.error(f"Request error: {endpoint_key} - {str(e)}")
            
            # Re-raise exception
            raise
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time in milliseconds"""
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time / self.total_requests
    
    def get_metrics(self) -> dict:
        """
        Get collected metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": (
                self.total_errors / self.total_requests
                if self.total_requests > 0
                else 0.0
            ),
            "avg_response_time_ms": self._calculate_avg_response_time(),
            "endpoint_metrics": self.endpoint_metrics.copy(),
        }
