"""
Chat Service - Handles business logic for chat interactions
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from ..agentic.state import AgentState
from .automem_client import get_default_client

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


class ChatService:
    """Service for handling chat interactions with the agent system."""
    
    def __init__(self) -> None:
        # Import here to avoid circular imports
        from ..agentic import app as agent_graph
        self.agent_graph: "CompiledStateGraph" = agent_graph
    
    def process_chat(
        self, 
        user_input: str, 
        user_id: int,
        conversation_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message through the orchestrator and agent system.
        
        Memory retrieval is now handled by memory_agent and knowledge_agent.
        
        Args:
            user_input: User's message/question
            user_id: ID of the authenticated user
            conversation_id: Optional ID of existing conversation for context
            context: Optional additional context from previous interactions
            
        Returns:
            Dict containing the response and metadata
        """
        automem = get_default_client()
        
        # Build initial state - memory retrieval happens in memory_agent
        initial_state: AgentState = {
            "user_input": user_input,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "intent": None,
            "knowledge_output": None,
            "memory_output": None,
            "general_output": None,
            "research_output": None,
            "writing_output": None,
            "code_output": None,
            "selected_agents": [],
            "final_output": None
        }
        
        # Execute through orchestrator -> retrieval/processing agents -> aggregator
        print(f"[CHAT] User {user_id}, Conversation {conversation_id}: {user_input[:50]}...")
        result = self.agent_graph.invoke(initial_state)
        
        # Store user message and AI response in AutoMem
        try:
            automem.store_message(
                user_id=user_id,
                conversation_id=conversation_id,
                role="user",
                content=user_input,
                scope="conversation"
            )
            print(f"[AutoMem] Stored user message")
        except Exception as e:
            print(f"[AutoMem] Store user error: {e}")

        ai_response = result.get("final_output") or ""
        try:
            automem.store_message(
                user_id=user_id,
                conversation_id=conversation_id,
                role="assistant",
                content=ai_response,
                scope="conversation"
            )
            print(f"[AutoMem] Stored AI response")
        except Exception as e:
            print(f"[AutoMem] Store AI error: {e}")
        
        return {
            "response": result.get("final_output", "No response generated"),
            "intent": result.get("intent"),
            "agents_used": result.get("selected_agents", []),
            "metadata": {
                "knowledge_used": bool(result.get("knowledge_output")),
                "memory_used": bool(result.get("memory_output")),
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
