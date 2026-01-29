"""
User controller.
Handles user profile requests and response formatting.
"""

from database import User


class UserController:
    """Controller for user profile operations."""
    
    async def get_profile(self, user: User) -> dict:
        """
        Get user's profile information.
        
        Args:
            user: Authenticated user
            
        Returns:
            User profile data
        """
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "created_at": user.created_at,
        }
