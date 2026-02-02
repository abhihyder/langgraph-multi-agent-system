"""
Code Agent - Generates production-quality code
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..state import AgentState
from ...utils.helpers import load_prompt


def code_agent(state: AgentState) -> Dict[str, Any]:
    """
    Code agent that generates high-quality, runnable code.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with code_output
    """
    user_input = state["user_input"]
    intent = state.get("intent", "")
    research_output = state.get("research_output", "")
    
    # Load code prompt
    code_prompt = load_prompt("code.md")
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    
    # Build context for code generation
    context = f"""
Task Intent: {intent}

User Request: {user_input}
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
