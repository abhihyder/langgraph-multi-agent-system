"""
SingleChat Handler

Processes text-based AI chat requests by delegating to the existing agentic system.
Routes: /api/chat/*

Flow:
    Gateway → SingleChatHandler → ChatService → LangGraph (Orchestrator → Agents → Aggregator)
    
Responsibilities:
- Extract chat request data (user input, conversation context)
- Invoke existing ChatService
- Return AI-generated response
- Handle chat-specific errors
- Preserve existing chat functionality

Integration:
- Uses existing ChatService (no changes to agentic logic)
- Maintains compatibility with current chat endpoints
- Adds handler-level observability and standardization
"""

from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
import logging

from app.handlers.base_handler import BaseHandler
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)


class SingleChatHandler(BaseHandler):
    """
    Handler for text-based AI chat requests.
    
    Delegates to existing agentic system (Orchestrator → Agents → Aggregator).
    """
    
    def __init__(self):
        """Initialize with ChatService dependency."""
        super().__init__()
        self.chat_service = ChatService()
        logger.info("SingleChatHandler initialized with ChatService")
    
    async def handle(self, request: Request) -> Dict[str, Any]:
        """
        Process chat request through agentic system.
        
        Args:
            request: FastAPI Request containing chat data
            
        Returns:
            Standardized response with AI-generated content
            
        Expected request body:
            {
                "message": str,              # User message (required)
                "user_id": int,              # User ID (required)
                "conversation_id": int,      # Optional conversation ID
                "context": dict              # Optional additional context
            }
        """
        async def process_chat(req: Request) -> Dict[str, Any]:
            # Parse request body
            try:
                body = await req.json()
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid JSON body: {str(e)}"
                )
            
            # Extract required fields
            message = body.get("message")
            if not message:
                raise HTTPException(
                    status_code=400,
                    detail="Missing required field: 'message'"
                )
            
            user_id = body.get("user_id")
            if not user_id:
                raise HTTPException(
                    status_code=400,
                    detail="Missing required field: 'user_id'"
                )
            
            # Extract optional fields
            conversation_id = body.get("conversation_id")
            context = body.get("context", {})
            
            logger.info("Processing chat request", extra={
                "message_length": len(message),
                "conversation_id": conversation_id,
                "user_id": user_id,
                "has_context": bool(context)
            })
            
            # Delegate to ChatService (existing agentic system)
            try:
                response = self.chat_service.process_chat(
                    user_input=message,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    context=context
                )
                
                return {
                    "response": response.get("response", ""),
                    "conversation_id": response.get("conversation_id"),
                    "agents_used": response.get("agents_used", []),
                    "metadata": response.get("metadata", {})
                }
                
            except Exception as e:
                logger.error(f"ChatService error: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Chat processing failed: {str(e)}"
                )
        
        # Execute with standardized error handling
        return await self._execute_with_error_handling(request, process_chat)
    
    async def validate_request(self, request: Request) -> bool:
        """
        Validate chat request before processing.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            True if valid
            
        Raises:
            HTTPException: If validation fails
        """
        # Check content type
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            raise HTTPException(
                status_code=415,
                detail="Content-Type must be application/json"
            )
        
        return True
