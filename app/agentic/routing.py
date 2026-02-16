"""
Routing Logic for Agent Graph

Handles conditional routing between nodes in the LangGraph workflow.
Following SOLID principles - single responsibility for routing decisions.
"""

from typing import Literal
from .states import AgentState
from .config import RETRIEVAL_AGENTS, PROCESSING_AGENTS, INTEGRATION_AGENTS
import logging


logger = logging.getLogger(__name__)


def route_from_orchestrator(state: AgentState) -> str:
    """
    Route from orchestrator to the first agent or aggregator.
    
    Priority order:
    1. Retrieval agents first (knowledge, memory) - they provide context
    2. Processing agents second (general, research, writing, code)
    3. Integration agents third (email) - external service operations
    4. Aggregator if no agents selected
    
    Args:
        state: Current agent state
        
    Returns:
        Name of next node to execute
    """
    selected = state.get("selected_agents", [])
    
    if not selected:
        logger.info("No agents selected, routing to aggregator")
        return "aggregator"
    
    # Check for retrieval agents first (they should execute before processing)
    for agent in ["knowledge", "memory"]:
        if agent in selected:
            logger.info(f"Routing to retrieval agent: {agent}")
            return agent
    
    # Then check for processing agents
    for agent in ["general", "research", "writing", "code"]:
        if agent in selected:
            logger.info(f"Routing to processing agent: {agent}")
            return agent
    
    # Then integration agents
    for agent in ["email"]:
        if agent in selected:
            logger.info(f"Routing to integration agent: {agent}")
            return agent
    
    logger.info("No matching agents, routing to aggregator")
    return "aggregator"


def route_from_agent(state: AgentState) -> str:
    """
    Route from current agent to the next agent or to aggregation.
    
    Returns the next agent in priority order, or routes to aggregation.
    Priority: retrieval agents → processing agents → integration agents → aggregation
    
    Args:
        state: Current agent state
        
    Returns:
        Name of next node to execute
    """
    selected = state.get("selected_agents", [])
    executed = set(state.get("executed_agents", []))
    
    # Find next agent to execute (in priority order)
    # Retrieval agents first
    for agent in ["knowledge", "memory"]:
        if agent in selected and agent not in executed:
            logger.info(f"Routing to next retrieval agent: {agent}")
            return agent
    
    # Then processing agents
    for agent in ["general", "research", "writing", "code"]:
        if agent in selected and agent not in executed:
            logger.info(f"Routing to next processing agent: {agent}")
            return agent
    
    # Then integration agents
    for agent in ["email"]:
        if agent in selected and agent not in executed:
            logger.info(f"Routing to next integration agent: {agent}")
            return agent
    
    # All selected agents have executed, check if we need aggregation
    processing_agents_selected = [a for a in selected if a in PROCESSING_AGENTS]
    
    # If exactly 1 processing agent, skip aggregator (passthrough)
    if len(processing_agents_selected) == 1:
        logger.info("Single processing agent, using passthrough")
        return "passthrough"
    
    # Otherwise, aggregate
    logger.info("Multiple agents executed, routing to aggregator")
    return "aggregator"


__all__ = [
    "route_from_orchestrator",
    "route_from_agent",
]
