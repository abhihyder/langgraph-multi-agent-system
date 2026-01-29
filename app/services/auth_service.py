"""
Authentication service.
Handles Google OAuth authentication and token management.
"""

from typing import Dict, Optional
from sqlalchemy.orm import Session
import httpx
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow

from config.settings import get_settings
from database import SessionLocal, User
from app.utils.auth.security import create_access_token

settings = get_settings()

# OAuth configuration constants
GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


class AuthService:
    """Service for authentication operations."""
    
    def _create_oauth_flow(self) -> Flow:
        """
        Create and configure Google OAuth flow.
        
        Returns:
            Configured Flow instance
        """
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                }
            },
            scopes=GOOGLE_SCOPES,
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        return flow
    
    def get_authorization_url(self, state: str = "default") -> str:
        """
        Get Google OAuth authorization URL.
        
        Args:
            state: State parameter for OAuth flow
            
        Returns:
            Google authorization URL
        """
        flow = self._create_oauth_flow()
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=state,
            prompt="consent",
        )
        return authorization_url
    
    def _verify_google_token(self, code: str) -> Dict:
        """
        Verify authorization code and extract user info from Google.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            User information from Google
            
        Raises:
            ValueError: If token verification fails
        """
        flow = self._create_oauth_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,  # type: ignore
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
        
        return {
            "google_id": id_info["sub"],
            "email": id_info["email"],
            "name": id_info.get("name", ""),
            "picture": id_info.get("picture", ""),
        }
    
    def _get_or_create_user(self, db: Session, user_info: Dict) -> User:
        """
        Get existing user or create new one.
        
        Args:
            db: Database session
            user_info: User information from Google
            
        Returns:
            User instance
        """
        user = db.query(User).filter(User.google_id == user_info["google_id"]).first()
        
        if user:
            # Update existing user
            user.email = user_info["email"]  # type: ignore
            user.name = user_info["name"]  # type: ignore
            user.picture = user_info["picture"]  # type: ignore
        else:
            # Create new user
            user = User(
                google_id=user_info["google_id"],
                email=user_info["email"],
                name=user_info["name"],
                picture=user_info["picture"],
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        return user
    
    def _generate_auth_response(self, user: User) -> Dict:
        """
        Generate authentication response with JWT token.
        
        Args:
            user: Authenticated user
            
        Returns:
            Dictionary with access token and user info
        """
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}  # type: ignore
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user.to_dict(),
        }
    
    async def authenticate_with_google(self, code: str) -> dict:
        """
        Authenticate user with Google OAuth code.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            Authentication result with token and user info
            
        Raises:
            ValueError: If authentication fails
        """
        try:
            # Step 1: Verify token with Google
            user_info = self._verify_google_token(code)
            
            # Step 2: Get or create user in database
            db = SessionLocal()
            try:
                user = self._get_or_create_user(db, user_info)
                
                # Step 3: Generate authentication response
                return self._generate_auth_response(user)
                
            finally:
                db.close()
                
        except Exception as e:
            raise ValueError(f"Failed to authenticate with Google: {str(e)}")
    
    async def get_user_info_from_google(self, access_token: str) -> Dict:
        """
        Fetch user information from Google using access token.
        
        Args:
            access_token: Google OAuth access token
            
        Returns:
            User information dictionary
            
        Raises:
            ValueError: If token is invalid or request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            
            if response.status_code != 200:
                raise ValueError("Failed to fetch user info from Google")
            
            return response.json()

