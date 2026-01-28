"""
Authentication API routes.

Provides endpoints for Google OAuth login flow and token management.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.auth.oauth import get_google_oauth_url, exchange_code_for_token

router = APIRouter(prefix="/auth", tags=["authentication"])


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
    # Store redirect_uri in state for retrieval after callback
    state = redirect_uri if redirect_uri else "default"
    
    authorization_url = get_google_oauth_url(state=state)
    return RedirectResponse(authorization_url)


@router.get("/google/callback", response_model=TokenResponse)
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State parameter (contains redirect_uri)")
):
    """
    Google OAuth callback endpoint.
    
    Google redirects here after user authorizes the application.
    Exchanges authorization code for access token and creates/updates user.
    
    Query Parameters:
        code: Authorization code from Google (required)
        state: State parameter containing frontend redirect URI
        
    Returns:
        JWT access token and user information
        
    Raises:
        HTTPException: 400 if authentication fails
        
    Example:
        # This endpoint is called automatically by Google after user login
        # Frontend should handle the response and store the access_token
        
        Response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "user": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "name": "John Doe",
                "picture": "https://example.com/photo.jpg"
            }
        }
    """
    try:
        result = await exchange_code_for_token(code)
        
        # If frontend redirect_uri was provided in state, redirect there
        if state and state != "default":
            # For API responses, we return JSON
            # Frontend should handle redirect using the token
            pass
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/logout")
async def logout():
    """
    Logout endpoint.
    
    For JWT-based auth, logout is handled client-side by removing the token.
    This endpoint exists for consistency and can be extended for token blacklisting.
    
    Returns:
        Success message
        
    Example:
        POST /auth/logout
        Authorization: Bearer <token>
        
        Response:
        {
            "message": "Successfully logged out"
        }
    """
    # TODO: Implement token blacklisting with Redis if needed
    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user_info():
    """
    Get current user information.
    
    Requires authentication via Bearer token.
    
    Returns:
        Current user profile
        
    Example:
        GET /auth/me
        Authorization: Bearer <token>
        
        Response:
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "user@example.com",
            "name": "John Doe",
            "picture": "https://example.com/photo.jpg",
            "created_at": "2024-01-01T00:00:00"
        }
    """
    # This will be implemented using get_current_user dependency
    # See app/api/routes.py for implementation
    pass
