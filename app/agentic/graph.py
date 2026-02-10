"""
LangGraph Workflow Definition with LangSmith Tracing

This file constructs the LangGraph with:
- Orchestrator router node
- Specialized agent nodes
- Aggregator node
- Conditional routing logic
- Memory handled by AutoMem service (no LangGraph checkpointing)
- LangSmith tracing for monitoring and debugging
"""

from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, END

from config.settings import get_settings
from .state import AgentState
from .orchestrator import orchestrator_router
from .agents import research_agent, writing_agent, code_agent, general_agent, knowledge_agent, memory_agent
from .aggregator import aggregator


settings = get_settings()

# Define agent types
RETRIEVAL_AGENTS = {"knowledge", "memory"}
PROCESSING_AGENTS = {"general", "research", "writing", "code"}


def route_from_orchestrator(state: AgentState) -> str:
    """
    Route from orchestrator to the first agent or aggregator.
    
    Priority order:
    1. Retrieval agents first (knowledge, memory) - they provide context
    2. Processing agents second (general, research, writing, code)
    3. Aggregator if no agents selected
    """
    selected = state.get("selected_agents", [])
    if not selected:
        return "aggregator"
    
    # Check for retrieval agents first (they should execute before processing)
    for agent in ["knowledge", "memory"]:
        if agent in selected:
            return agent
    
    # Then check for processing agents
    for agent in ["general", "research", "writing", "code"]:
        if agent in selected:
            return agent
    
    return "aggregator"


def route_from_agent(state: AgentState) -> str:
    """
    Route from current agent to the next agent or to aggregation.
    
    Returns the next agent in priority order, or routes to aggregation.
    Priority: retrieval agents → processing agents → aggregation
    """
    selected = state.get("selected_agents", [])
    
    # Get list of agents that have already executed from state tracking
    executed = set(state.get("executed_agents", []))
    
    # Find next agent to execute (in priority order)
    # Retrieval agents first
    for agent in ["knowledge", "memory"]:
        if agent in selected and agent not in executed:
            return agent
    
    # Then processing agents
    for agent in ["general", "research", "writing", "code"]:
        if agent in selected and agent not in executed:
            return agent
    
    # All selected agents have executed, check if we need aggregation
    processing_agents_selected = [a for a in selected if a in PROCESSING_AGENTS]
    
    # If exactly 1 processing agent, skip aggregator (passthrough)
    if len(processing_agents_selected) == 1:
        return "passthrough"
    
    # Otherwise, aggregate
    return "aggregator"


def passthrough_output(state: AgentState) -> Dict[str, Any]:
    """
    Pass single processing agent output directly as final output.
    Skips unnecessary aggregator LLM call.
    """
    # Find which processing agent ran
    for agent_name in PROCESSING_AGENTS:
        output = state.get(f"{agent_name}_output")
        if output:
            return {"final_output": output}
    
    # Fallback (shouldn't happen)
    return {"final_output": "No response generated."}


def build_graph():
    """
    Build and compile the LangGraph workflow with LangSmith tracing.
    
    Memory is handled by AutoMem service (no LangGraph checkpointing).
    LangSmith tracing is automatically enabled via environment variables.
    
    Returns:
        Compiled graph with tracing enabled
    """
    # Create graph with shared state
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("orchestrator", orchestrator_router)
    workflow.add_node("knowledge", knowledge_agent)
    workflow.add_node("memory", memory_agent)
    workflow.add_node("general", general_agent)
    workflow.add_node("research", research_agent)
    workflow.add_node("writing", writing_agent)
    workflow.add_node("code", code_agent)
    workflow.add_node("passthrough", passthrough_output)  # NEW: Direct output
    workflow.add_node("aggregator", aggregator)
    
    # Set entry point
    workflow.set_entry_point("orchestrator")
    
    # Route from orchestrator to first agent (retrieval agents have priority)
    workflow.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "knowledge": "knowledge",
            "memory": "memory",
            "general": "general",
            "research": "research",
            "writing": "writing",
            "code": "code",
            "aggregator": "aggregator"
        }
    )
    
    # Each agent routes to the next agent or to aggregation
    # This ensures sequential execution: retrieval → processing → aggregation
    for agent in ["knowledge", "memory", "general", "research", "writing", "code"]:
        workflow.add_conditional_edges(
            agent,
            route_from_agent,
            {
                "knowledge": "knowledge",
                "memory": "memory",
                "general": "general",
                "research": "research",
                "writing": "writing",
                "code": "code",
                "passthrough": "passthrough",
                "aggregator": "aggregator"
            }
        )
    
    # Both end nodes go to END
    workflow.add_edge("passthrough", END)
    workflow.add_edge("aggregator", END)
    
    # Compile without checkpointing (memory handled by AutoMem)
    # LangSmith tracing will automatically track all LLM calls and graph execution
    return workflow.compile()


# Create the compiled graph instance
app = build_graph()
