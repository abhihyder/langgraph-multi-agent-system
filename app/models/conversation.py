"""
Conversation model for storing chat history.
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Conversation(Base):
    """Conversation model for storing user queries and AI responses."""
    
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    agents_used = Column(JSON)  # List of agents that participated
    conversation_metadata = Column(JSON)  # Additional information about the conversation
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    feedbacks = relationship("Feedback", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, created_at={self.created_at})>"
    
    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "query": self.query,
            "response": self.response,
            "agents_used": self.agents_used,
            "conversation_metadata": self.conversation_metadata,
            "created_at": self.created_at.isoformat(),
        }
