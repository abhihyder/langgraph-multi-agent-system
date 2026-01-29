"""
Query response models.
"""

from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel, Field, ConfigDict


class AgentResponse(BaseModel):
    """Response from a single agent."""
    agent: str = Field(..., description="Agent name (research/writing/code)")
    response: str = Field(..., description="Agent's response text")
    metadata: Dict = Field(default_factory=dict, description="Agent-specific metadata")


class QueryResponse(BaseModel):
    """Response model for processed query."""
    conversation_id: int = Field(..., description="Conversation identifier")
    query: str = Field(..., description="Original user query")
    response: str = Field(..., description="Final aggregated response")
    agents_used: List[str] = Field(..., description="List of agents that contributed")
    agent_responses: List[AgentResponse] = Field(
        ...,
        description="Individual agent responses"
    )
    metadata: Dict = Field(default_factory=dict, description="Processing metadata")
    created_at: datetime = Field(..., description="Response timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "query": "Write a Python function to calculate fibonacci",
                "response": "Here's a Python function...",
                "agents_used": ["orchestrator", "code", "aggregator"],
                "agent_responses": [
                    {
                        "agent": "code",
                        "response": "def fibonacci(n): ...",
                        "metadata": {"language": "python"}
                    }
                ],
                "metadata": {
                    "tokens_used": 150,
                    "processing_time": 2.5
                },
                "created_at": "2024-01-01T00:00:00"
            }
        }
    )
