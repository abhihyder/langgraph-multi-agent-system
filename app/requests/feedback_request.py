"""
Feedback request model.
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class FeedbackRequest(BaseModel):
    """Request model for submitting feedback."""
    conversation_id: int = Field(..., description="Conversation to provide feedback on")
    action: str = Field(
        ...,
        pattern="^(accept|reject|regenerate)$",
        description="Feedback action: accept, reject, or regenerate"
    )
    reason: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional explanation for feedback"
    )
    preferences: Optional[Dict] = Field(
        None,
        description="Preferences for regeneration (if action=regenerate)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "action": "regenerate",
                "reason": "Response too technical, need simpler explanation",
                "preferences": {
                    "tone": "casual",
                    "complexity": "beginner"
                }
            }
        }
    )
