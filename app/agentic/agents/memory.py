"""
Memory Agent - Retrieves user's conversation history using AutoMem
This is a retrieval agent (no LLM) that fetches relevant user-specific memories.
"""

from typing import Dict, Any, List
from ..state import AgentState
from ...services.automem_client import get_default_client
from ...utils.tracing import trace_agent


@trace_agent("memory_agent", run_type="retriever", tags=["agent", "memory", "retrieval"])
def memory_agent(state: AgentState) -> Dict[str, Any]:
    """
    Retrieval agent that fetches user's conversation history and memories.
    Uses semantic search via AutoMem - no LLM calls, just memory retrieval.
    
    Retrieves 3 types of memories:
    1. Recent chronological (last 5 messages for context flow)
    2. Short-term semantic (relevant to current conversation)
    3. Long-term semantic (relevant across all conversations)
    
    Args:
        state: Current agent state with user_input, user_id, conversation_id
        
    Returns:
        Dict with memory_output containing retrieved conversation history
    """
    user_input = state["user_input"]
    user_id = state.get("user_id")
    conversation_id = state.get("conversation_id")
    
    if not user_id:
        return {"memory_output": None}
    
    automem = get_default_client()
    
    try:
        # 1. Recent chronological messages (for conversational flow)
        recent_messages = []
        try:
            recent_messages = automem.recall(
                user_id=user_id,
                conversation_id=conversation_id,
                query=None,
                top_k=5,
                use_vector=False
            )
            print(f"[MEMORY AGENT] Recent messages: {len(recent_messages)}")
        except Exception as e:
            print(f"[MEMORY AGENT] Recent messages error: {e}")
        
        # 2. Short-term semantic (relevant to current conversation)
        short_term_memories = []
        try:
            short_term_memories = automem.recall(
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
            
            print(f"[MEMORY AGENT] Short-term semantic: {len(short_term_memories)}")
        except Exception as e:
            print(f"[MEMORY AGENT] Short-term recall error: {e}")
        
        # 3. Long-term semantic (relevant across all conversations)
        long_term_memories = []
        try:
            # Use exclude_tags to filter out current conversation at API level
            exclude_tags = [f"conversation_{conversation_id}"] if conversation_id else None
            
            long_term_memories = automem.recall(
                user_id=user_id,
                conversation_id=None,
                query=user_input,
                top_k=15,
                use_vector=True,
                exclude_tags=exclude_tags
            )
            
            print(f"[MEMORY AGENT] Long-term semantic: {len(long_term_memories)}")
        except Exception as e:
            print(f"[MEMORY AGENT] Long-term recall error: {e}")
        
        # Combine all memories
        all_memories = recent_messages + short_term_memories + long_term_memories
        
        if not all_memories:
            print("[MEMORY AGENT] No memories found")
            return {"memory_output": None}
        
        # Format memories
        memory_parts = []
        
        if recent_messages:
            memory_parts.append("=== RECENT CONVERSATION ===")
            for msg in recent_messages:
                content = msg.get("memory", {}).get("content") or msg.get("content", "")
                tags = msg.get("memory", {}).get("tags", [])
                role = next((tag for tag in tags if tag in ["user", "assistant"]), "unknown")
                if content:
                    memory_parts.append(f"{role}: {content}")
        
        if short_term_memories:
            memory_parts.append("\n=== RELEVANT FROM THIS CONVERSATION ===")
            for msg in short_term_memories:
                content = msg.get("memory", {}).get("content") or msg.get("content", "")
                if content:
                    memory_parts.append(f"• {content}")
        
        if long_term_memories:
            memory_parts.append("\n=== RELEVANT FROM PAST CONVERSATIONS ===")
            for msg in long_term_memories:
                content = msg.get("memory", {}).get("content") or msg.get("content", "")
                if content:
                    memory_parts.append(f"• {content}")
        
        memory_output = "\n".join(memory_parts)
        
        print(f"[MEMORY AGENT] Retrieved total: {len(all_memories)} memories")
        
        return {
            "memory_output": memory_output
        }
        
    except Exception as e:
        print(f"[MEMORY AGENT] Error retrieving memories: {e}")
        return {
            "memory_output": None
        }
