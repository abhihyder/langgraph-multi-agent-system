"""
Feedback model for storing user feedback on AI responses.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import Base


class FeedbackAction(enum.Enum):
    """Enum for feedback actions."""
    LIKE = "like"
    DISLIKE = "dislike"
    REPORT = "report"


class Feedback(Base):
    """Feedback model for storing user feedback on conversations."""
    
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    action = Column(Enum(FeedbackAction), nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="feedbacks")
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, conversation_id={self.conversation_id}, action={self.action})>"
    
    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "action": self.action.value if hasattr(self.action, 'value') else self.action,
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
        }
