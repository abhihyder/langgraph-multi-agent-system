"""
Routes package.
Exports routers for authentication and API endpoints.
"""

from app.routes.auth import router as auth_router
from app.routes.api import router as api_router

__all__ = ["auth_router", "api_router"]
