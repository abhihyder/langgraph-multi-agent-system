"""
Boss Agent (Router) - Analyzes user input and routes to appropriate agents

The Boss Agent NEVER answers questions directly. It only:
1. Analyzes the user's intent
2. Decides which specialized agents are needed
3. Updates the state with selected agents
"""

import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .state import AgentState


def load_prompt(filename: str) -> str:
    """Load prompt template from file"""
    with open(f"prompts/{filename}", "r") as f:
        return f.read()


def boss_router(state: AgentState) -> Dict[str, Any]:
    """
    Boss agent that routes requests to appropriate specialized agents.
    
    Args:
        state: Current agent state with user input
        
    Returns:
        Updated state with intent and selected_agents
    """
    user_input = state["user_input"]
    
    # Load boss prompt
    boss_prompt = load_prompt("boss.md")
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Create messages
    messages = [
        SystemMessage(content=boss_prompt),
        HumanMessage(content=f"User input: {user_input}")
    ]
    
    # Get routing decision
    response = llm.invoke(messages)
    
    # Parse JSON response
    try:
        # Extract JSON from response (handles markdown code blocks)
        content = str(response.content).strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        routing_decision = json.loads(content)
        
        # Update state
        return {
            "intent": routing_decision.get("intent", ""),
            "selected_agents": routing_decision.get("selected_agents", [])
        }
    except json.JSONDecodeError as e:
        print(f"Error parsing boss response: {e}")
        print(f"Response content: {response.content}")
        # Fallback: route to writing agent
        return {
            "intent": "fallback - parsing error",
            "selected_agents": ["writing"]
        }


def should_route_to_agents(state: AgentState) -> list[str]:
    """
    Conditional routing function for LangGraph.
    Returns list of agent names to execute.
    """
    return state.get("selected_agents", [])
