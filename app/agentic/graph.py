"""
LangGraph Workflow Definition with LangSmith Tracing

This file constructs the LangGraph with:
- Orchestrator router node
- Specialized agent graph nodes (all graph-based now)
- Aggregator node
- Conditional routing logic
- Memory handled by AutoMem service (no LangGraph checkpointing)
- LangSmith tracing for monitoring and debugging

Following SOLID principles:
- Single Responsibility: Only graph construction logic here
- Other concerns (routing, wrappers, config) are in separate modules

Architecture:
All agents are now graph-based for consistency and scalability:
- Retrieval Agents: KnowledgeAgentGraph, MemoryAgentGraph
- Processing Agents: GeneralAgentGraph, ResearchAgentGraph, WritingAgentGraph, CodeAgentGraph
- Integration Agents: EmailAgentGraph
"""

from langgraph.graph import StateGraph, END

from config.settings import get_settings
from .states import AgentState
from .orchestrator import orchestrator_router
from .aggregator import aggregator
from .config import RETRIEVAL_AGENTS, PROCESSING_AGENTS, INTEGRATION_AGENTS
from .routing import route_from_orchestrator, route_from_agent
from .wrappers import (
    email_agent_graph_wrapper,
    general_agent_graph_wrapper,
    research_agent_graph_wrapper,
    writing_agent_graph_wrapper,
    code_agent_graph_wrapper,
    knowledge_agent_graph_wrapper,
    memory_agent_graph_wrapper,
    passthrough_output
)


settings = get_settings()


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
    
    # Add nodes - All graph-based agents now
    workflow.add_node("orchestrator", orchestrator_router)
    workflow.add_node("knowledge", knowledge_agent_graph_wrapper)  # Graph-based
    workflow.add_node("memory", memory_agent_graph_wrapper)  # Graph-based
    workflow.add_node("general", general_agent_graph_wrapper)  # Graph-based
    workflow.add_node("research", research_agent_graph_wrapper)  # Graph-based
    workflow.add_node("writing", writing_agent_graph_wrapper)  # Graph-based
    workflow.add_node("code", code_agent_graph_wrapper)  # Graph-based
    workflow.add_node("email", email_agent_graph_wrapper)  # Graph-based
    workflow.add_node("passthrough", passthrough_output)  # Direct output for single agent
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
            "email": "email",
            "aggregator": "aggregator"
        }
    )
    
    # Each agent routes to the next agent or to aggregation
    # This ensures sequential execution: retrieval → processing → integration → aggregation
    for agent in ["knowledge", "memory", "general", "research", "writing", "code", "email"]:
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
                "email": "email",
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
