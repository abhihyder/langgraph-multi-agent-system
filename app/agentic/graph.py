"""
LangGraph Workflow Definition

This file constructs the LangGraph with:
- Orchestrator router node
- Specialized agent nodes
- Aggregator node
- Conditional routing logic
- Checkpointing for conversation memory
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

from config.settings import get_settings
from .state import AgentState
from .orchestrator import orchestrator_router
from .agents import research_agent, writing_agent, code_agent, general_agent
from .aggregator import aggregator


# Initialize checkpointer once at module level
settings = get_settings()

# Create PostgresSaver checkpointer - it will be initialized on first use
checkpointer = None

def get_checkpointer():
    """Get or create the PostgresSaver checkpointer."""
    global checkpointer
    if checkpointer is None:
        # PostgresSaver requires dict row factory with proper typing
        from psycopg import Connection
        from psycopg.rows import dict_row
        
        conn: Connection = Connection.connect(
            settings.DATABASE_URL, 
            autocommit=True, 
            prepare_threshold=0,
            row_factory=dict_row  # type: ignore
        )
        checkpointer = PostgresSaver(conn)  # type: ignore
        checkpointer.setup()
    return checkpointer


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
    Build and compile the LangGraph workflow with checkpointing.
    
    Uses PostgresSaver for persistent conversation memory across sessions.
    Each conversation is identified by a thread_id.
    
    Returns:
        Compiled graph with checkpointing enabled
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
    
    # Get checkpointer for conversation memory
    checkpointer = get_checkpointer()
    
    # Compile the graph with checkpointing
    return workflow.compile(checkpointer=checkpointer)


# Create the compiled graph instance
app = build_graph()
