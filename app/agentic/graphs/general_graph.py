"""
General Agent Graph - LangGraph implementation of general agent

Handles generic queries and general conversation using a multi-node graph.

Architecture:
    user_input → prepare_context → generate_response → format_output
                      ↓
                  error_handler (if needed)
"""

from typing import Dict, Any
import logging

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from .base_graph import BaseAgentGraph, log_node_execution, retry_on_failure, NodeType
from ..states import AgentState
from ...utils.helpers import load_prompt
from ...utils.llm_factory import get_llm
from config.llm_config import get_llm_config

logger = logging.getLogger(__name__)


class GeneralAgentGraph(BaseAgentGraph):
    """
    General Agent as a LangGraph sub-graph.
    
    Handles:
    - General questions and conversation
    - Simple factual queries
    - Questions that don't require specialized processing
    
    Nodes:
    1. prepare_context (Processing) - Gather context from retrieval agents
    2. generate_response (LLM) - Generate response using LLM
    3. format_output (Processing) - Format result for orchestrator
    4. error_handler (Processing) - Handle errors gracefully
    """
    
    def __init__(self):
        super().__init__()
        self.llm_config = get_llm_config()
        self.graph = self.build_graph()
    
    def build_graph(self):
        """Build the general agent graph with all nodes and edges"""
        logger.info("Building GeneralAgentGraph")
        
        # Create StateGraph
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("prepare_context", self.prepare_context_node)
        graph.add_node("generate_response", self.generate_response_node)
        graph.add_node("format_output", self.format_output_node)
        graph.add_node("error_handler", self.error_handler_node)
        
        # Add edges
        graph.add_conditional_edges(
            "prepare_context",
            self.check_for_errors,
            {
                "success": "generate_response",
                "error": "error_handler"
            }
        )
        
        graph.add_conditional_edges(
            "generate_response",
            self.check_for_errors,
            {
                "success": "format_output",
                "error": "error_handler"
            }
        )
        
        graph.add_edge("format_output", END)
        graph.add_edge("error_handler", END)
        
        # Set entry point
        graph.set_entry_point("prepare_context")
        
        logger.info("GeneralAgentGraph built successfully")
        return graph.compile()
    
    # ========== NODE IMPLEMENTATIONS ==========
    
    @log_node_execution(NodeType.PROCESSING)
    def prepare_context_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Processing Node: Prepare context from retrieval agents"""
        logger.info("Preparing context for general agent")
        
        try:
            # Get context from retrieval agents
            knowledge_output = state.get("knowledge_output")
            memory_output = state.get("memory_output")
            
            # Build context section
            context_parts = []
            if knowledge_output:
                context_parts.append(f"Knowledge Base Context:\n{knowledge_output}")
            if memory_output:
                context_parts.append(f"Conversation Memory:\n{memory_output}")
            
            context = "\n\n".join(context_parts) if context_parts else "No additional context available."
            
            state["prepared_context"] = context
            logger.info(f"Context prepared ({len(context)} chars)")
            
            return state
            
        except Exception as e:
            logger.error(f"Context preparation failed: {str(e)}")
            state["error"] = f"Failed to prepare context: {str(e)}"
            state["error_type"] = "ContextPreparationError"
            return state
    
    @log_node_execution(NodeType.LLM)
    @retry_on_failure(max_retries=3)
    def generate_response_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LLM Node: Generate response using LLM"""
        logger.info("Generating general response with LLM")
        
        try:
            user_input = state["user_input"]
            intent = state.get("intent", "")
            context = state.get("prepared_context", "")
            
            # Load general prompt
            general_prompt = load_prompt("general.md")
            
            # Initialize LLM
            llm = get_llm(
                self.llm_config.GENERAL_LLM,
                temperature=0.7
            )
            
            # Construct messages
            messages = [
                SystemMessage(content=general_prompt),
                HumanMessage(content=f"""User Query: {user_input}
                Intent: {intent}

                Context:
                {context}

                Please provide a helpful, conversational response to the user's query.""")
            ]
            
            # Invoke LLM
            response = llm.invoke(messages)
            content = str(response.content) if hasattr(response, "content") else str(response)
            
            logger.info(f"General response generated ({len(content)} chars)")
            state["general_response"] = content
            
            return state
            
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            state["error"] = f"Failed to generate response: {str(e)}"
            state["error_type"] = "LLMGenerationError"
            return state
    
    @log_node_execution(NodeType.PROCESSING)
    def format_output_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Processing Node: Format result for orchestrator"""
        logger.info("Formatting general agent output")
        
        try:
            general_response = state.get("general_response", "")
            
            # Format output
            state["general_output"] = general_response
            state["formatted_result"] = {
                "success": True,
                "output": general_response,
                "agent": "general"
            }
            
            logger.info("General agent output formatted successfully")
            return state
            
        except Exception as e:
            logger.error(f"Output formatting failed: {str(e)}")
            state["error"] = f"Failed to format output: {str(e)}"
            state["error_type"] = "FormattingError"
            return state
    
    @log_node_execution(NodeType.ERROR)
    def error_handler_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Error handler node"""
        logger.info("Handling general agent error")
        
        error_msg = state.get("error", "Unknown error occurred")
        error_type = state.get("error_type", "Error")
        
        output = f"❌ General agent error:\n\n{error_type}: {error_msg}"
        
        state["general_output"] = output
        state["formatted_result"] = {
            "success": False,
            "error": error_msg,
            "error_type": error_type,
            "agent": "general"
        }
        
        return state
    
    def check_for_errors(self, state: Dict[str, Any]) -> str:
        """Router: Check if errors occurred"""
        if state.get("error"):
            return "error"
        return "success"


# Factory function
def create_general_agent_graph() -> GeneralAgentGraph:
    """Factory function to create general agent graph"""
    return GeneralAgentGraph()


__all__ = ["GeneralAgentGraph", "create_general_agent_graph"]
