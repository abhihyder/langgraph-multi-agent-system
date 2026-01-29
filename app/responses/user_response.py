"""
User response models.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserProfile(BaseModel):
    """User profile information."""
    id: int
    email: str
    name: str
    picture: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "name": "John Doe",
                "picture": "https://example.com/photo.jpg",
                "created_at": "2024-01-01T00:00:00"
            }
        }
    )
