"""
Agent Wrappers and Utility Functions

Contains wrapper functions for integrating specialized graph-based agents
with the main orchestrator's function-based interface.
"""

from typing import Dict, Any
import logging
import traceback

from .states import AgentState
from .graphs.email_graph import create_email_agent_graph
from .graphs.general_graph import create_general_agent_graph
from .graphs.research_graph import create_research_agent_graph
from .graphs.writing_graph import create_writing_agent_graph
from .graphs.code_graph import create_code_agent_graph
from .graphs.knowledge_graph import create_knowledge_agent_graph
from .graphs.memory_graph import create_memory_agent_graph


logger = logging.getLogger(__name__)


def email_agent_graph_wrapper(state: AgentState) -> Dict[str, Any]:
    """
    Wrapper function for EmailAgentGraph to integrate with orchestrator.
    
    Bridges the gap between:
    - Orchestrator's AgentState interface
    - Email graph's EmailState interface
    
    This function:
    1. Extracts relevant fields from AgentState
    2. Creates EmailAgentGraph instance
    3. Invokes the graph
    4. Maps graph output back to AgentState format
    
    Args:
        state: AgentState from orchestrator
        
    Returns:
        Updated state with email_output and executed_agents
    """
    logger.info("Email Agent Graph: Processing request")
    
    # Extract input from state
    user_input = state.get("user_input", "")
    intent = state.get("intent", "")
    gmail_credentials = state.get("gmail_credentials")
    
    # Create graph input state
    graph_input = {
        "user_input": user_input,
        "intent": intent,
        "gmail_credentials": gmail_credentials,
        "user_request": user_input
    }
    
    try:
        # Create and invoke email agent graph
        email_graph = create_email_agent_graph(credentials=gmail_credentials)
        result = email_graph.invoke(graph_input)
        
        # Extract output
        email_output = result.get("email_output", "Email processing completed")
        formatted_result = result.get("formatted_result", {})
        
        # Check for errors
        if result.get("error"):
            logger.error(f"Email Agent Graph error: {result['error']}")
            email_output = result.get("email_output", f"Error: {result['error']}")
        
        # Update executed agents
        executed = state.get("executed_agents", [])
        
        logger.info(f"Email Agent Graph: Completed. Output length: {len(email_output)}")
        
        return {
            **state,
            "email_output": email_output,
            "executed_agents": executed + ["email"]
        }
    
    except Exception as e:
        logger.error(f"Email Agent Graph wrapper failed: {str(e)}")
        logger.error(traceback.format_exc())
        
        executed = state.get("executed_agents", [])
        return {
            **state,
            "email_output": f"Error: Email agent failed - {str(e)}",
            "executed_agents": executed + ["email"]
        }


def general_agent_graph_wrapper(state: AgentState) -> Dict[str, Any]:
    """Wrapper for GeneralAgentGraph"""
    logger.info("General Agent Graph: Processing request")
    
    try:
        graph = create_general_agent_graph()
        result = graph.invoke(dict(state))
        
        general_output = result.get("general_output", "")
        executed = state.get("executed_agents", [])
        
        logger.info(f"General Agent Graph: Completed. Output length: {len(general_output)}")
        
        # Return full result with updated executed_agents
        return {
            **result,
            "executed_agents": executed + ["general"]
        }
    
    except Exception as e:
        logger.error(f"General Agent Graph wrapper failed: {str(e)}")
        executed = state.get("executed_agents", [])
        return {
            **state,
            "general_output": f"Error: General agent failed - {str(e)}",
            "executed_agents": executed + ["general"]
        }


def research_agent_graph_wrapper(state: AgentState) -> Dict[str, Any]:
    """Wrapper for ResearchAgentGraph"""
    logger.info("Research Agent Graph: Processing request")
    
    try:
        graph = create_research_agent_graph()
        result = graph.invoke(dict(state))
        
        research_output = result.get("research_output", "")
        executed = state.get("executed_agents", [])
        
        logger.info(f"Research Agent Graph: Completed. Output length: {len(research_output)}")
        
        return {
            **result,
            "executed_agents": executed + ["research"]
        }
    
    except Exception as e:
        logger.error(f"Research Agent Graph wrapper failed: {str(e)}")
        executed = state.get("executed_agents", [])
        return {
            **state,
            "research_output": f"Error: Research agent failed - {str(e)}",
            "executed_agents": executed + ["research"]
        }


def writing_agent_graph_wrapper(state: AgentState) -> Dict[str, Any]:
    """Wrapper for WritingAgentGraph"""
    logger.info("Writing Agent Graph: Processing request")
    
    try:
        graph = create_writing_agent_graph()
        result = graph.invoke(dict(state))
        
        writing_output = result.get("writing_output", "")
        executed = state.get("executed_agents", [])
        
        logger.info(f"Writing Agent Graph: Completed. Output length: {len(writing_output)}")
        
        return {
            **result,
            "executed_agents": executed + ["writing"]
        }
    
    except Exception as e:
        logger.error(f"Writing Agent Graph wrapper failed: {str(e)}")
        executed = state.get("executed_agents", [])
        return {
            **state,
            "writing_output": f"Error: Writing agent failed - {str(e)}",
            "executed_agents": executed + ["writing"]
        }


def code_agent_graph_wrapper(state: AgentState) -> Dict[str, Any]:
    """Wrapper for CodeAgentGraph"""
    logger.info("Code Agent Graph: Processing request")
    
    try:
        graph = create_code_agent_graph()
        result = graph.invoke(dict(state))
        
        code_output = result.get("code_output", "")
        executed = state.get("executed_agents", [])
        
        logger.info(f"Code Agent Graph: Completed. Output length: {len(code_output)}")
        
        return {
            **result,
            "executed_agents": executed + ["code"]
        }
    
    except Exception as e:
        logger.error(f"Code Agent Graph wrapper failed: {str(e)}")
        executed = state.get("executed_agents", [])
        return {
            **state,
            "code_output": f"Error: Code agent failed - {str(e)}",
            "executed_agents": executed + ["code"]
        }


def knowledge_agent_graph_wrapper(state: AgentState) -> Dict[str, Any]:
    """Wrapper for KnowledgeAgentGraph"""
    logger.info("Knowledge Agent Graph: Processing request")
    
    try:
        graph = create_knowledge_agent_graph()
        result = graph.invoke(dict(state))
        
        knowledge_output = result.get("knowledge_output")
        executed = state.get("executed_agents", [])
        
        logger.info(f"Knowledge Agent Graph: Completed")
        
        return {
            **result,
            "executed_agents": executed + ["knowledge"]
        }
    
    except Exception as e:
        logger.error(f"Knowledge Agent Graph wrapper failed: {str(e)}")
        executed = state.get("executed_agents", [])
        return {
            **state,
            "knowledge_output": None,
            "executed_agents": executed + ["knowledge"]
        }


def memory_agent_graph_wrapper(state: AgentState) -> Dict[str, Any]:
    """Wrapper for MemoryAgentGraph"""
    logger.info("Memory Agent Graph: Processing request")
    
    try:
        graph = create_memory_agent_graph()
        result = graph.invoke(dict(state))
        
        memory_output = result.get("memory_output")
        executed = state.get("executed_agents", [])
        
        logger.info(f"Memory Agent Graph: Completed")
        
        return {
            **result,
            "executed_agents": executed + ["memory"]
        }
    
    except Exception as e:
        logger.error(f"Memory Agent Graph wrapper failed: {str(e)}")
        executed = state.get("executed_agents", [])
        return {
            **state,
            "memory_output": None,
            "executed_agents": executed + ["memory"]
        }


def passthrough_output(state: AgentState) -> Dict[str, Any]:
    """
    Pass single processing agent output directly as final output.
    Skips unnecessary aggregator LLM call for efficiency.
    
    Used when only one processing agent was selected - no need to aggregate.
    
    Args:
        state: Current agent state
        
    Returns:
        State with final_output set to the single agent's output
    """
    from .config import PROCESSING_AGENTS
    
    # Find which processing agent ran
    for agent_name in PROCESSING_AGENTS:
        output = state.get(f"{agent_name}_output")
        if output:
            logger.info(f"Passing through output from {agent_name}")
            return {**state, "final_output": output}
    
    # Fallback (shouldn't happen)
    logger.warning("Passthrough called but no processing agent output found")
    return {**state, "final_output": "No response generated."}
