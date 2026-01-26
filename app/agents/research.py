"""
Research Agent - Provides factual, research-based information
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..state import AgentState


def load_prompt(filename: str) -> str:
    """Load prompt template from file"""
    with open(f"prompts/{filename}", "r") as f:
        return f.read()


def research_agent(state: AgentState) -> Dict[str, Any]:
    """
    Research agent that provides factual, analytical information.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with research_output
    """
    user_input = state["user_input"]
    intent = state.get("intent", "")
    
    # Load research prompt
    research_prompt = load_prompt("research.md")
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    # Create messages with context
    messages = [
        SystemMessage(content=research_prompt),
        HumanMessage(content=f"""
Task Intent: {intent}

User Question: {user_input}

Provide comprehensive research-based information to answer this question.
""")
    ]
    
    # Get research response
    response = llm.invoke(messages)
    
    # Update only research_output field
    return {
        "research_output": response.content
    }
