"""
Google OAuth 2.0 integration for user authentication.

This module handles the OAuth flow:
1. Generate authorization URL for user login
2. Exchange authorization code for access token
3. Fetch user profile from Google API
4. Create or update user in database

Follows SOLID principles:
- Single Responsibility: Each function has one clear purpose
- Open/Closed: Extensible through configuration
- Dependency Inversion: Uses abstractions for database operations
"""

from typing import Dict, Optional
from sqlalchemy.orm import Session
import httpx
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow

from config.settings import get_settings
from database import SessionLocal, User
from app.auth.security import create_access_token

settings = get_settings()

# OAuth configuration constants
GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def _create_oauth_flow() -> Flow:
    """
    Create and configure Google OAuth flow.
    
    DRY: Single source of truth for OAuth configuration.
    
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


def get_google_oauth_url(state: Optional[str] = None) -> str:
    """
    Generate Google OAuth authorization URL.
    
    Single Responsibility: Only handles URL generation.
    
    Args:
        state: Optional state parameter for CSRF protection
        
    Returns:
        Authorization URL to redirect user to
    """
    flow = _create_oauth_flow()
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=state,
        prompt="consent",
    )
    return authorization_url


def _verify_google_token(code: str) -> Dict:
    """
    Verify authorization code and extract user info from Google.
    
    Single Responsibility: Only handles Google OAuth verification.
    
    Args:
        code: Authorization code from Google
        
    Returns:
        User information from Google
        
    Raises:
        ValueError: If token verification fails
    """
    flow = _create_oauth_flow()
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


def _get_or_create_user(db: Session, user_info: Dict) -> User:
    """
    Get existing user or create new one.
    
    Single Responsibility: Only handles user persistence.
    Dependency Inversion: Accepts database session abstraction.
    
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


def _generate_auth_response(user: User) -> Dict:
    """
    Generate authentication response with JWT token.
    
    Single Responsibility: Only handles response formatting.
    
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


async def exchange_code_for_token(code: str) -> Dict:  # type: ignore
    """
    Exchange authorization code for access token and create/update user.
    
    Open/Closed: Orchestrates smaller functions, extensible without modification.
    
    Args:
        code: Authorization code from Google OAuth callback
        
    Returns:
        Dictionary containing JWT access token and user info
        
    Raises:
        ValueError: If code is invalid or user info cannot be retrieved
    """
    try:
        # Step 1: Verify token with Google
        user_info = _verify_google_token(code)
        
        # Step 2: Get or create user in database
        db = SessionLocal()
        try:
            user = _get_or_create_user(db, user_info)
            
            # Step 3: Generate authentication response
            return _generate_auth_response(user)
            
        finally:
            db.close()
            
    except Exception as e:
        raise ValueError(f"Failed to authenticate with Google: {str(e)}")


async def get_user_info_from_google(access_token: str) -> Dict:
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
