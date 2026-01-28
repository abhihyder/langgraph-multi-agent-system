"""
SQLAlchemy ORM models for the multi-agent system.
Defines database schema with proper relationships and constraints.
"""

from datetime import datetime
from typing import Optional, Dict, List

from sqlalchemy import (
    Column, String, DateTime, Integer, Boolean, Text, 
    ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """
    User model for authentication and profile management.
    Supports Google OAuth authentication.
    """
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Google OAuth fields
    google_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    picture = Column(String(500), nullable=True)
    
    # User status
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    personas = relationship("Persona", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
    
    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login is not None else None,  # type: ignore
        }


class Persona(Base):
    """
    User-specific agent preferences and learning data.
    Each user has separate personas for different agent types.
    """
    __tablename__ = "personas"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Agent identification
    agent_type = Column(String(100), nullable=False)  # e.g., "research", "code.python"
    
    # User preferences
    tone = Column(String(50), default="professional")  # formal, casual, technical
    verbosity = Column(String(50), default="balanced")  # brief, detailed, comprehensive
    style_preferences = Column(JSONB, default=dict)
    
    # Learning metrics
    accepted_responses = Column(Integer, default=0)
    rejected_responses = Column(Integer, default=0)
    regeneration_patterns = Column(JSONB, default=dict)
    preferred_structures = Column(JSONB, default=list)
    
    # Context
    domain_knowledge = Column(JSONB, default=list)  # Areas user is expert in
    learning_goals = Column(JSONB, default=list)
    communication_style = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="personas")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'agent_type', name='uq_user_agent'),
        Index('idx_persona_user_agent', 'user_id', 'agent_type'),
    )
    
    def __repr__(self):
        return f"<Persona(user_id={self.user_id}, agent_type={self.agent_type})>"
    
    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "tone": self.tone,
            "verbosity": self.verbosity,
            "style_preferences": self.style_preferences,
            "accepted_responses": self.accepted_responses,
            "rejected_responses": self.rejected_responses,
            "last_used": self.last_used.isoformat() if self.last_used is not None else None,  # type: ignore
        }


class Conversation(Base):
    """
    Conversation history for each user interaction.
    Stores query, response, and metadata for learning and retrieval.
    """
    __tablename__ = "conversations"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Conversation data
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    
    # Agent information
    agents_used = Column(JSONB, default=list)  # List of agents that contributed
    routing_decision = Column(JSONB, default=dict)  # Orchestrator routing info
    
    # Performance metrics
    response_time_ms = Column(Integer, nullable=True)
    token_usage = Column(JSONB, default=dict)  # Input/output tokens
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    feedbacks = relationship("Feedback", back_populates="conversation", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_conversation_user_date', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id})>"
    
    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "query": self.query,
            "response": self.response,
            "agents_used": self.agents_used,
            "response_time_ms": self.response_time_ms,
            "created_at": self.created_at.isoformat(),
        }


class Feedback(Base):
    """
    User feedback on AI responses.
    Used for learning and improving agent performance.
    """
    __tablename__ = "feedbacks"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    
    # Feedback data
    action = Column(SQLEnum("accept", "reject", "regenerate", "edit", name="feedback_action"), nullable=False)
    reason = Column(Text, nullable=True)
    edits = Column(Text, nullable=True)  # Diff if user edited
    
    # Extra data
    extra_data = Column(JSONB, default=dict)  # Additional context
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="feedbacks")
    
    # Indexes
    __table_args__ = (
        Index('idx_feedback_conversation', 'conversation_id'),
        Index('idx_feedback_action', 'action'),
    )
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, action={self.action})>"
    
    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "action": self.action,
            "reason": self.reason,
            "created_at": self.created_at.isoformat(),
        }
