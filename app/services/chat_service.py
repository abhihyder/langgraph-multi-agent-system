"""
Chat Service - Handles business logic for chat interactions
"""

from typing import Dict, Any, Optional
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
from ..agentic import AgentState
from ..agentic import app as agent_graph


class ChatService:
    """Service for handling chat interactions with the agent system."""
    
    def process_chat(
        self, 
        user_input: str, 
        user_id: int,
        conversation_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message through the orchestrator and agent system.
        
        Uses LangGraph's checkpointing for automatic conversation memory.
        Each conversation is identified by a thread_id (conversation_id).
        
        Args:
            user_input: User's message/question
            user_id: ID of the authenticated user
            conversation_id: Optional ID of existing conversation for context
            context: Optional additional context from previous interactions
            
        Returns:
            Dict containing the response and metadata
        """
        # Create thread configuration for checkpointing
        # thread_id uses conversation_id which is now guaranteed to exist
        thread_id = f"user_{user_id}_conv_{conversation_id}"
        config = RunnableConfig(
            configurable={
                "thread_id": thread_id
            }
        )
        
        # Build initial state - conversation_id is always present now
        try:
            # Try to get previous state from checkpointer
            current_state = agent_graph.get_state(config)
            
            if current_state.values:  # type: ignore
                # Continuing conversation - load previous messages
                existing_messages = current_state.values.get("messages", [])  # type: ignore
                updated_messages = list(existing_messages) + [HumanMessage(content=user_input)]
                
                # Preserve context, update input and reset outputs
                initial_state: AgentState = {
                    "user_input": user_input,
                    "messages": updated_messages,
                    "conversation_id": conversation_id,
                    "user_id": current_state.values.get("user_id") or user_id,  # type: ignore
                    "intent": None,
                    "general_output": None,
                    "research_output": None,
                    "writing_output": None,
                    "code_output": None,
                    "selected_agents": [],
                    "final_output": None
                }
            else:
                # No previous state - first message in this conversation
                initial_state: AgentState = {
                    "user_input": user_input,
                    "messages": [HumanMessage(content=user_input)],
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "intent": None,
                    "general_output": None,
                    "research_output": None,
                    "writing_output": None,
                    "code_output": None,
                    "selected_agents": [],
                    "final_output": None
                }
        except Exception as e:
            # If state loading fails, treat as new conversation
            print(f"[WARNING] Could not load state: {e}")
            initial_state: AgentState = {
                "user_input": user_input,
                "messages": [HumanMessage(content=user_input)],
                "conversation_id": conversation_id,
                "user_id": user_id,
                "intent": None,
                "general_output": None,
                "research_output": None,
                "writing_output": None,
                "code_output": None,
                "selected_agents": [],
                "final_output": None
            }
        
        # Execute through orchestrator -> agents -> aggregator
        # Checkpointer automatically saves state after execution
        print(f"[DEBUG] Thread ID: {thread_id}")
        print(f"[DEBUG] Conversation ID: {conversation_id}")
        print(f"[DEBUG] Messages count: {len(initial_state.get('messages', []))}")
        if len(initial_state.get('messages', [])) > 0:
            print(f"[DEBUG] Last message: {initial_state['messages'][-1].content[:50]}...")
        
        result = agent_graph.invoke(initial_state, config=config)
        
        print(f"[DEBUG] Result messages count: {len(result.get('messages', []))}")
        
        # Add AI response to messages (will be saved by checkpointer on next call)
        # This happens automatically through state updates
        
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
