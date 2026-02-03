"""
Shared State Schema for Agentic AI System

This defines the mutable state object passed between all nodes in the LangGraph.
Each agent only writes to its designated field.
"""

from typing import TypedDict, Optional, List
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    Shared state between all agents in the workflow.
    
    PostgresSaver automatically persists this entire state at each checkpoint,
    providing conversation memory without manual history management.
    
    Attributes:
        user_input: Original user query
        messages: Conversation history as LangChain messages
        conversation_id: ID of the current conversation (for database lookup)
        user_id: ID of the authenticated user
        intent: Orchestrator agent's interpretation of user intent
        general_output: Output from general agent
        research_output: Output from research agent
        writing_output: Output from writing agent
        code_output: Output from code agent
        selected_agents: List of agents selected by orchestrator
        final_output: Aggregated final response
    """
    user_input: str
    messages: List[BaseMessage]
    conversation_id: Optional[int]
    user_id: Optional[int]
    intent: Optional[str]
    
    # Agent outputs
    general_output: Optional[str]
    research_output: Optional[str]
    writing_output: Optional[str]
    code_output: Optional[str]
    
    # Control fields
    selected_agents: List[str]
    final_output: Optional[str]
