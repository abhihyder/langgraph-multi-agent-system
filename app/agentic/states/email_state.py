"""
Email State Definition

State schema specific to email agent graph operations.
Extends BaseAgentState with email-specific fields.
"""

from typing import Dict, Any, Optional
from .base_state import BaseAgentState


class EmailState(BaseAgentState):
    """
    State for email agent graph.
    Extends BaseAgentState with email-specific fields.
    
    Email-specific fields:
        action: Email action type (send, read, search, compose, reply, etc.)
        email_params: Action-specific parameters (to, subject, body, etc.)
        email_content: AI-composed email content
        gmail_response: Response from Gmail API
        gmail_credentials: OAuth2 credentials for Gmail
        email_output: Final formatted output for aggregator
    """
    # Email-specific fields
    email_params: Dict[str, Any]  # Action-specific parameters
    email_content: Optional[Dict[str, Any]]  # Composed email content
    gmail_response: Optional[Dict[str, Any]]  # Response from Gmail API
    gmail_credentials: Optional[Dict[str, Any]]  # OAuth2 credentials
    email_output: str  # Final output for aggregator


__all__ = ["EmailState"]
