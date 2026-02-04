"""
Chat Service - Handles business logic for chat interactions
"""

from typing import Dict, Any, Optional, cast
from langchain_core.messages import HumanMessage, AIMessage
from ..agentic import AgentState
from ..agentic import app as agent_graph
from .automem_client import get_default_client


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
        
        Memory is handled by AutoMem service for both short-term and long-term recall.
        
        Args:
            user_input: User's message/question
            user_id: ID of the authenticated user
            conversation_id: Optional ID of existing conversation for context
            context: Optional additional context from previous interactions
            
        Returns:
            Dict containing the response and metadata
        """
        # AutoMem: recall relevant memories for this user/conversation
        automem = get_default_client()
        
        # STEP 1: Get recent chronological messages for conversational flow
        recent_messages = []
        try:
            # Get last 5 messages chronologically (no query = chronological sort)
            recent_messages = automem.recall(user_id=user_id, conversation_id=conversation_id, query=None, top_k=5, use_vector=False)
            print(f"[AutoMem] Recent chronological (conv {conversation_id}): {len(recent_messages)} messages")
        except Exception as e:
            print(f"[AutoMem] Recent messages error: {e}")
        
        # STEP 2: Get semantically relevant short-term memories
        short_term_memories = []
        try:
            # Try vector search for semantically relevant content
            short_term_memories = automem.recall(user_id=user_id, conversation_id=conversation_id, query=user_input, top_k=3, use_vector=True)
            
            # Remove duplicates with recent_messages
            recent_ids = {m.get("id") for m in recent_messages}
            short_term_memories = [m for m in short_term_memories if m.get("id") not in recent_ids]
            
            print(f"[AutoMem] Semantic short-term (conv {conversation_id}): {len(short_term_memories)} memories")
        except Exception as e:
            print(f"[AutoMem] Short-term recall error: {e}")
        
        # Retrieve long-term (user-scoped) memories across ALL conversations
        long_term_memories = []
        try:
            # Request MORE results since we'll filter out current conversation
            # e.g., if we want 3 final results, request 10 to account for filtering
            requested_long_term = 10
            
            # Try vector search first
            long_term_memories = automem.recall(user_id=user_id, conversation_id=None, query=user_input, top_k=requested_long_term, use_vector=True)
            
            # If vector search got nothing, fall back to tag-only mode
            if not long_term_memories:
                print(f"[AutoMem] Long-term vector missed, trying tag-only mode")
                long_term_memories = automem.recall(user_id=user_id, conversation_id=None, query=None, top_k=requested_long_term, use_vector=False)
            
            # Filter out memories from current conversation (already in short-term)
            current_conv_tag = f"conversation_{conversation_id}"
            long_term_memories = [
                m for m in long_term_memories 
                if current_conv_tag not in m.get("memory", {}).get("tags", [])
            ]
            
            # Now trim to desired limit (3) after filtering
            long_term_memories = long_term_memories[:3]
            
            print(f"[AutoMem] Long-term recall (cross-conversation): {len(long_term_memories)} memories")
        except Exception as e:
            print(f"[AutoMem] Long-term recall error: {e}")
        
        # Combine all memory types:
        # 1. Recent chronological (for flow: "it" references, follow-ups)
        # 2. Long-term cross-conversation (for persistent facts)
        # 3. Semantic short-term (for relevant context beyond recency)
        recalled = recent_messages + long_term_memories + short_term_memories
        print(f"[AutoMem] Total context: {len(recent_messages)} recent + {len(long_term_memories)} long-term + {len(short_term_memories)} semantic = {len(recalled)} memories")

        # Build initial state with recalled memories
        mem_msgs = []
        if recalled:
            # Extract and format memory content for better LLM understanding
            memory_parts = []
            for m in recalled:
                # Get main memory content
                memory_content = m.get("memory", {}).get("content") or m.get("content", "")
                if memory_content:
                    memory_parts.append(f"- {memory_content}")
                
                # Also include relevant relations that might have additional context
                relations = m.get("relations", [])
                for rel in relations[:2]:  # Limit to top 2 relations per memory
                    rel_memory = rel.get("memory", {})
                    rel_summary = rel_memory.get("summary", "")
                    if rel_summary and "name" in rel_summary.lower():
                        memory_parts.append(f"- Related: {rel_summary}")
            
            if memory_parts:
                memory_text = "Previous context from our conversations:\n" + "\n".join(memory_parts)
                mem_msgs.append(HumanMessage(content=memory_text))

        initial_state: AgentState = {
            "user_input": user_input,
            "messages": cast(list, mem_msgs + [HumanMessage(content=user_input)]),
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
        print(f"[DEBUG] Conversation ID: {conversation_id}")
        print(f"[DEBUG] User ID: {user_id}")
        print(f"[DEBUG] Messages count: {len(initial_state.get('messages', []))}")
        if len(initial_state.get('messages', [])) > 0:
            print(f"[DEBUG] Last message: {initial_state['messages'][-1].content[:50]}...")
        
        result = agent_graph.invoke(initial_state)
        
        print(f"[DEBUG] Result messages count: {len(result.get('messages', []))}")
        
        # Persist the human message and AI response into AutoMem (short-term)
        try:
            result_store = automem.store_message(user_id=user_id, conversation_id=conversation_id, role="user", content=user_input, scope="conversation")
            print(f"[AutoMem] Stored user message: {result_store}")
        except Exception as e:
            print(f"[AutoMem] Store user message error: {e}")

        ai_text = result.get("final_output") or ""
        try:
            result_store = automem.store_message(user_id=user_id, conversation_id=conversation_id, role="assistant", content=ai_text, scope="conversation")
            print(f"[AutoMem] Stored assistant message: {result_store}")
        except Exception as e:
            print(f"[AutoMem] Store assistant message error: {e}")
        
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
