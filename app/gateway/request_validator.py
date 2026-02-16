"""
Request Validator

Validates incoming requests for security and data integrity.
"""

import logging
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status
import re

logger = logging.getLogger(__name__)


class RequestValidator:
    """
    Request validation component.
    
    Features:
    - Content-Type validation
    - Request size limits
    - Header validation
    - Path validation
    - Metrics tracking
    """
    
    def __init__(
        self,
        max_content_length: int = 10 * 1024 * 1024,  # 10 MB
        allowed_content_types: Optional[List[str]] = None,
    ):
        """
        Initialize request validator.
        
        Args:
            max_content_length: Maximum request body size in bytes
            allowed_content_types: List of allowed content types
        """
        self.max_content_length = max_content_length
        self.allowed_content_types = allowed_content_types or [
            "application/json",
            "multipart/form-data",
            "application/x-www-form-urlencoded",
            "audio/mpeg",
            "audio/wav",
            "audio/ogg",
        ]
        
        # Metrics
        self.total_validations = 0
        self.failed_validations = 0
        
        logger.info(f"Request validator initialized with max size: {max_content_length} bytes")
    
    async def validate(self, request: Request) -> None:
        """
        Validate incoming request.
        
        Args:
            request: FastAPI request
            
        Raises:
            HTTPException: If validation fails
        """
        self.total_validations += 1
        
        try:
            # Validate content length
            await self._validate_content_length(request)
            
            # Validate content type for POST/PUT/PATCH
            if request.method in ["POST", "PUT", "PATCH"]:
                await self._validate_content_type(request)
            
            # Validate headers
            await self._validate_headers(request)
            
            # Validate path
            await self._validate_path(request)
            
            logger.debug(f"Request validation passed for {request.method} {request.url.path}")
            
        except HTTPException:
            self.failed_validations += 1
            raise
    
    async def _validate_content_length(self, request: Request) -> None:
        """
        Validate request content length.
        
        Args:
            request: FastAPI request
            
        Raises:
            HTTPException: If content length exceeds limit
        """
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            logger.warning(
                f"Request content length {content_length} exceeds limit "
                f"{self.max_content_length}"
            )
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"Request body too large. Maximum size: {self.max_content_length} bytes",
            )
    
    async def _validate_content_type(self, request: Request) -> None:
        """
        Validate request content type.
        
        Args:
            request: FastAPI request
            
        Raises:
            HTTPException: If content type not allowed
        """
        content_type = request.headers.get("content-type", "")
        
        # Extract base content type (remove parameters like charset)
        base_content_type = content_type.split(";")[0].strip()
        
        # Check if content type is allowed (exact match or starts with for multipart)
        is_allowed = any(
            base_content_type == allowed or base_content_type.startswith(allowed)
            for allowed in self.allowed_content_types
        )
        
        if not is_allowed and content_type:
            logger.warning(f"Invalid content type: {content_type}")
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported content type: {content_type}. "
                f"Allowed: {', '.join(self.allowed_content_types)}",
            )
    
    async def _validate_headers(self, request: Request) -> None:
        """
        Validate required headers.
        
        Args:
            request: FastAPI request
            
        Raises:
            HTTPException: If required headers missing
        """
        # Check for suspicious headers (basic security)
        suspicious_patterns = [
            r"<script",
            r"javascript:",
            r"onerror=",
            r"onclick=",
        ]
        
        for header_name, header_value in request.headers.items():
            for pattern in suspicious_patterns:
                if re.search(pattern, header_value, re.IGNORECASE):
                    logger.warning(f"Suspicious header detected: {header_name}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid header value detected",
                    )
    
    async def _validate_path(self, request: Request) -> None:
        """
        Validate request path for security.
        
        Args:
            request: FastAPI request
            
        Raises:
            HTTPException: If path contains suspicious patterns
        """
        path = str(request.url.path)
        
        # Check for path traversal attempts
        if ".." in path or "~" in path:
            logger.warning(f"Path traversal attempt detected: {path}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid path",
            )
        
        # Check for SQL injection patterns
        sql_patterns = [
            r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)",
            r"(\bOR\b.*=.*\b|\bAND\b.*=.*\b)",
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                logger.warning(f"SQL injection attempt detected in path: {path}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request path",
                )
    
    def get_metrics(self) -> Dict:
        """
        Get validator metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "total_validations": self.total_validations,
            "failed_validations": self.failed_validations,
            "failure_rate": (
                self.failed_validations / self.total_validations
                if self.total_validations > 0
                else 0
            ),
        }
    
    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        self.total_validations = 0
        self.failed_validations = 0
