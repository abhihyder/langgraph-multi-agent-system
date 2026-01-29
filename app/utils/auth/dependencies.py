"""
FastAPI dependency injection for authentication.

Provides dependency functions to extract and validate current user from JWT tokens.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError

from database import SessionLocal, User
from .security import verify_access_token

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get current authenticated user.
    
    Validates JWT token and retrieves user from database.
    Raises 401 if token is invalid or user not found.
    
    Args:
        credentials: HTTP Authorization header with Bearer token
        
    Returns:
        Authenticated User object
        
    Raises:
        HTTPException: 401 if authentication fails
        
    Example:
        @app.get("/api/profile")
        async def get_profile(user: User = Depends(get_current_user)):
            return {"email": user.email, "name": user.name}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify JWT token
        token = credentials.credentials
        payload = verify_access_token(token)
        
        user_id: str|None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
    except InvalidTokenError:
        raise credentials_exception
    
    # Retrieve user from database
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None:
            raise credentials_exception
        
        return user
        
    finally:
        db.close()


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[User]:
    """
    Dependency to get current user if authenticated, None otherwise.
    
    Useful for endpoints that work for both authenticated and anonymous users.
    
    Args:
        credentials: Optional HTTP Authorization header
        
    Returns:
        User object if authenticated, None otherwise
        
    Example:
        @app.get("/api/public")
        async def public_endpoint(user: Optional[User] = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user.name}"}
            return {"message": "Hello anonymous user"}
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_access_token(token)
        
        user_id: str|None = payload.get("sub")
        if user_id is None:
            return None
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user
        finally:
            db.close()
            
    except (InvalidTokenError, Exception):
        return None


async def verify_admin_user(user: User = Depends(get_current_user)) -> User:
    """
    Dependency to verify user has admin privileges.
    
    Args:
        user: Current authenticated user
        
    Returns:
        User object if admin
        
    Raises:
        HTTPException: 403 if user is not admin
        
    Example:
        @app.delete("/api/admin/users/{user_id}")
        async def delete_user(
            user_id: str,
            admin: User = Depends(verify_admin_user)
        ):
            # Only admins can delete users
            pass
    """
    # TODO: Add is_admin field to User model
    # For now, check if user has admin metadata
    if not user.metadata.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    
    return user
