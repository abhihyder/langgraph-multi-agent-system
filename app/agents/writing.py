"""
Writing Agent - Creates well-structured, human-friendly content
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..state import AgentState
from ..utils import load_prompt


def writing_agent(state: AgentState) -> Dict[str, Any]:
    """
    Writing agent that creates clear, structured content.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with writing_output
    """
    user_input = state["user_input"]
    intent = state.get("intent", "")
    research_output = state.get("research_output", "")
    
    # Load writing prompt
    writing_prompt = load_prompt("writing.md")
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    # Build context for writing
    context = f"""
Task Intent: {intent}

User Question: {user_input}
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
    
    # Update only writing_output field
    return {
        "writing_output": response.content
    }
