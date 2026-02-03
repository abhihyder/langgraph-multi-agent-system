"""
Query controller.
Handles query processing requests and response formatting.
"""

from datetime import datetime
from database import User
from app.services.chat_service import ChatService
from app.services.conversation_service import ConversationService


class QueryController:
    """Controller for query processing operations."""
    
    def __init__(self):
        self.chat_service = ChatService()
        self.conversation_service = ConversationService()
    
    async def process_query(
        self, 
        query: str, 
        context: dict | None, 
        user: User,
        conversation_id: int | None = None
    ) -> dict:
        """
        Process user query through multi-agent system.
        
        Args:
            query: User's query text
            context: Additional context for processing
            user: Authenticated user
            conversation_id: Optional ID of existing conversation for context
            
        Returns:
            Query response with conversation details
        """
        # Create conversation record FIRST if this is a new conversation
        # This ensures we have a conversation_id for the checkpointer thread_id
        is_new_conversation = conversation_id is None
        created_at = datetime.utcnow()
        
        if is_new_conversation:
            # Create conversation to get an ID
            conversation = self.conversation_service.create_conversation(
                user_id=user.id,  # type: ignore
                query=query,
                response="",  # Will be updated below
                agents_used=[],
            )
            conversation_id = conversation.id  # type: ignore
            created_at = conversation.created_at  # type: ignore
        
        # Process query through agents with conversation history
        # Now conversation_id exists for both new and existing conversations
        agent_result = self.chat_service.process_chat(
            user_input=query,
            user_id=user.id,  # type: ignore
            conversation_id=conversation_id,
            context=context
        )
        
        # For new conversations, update the record with actual response
        if is_new_conversation:
            # Update the conversation we just created
            from database import SessionLocal
            db = SessionLocal()
            try:
                from database import Conversation
                conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
                if conv:
                    conv.response = agent_result["response"]
                    conv.agents_used = agent_result.get("agents_used", [])
                    db.commit()
            finally:
                db.close()
        
        return {
            "conversation_id": conversation_id,
            "query": query,
            "response": agent_result["response"],
            "agents_used": agent_result.get("agents_used", []),
            "agent_responses": [],
            "metadata": agent_result.get("metadata", {}),
            "created_at": created_at,
        }
