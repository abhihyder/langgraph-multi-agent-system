"""
Authentication Middleware for Gateway
"""

import logging
import os
from typing import Optional
import jwt
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for API Gateway.
    
    Validates JWT tokens and sets user context.
    """
    
    # Public endpoints that don't require authentication
    PUBLIC_PATHS = [
        "/health",
        "/docs",
        "/openapi.json",
        "/auth/google/login",
        "/auth/google/callback",
    ]
    
    def __init__(self, app=None):
        """Initialize auth middleware"""
        if app is not None:
            super().__init__(app)
        self.public_paths = self.PUBLIC_PATHS.copy()
        self.total_requests = 0
        self.authenticated_requests = 0
        self.failed_auth_attempts = 0
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request through auth middleware.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler
        """
        self.total_requests += 1
        
        # Skip auth for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        # Extract and validate token
        token = self._extract_token(request)
        
        if not token:
            self.failed_auth_attempts += 1
            logger.warning(f"Missing token for {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate token and set user context
        try:
            user_id = self._verify_token(token)
            request.state.user_id = user_id
            request.state.authenticated = True
            self.authenticated_requests += 1
            logger.debug(f"Request authenticated for user: {user_id}")
            return await call_next(request)
        except HTTPException:
            self.failed_auth_attempts += 1
            raise
        except Exception as e:
            self.failed_auth_attempts += 1
            logger.error(f"Token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def _is_public_path(self, path: str) -> bool:
        """
        Check if path is public.
        
        Args:
            path: Request path
            
        Returns:
            True if public path
        """
        return any(path.startswith(public) for public in self.PUBLIC_PATHS)
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from Authorization header.
        
        Args:
            request: FastAPI request
            
        Returns:
            Token string or None
        """
        auth_header = request.headers.get("authorization", "")
        
        if auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        
        return None
    
    def _verify_token(self, token: str) -> int:
        """
        Verify JWT token and extract user ID.
        
        Args:
            token: JWT token string
            
        Returns:
            User ID
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Decode token
            secret_key = os.getenv("JWT_SECRET_KEY", "default-secret-key")
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user_id"
                )
            
            return user_id
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def get_metrics(self) -> dict:
        """
        Get authentication metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "total_requests": self.total_requests,
            "authenticated_requests": self.authenticated_requests,
            "failed_auth_attempts": self.failed_auth_attempts,
            "authentication_rate": (
                self.authenticated_requests / self.total_requests
                if self.total_requests > 0
                else 0.0
            )
        }
