"""
Shared State Schema for Agentic AI System

This defines the mutable state object passed between all nodes in the LangGraph.
Each agent only writes to its designated field.
"""

from typing import TypedDict, Optional, List


class AgentState(TypedDict):
    """
    Shared state between all agents in the workflow.
    
    Attributes:
        user_input: Original user query
        intent: Boss agent's interpretation of user intent
        research_output: Output from research agent
        writing_output: Output from writing agent
        code_output: Output from code agent
        selected_agents: List of agents selected by boss
        final_output: Aggregated final response
    """
    user_input: str
    intent: Optional[str]
    
    # Agent outputs
    research_output: Optional[str]
    writing_output: Optional[str]
    code_output: Optional[str]
    
    # Control fields
    selected_agents: List[str]
    final_output: Optional[str]
