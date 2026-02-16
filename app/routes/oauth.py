"""
OAuth2 Authentication Routes

Handles OAuth2 flows for third-party services:
- Gmail
- Google Drive (future)
- Other OAuth2 services (future)
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from config.settings import get_settings
from app.integrations.email import GmailService


settings = get_settings()
router = APIRouter(prefix="/auth", tags=["authentication"])


# Gmail OAuth2 configuration
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose'
]

# Client configuration (should be in environment variables)
# TODO: Move to settings and secure storage
CLIENT_CONFIG = {
    "web": {
        "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
        "client_secret": "YOUR_CLIENT_SECRET",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8000/auth/gmail/callback"]
    }
}


def create_gmail_flow(redirect_uri: str) -> Flow:
    """
    Create OAuth2 flow for Gmail authentication.
    
    Args:
        redirect_uri: Callback URL for OAuth2 flow
        
    Returns:
        Configured Flow instance
    """
    flow = Flow.from_client_config(
        client_config=CLIENT_CONFIG,
        scopes=GMAIL_SCOPES,
        redirect_uri=redirect_uri
    )
    return flow


def store_credentials(user_id: str, credentials: Credentials):
    """
    Store OAuth2 credentials securely.
    
    TODO: Implement secure credential storage
    - Store in database (encrypted)
    - Associate with user ID
    - Handle token refresh
    - Implement expiration checking
    
    Args:
        user_id: User identifier
        credentials: OAuth2 credentials to store
    """
    # For now, this is a placeholder
    # In production, store in database with encryption
    # Example:
    # credential_data = {
    #     "token": credentials.token,
    #     "refresh_token": credentials.refresh_token,
    #     "token_uri": credentials.token_uri,
    #     "client_id": credentials.client_id,
    #     "client_secret": credentials.client_secret,
    #     "scopes": credentials.scopes,
    #     "expiry": credentials.expiry.isoformat() if credentials.expiry else None
    # }
    # db.credentials.insert({"user_id": user_id, "service": "gmail", "data": encrypt(credential_data)})
    pass


def load_credentials(user_id: str) -> Optional[Credentials]:
    """
    Load OAuth2 credentials for a user.
    
    TODO: Implement credential retrieval
    - Fetch from database
    - Decrypt credentials
    - Check expiration
    - Refresh if needed
    
    Args:
        user_id: User identifier
        
    Returns:
        OAuth2 credentials if available, None otherwise
    """
    # For now, this is a placeholder
    # In production, load from database and decrypt
    # Example:
    # credential_record = db.credentials.find_one({"user_id": user_id, "service": "gmail"})
    # if credential_record:
    #     data = decrypt(credential_record["data"])
    #     return Credentials(
    #         token=data["token"],
    #         refresh_token=data["refresh_token"],
    #         token_uri=data["token_uri"],
    #         client_id=data["client_id"],
    #         client_secret=data["client_secret"],
    #         scopes=data["scopes"]
    #     )
    return None


@router.get("/gmail/login")
async def gmail_login(request: Request):
    """
    Initiate Gmail OAuth2 authentication flow.
    
    Redirects user to Google's consent screen.
    """
    try:
        # Get the redirect URI from request
        redirect_uri = str(request.url_for("gmail_callback"))
        
        # Create OAuth2 flow
        flow = create_gmail_flow(redirect_uri)
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',  # Enable refresh token
            include_granted_scopes='true',  # Incremental authorization
            prompt='consent'  # Force consent screen to get refresh token
        )
        
        # Store state in session (for CSRF protection)
        # TODO: Implement proper session management
        # request.session['oauth_state'] = state
        
        return RedirectResponse(url=authorization_url)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate OAuth2 flow: {str(e)}"
        )


@router.get("/gmail/callback")
async def gmail_callback(request: Request, code: str, state: Optional[str] = None):
    """
    Handle OAuth2 callback from Google.
    
    Exchanges authorization code for access token and stores credentials.
    
    Args:
        code: Authorization code from Google
        state: CSRF protection state (should match session state)
    """
    try:
        # Verify state for CSRF protection
        # TODO: Implement proper state verification
        # session_state = request.session.get('oauth_state')
        # if state != session_state:
        #     raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        # Get the redirect URI
        redirect_uri = str(request.url_for("gmail_callback"))
        
        # Create OAuth2 flow
        flow = create_gmail_flow(redirect_uri)
        
        # Exchange authorization code for credentials
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user ID (from session/JWT)
        # TODO: Implement proper user identification
        user_id = "default_user"  # Placeholder
        
        # Store credentials
        store_credentials(user_id, credentials)
        
        # Verify credentials work by getting user profile
        service = build('gmail', 'v1', credentials=credentials)
        profile = service.users().getProfile(userId='me').execute()
        
        return JSONResponse(
            content={
                "success": True,
                "message": "Gmail authentication successful",
                "email": profile.get("emailAddress"),
                "messages_total": profile.get("messagesTotal", 0)
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OAuth2 callback failed: {str(e)}"
        )


@router.get("/gmail/status")
async def gmail_auth_status(request: Request):
    """
    Check Gmail authentication status for current user.
    
    Returns whether user has valid Gmail credentials.
    """
    try:
        # Get user ID from session/JWT
        # TODO: Implement proper user identification
        user_id = "default_user"  # Placeholder
        
        # Check if credentials exist
        credentials = load_credentials(user_id)
        
        if credentials and credentials.valid:
            # Credentials exist and are valid
            return JSONResponse(
                content={
                    "authenticated": True,
                    "service": "gmail",
                    "scopes": credentials.scopes
                }
            )
        elif credentials and credentials.expired and credentials.refresh_token:
            # Credentials expired but can be refreshed
            # TODO: Implement automatic token refresh
            return JSONResponse(
                content={
                    "authenticated": False,
                    "message": "Credentials expired, refresh needed",
                    "can_refresh": True
                }
            )
        else:
            # No valid credentials
            return JSONResponse(
                content={
                    "authenticated": False,
                    "message": "No Gmail credentials found",
                    "login_url": "/auth/gmail/login"
                }
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check auth status: {str(e)}"
        )


@router.post("/gmail/revoke")
async def revoke_gmail_access(request: Request):
    """
    Revoke Gmail OAuth2 access for current user.
    
    Deletes stored credentials and revokes tokens with Google.
    """
    try:
        # Get user ID from session/JWT
        # TODO: Implement proper user identification
        user_id = "default_user"  # Placeholder
        
        # Load credentials
        credentials = load_credentials(user_id)
        
        if not credentials:
            return JSONResponse(
                content={
                    "success": False,
                    "message": "No credentials to revoke"
                }
            )
        
        # Revoke token with Google
        # TODO: Implement token revocation
        # import requests
        # requests.post('https://oauth2.googleapis.com/revoke',
        #     params={'token': credentials.token},
        #     headers = {'content-type': 'application/x-www-form-urlencoded'})
        
        # Delete stored credentials
        # TODO: Implement credential deletion from database
        # db.credentials.delete_one({"user_id": user_id, "service": "gmail"})
        
        return JSONResponse(
            content={
                "success": True,
                "message": "Gmail access revoked successfully"
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to revoke access: {str(e)}"
        )
