"""
Main API routes for Multi-Agent AI System.

Provides REST endpoints for:
- Query processing (/api/query)
- Conversation management (/api/conversations)
- Feedback submission (/api/feedback)
- Persona management (/api/persona)
- User profile (/api/user)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from database import SessionLocal, User, Conversation, Feedback, Persona
from app.auth.dependencies import get_current_user
from app.api.models import (
    QueryRequest,
    QueryResponse,
    ConversationListItem,
    ConversationDetail,
    FeedbackRequest,
    FeedbackResponse,
    PersonaUpdate,
    PersonaResponse,
    UserProfile,
    ErrorResponse,
)

router = APIRouter(prefix="/api", tags=["api"])


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
    """
    # TODO: Implement actual agent processing
    # For now, return a placeholder
    
    db = SessionLocal()
    try:
        # Create conversation record
        conversation = Conversation(
            user_id=user.id,
            query=request.query,
            response="Placeholder response - agent integration pending",
            agents_used=["orchestrator"],
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        return QueryResponse(
            conversation_id=conversation.id,  # type: ignore
            query=conversation.query,  # type: ignore
            response=conversation.response,  # type: ignore
            agents_used=conversation.agents_used,  # type: ignore
            agent_responses=[],
            metadata={},
            created_at=conversation.created_at,  # type: ignore
        )
        
    finally:
        db.close()


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
    db = SessionLocal()
    try:
        conversations = (
            db.query(Conversation)
            .filter(Conversation.user_id == user.id)
            .order_by(Conversation.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        return [
            ConversationListItem(
                id=conv.id,  # type: ignore
                title=conv.routing_decision.get("title") if conv.routing_decision is not None else None,  # type: ignore
                last_query=conv.query[:100],  # type: ignore
                created_at=conv.created_at,  # type: ignore
                updated_at=conv.created_at,  # type: ignore
                message_count=1,  # TODO: Count messages in conversation
            )
            for conv in conversations
        ]
        
    finally:
        db.close()


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
    db = SessionLocal()
    try:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id
            )
            .first()
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # TODO: Fetch all messages in conversation thread
        messages = [
            {
                "query": conversation.query,
                "response": conversation.response,
                "timestamp": conversation.created_at.isoformat(),
            }
        ]
        
        return ConversationDetail(
            id=conversation.id,  # type: ignore
            title=conversation.routing_decision.get("title") if conversation.routing_decision is not None else None,  # type: ignore
            messages=messages,
            created_at=conversation.created_at,  # type: ignore
            updated_at=conversation.created_at,  # type: ignore
        )
        
    finally:
        db.close()


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
    db = SessionLocal()
    try:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id
            )
            .first()
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        db.delete(conversation)
        db.commit()
        
    finally:
        db.close()


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
    db = SessionLocal()
    try:
        # Verify conversation exists and belongs to user
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == request.conversation_id,
                Conversation.user_id == user.id
            )
            .first()
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Create feedback record
        feedback = Feedback(
            conversation_id=request.conversation_id,
            action=request.action,
            reason=request.reason,
            extra_data=request.preferences or {},
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        # Handle regeneration
        new_response = None
        if request.action == "regenerate":
            # TODO: Regenerate response with preferences
            new_response = "Regenerated response - implementation pending"
        
        # TODO: Update persona based on feedback
        # TODO: Trigger supervisor learning
        
        return FeedbackResponse(
            feedback_id=feedback.id,  # type: ignore
            status="success",
            message=f"Feedback recorded: {request.action}",
            new_response=new_response,
        )
        
    finally:
        db.close()


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
    db = SessionLocal()
    try:
        # Get or create a default persona (using "general" agent type)
        persona = db.query(Persona).filter(
            Persona.user_id == user.id,
            Persona.agent_type == "general"
        ).first()
        
        if not persona:
            # Create default persona for new user
            persona = Persona(
                user_id=user.id,
                agent_type="general",
                tone="professional",
                verbosity="balanced",
                communication_style="formal",
            )
            db.add(persona)
            db.commit()
            db.refresh(persona)
        
        return PersonaResponse(
            id=persona.id,  # type: ignore
            user_id=persona.user_id,  # type: ignore
            communication_style=persona.communication_style or "formal",  # type: ignore
            expertise_level="intermediate",  # Default value
            interests=persona.domain_knowledge or [],  # type: ignore
            preferred_agents=[],  # Default empty list
            interaction_count=persona.accepted_responses + persona.rejected_responses,  # type: ignore
            learning_data={
                "tone": persona.tone,
                "verbosity": persona.verbosity,
                "accepted": persona.accepted_responses,
                "rejected": persona.rejected_responses,
            },
            created_at=persona.created_at,  # type: ignore
            updated_at=persona.updated_at,  # type: ignore
        )
        
    finally:
        db.close()


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
    db = SessionLocal()
    try:
        persona = db.query(Persona).filter(
            Persona.user_id == user.id,
            Persona.agent_type == "general"
        ).first()
        
        if not persona:
            persona = Persona(
                user_id=user.id,
                agent_type="general",
                tone="professional",
                verbosity="balanced",
            )
            db.add(persona)
        
        # Update fields (map API fields to database fields)
        if request.communication_style:
            persona.communication_style = request.communication_style  # type: ignore
            # Also update tone based on communication style
            tone_map = {"casual": "casual", "formal": "professional", "technical": "technical"}
            persona.tone = tone_map.get(request.communication_style, "professional")  # type: ignore
        
        if request.preferred_response_length:
            # Map response length to verbosity
            verbosity_map = {"concise": "brief", "moderate": "balanced", "detailed": "comprehensive"}
            persona.verbosity = verbosity_map.get(request.preferred_response_length, "balanced")  # type: ignore
        
        if request.custom_preferences:
            # Store custom preferences in style_preferences JSONB field
            if persona.style_preferences is None:  # type: ignore
                persona.style_preferences = {}  # type: ignore
            persona.style_preferences.update(request.custom_preferences)  # type: ignore
        
        db.commit()
        db.refresh(persona)
        
        return PersonaResponse(
            id=persona.id,  # type: ignore
            user_id=persona.user_id,  # type: ignore
            communication_style=persona.communication_style or "formal",  # type: ignore
            expertise_level="intermediate",  # Default value
            interests=persona.domain_knowledge or [],  # type: ignore
            preferred_agents=[],  # Default empty list
            interaction_count=persona.accepted_responses + persona.rejected_responses,  # type: ignore
            learning_data={
                "tone": persona.tone,
                "verbosity": persona.verbosity,
                "accepted": persona.accepted_responses,
                "rejected": persona.rejected_responses,
                "style_preferences": persona.style_preferences,
            },
            created_at=persona.created_at,  # type: ignore
            updated_at=persona.updated_at,  # type: ignore
        )
        
    finally:
        db.close()


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
    return UserProfile(
        id=user.id,  # type: ignore
        email=user.email,  # type: ignore
        name=user.name,  # type: ignore
        picture=user.picture,  # type: ignore
        created_at=user.created_at,  # type: ignore
    )
