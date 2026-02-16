"""
Base Handler Abstract Class

Defines the common interface for all request handlers.
All concrete handlers (SingleChat, Voice, ThirdParty) must inherit from this class.

Architecture:
    Gateway → Handler.handle() → Service Layer → Response
    
Responsibilities:
- Define handler interface (abstract methods)
- Common error handling patterns
- Request/response standardization
- Logging hooks

Pattern:
    class MyHandler(BaseHandler):
        async def handle(self, request: Request) -> Dict[str, Any]:
            # Implementation
            pass
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
import logging
import time

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """
    Abstract base class for all request handlers.
    
    Provides common functionality and enforces implementation of handle() method.
    """
    
    def __init__(self):
        """Initialize handler with common attributes."""
        self.name: str = self.__class__.__name__
        logger.info(f"{self.name} initialized")
    
    @abstractmethod
    async def handle(self, request: Request) -> Dict[str, Any]:
        """
        Process the request and return standardized response.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Dict containing response data with standardized format:
            {
                "success": bool,
                "data": Any,
                "error": Optional[str],
                "handler": str,
                "processing_time": float
            }
            
        Raises:
            HTTPException: For HTTP-level errors
            Exception: For internal processing errors
        """
        pass
    
    async def _execute_with_error_handling(
        self,
        request: Request,
        execution_func,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute handler logic with standardized error handling and timing.
        
        Args:
            request: FastAPI Request object
            execution_func: Async function to execute
            **kwargs: Additional arguments to pass to execution_func
            
        Returns:
            Standardized response dict
        """
        start_time = time.time()
        
        try:
            logger.info(f"{self.name} processing request", extra={
                "path": request.url.path,
                "method": request.method,
                "handler": self.name
            })
            
            # Execute the actual handler logic
            result = await execution_func(request, **kwargs)
            
            processing_time = time.time() - start_time
            
            logger.info(f"{self.name} completed successfully", extra={
                "handler": self.name,
                "processing_time": processing_time
            })
            
            return {
                "success": True,
                "data": result,
                "error": None,
                "handler": self.name,
                "processing_time": round(processing_time, 3)
            }
            
        except HTTPException as e:
            # Re-raise HTTP exceptions (auth, validation, etc.)
            processing_time = time.time() - start_time
            logger.warning(f"{self.name} HTTP exception", extra={
                "handler": self.name,
                "status_code": e.status_code,
                "detail": e.detail,
                "processing_time": processing_time
            })
            raise
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"{self.name} processing failed", extra={
                "handler": self.name,
                "error": str(e),
                "processing_time": processing_time
            }, exc_info=True)
            
            return {
                "success": False,
                "data": None,
                "error": f"{self.name} error: {str(e)}",
                "handler": self.name,
                "processing_time": round(processing_time, 3)
            }
    
    def _standardize_response(
        self,
        data: Any,
        success: bool = True,
        error: Optional[str] = None,
        processing_time: float = 0.0
    ) -> Dict[str, Any]:
        """
        Create standardized response format.
        
        Args:
            data: Response data
            success: Whether operation succeeded
            error: Error message if failed
            processing_time: Time taken to process
            
        Returns:
            Standardized response dict
        """
        return {
            "success": success,
            "data": data,
            "error": error,
            "handler": self.name,
            "processing_time": round(processing_time, 3)
        }
    
    async def validate_request(self, request: Request) -> bool:
        """
        Optional: Validate request before processing.
        Override in subclasses for custom validation.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            True if valid, raises HTTPException otherwise
            
        Raises:
            HTTPException: If validation fails
        """
        return True
    
    def get_handler_info(self) -> Dict[str, Any]:
        """
        Get information about this handler.
        
        Returns:
            Dict with handler metadata
        """
        base_name = self.__class__.__base__.__name__ if self.__class__.__base__ else "object"
        return {
            "name": self.name,
            "type": base_name,
            "module": self.__class__.__module__
        }
