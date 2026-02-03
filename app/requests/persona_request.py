"""
Persona request models.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PersonaUpdate(BaseModel):
    """Request model for updating user persona preferences."""
    communication_style: Optional[str] = Field(
        None,
        description="Preferred communication style (casual/formal/technical)"
    )
    expertise_level: Optional[str] = Field(
        None,
        description="User's expertise level (beginner/intermediate/expert)"
    )
    preferred_agents: Optional[List[str]] = Field(
        None,
        description="Preferred agents for queries"
    )
    preferred_response_length: Optional[str] = Field(
        None,
        description="Preferred response length (concise/moderate/detailed)"
    )
    custom_preferences: Optional[Dict] = Field(
        None,
        description="Additional custom preferences"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "communication_style": "casual",
                "expertise_level": "intermediate",
                "preferred_agents": ["code", "research"],
                "preferred_response_length": "moderate",
                "custom_preferences": {
                    "programming_languages": ["python", "javascript"],
                    "avoid_topics": ["sports"]
                }
            }
        }
    )
