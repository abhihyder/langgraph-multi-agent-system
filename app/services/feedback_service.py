"""
Feedback service.
Handles feedback persistence and processing.
"""

from database import SessionLocal, Feedback


class FeedbackService:
    """Service for feedback management."""
    
    def create_feedback(
        self,
        conversation_id: int,
        action: str,
        reason: str | None = None,
        extra_data: dict | None = None
    ) -> Feedback:
        """
        Create a feedback record.
        
        Args:
            conversation_id: ID of the conversation
            action: Feedback action (accept/reject/regenerate)
            reason: Optional reason for feedback
            extra_data: Additional data
            
        Returns:
            Created feedback object
        """
        db = SessionLocal()
        try:
            feedback = Feedback(
                conversation_id=conversation_id,
                action=action,
                reason=reason,
                extra_data=extra_data or {},
            )
            db.add(feedback)
            db.commit()
            db.refresh(feedback)
            return feedback
        finally:
            db.close()
