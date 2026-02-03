import os
import time
from typing import Any, Dict, List, Optional
import httpx


class AutoMemClient:
    """Synchronous client for AutoMem HTTP API.

    Expects the AutoMem service to expose endpoints:
      - POST /recall
      - POST /memory
      - POST /associate

    Environment:
      AUTOMEM_URL (default: http://localhost:8001)
      AUTOMEM_API_TOKEN (optional)
    """

    def __init__(self, base_url: Optional[str] = None, api_token: Optional[str] = None, timeout: int = 10):
        self.base_url = base_url or os.getenv("AUTOMEM_URL", "http://localhost:8001")
        self.api_token = api_token or os.getenv("AUTOMEM_API_TOKEN")
        self.timeout = timeout
        self.client = httpx.Client(timeout=self.timeout)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def recall(self, user_id: int, conversation_id: Optional[int] = None, query: Optional[str] = None, top_k: int = 5, use_vector: bool = True) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for the user/conversation using GET request.
        
        Args:
            user_id: User ID for filtering
            conversation_id: Optional conversation ID for conversation-scoped recall
            query: Optional search query. If empty, uses tag-only mode (good for unindexed memories)
            top_k: Number of results to return
            use_vector: If False, omits query to use tag-only mode (fallback when embeddings not ready)
        """
        url = f"{self.base_url}/recall"
        params: Dict[str, Any] = {
            "limit": top_k,
        }
        
        # Only include query if we want vector search AND have a query
        if use_vector and query and query.strip():
            params["query"] = query
        # else: omit query to trigger tag-only mode for unindexed memories
        
        # Add conversation_id or user_id tags for scoping
        if conversation_id:
            params["tags"] = f"conversation_{conversation_id}"
        elif user_id:
            params["tags"] = f"user_{user_id}"
            
        try:
            r = self.client.get(url, params=params, headers=self._headers())
            r.raise_for_status()
            data = r.json()
            
            # Check if vector search matched anything
            vector_matched = data.get("vector_search", {}).get("matched", False)
            if not vector_matched and use_vector:
                print(f"[AutoMem] Vector search missed, embeddings may be pending")
            
            # AutoMem returns results in 'results' field
            memories = data.get("results", [])
            return memories
        except Exception as e:
            print(f"[AutoMem] recall error: {e}")
            return []

    def store_message(self, user_id: int, conversation_id: Optional[int], role: str, content: str, scope: str = "conversation", metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Store a message into AutoMem with proper tags for scoping."""
        url = f"{self.base_url}/memory"
        
        # Build tags - ALWAYS include user_id for cross-conversation recall
        tags = [f"user_{user_id}", role]
        
        # Add conversation tag for conversation-scoped recall
        if conversation_id:
            tags.append(f"conversation_{conversation_id}")
        
        payload = {
            "content": content,
            "type": "conversation",
            "importance": 0.7 if role == "user" else 0.5,
            "tags": tags,
        }
        if metadata:
            payload["metadata"] = metadata
            
        try:
            r = self.client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            result = r.json()
            
            # Give AutoMem a moment to process embeddings
            # This helps with immediate recall in the next turn
            time.sleep(0.5)
            
            return result
        except Exception as e:
            print(f"[AutoMem] store_message error: {e}")
            return None

    def associate(self, memory1_id: str, memory2_id: str, relation_type: str = "RELATED_TO", strength: float = 0.8) -> bool:
        """Create a relationship between two memories."""
        url = f"{self.base_url}/associate"
        payload = {
            "memory1_id": memory1_id,
            "memory2_id": memory2_id,
            "type": relation_type,
            "strength": strength
        }
        try:
            r = self.client.post(url, json=payload, headers=self._headers())
            r.raise_for_status()
            return True
        except Exception as e:
            print(f"[AutoMem] associate error: {e}")
            return False


_default_client: Optional[AutoMemClient] = None


def get_default_client() -> AutoMemClient:
    global _default_client
    if _default_client is None:
        _default_client = AutoMemClient()
    return _default_client
