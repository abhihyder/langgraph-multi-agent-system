"""
Authentication routes.
Provides endpoints for Google OAuth login flow and token management.
"""

from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.controllers.auth_controller import AuthController

router = APIRouter(prefix="/auth", tags=["authentication"])
auth_controller = AuthController()


class TokenResponse(BaseModel):
    """Response model for successful authentication."""
    access_token: str
    token_type: str
    user: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "name": "John Doe",
                    "picture": "https://example.com/photo.jpg"
                }
            }
        }


@router.get("/google/login")
async def google_login(
    redirect_uri: Optional[str] = Query(None, description="Frontend redirect URI after login")
):
    """
    Initiate Google OAuth login flow.
    
    Redirects user to Google login page.
    After successful login, Google redirects back to /auth/google/callback.
    
    Query Parameters:
        redirect_uri: Optional frontend URL to redirect to after authentication
        
    Returns:
        Redirect to Google OAuth authorization page
        
    Example:
        GET /auth/google/login?redirect_uri=http://localhost:3000/dashboard
    """
    authorization_url = await auth_controller.login(redirect_uri=redirect_uri)
    return RedirectResponse(authorization_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State parameter (contains redirect_uri)")
):
    """
    Google OAuth callback endpoint.
    
    Google redirects here after user authorizes the application.
    Exchanges authorization code for access token and creates/updates user.
    Then redirects to frontend with token and user data as query parameters.
    
    Query Parameters:
        code: Authorization code from Google (required)
        state: State parameter containing frontend redirect URI
        
    Returns:
        Redirect to frontend with token and user data
        
    Raises:
        HTTPException: 400 if authentication fails
    """
    return await auth_controller.callback(code=code, state=state)


@router.post("/logout")
async def logout():
    """
    Logout endpoint.
    
    Clears authentication cookies.
    
    Returns:
        Success message with cleared cookies
        
    Example:
        POST /auth/logout
        
        Response:
        {
            "message": "Successfully logged out"
        }
    """
    return await auth_controller.logout()
