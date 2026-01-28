"""
API module for Multi-Agent AI System.

Provides REST API endpoints for query processing, conversation history,
feedback management, and persona configuration.
"""

from app.api.routes import router

__all__ = ["router"]
