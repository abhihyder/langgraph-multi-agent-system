"""
Feedback controller.
Handles feedback submission requests and response formatting.
"""

from fastapi import HTTPException, status

from database import User
from app.services.feedback_service import FeedbackService
from app.services.conversation_service import ConversationService


class FeedbackController:
    """Controller for feedback operations."""
    
    def __init__(self):
        self.feedback_service = FeedbackService()
        self.conversation_service = ConversationService()
    
    async def submit_feedback(
        self,
        conversation_id: int,
        action: str,
        reason: str | None = None,
        preferences: dict | None = None,
        user: User | None = None
    ) -> dict:
        """
        Submit feedback on a conversation response.
        
        Args:
            conversation_id: ID of the conversation
            action: Feedback action (accept/reject/regenerate)
            reason: Optional reason for feedback
            preferences: Optional preferences for regeneration
            user: Authenticated user
            
        Returns:
            Feedback response with status and new response if regenerated
            
        Raises:
            HTTPException: If conversation not found
        """
        # Verify conversation exists and belongs to user
        conversation = self.conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user.id  # type: ignore
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Create feedback record
        feedback = self.feedback_service.create_feedback(
            conversation_id=conversation_id,
            action=action,
            reason=reason,
            extra_data=preferences or {}
        )
        
        # Handle regeneration
        new_response = None
        if action == "regenerate":
            # TODO: Implement regeneration with preferences
            new_response = "Regenerated response - implementation pending"
        
        # TODO: Update persona based on feedback
        # TODO: Trigger supervisor learning
        
        return {
            "feedback_id": feedback.id,
            "status": "success",
            "message": f"Feedback recorded: {action}",
            "new_response": new_response,
        }
