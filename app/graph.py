"""
LangGraph Workflow Definition

This file constructs the LangGraph with:
- Boss router node
- Specialized agent nodes
- Aggregator node
- Conditional routing logic
"""

from typing import Literal
from langgraph.graph import StateGraph, END

from .state import AgentState
from .router import boss_router
from .agents import research_agent, writing_agent, code_agent
from .aggregator import aggregator


def route_to_agents(state: AgentState) -> list[str]:
    """
    Conditional routing function that determines which agents to execute.
    Returns list of agent names based on boss router decision.
    """
    selected = state.get("selected_agents", [])
    if not selected:
        return ["aggregator"]  # Skip to aggregator if no agents selected
    return selected


def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph workflow.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create graph with shared state
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("boss", boss_router)
    workflow.add_node("research", research_agent)
    workflow.add_node("writing", writing_agent)
    workflow.add_node("code", code_agent)
    workflow.add_node("aggregator", aggregator)
    
    # Set entry point
    workflow.set_entry_point("boss")
    
    # Add conditional edges from boss to specialized agents
    workflow.add_conditional_edges(
        "boss",
        route_to_agents,
        {
            "research": "research",
            "writing": "writing",
            "code": "code",
            "aggregator": "aggregator"
        }
    )
    
    # All specialized agents flow to aggregator
    workflow.add_edge("research", "aggregator")
    workflow.add_edge("writing", "aggregator")
    workflow.add_edge("code", "aggregator")
    
    # Aggregator is the end
    workflow.add_edge("aggregator", END)
    
    # Compile the graph
    return workflow.compile()


# Create the compiled graph instance
app = build_graph()
