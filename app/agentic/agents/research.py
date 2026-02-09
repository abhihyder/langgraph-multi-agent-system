"""
Research Agent - Provides factual, research-based information
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage

from ..state import AgentState
from ...utils.helpers import load_prompt
from ...utils.llm_factory import get_llm
from ...utils.tracing import trace_agent
from config.llm_config import get_llm_config


@trace_agent("research_agent", run_type="chain", tags=["agent", "research"])
def research_agent(state: AgentState) -> Dict[str, Any]:
    """
    Research agent that provides factual, analytical information.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with research_output
    """
    llm_config = get_llm_config()
    user_input = state["user_input"]
    intent = state.get("intent", "")
    
    # Get context from retrieval agents
    knowledge_output = state.get("knowledge_output")
    memory_output = state.get("memory_output")
    
    # Load research prompt
    research_prompt = load_prompt("research.md")
    
    # Initialize LLM with configurable provider and model
    llm = get_llm(
        llm_config.RESEARCH_LLM,
        temperature=llm_config.RESEARCH_TEMPERATURE
    )
    
    # Build context section
    context_parts = []
    if knowledge_output:
        context_parts.append(f"=== COMPANY KNOWLEDGE ===\n{knowledge_output}")
    if memory_output:
        context_parts.append(f"=== USER HISTORY ===\n{memory_output}")
    
    context_section = "\n\n".join(context_parts) if context_parts else "No additional context available."
    
    # Create messages
    messages = [
        SystemMessage(content=research_prompt),
        HumanMessage(content=f"""Task Intent: {intent}

        User Question: {user_input}

        {context_section}

        Provide comprehensive research-based information using the context above when relevant.
        """)
    ]
    
    # Get research response
    response = llm.invoke(messages)
    
    # Update only research_output field
    return {
        "research_output": response.content
    }
