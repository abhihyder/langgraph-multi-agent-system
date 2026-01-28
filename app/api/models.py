"""
Pydantic models for API request/response validation.

Defines schemas for all API endpoints with proper validation and examples.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Query Models
# ============================================================================

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
                "conversation_id": None,
                "agent_preferences": {"prefer_agents": ["code"]}
            }
        }
    )


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


# ============================================================================
# Conversation Models
# ============================================================================

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


# ============================================================================
# Feedback Models
# ============================================================================

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


# ============================================================================
# Persona Models
# ============================================================================

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


# ============================================================================
# User Models
# ============================================================================

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


# ============================================================================
# Error Models
# ============================================================================

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
