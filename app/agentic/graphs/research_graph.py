"""
Research Agent Graph - LangGraph implementation

Provides factual, research-based information with analytical depth.

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


class ResearchAgentGraph(BaseAgentGraph):
    """
    Research Agent as a LangGraph sub-graph.
    
    Handles factual, analytical research with:
    - In-depth analysis
    - Fact-based responses
    - Citation and source awareness
    - Analytical reasoning
    """
    
    def __init__(self):
        super().__init__()
        self.llm_config = get_llm_config()
        self.graph = self.build_graph()
    
    def build_graph(self):
        """Build the Research agent graph"""
        logger.info("Building ResearchAgentGraph")
        
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
        
        logger.info("ResearchAgentGraph built successfully")
        return graph.compile()
    
    @log_node_execution(NodeType.PROCESSING)
    def prepare_context_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Processing Node: Prepare research context"""
        logger.info("Preparing context for Research agent")
        
        try:
            knowledge_output = state.get("knowledge_output")
            memory_output = state.get("memory_output")
            
            context_parts = []
            if knowledge_output:
                context_parts.append(f"=== COMPANY KNOWLEDGE ===\n{knowledge_output}")
            if memory_output:
                context_parts.append(f"=== USER HISTORY ===\n{memory_output}")
            
            context = "\n\n".join(context_parts) if context_parts else "No additional context available."
            logger.info(f"Research context prepared ({len(context)} chars)")
            
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
        """LLM Node: Generate research-based response"""
        logger.info("Generating Research response with LLM")
        
        try:
            user_input = state["user_input"]
            intent = state.get("intent", "")
            context = state.get("prepared_context", "")
            
            # Load prompt
            prompt = load_prompt("research.md")
            
            # Initialize LLM with research-specific config
            llm = get_llm(
                self.llm_config.RESEARCH_LLM,
                temperature=self.llm_config.RESEARCH_TEMPERATURE
            )
            
            # Construct messages
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=f"""Research Query: {user_input}
Intent: {intent}

Available Context:
{context}

Provide a factual, well-researched response with analytical depth.""")
            ]
            
            response = llm.invoke(messages)
            content = str(response.content) if hasattr(response, "content") else str(response)
            
            logger.info(f"Research response generated ({len(content)} chars)")
            
            return {
                **state,
                "research_output": content
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
        """Processing Node: Format research output"""
        logger.info("Formatting Research agent output")
        
        try:
            research_output = state.get("research_output", "")
            
            logger.info("Research agent output formatted successfully")
            return {
                **state,
                "formatted_result": {
                    "success": True,
                    "output": research_output,
                    "agent": "research"
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
        
        output = f"❌ Research agent error:\n\n{error_type}: {error_msg}"
        
        return {
            **state,
            "research_output": output,
            "formatted_result": {
                "success": False,
                "error": error_msg,
                "error_type": error_type,
                "agent": "research"
            }
        }
    
    def check_for_errors(self, state: Dict[str, Any]) -> str:
        """Router: Check if errors occurred"""
        return "error" if state.get("error") else "success"


def create_research_agent_graph() -> ResearchAgentGraph:
    """Factory function to create Research agent graph"""
    return ResearchAgentGraph()


__all__ = ["ResearchAgentGraph", "create_research_agent_graph"]
