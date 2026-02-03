"""
Conversation controller.
Handles conversation management requests and response formatting.
"""

from typing import List
from fastapi import HTTPException, status

from database import User
from app.services.conversation_service import ConversationService


class ConversationController:
    """Controller for conversation management operations."""
    
    def __init__(self):
        self.conversation_service = ConversationService()
    
    async def list_conversations(
        self,
        user: User,
        limit: int = 20,
        offset: int = 0
    ) -> List[dict]:
        """
        List user's conversations with pagination.
        
        Args:
            user: Authenticated user
            limit: Number of conversations to return
            offset: Pagination offset
            
        Returns:
            List of conversation summaries
        """
        conversations = self.conversation_service.get_user_conversations(
            user_id=user.id,  # type: ignore
            limit=limit,
            offset=offset
        )
        
        return [
            {
                "id": conv.id,
                "title": conv.routing_decision.get("title") if conv.routing_decision else None,
                "last_query": conv.query[:100],
                "created_at": conv.created_at,
                "updated_at": conv.created_at,
                "message_count": 1,
            }
            for conv in conversations
        ]
    
    async def get_conversation(
        self,
        conversation_id: int,
        user: User
    ) -> dict:
        """
        Get detailed conversation history.
        
        Args:
            conversation_id: ID of the conversation
            user: Authenticated user
            
        Returns:
            Conversation details with messages
            
        Raises:
            HTTPException: If conversation not found
        """
        conversation = self.conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user.id  # type: ignore
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        messages = [
            {
                "query": conversation.query,
                "response": conversation.response,
                "timestamp": conversation.created_at.isoformat(),
            }
        ]
        
        return {
            "id": conversation.id,
            "title": conversation.routing_decision.get("title") if conversation.routing_decision else None,
            "messages": messages,
            "created_at": conversation.created_at,
            "updated_at": conversation.created_at,
        }
    
    async def delete_conversation(
        self,
        conversation_id: int,
        user: User
    ) -> None:
        """
        Delete a conversation.
        
        Args:
            conversation_id: ID of the conversation
            user: Authenticated user
            
        Raises:
            HTTPException: If conversation not found
        """
        deleted = self.conversation_service.delete_conversation(
            conversation_id=conversation_id,
            user_id=user.id  # type: ignore
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
