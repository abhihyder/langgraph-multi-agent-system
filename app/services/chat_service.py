"""
Chat Service - Handles business logic for chat interactions
"""

from typing import Dict, Any, Optional
from ..state import AgentState
from ..graph import app as agent_graph


class ChatService:
    """Service for handling chat interactions with the agent system."""
    
    def process_chat(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a chat message through the orchestrator and agent system.
        
        Args:
            user_input: User's message/question
            context: Optional context from previous interactions
            
        Returns:
            Dict containing the response and metadata
        """
        # Initialize state for the agent system
        initial_state: AgentState = {
            "user_input": user_input,
            "intent": None,
            "research_output": None,
            "writing_output": None,
            "code_output": None,
            "selected_agents": [],
            "final_output": None
        }
        
        # Execute through orchestrator -> agents -> aggregator
        result = agent_graph.invoke(initial_state)
        
        return {
            "response": result.get("final_output", "No response generated"),
            "intent": result.get("intent"),
            "agents_used": result.get("selected_agents", []),
            "metadata": {
                "research_output": result.get("research_output"),
                "writing_output": result.get("writing_output"),
                "code_output": result.get("code_output")
            }
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about available agents.
        
        Returns:
            Dict containing agent information
        """
        return {
            "agents": [
                {
                    "name": "research",
                    "description": "Performs research using web search and optional MCP tools",
                    "capabilities": ["web_search", "fact_finding", "data_gathering"]
                },
                {
                    "name": "writing",
                    "description": "Generates written content and articles",
                    "capabilities": ["content_creation", "article_writing", "summarization"]
                },
                {
                    "name": "code",
                    "description": "Generates and explains code solutions",
                    "capabilities": ["code_generation", "code_explanation", "debugging"]
                }
            ],
            "orchestrator": {
                "name": "orchestrator",
                "description": "Routes requests to appropriate specialized agents",
                "role": "router"
            }
        }
