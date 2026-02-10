"""
Writing Agent - Creates well-structured, human-friendly content
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage

from ..state import AgentState
from ...utils.helpers import load_prompt
from ...utils.llm_factory import get_llm
from ...utils.tracing import trace_agent
from config.llm_config import get_llm_config


@trace_agent("writing_agent", run_type="chain", tags=["agent", "writing"])
def writing_agent(state: AgentState) -> Dict[str, Any]:
    """
    Writing agent that creates clear, structured content.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with writing_output
    """
    llm_config = get_llm_config()
    user_input = state["user_input"]
    intent = state.get("intent", "")
    
    # Get context from other agents
    research_output = state.get("research_output", "")
    knowledge_output = state.get("knowledge_output")
    memory_output = state.get("memory_output")
    
    # Load writing prompt
    writing_prompt = load_prompt("writing.md")
    
    # Initialize LLM with configurable provider and model
    llm = get_llm(
        llm_config.WRITING_LLM,
        temperature=llm_config.WRITING_TEMPERATURE
    )
    
    # Build context for writing
    context = f"""Task Intent: {intent}

    User Question: {user_input}
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

        Research Context (use this information):
        {research_output}
        """
    
    # Create messages
    messages = [
        SystemMessage(content=writing_prompt),
        HumanMessage(content=context + "\n\nCreate well-structured content to address the user's needs.")
    ]
    
    # Get writing response
    response = llm.invoke(messages)
    
    # Update only writing_output field and mark as executed
    executed = state.get("executed_agents", [])
    return {
        "writing_output": response.content,
        "executed_agents": executed + ["writing"]
    }
