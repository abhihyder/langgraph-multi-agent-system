"""
Authentication controller.
Handles authentication request processing and response formatting.
"""

from typing import Optional
from urllib.parse import urlencode
import json
from fastapi.responses import RedirectResponse

from app.services.auth_service import AuthService
from config.settings import get_settings

settings = get_settings()


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
    
    async def callback(self, code: str, state: Optional[str] = None) -> RedirectResponse:
        """
        Handle Google OAuth callback.
        
        Args:
            code: Authorization code from Google
            state: State parameter containing redirect URI
            
        Returns:
            Redirect to frontend with token and user data in URL
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            auth_data = await self.auth_service.authenticate_with_google(code)
            
            # Prepare data for frontend
            token = auth_data["access_token"]
            user_data = auth_data["user"]
            
            # URL encode the user data
            user_json = json.dumps(user_data)
            
            # Build redirect URL with query parameters
            frontend_url = settings.FRONTEND_URL
            params = {
                "token": token,
                "user": user_json
            }
            redirect_url = f"{frontend_url}/login?{urlencode(params)}"
            
            return RedirectResponse(url=redirect_url)
            
        except ValueError as e:
            # On error, redirect to frontend login with error
            error_url = f"{settings.FRONTEND_URL}/login?error={str(e)}"
            return RedirectResponse(url=error_url)
    
    async def logout(self) -> dict:
        """
        Handle logout request.
        
        Returns:
            Success message
        """
        # Frontend handles cookie cleanup
        return {"message": "Successfully logged out"}
