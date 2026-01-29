"""
Query controller.
Handles query processing requests and response formatting.
"""

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
        user: User
    ) -> dict:
        """
        Process user query through multi-agent system.
        
        Args:
            query: User's query text
            context: Additional context for processing
            user: Authenticated user
            
        Returns:
            Query response with conversation details
        """
        # Process query through agents
        agent_result = self.chat_service.process_chat(
            user_input=query,
            context=context
        )
        
        # Save conversation
        conversation = self.conversation_service.create_conversation(
            user_id=user.id,  # type: ignore
            query=query,
            response=agent_result["response"],
            agents_used=agent_result.get("agents_used", []),
        )
        
        return {
            "conversation_id": conversation.id,
            "query": conversation.query,
            "response": conversation.response,
            "agents_used": conversation.agents_used,
            "agent_responses": [],
            "metadata": agent_result.get("metadata", {}),
            "created_at": conversation.created_at,
        }
