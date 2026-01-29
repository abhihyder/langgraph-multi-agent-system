"""
Error response model.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code for programmatic handling")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Conversation not found",
                "code": "CONVERSATION_NOT_FOUND"
            }
        }
    )
