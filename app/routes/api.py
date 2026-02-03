"""
Main API routes for Multi-Agent AI System.

Provides REST endpoints for:
- Query processing (/api/query)
- Conversation management (/api/conversations)
- Feedback submission (/api/feedback)
- Persona management (/api/persona)
- User profile (/api/user)
"""

from typing import List
from fastapi import APIRouter, Depends, Query, status

from database import User
from app.utils.auth.dependencies import get_current_user
from app.controllers.query_controller import QueryController
from app.controllers.conversation_controller import ConversationController
from app.controllers.feedback_controller import FeedbackController
from app.controllers.persona_controller import PersonaController
from app.controllers.user_controller import UserController
from app.requests import QueryRequest, FeedbackRequest, PersonaUpdate
from app.responses import (
    QueryResponse,
    ConversationListItem,
    ConversationDetail,
    FeedbackResponse,
    PersonaResponse,
    UserProfile,
)

router = APIRouter(prefix="/api", tags=["api"])

# Initialize controllers
query_controller = QueryController()
conversation_controller = ConversationController()
feedback_controller = FeedbackController()
persona_controller = PersonaController()
user_controller = UserController()


# ============================================================================
# Query Processing
# ============================================================================

@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Process user query",
    description="Send a query to the multi-agent system for processing"
)
async def process_query(
    request: QueryRequest,
    user: User = Depends(get_current_user)
):
    """
    Process a user query through the multi-agent system.
    
    The query is routed to appropriate agents based on:
    - Query content and type
    - User persona preferences
    - Conversation history
    
    Agents collaborate to generate comprehensive responses.
    
    Flow: Route → Controller → Service → Orchestrator → Agents → Aggregator
    """
    result = await query_controller.process_query(
        query=request.query,
        context=request.context,
        user=user,
        conversation_id=request.conversation_id
    )
    
    return QueryResponse(**result)


# ============================================================================
# Conversation Management
# ============================================================================

@router.get(
    "/conversations",
    response_model=List[ConversationListItem],
    summary="List conversations",
    description="Get list of user's conversations with summary"
)
async def list_conversations(
    limit: int = Query(20, ge=1, le=100, description="Number of conversations to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    user: User = Depends(get_current_user)
):
    """
    List user's conversations with pagination.
    
    Returns summary information for each conversation:
    - Conversation ID and title
    - Last query preview
    - Message count
    - Timestamps
    """
    conversations = await conversation_controller.list_conversations(
        user=user,
        limit=limit,
        offset=offset
    )
    
    return [ConversationListItem(**conv) for conv in conversations]


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail,
    summary="Get conversation details",
    description="Get full conversation history with all messages"
)
async def get_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user)
):
    """
    Get detailed conversation history.
    
    Returns all messages in the conversation with:
    - Query and response pairs
    - Agent information
    - Timestamps and metadata
    """
    result = await conversation_controller.get_conversation(
        conversation_id=conversation_id,
        user=user
    )
    
    return ConversationDetail(**result)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
    description="Delete a conversation and all associated data"
)
async def delete_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user)
):
    """
    Delete a conversation.
    
    Removes conversation and all associated messages.
    This action cannot be undone.
    """
    await conversation_controller.delete_conversation(
        conversation_id=conversation_id,
        user=user
    )


# ============================================================================
# Feedback Management
# ============================================================================

@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback",
    description="Submit feedback on a response (accept/reject/regenerate)"
)
async def submit_feedback(
    request: FeedbackRequest,
    user: User = Depends(get_current_user)
):
    """
    Submit feedback on a conversation response.
    
    Actions:
    - **accept**: Mark response as helpful
    - **reject**: Mark response as unhelpful
    - **regenerate**: Request new response with preferences
    
    Feedback is used to:
    - Update user persona
    - Train supervisor learning agent
    - Improve future responses
    """
    result = await feedback_controller.submit_feedback(
        conversation_id=request.conversation_id,
        action=request.action,
        reason=request.reason,
        preferences=request.preferences,
        user=user
    )
    
    return FeedbackResponse(**result)


# ============================================================================
# Persona Management
# ============================================================================

@router.get(
    "/persona",
    response_model=PersonaResponse,
    summary="Get user persona",
    description="Get current user's persona and preferences"
)
async def get_persona(user: User = Depends(get_current_user)):
    """
    Get user's persona profile.
    
    Returns learned preferences and interaction patterns:
    - Communication style
    - Expertise level
    - Preferred agents
    - Interests and topics
    - Learning data and statistics
    """
    result = await persona_controller.get_persona(user=user)
    return PersonaResponse(**result)


@router.put(
    "/persona",
    response_model=PersonaResponse,
    summary="Update user persona",
    description="Update user preferences and persona settings"
)
async def update_persona(
    request: PersonaUpdate,
    user: User = Depends(get_current_user)
):
    """
    Update user persona preferences.
    
    Allows manual configuration of:
    - Communication style (casual/formal/technical)
    - Expertise level (beginner/intermediate/expert)
    - Preferred agents
    - Response length preferences
    - Custom preferences
    """
    result = await persona_controller.update_persona(
        user=user,
        communication_style=request.communication_style,
        preferred_response_length=request.preferred_response_length,
        custom_preferences=request.custom_preferences
    )
    
    return PersonaResponse(**result)


# ============================================================================
# User Profile
# ============================================================================

@router.get(
    "/user/profile",
    response_model=UserProfile,
    summary="Get user profile",
    description="Get current user's profile information"
)
async def get_user_profile(user: User = Depends(get_current_user)):
    """
    Get authenticated user's profile.
    
    Returns:
    - User ID and email
    - Name and profile picture
    - Account creation date
    """
    result = await user_controller.get_profile(user=user)
    return UserProfile(**result)
