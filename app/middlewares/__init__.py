"""
Middleware components
"""

from .cors_middleware import setup_cors
from .error_middleware import setup_error_handlers

__all__ = ['setup_cors', 'setup_error_handlers']
