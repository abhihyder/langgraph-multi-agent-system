"""
States Package - State Management for Agentic System

Contains all state definitions for the multi-agent system:
- AgentState: Main orchestrator state
- BaseAgentState: Base state for individual agent graphs
- EmailState: State for email agent graph
"""

from .agent_state import AgentState
from .base_state import BaseAgentState
from .email_state import EmailState

__all__ = [
    "AgentState",
    "BaseAgentState",
    "EmailState",
]
