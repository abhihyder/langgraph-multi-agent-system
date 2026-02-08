"""
Orchestrator Agent (Router) - Analyzes user input and routes to appropriate agents

The Orchestrator Agent NEVER answers questions directly. It only:
1. Analyzes the user's intent
2. Decides which specialized agents are needed
3. Updates the state with selected agents
"""

import json
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage

from .state import AgentState
from ..utils.helpers import load_prompt
from ..utils.llm_factory import get_llm
from config.llm_config import get_llm_config


def orchestrator_router(state: AgentState) -> Dict[str, Any]:
    """
    Orchestrator agent that routes requests to appropriate specialized agents.
    
    Args:
        state: Current agent state with user input
        
    Returns:
        Updated state with intent and selected_agents
    """
    llm_config = get_llm_config()
    user_input = state["user_input"]
    
    # Load orchestrator prompt
    orchestrator_prompt = load_prompt("orchestrator.md")
    
    # Initialize LLM with configurable provider and model
    llm = get_llm(
        llm_config.ORCHESTRATOR_LLM,
        temperature=llm_config.ORCHESTRATOR_TEMPERATURE
    )
    
    # Create messages
    messages = [
        SystemMessage(content=orchestrator_prompt),
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
        print(f"Error parsing orchestrator response: {e}")
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
