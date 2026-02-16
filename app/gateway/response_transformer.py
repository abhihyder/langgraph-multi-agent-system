"""
Response Transformer

Transforms and standardizes API responses.
"""

import logging
from typing import Any, Dict
from fastapi import Response
from fastapi.responses import JSONResponse
import json

logger = logging.getLogger(__name__)


class ResponseTransformer:
    """
    Response transformation component.
    
    Features:
    - Standardize response format
    - Add common headers
    - Handle error responses
    - Metrics tracking
    """
    
    def __init__(self):
        """Initialize response transformer."""
        self.total_transformations = 0
        logger.info("Response transformer initialized")
    
    async def transform(self, response: Any) -> Response:
        """
        Transform response to standard format.
        
        Args:
            response: Response from handler
            
        Returns:
            Transformed Response object
        """
        self.total_transformations += 1
        
        # If already a Response object, add headers and return
        if isinstance(response, Response):
            self._add_common_headers(response)
            return response
        
        # If dict, wrap in standard format
        if isinstance(response, dict):
            transformed_data = self._standardize_response(response)
            json_response = JSONResponse(content=transformed_data)
            self._add_common_headers(json_response)
            return json_response
        
        # For other types, convert to JSON
        try:
            json_response = JSONResponse(content={"data": response})
            self._add_common_headers(json_response)
            return json_response
        except Exception as e:
            logger.error(f"Failed to transform response: {e}")
            return JSONResponse(
                content={"error": "Response transformation failed"},
                status_code=500,
            )
    
    def _standardize_response(self, data: Dict) -> Dict:
        """
        Standardize response format.
        
        Args:
            data: Response data
            
        Returns:
            Standardized response dictionary
        """
        # If already has standard fields, return as is
        if "success" in data or "error" in data:
            return data
        
        # Wrap in standard format
        return {
            "success": True,
            "data": data,
        }
    
    def _add_common_headers(self, response: Response) -> None:
        """
        Add common headers to response.
        
        Args:
            response: Response object to modify
        """
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Add API version header
        response.headers["X-API-Version"] = "2.0"
    
    def get_metrics(self) -> Dict:
        """
        Get transformer metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "total_transformations": self.total_transformations,
        }
    
    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        self.total_transformations = 0
