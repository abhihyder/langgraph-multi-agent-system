"""
Persona response model.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class PersonaResponse(BaseModel):
    """Response model for persona data."""
    id: int
    user_id: int
    communication_style: Optional[str]
    expertise_level: Optional[str]
    interests: List[str]
    preferred_agents: List[str]
    interaction_count: int
    learning_data: Dict
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "789e0123-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "communication_style": "casual",
                "expertise_level": "intermediate",
                "interests": ["python", "machine-learning"],
                "preferred_agents": ["code", "research"],
                "interaction_count": 42,
                "learning_data": {
                    "avg_query_length": 120,
                    "most_used_agent": "code",
                    "satisfaction_rate": 0.85
                },
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-15T00:00:00"
            }
        }
    )
