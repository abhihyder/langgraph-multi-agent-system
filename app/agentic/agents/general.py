"""
General Agent - Handles generic queries and general conversation

This agent handles:
- General questions that don't require specialized processing
- Casual conversation
- Simple factual queries
- Questions that don't fit into research/writing/code categories
"""

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

from ..state import AgentState
from ...utils.helpers import load_prompt
from ...utils.llm_factory import get_llm
from config.llm_config import get_llm_config


def general_agent(state: AgentState) -> Dict[str, Any]:
    """
    General agent that handles generic queries and conversation.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with general_output
    """
    llm_config = get_llm_config()
    user_input = state["user_input"]
    intent = state.get("intent", "")
    
    # Get context from retrieval agents
    knowledge_output = state.get("knowledge_output")
    memory_output = state.get("memory_output")
    
    # Load general prompt
    general_prompt = load_prompt("general.md")
    
    # Initialize LLM with configurable provider and model
    llm = get_llm(
        llm_config.GENERAL_LLM,
        temperature=0.7
    )
    
    # Build context section
    context_parts = []
    if knowledge_output:
        context_parts.append(f"=== COMPANY KNOWLEDGE ===\n{knowledge_output}")
    if memory_output:
        context_parts.append(f"=== USER HISTORY ===\n{memory_output}")
    
    context_section = "\n\n".join(context_parts) if context_parts else "No additional context available."
    
    # Build messages
    llm_messages: List[BaseMessage] = [
        SystemMessage(content=general_prompt),
        HumanMessage(content=f"""Task Intent: {intent}

        User Question: {user_input}

        {context_section}

        Provide a helpful, conversational response using the context above when relevant.
        """)
    ]
    
    # Get response
    response = llm.invoke(llm_messages)
    
    # Update only general_output field
    return {
        "general_output": response.content
    }
