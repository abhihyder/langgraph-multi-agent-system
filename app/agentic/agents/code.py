"""
Code Agent - Generates production-quality code
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage

from ..state import AgentState
from ...utils.helpers import load_prompt
from ...utils.llm_factory import get_llm
from ...utils.tracing import trace_agent
from config.llm_config import get_llm_config


@trace_agent("code_agent", run_type="chain", tags=["agent", "code"])
def code_agent(state: AgentState) -> Dict[str, Any]:
    """
    Code agent that generates high-quality, runnable code.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with code_output
    """
    llm_config = get_llm_config()
    user_input = state["user_input"]
    intent = state.get("intent", "")
    
    # Get context from other agents
    research_output = state.get("research_output", "")
    knowledge_output = state.get("knowledge_output")
    memory_output = state.get("memory_output")
    
    # Load code prompt
    code_prompt = load_prompt("code.md")
    
    # Initialize LLM with configurable provider and model
    llm = get_llm(
        llm_config.CODE_LLM,
        temperature=llm_config.CODE_TEMPERATURE
    )
    
    # Build context for code generation
    context = f"""Task Intent: {intent}

    User Request: {user_input}
    """
    
    if knowledge_output:
        context += f"""

        === COMPANY KNOWLEDGE ===
        {knowledge_output}
        """
    
    if memory_output:
        context += f"""

        === USER HISTORY ===
        {memory_output}
        """
            
    if research_output:
        context += f"""

        Technical Context:
        {research_output}
        """
    # Create messages
    messages = [
        SystemMessage(content=code_prompt),
        HumanMessage(content=context + "\n\nGenerate production-quality code to fulfill this request.")
    ]
    
    # Get code response
    response = llm.invoke(messages)
    
    # Update only code_output field
    return {
        "code_output": response.content
    }
