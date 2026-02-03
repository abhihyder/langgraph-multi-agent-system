"""
Query request model.
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class QueryRequest(BaseModel):
    """Request model for processing a user query."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User question or prompt"
    )
    conversation_id: Optional[int] = Field(
        None,
        description="Optional ID of existing conversation to continue"
    )
    context: Optional[Dict] = Field(
        None,
        description="Additional context for query processing"
    )
    conversation_id: Optional[int] = Field(
        None,
        description="Continue existing conversation (optional)"
    )
    agent_preferences: Optional[Dict] = Field(
        None,
        description="Override default agent selection preferences"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Write a Python function to calculate fibonacci numbers",
                "context": {"language": "python", "level": "beginner"},
                "conversation_id": None,
                "agent_preferences": {"prefer_agents": ["code"]}
            }
        }
    )
