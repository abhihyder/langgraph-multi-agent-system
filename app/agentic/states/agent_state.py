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
        conversation_id: ID of the current conversation (for database lookup)
        user_id: ID of the authenticated user
        intent: Orchestrator agent's interpretation of user intent
        knowledge_output: Company policies/docs from knowledge agent (retrieval)
        memory_output: User history from memory agent (retrieval)
        general_output: Output from general agent (LLM)
        research_output: Output from research agent (LLM)
        writing_output: Output from writing agent (LLM)
        code_output: Output from code agent (LLM)
        selected_agents: List of agents selected by orchestrator
        final_output: Aggregated final response
    """
    user_input: str
    conversation_id: Optional[int]
    user_id: Optional[int]
    intent: Optional[str]
    
    # Retrieval agent outputs (AutoMem-based, no LLM)
    knowledge_output: Optional[str]  # Company policies, documentation
    memory_output: Optional[str]     # User conversation history
    
    # Processing agent outputs (LLM-based)
    general_output: Optional[str]
    research_output: Optional[str]
    writing_output: Optional[str]
    code_output: Optional[str]
    
    # Internal processing fields (intermediate states within agent graphs)
    prepared_context: Optional[str]  # Context prepared by processing agents
    general_response: Optional[str]   # Intermediate response from general agent
    research_response: Optional[str]  # Intermediate response from research agent
    writing_response: Optional[str]   # Intermediate response from writing agent
    code_response: Optional[str]      # Intermediate response from code agent
    
    # Control fields
    selected_agents: List[str]
    executed_agents: List[str]  # Track which agents have executed
    final_output: Optional[str]
