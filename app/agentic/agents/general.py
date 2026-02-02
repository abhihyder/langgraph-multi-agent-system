"""
General Agent - Handles generic queries and general conversation

This agent handles:
- General questions that don't require specialized processing
- Casual conversation
- Simple factual queries
- Questions that don't fit into research/writing/code categories
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

from ..state import AgentState
from ...utils.helpers import load_prompt


def general_agent(state: AgentState) -> Dict[str, Any]:
    """
    General agent that handles generic queries and conversation.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with general_output
    """
    user_input = state["user_input"]
    intent = state.get("intent", "")
    messages = state.get("messages", [])
    
    # Load general prompt
    general_prompt = load_prompt("general.md")
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    # Build messages with conversation history
    llm_messages: List[BaseMessage] = [SystemMessage(content=general_prompt)]
    
    # Add conversation history (excluding the last message which is the current user input)
    if len(messages) > 1:
        llm_messages.extend(messages[:-1])
    
    # Add current query with context
    llm_messages.append(HumanMessage(content=f"""Task Intent: {intent}

User Question: {user_input}

Provide a helpful, conversational response to the user's question.
"""))
    
    # Get response
    response = llm.invoke(llm_messages)
    
    # Update only general_output field
    return {
        "general_output": response.content
    }
