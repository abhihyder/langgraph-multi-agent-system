"""
Authentication controller.
Handles authentication request processing and response formatting.
"""

from typing import Optional
from fastapi import HTTPException, status

from app.services.auth_service import AuthService


class AuthController:
    """Controller for authentication operations."""
    
    def __init__(self):
        self.auth_service = AuthService()
    
    async def login(self, redirect_uri: Optional[str] = None) -> str:
        """
        Initiate Google OAuth login flow.
        
        Args:
            redirect_uri: Optional frontend redirect URI after login
            
        Returns:
            Google OAuth authorization URL
        """
        state = redirect_uri if redirect_uri else "default"
        return self.auth_service.get_authorization_url(state=state)
    
    async def callback(self, code: str, state: Optional[str] = None) -> dict:
        """
        Handle Google OAuth callback.
        
        Args:
            code: Authorization code from Google
            state: State parameter containing redirect URI
            
        Returns:
            Token response with access token and user info
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            return await self.auth_service.authenticate_with_google(code)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    
    async def logout(self) -> dict:
        """
        Handle logout request.
        
        Returns:
            Success message
        """
        # TODO: Implement token blacklisting if needed
        return {"message": "Successfully logged out"}
