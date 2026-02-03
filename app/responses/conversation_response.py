"""
Conversation response models.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class ConversationListItem(BaseModel):
    """Summary of a conversation for list views."""
    id: int
    title: Optional[str]
    last_query: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Python Fibonacci Discussion",
                "last_query": "Can you optimize it?",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:15:00",
                "message_count": 5
            }
        }
    )


class ConversationDetail(BaseModel):
    """Detailed conversation with all messages."""
    id: int
    title: Optional[str]
    messages: List[Dict]  # List of query/response pairs
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Python Fibonacci Discussion",
                "messages": [
                    {
                        "query": "Write fibonacci function",
                        "response": "Here's the function...",
                        "timestamp": "2024-01-01T00:00:00"
                    }
                ],
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:15:00"
            }
        }
    )
