"""
Knowledge Agent Graph - LangGraph implementation

Retrieves global company knowledge using AutoMem (no LLM).

Architecture:
    user_input → retrieve_knowledge → format_output
                      ↓
                  error_handler (if needed)
"""

from typing import Dict, Any
import logging

from langgraph.graph import StateGraph, END

from .base_graph import BaseAgentGraph, log_node_execution, NodeType
from ..states.agent_state import AgentState
from ...core.memory import get_memory_driver

logger = logging.getLogger(__name__)


class KnowledgeAgentGraph(BaseAgentGraph):
    """
    Knowledge Agent as a LangGraph sub-graph.
    
    Retrieval agent (no LLM) that:
    - Fetches relevant company policies and documentation
    - Uses semantic search via AutoMem
    - Returns structured knowledge base results
    """
    
    def __init__(self):
        super().__init__()
        self.driver = get_memory_driver()
        # Instance variables to store intermediate results
        self._documents = []
        self._knowledge_raw = None
        self._knowledge_found = False
        self._categories = []
        self.graph = self.build_graph()
    
    def build_graph(self):
        """Build the Knowledge agent graph"""
        logger.info("Building KnowledgeAgentGraph")
        
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("retrieve_knowledge", self.retrieve_knowledge_node)
        graph.add_node("format_output", self.format_output_node)
        graph.add_node("error_handler", self.error_handler_node)
        
        # Add edges
        graph.add_conditional_edges(
            "retrieve_knowledge",
            self.check_for_errors,
            {"success": "format_output", "error": "error_handler"}
        )
        
        graph.add_edge("format_output", END)
        graph.add_edge("error_handler", END)
        graph.set_entry_point("retrieve_knowledge")
        
        logger.info("KnowledgeAgentGraph built successfully")
        return graph.compile()
    
    @log_node_execution(NodeType.TOOL)
    def retrieve_knowledge_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Tool Node: Retrieve global knowledge via semantic search"""
        logger.info("Retrieving global knowledge")
        
        try:
            user_input = state["user_input"]
            
            # Semantic search across global knowledge base
            documents = self.driver.recall_global_knowledge(
                query=user_input,
                top_k=5  # Get top 5 most relevant company docs
            )
            
            if not documents:
                logger.info("No relevant company knowledge found")
                self._documents = []
                self._knowledge_found = False
                return state
            
            # Format retrieved documents
            knowledge_parts = []
            categories_found = set()
            
            for doc in documents:
                content = doc.get("memory", {}).get("content") or doc.get("content", "")
                if not content:
                    continue
                
                category = doc.get("memory", {}).get("category") or doc.get("category", "general")
                categories_found.add(category)
                
                # Format with category header
                knowledge_parts.append(f"[{category.upper()}]\n{content}")
            
            knowledge_output = "\n\n---\n\n".join(knowledge_parts) if knowledge_parts else None
            
            # Store in instance variables
            self._documents = documents
            self._knowledge_raw = knowledge_output
            self._knowledge_found = bool(knowledge_output)
            self._categories = list(categories_found)
            
            logger.info(f"Retrieved {len(documents)} knowledge documents from {len(categories_found)} categories")
            return state
            
        except Exception as e:
            logger.error(f"Knowledge retrieval failed: {str(e)}")
            state["error"] = f"Failed to retrieve knowledge: {str(e)}"
            state["error_type"] = "KnowledgeRetrievalError"
            return state
    
    @log_node_execution(NodeType.PROCESSING)
    def format_output_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Processing Node: Format knowledge output"""
        logger.info("Formatting Knowledge agent output")
        
        try:
            # Use instance variables
            knowledge_raw = self._knowledge_raw
            knowledge_found = self._knowledge_found
            
            if knowledge_found and knowledge_raw:
                state["knowledge_output"] = knowledge_raw
            else:
                state["knowledge_output"] = None
            
            logger.info("Knowledge agent output formatted successfully")
            return state
            
        except Exception as e:
            logger.error(f"Output formatting failed: {str(e)}")
            state["error"] = f"Failed to format output: {str(e)}"
            state["error_type"] = "FormattingError"
            return state
    
    @log_node_execution(NodeType.ERROR)
    def error_handler_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Error handler node"""
        error_msg = state.get("error", "Unknown error occurred")
        error_type = state.get("error_type", "Error")
        
        logger.error(f"Knowledge agent error: {error_type} - {error_msg}")
        
        state["knowledge_output"] = None
        state["formatted_result"] = {
            "success": False,
            "error": error_msg,
            "error_type": error_type,
            "agent": "knowledge"
        }
        
        return state
    
    def check_for_errors(self, state: Dict[str, Any]) -> str:
        """Router: Check if errors occurred"""
        return "error" if state.get("error") else "success"


def create_knowledge_agent_graph() -> KnowledgeAgentGraph:
    """Factory function to create Knowledge agent graph"""
    return KnowledgeAgentGraph()


__all__ = ["KnowledgeAgentGraph", "create_knowledge_agent_graph"]
