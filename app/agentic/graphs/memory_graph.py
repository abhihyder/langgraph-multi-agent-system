"""
Memory Agent Graph - LangGraph implementation

Retrieves user's conversation history using AutoMem (no LLM).

Architecture:
    user_input → retrieve_memory → format_output
                      ↓
                  error_handler (if needed)
"""

from typing import Dict, Any, List
import logging

from langgraph.graph import StateGraph, END

from .base_graph import BaseAgentGraph, log_node_execution, NodeType
from ..states.agent_state import AgentState
from ...core.memory import get_memory_driver

logger = logging.getLogger(__name__)


class MemoryAgentGraph(BaseAgentGraph):
    """
    Memory Agent as a LangGraph sub-graph.
    
    Retrieval agent (no LLM) that:
    - Fetches user's conversation history
    - Retrieves 3 types of memories:
      1. Recent chronological (last 5 messages)
      2. Short-term semantic (current conversation)
      3. Long-term semantic (across all conversations)
    - Uses semantic search via AutoMem
    """
    
    def __init__(self):
        super().__init__()
        self.driver = get_memory_driver()
        # Instance variables to store intermediate results between nodes
        self._all_memories = []
        self._recent_count = 0
        self._short_term_count = 0
        self._long_term_count = 0
        self._memory_found = False
        self.graph = self.build_graph()
    
    def build_graph(self):
        """Build the Memory agent graph"""
        logger.info("Building MemoryAgentGraph")
        
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("retrieve_memory", self.retrieve_memory_node)
        graph.add_node("format_output", self.format_output_node)
        graph.add_node("error_handler", self.error_handler_node)
        
        # Add edges
        graph.add_conditional_edges(
            "retrieve_memory",
            self.check_for_errors,
            {"success": "format_output", "error": "error_handler"}
        )
        
        graph.add_edge("format_output", END)
        graph.add_edge("error_handler", END)
        graph.set_entry_point("retrieve_memory")
        
        logger.info("MemoryAgentGraph built successfully")
        return graph.compile()
    
    @log_node_execution(NodeType.TOOL)
    def retrieve_memory_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Tool Node: Retrieve user memories via semantic search"""
        logger.info("Retrieving user memories")
        
        try:
            user_input = state["user_input"]
            user_id = state.get("user_id")
            conversation_id = state.get("conversation_id")
            
            if not user_id:
                logger.info("No user_id provided, skipping memory retrieval")
                self._memory_found = False
                self._all_memories = []
                return state
            
            # 1. Recent chronological messages (for conversational flow)
            recent_messages = []
            try:
                recent_messages = self.driver.recall(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    query=None,
                    top_k=5,
                    use_vector=False
                )
                logger.info(f"Recent messages: {len(recent_messages)}")
            except Exception as e:
                logger.warning(f"Recent messages error: {e}")
            
            # 2. Short-term semantic (relevant to current conversation)
            short_term_memories = []
            try:
                short_term_memories = self.driver.recall(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    query=user_input,
                    top_k=10,
                    use_vector=True
                )
                
                # Remove duplicates with recent messages
                recent_ids = {m.get("id") for m in recent_messages}
                short_term_memories = [m for m in short_term_memories 
                                      if m.get("id") not in recent_ids]
                
                logger.info(f"Short-term semantic: {len(short_term_memories)}")
            except Exception as e:
                logger.warning(f"Short-term recall error: {e}")
            
            # 3. Long-term semantic (relevant across all conversations)
            long_term_memories = []
            try:
                # Use exclude_tags to filter out current conversation
                exclude_tags = [f"conversation_{conversation_id}"] if conversation_id else None
                
                long_term_memories = self.driver.recall(
                    user_id=user_id,
                    conversation_id=None,
                    query=user_input,
                    top_k=15,
                    use_vector=True,
                    exclude_tags=exclude_tags
                )
                
                logger.info(f"Long-term semantic: {len(long_term_memories)}")
            except Exception as e:
                logger.warning(f"Long-term recall error: {e}")
            
            # Combine all memories
            all_memories = recent_messages + short_term_memories + long_term_memories
            
            # Store in instance variables for use by format_output_node
            self._all_memories = all_memories
            self._recent_count = len(recent_messages)
            self._short_term_count = len(short_term_memories)
            self._long_term_count = len(long_term_memories)
            self._memory_found = len(all_memories) > 0
            
            logger.info(f"Total memories retrieved: {len(all_memories)}")
            return state
            
        except Exception as e:
            logger.error(f"Memory retrieval failed: {str(e)}")
            return {
                **state,
                "error": f"Failed to retrieve memories: {str(e)}",
                "error_type": "MemoryRetrievalError"
            }
    
    @log_node_execution(NodeType.PROCESSING)
    def format_output_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Processing Node: Format memory output"""
        logger.info("Formatting Memory agent output")
        
        try:
            # Use instance variables instead of state
            all_memories = self._all_memories
            memory_found = self._memory_found
            
            if not memory_found or not all_memories:
                logger.info("No memories to format")
                return {
                    **state,
                    "memory_output": None
                }
            
            # Format memories by type
            sections = []
            
            # Recent messages section
            recent_count = self._recent_count
            if recent_count > 0:
                sections.append("=== RECENT CONVERSATION ===")
                for i, mem in enumerate(all_memories[:recent_count]):
                    content = mem.get("memory", {}).get("content") or mem.get("content", "")
                    # Try multiple paths to get role
                    role = (mem.get("memory", {}).get("role") or 
                           mem.get("role") or 
                           mem.get("memory", {}).get("metadata", {}).get("role") or
                           "user")
                    # Format role for display
                    display_role = "AI" if role in ["assistant", "ai", "system"] else "user"
                    sections.append(f"[{display_role}] {content}")
            
            # Short-term memories
            short_term_count = self._short_term_count
            if short_term_count > 0:
                start_idx = recent_count
                end_idx = start_idx + short_term_count
                sections.append("\n=== RELEVANT FROM THIS CONVERSATION ===")
                for mem in all_memories[start_idx:end_idx]:
                    content = mem.get("memory", {}).get("content") or mem.get("content", "")
                    sections.append(f"• {content}")
            
            # Long-term memories
            long_term_count = self._long_term_count
            if long_term_count > 0:
                start_idx = recent_count + short_term_count
                sections.append("\n=== RELEVANT FROM PAST CONVERSATIONS ===")
                for mem in all_memories[start_idx:]:
                    content = mem.get("memory", {}).get("content") or mem.get("content", "")
                    timestamp = mem.get("created_at", "")
                    sections.append(f"• [{timestamp}] {content}")
            
            memory_output = "\n".join(sections)
            
            logger.info("Memory agent output formatted successfully")
            return {
                **state,
                "memory_output": memory_output
            }
            
        except Exception as e:
            logger.error(f"Output formatting failed: {str(e)}")
            return {
                **state,
                "error": f"Failed to format output: {str(e)}",
                "error_type": "FormattingError"
            }
    
    @log_node_execution(NodeType.ERROR)
    def error_handler_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Error handler node"""
        error_msg = state.get("error", "Unknown error occurred")
        error_type = state.get("error_type", "Error")
        
        logger.error(f"Memory agent error: {error_type} - {error_msg}")
        
        return {
            **state,
            "memory_output": None,
            "formatted_result": {
                "success": False,
                "error": error_msg,
                "error_type": error_type,
                "agent": "memory"
            }
        }
    
    def check_for_errors(self, state: Dict[str, Any]) -> str:
        """Router: Check if errors occurred"""
        return "error" if state.get("error") else "success"


def create_memory_agent_graph() -> MemoryAgentGraph:
    """Factory function to create Memory agent graph"""
    return MemoryAgentGraph()


__all__ = ["MemoryAgentGraph", "create_memory_agent_graph"]
