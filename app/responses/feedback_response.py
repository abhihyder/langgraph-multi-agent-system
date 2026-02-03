"""
Feedback response model.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""
    feedback_id: int
    status: str
    message: str
    new_response: Optional[str] = Field(
        None,
        description="New response if action was 'regenerate'"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "feedback_id": "456e7890-e89b-12d3-a456-426614174000",
                "status": "success",
                "message": "Feedback recorded and persona updated",
                "new_response": "Let me explain in simpler terms..."
            }
        }
    )
