"""
LangGraph Workflow Definition

This file constructs the LangGraph with:
- Orchestrator router node
- Specialized agent nodes
- Aggregator node
- Conditional routing logic
- Memory handled by AutoMem service (no LangGraph checkpointing)
"""

from typing import Literal
from langgraph.graph import StateGraph, END

from config.settings import get_settings
from .state import AgentState
from .orchestrator import orchestrator_router
from .agents import research_agent, writing_agent, code_agent, general_agent
from .aggregator import aggregator


settings = get_settings()


def route_to_agents(state: AgentState) -> list[str]:
    """
    Conditional routing function that determines which agents to execute.
    Returns list of agent names based on orchestrator router decision.
    """
    selected = state.get("selected_agents", [])
    if not selected:
        return ["aggregator"]  # Skip to aggregator if no agents selected
    return selected


def build_graph():
    """
    Build and compile the LangGraph workflow.
    
    Memory is handled by AutoMem service (no LangGraph checkpointing).
    
    Returns:
        Compiled graph
    """
    # Create graph with shared state
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("orchestrator", orchestrator_router)
    workflow.add_node("general", general_agent)
    workflow.add_node("research", research_agent)
    workflow.add_node("writing", writing_agent)
    workflow.add_node("code", code_agent)
    workflow.add_node("aggregator", aggregator)
    
    # Set entry point
    workflow.set_entry_point("orchestrator")
    
    # Add conditional edges from orchestrator to agents
    workflow.add_conditional_edges(
        "orchestrator",
        route_to_agents,
        {
            "general": "general",
            "research": "research",
            "writing": "writing",
            "code": "code",
            "aggregator": "aggregator"
        }
    )
    
    # All agents flow to aggregator
    workflow.add_edge("general", "aggregator")
    workflow.add_edge("research", "aggregator")
    workflow.add_edge("writing", "aggregator")
    workflow.add_edge("code", "aggregator")
    
    # Aggregator is the end
    workflow.add_edge("aggregator", END)
    
    # Compile without checkpointing (memory handled by AutoMem)
    return workflow.compile()


# Create the compiled graph instance
app = build_graph()
