"""
Knowledge Agent - Retrieves global company knowledge using AutoMem
This is a retrieval agent (no LLM) that fetches relevant company policies and documentation.
"""

from typing import Dict, Any
from ..state import AgentState
from ...services.automem_client import get_default_client


def knowledge_agent(state: AgentState) -> Dict[str, Any]:
    """
    Retrieval agent that fetches relevant global knowledge (company policies, docs).
    Uses semantic search via AutoMem - no LLM calls, just memory retrieval.
    
    Args:
        state: Current agent state with user_input
        
    Returns:
        Dict with knowledge_output containing retrieved documents
    """
    user_input = state["user_input"]
    
    print(f"\n[KNOWLEDGE AGENT] Retrieving global knowledge for: {user_input[:50]}...")
    
    automem = get_default_client()
    
    try:
        # Semantic search across global knowledge base
        # AutoMem's vector search handles multi-topic queries automatically
        documents = automem.recall_global_knowledge(
            query=user_input,
            top_k=5  # Get top 5 most relevant company docs
        )
        
        if not documents:
            print("[KNOWLEDGE AGENT] No relevant company knowledge found")
            return {
                "knowledge_output": None
            }
        
        # Format retrieved documents
        knowledge_parts = []
        categories_found = set()
        
        for doc in documents:
            content = doc.get("memory", {}).get("content") or doc.get("content", "")
            if content:
                # Extract metadata
                memory = doc.get("memory", {})
                tags = memory.get("tags", [])
                metadata = memory.get("metadata", {})
                
                # Get category and title
                category = next((tag.replace("category_", "").upper() 
                               for tag in tags if tag.startswith("category_")), "GENERAL")
                title = metadata.get("title", "")
                doc_id = metadata.get("doc_id", "")
                
                categories_found.add(category)
                
                # Format as structured knowledge
                doc_info = f"[{category}]"
                if doc_id:
                    doc_info += f" {doc_id}"
                if title:
                    doc_info += f" - {title}"
                
                knowledge_parts.append(f"{doc_info}\n{content}")
        
        knowledge_output = "\n\n".join(knowledge_parts)
        
        print(f"[KNOWLEDGE AGENT] Retrieved {len(documents)} documents from categories: {', '.join(categories_found)}")
        
        return {
            "knowledge_output": knowledge_output
        }
        
    except Exception as e:
        print(f"[KNOWLEDGE AGENT] Error retrieving knowledge: {e}")
        return {
            "knowledge_output": None
        }
