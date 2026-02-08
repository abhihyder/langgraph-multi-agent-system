"""
LangGraph Workflow Definition

This file constructs the LangGraph with:
- Orchestrator router node
- Specialized agent nodes
- Aggregator node
- Conditional routing logic
- Memory handled by AutoMem service (no LangGraph checkpointing)
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


def route_to_agents(state: AgentState) -> list[str]:
    """
    Conditional routing function that determines which agents to execute.
    Returns list of agent names based on orchestrator router decision.
    
    Ensures retrieval agents (knowledge, memory) execute BEFORE processing agents
    since execution is sequential, not parallel.
    """
    selected = state.get("selected_agents", [])
    if not selected:
        return ["aggregator"]  # Skip to aggregator if no agents selected
    
    # Separate retrieval and processing agents
    retrieval = [a for a in selected if a in RETRIEVAL_AGENTS]
    processing = [a for a in selected if a in PROCESSING_AGENTS]
    
    # Return retrieval first, then processing (sequential execution order)
    return retrieval + processing


def needs_aggregation(state: AgentState) -> Literal["aggregator", "passthrough"]:
    """
    Determine if aggregation is needed or if we can use single agent output directly.
    
    Logic:
    - Retrieval agents (knowledge, memory) provide context, don't need aggregation
    - If only 1 processing agent ran, use its output directly (skip aggregator)
    - If 0 or 2+ processing agents, use aggregator
    
    Returns:
        "passthrough" - Use single processing agent output directly
        "aggregator" - Need to aggregate multiple outputs
    """
    selected = state.get("selected_agents", [])
    
    # Count processing agents
    processing_agents_selected = [a for a in selected if a in PROCESSING_AGENTS]
    
    # If exactly 1 processing agent, skip aggregator
    if len(processing_agents_selected) == 1:
        return "passthrough"
    
    # If 0 or multiple processing agents, aggregate
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
    Build and compile the LangGraph workflow.
    
    Memory is handled by AutoMem service (no LangGraph checkpointing).
    
    Returns:
        Compiled graph
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
    
    # Add conditional edges from orchestrator to agents
    workflow.add_conditional_edges(
        "orchestrator",
        route_to_agents,
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
    
    # All agents route conditionally to either passthrough or aggregator
    # This checks if only 1 processing agent ran
    for agent in ["knowledge", "memory", "general", "research", "writing", "code"]:
        workflow.add_conditional_edges(
            agent,
            needs_aggregation,
            {
                "passthrough": "passthrough",
                "aggregator": "aggregator"
            }
        )
    
    # Both end nodes go to END
    workflow.add_edge("passthrough", END)
    workflow.add_edge("aggregator", END)
    
    # Compile without checkpointing (memory handled by AutoMem)
    return workflow.compile()


# Create the compiled graph instance
app = build_graph()
