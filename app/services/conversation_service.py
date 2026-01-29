"""
Conversation service.
Handles conversation persistence and retrieval.
"""

from typing import List, Optional
from database import SessionLocal, Conversation


class ConversationService:
    """Service for conversation management."""
    
    def create_conversation(
        self,
        user_id: int,
        query: str,
        response: str,
        agents_used: list | None = None
    ) -> Conversation:
        """
        Create a new conversation record.
        
        Args:
            user_id: ID of the user
            query: User's query
            response: AI's response
            agents_used: List of agents that participated
            
        Returns:
            Created conversation object
        """
        db = SessionLocal()
        try:
            conversation = Conversation(
                user_id=user_id,
                query=query,
                response=response,
                agents_used=agents_used or [],
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            return conversation
        finally:
            db.close()
    
    def get_user_conversations(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[Conversation]:
        """
        Get user's conversations with pagination.
        
        Args:
            user_id: ID of the user
            limit: Number of conversations to return
            offset: Pagination offset
            
        Returns:
            List of conversations
        """
        db = SessionLocal()
        try:
            return (
                db.query(Conversation)
                .filter(Conversation.user_id == user_id)
                .order_by(Conversation.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
        finally:
            db.close()
    
    def get_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> Optional[Conversation]:
        """
        Get a specific conversation.
        
        Args:
            conversation_id: ID of the conversation
            user_id: ID of the user (for authorization)
            
        Returns:
            Conversation object or None if not found
        """
        db = SessionLocal()
        try:
            return (
                db.query(Conversation)
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id
                )
                .first()
            )
        finally:
            db.close()
    
    def delete_conversation(
        self,
        conversation_id: int,
        user_id: int
    ) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: ID of the conversation
            user_id: ID of the user (for authorization)
            
        Returns:
            True if deleted, False if not found
        """
        db = SessionLocal()
        try:
            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id
                )
                .first()
            )
            
            if not conversation:
                return False
            
            db.delete(conversation)
            db.commit()
            return True
        finally:
            db.close()
