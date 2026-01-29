"""
JWT token management and security utilities.

Handles creation and verification of JWT access tokens for session management.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import jwt
from jwt.exceptions import InvalidTokenError

from config.settings import get_settings

settings = get_settings()


def create_access_token(
    data: Dict[str, str],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data to encode (typically user ID and email)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_access_token(
        ...     data={"sub": "user_id", "email": "user@example.com"}
        ... )
        >>> # Use token in Authorization header: Bearer <token>
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()}) # type: ignore
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    
    return encoded_jwt


def verify_access_token(token: str) -> Dict[str, str]:
    """
    Verify and decode a JWT access token.
    
    Args:
        token: JWT token string to verify
        
    Returns:
        Decoded token payload
        
    Raises:
        InvalidTokenError: If token is invalid, expired, or malformed
        
    Example:
        >>> try:
        ...     payload = verify_access_token(token)
        ...     user_id = payload["sub"]
        ...     email = payload["email"]
        ... except InvalidTokenError:
        ...     # Handle invalid token
        ...     pass
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except InvalidTokenError as e:
        raise InvalidTokenError(f"Invalid token: {str(e)}")


def decode_token_without_verification(token: str) -> Optional[Dict]:
    """
    Decode a token without verifying signature (for debugging only).
    
    WARNING: Never use this for authentication in production!
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded payload or None if invalid
    """
    try:
        return jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=[settings.JWT_ALGORITHM],
        )
    except Exception:
        return None
