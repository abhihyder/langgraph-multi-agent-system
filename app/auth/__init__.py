"""
Authentication module for Multi-Agent AI System.

Provides Google OAuth2.0 authentication and JWT-based session management.
"""

from app.auth.oauth import get_google_oauth_url, exchange_code_for_token
from app.auth.security import create_access_token, verify_access_token
from app.auth.dependencies import get_current_user, get_optional_user
from app.auth.routes import router

__all__ = [
    "get_google_oauth_url",
    "exchange_code_for_token",
    "create_access_token",
    "verify_access_token",
    "get_current_user",
    "get_optional_user",
    "router",
]
