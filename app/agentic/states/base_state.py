"""
Base State Definition for Agent Graphs

Provides the foundation state structure that all specialized agent graphs extend.
Following SOLID principles - single responsibility for state management.
"""

from typing import TypedDict, Optional, Dict, Any, List


class BaseAgentState(TypedDict, total=False):
    """
    Base state structure for agent graphs.
    Each agent graph can extend this with domain-specific fields.
    
    Design Principles:
    - Immutable user inputs (user_input, user_request)
    - Each node writes to specific fields
    - Error handling fields for failure scenarios
    - Metadata for observability
    
    Attributes:
        user_input: Original user query/command (immutable)
        user_request: Processed user request (immutable)
        params: Extracted parameters for actions
        
        parsed_intent: Intent analysis result
        action: Action to be performed
        validated: Whether parameters are validated
        
        result: Raw result from execution
        formatted_result: Formatted output for user
        
        error: Error message if execution failed
        error_type: Type/category of error
        retry_count: Number of retry attempts
        
        node_history: List of executed nodes (for debugging)
        execution_time: Total execution time in seconds
    """
    # ========== Input Fields (Immutable) ==========
    user_input: str
    user_request: str
    params: Dict[str, Any]
    
    # ========== Processing Fields ==========
    parsed_intent: Dict[str, Any]
    action: str
    validated: bool
    
    # ========== Output Fields ==========
    result: Any
    formatted_result: Dict[str, Any]
    
    # ========== Error Handling Fields ==========
    error: Optional[str]
    error_type: Optional[str]
    retry_count: int
    
    # ========== Metadata Fields ==========
    node_history: List[str]  # Track which nodes executed
    execution_time: float


__all__ = ["BaseAgentState"]
