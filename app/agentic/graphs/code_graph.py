"""
Code Agent Graph - LangGraph implementation

Generates production-quality, runnable code.

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
from ..states.agent_state import AgentState
from ...utils.helpers import load_prompt
from ...utils.llm_factory import get_llm
from config.llm_config import get_llm_config

logger = logging.getLogger(__name__)


class CodeAgentGraph(BaseAgentGraph):
    """
    Code Agent as a LangGraph sub-graph.
    
    Handles code generation with:
    - Production-quality code
    - Best practices and patterns
    - Error handling
    - Documentation
    - Testing considerations
    """
    
    def __init__(self):
        super().__init__()
        self.llm_config = get_llm_config()
        self.graph = self.build_graph()
    
    def build_graph(self):
        """Build the Code agent graph"""
        logger.info("Building CodeAgentGraph")
        
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
            {"success": "generate_response", "error": "error_handler"}
        )
        
        graph.add_conditional_edges(
            "generate_response",
            self.check_for_errors,
            {"success": "format_output", "error": "error_handler"}
        )
        
        graph.add_edge("format_output", END)
        graph.add_edge("error_handler", END)
        graph.set_entry_point("prepare_context")
        
        logger.info("CodeAgentGraph built successfully")
        return graph.compile()
    
    @log_node_execution(NodeType.PROCESSING)
    def prepare_context_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Processing Node: Prepare code generation context"""
        logger.info("Preparing context for Code agent")
        
        try:
            intent = state.get("intent", "")
            user_input = state["user_input"]
            research_output = state.get("research_output", "")
            knowledge_output = state.get("knowledge_output")
            memory_output = state.get("memory_output")
            
            # Build comprehensive context for code generation
            context = f"""Task Intent: {intent}

User Request: {user_input}
"""
            
            if knowledge_output:
                context += f"\n\n=== RELEVANT DOCUMENTATION ===\n{knowledge_output}"
            
            if research_output:
                context += f"\n\n=== TECHNICAL RESEARCH ===\n{research_output}"
            
            if memory_output:
                context += f"\n\n=== PREVIOUS CONTEXT ===\n{memory_output}"
            
            logger.info(f"Code context prepared ({len(context)} chars)")
            
            return {
                **state,
                "prepared_context": context
            }
            
        except Exception as e:
            logger.error(f"Context preparation failed: {str(e)}")
            return {
                **state,
                "error": f"Failed to prepare context: {str(e)}",
                "error_type": "ContextPreparationError"
            }
    
    @log_node_execution(NodeType.LLM)
    @retry_on_failure(max_retries=3)
    def generate_response_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LLM Node: Generate production-quality code"""
        logger.info("Generating Code response with LLM")
        
        try:
            context = state.get("prepared_context", "")
            
            # Load prompt
            prompt = load_prompt("code.md")
            
            # Initialize LLM with code-specific config
            llm = get_llm(
                self.llm_config.CODE_LLM,
                temperature=self.llm_config.CODE_TEMPERATURE
            )
            
            # Construct messages
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=f"""{context}

Generate production-quality, well-documented code that follows best practices and includes proper error handling.""")
            ]
            
            response = llm.invoke(messages)
            content = str(response.content) if hasattr(response, "content") else str(response)
            
            logger.info(f"Code response generated ({len(content)} chars)")
            
            return {
                **state,
                "code_output": content
            }
            
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            return {
                **state,
                "error": f"Failed to generate response: {str(e)}",
                "error_type": "LLMGenerationError"
            }
    
    @log_node_execution(NodeType.PROCESSING)
    def format_output_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Processing Node: Format code output"""
        logger.info("Formatting Code agent output")
        
        try:
            code_output = state.get("code_output", "")
            
            logger.info("Code agent output formatted successfully")
            return {
                **state,
                "formatted_result": {
                    "success": True,
                    "output": code_output,
                    "agent": "code"
                }
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
        
        output = f"❌ Code agent error:\n\n{error_type}: {error_msg}"
        
        return {
            **state,
            "code_output": output,
            "formatted_result": {
                "success": False,
                "error": error_msg,
                "error_type": error_type,
                "agent": "code"
            }
        }
    
    def check_for_errors(self, state: Dict[str, Any]) -> str:
        """Router: Check if errors occurred"""
        return "error" if state.get("error") else "success"


def create_code_agent_graph() -> CodeAgentGraph:
    """Factory function to create Code agent graph"""
    return CodeAgentGraph()


__all__ = ["CodeAgentGraph", "create_code_agent_graph"]
