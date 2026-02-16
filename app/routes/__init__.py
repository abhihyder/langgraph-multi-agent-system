"""
Routes package.
Exports routers for authentication and API endpoints.
"""

from app.routes.auth import router as auth_router
from app.routes.api import router as api_router
from app.routes.oauth import router as oauth_router
from app.routes.email import router as email_router

__all__ = ["auth_router", "api_router", "oauth_router", "email_router"]
