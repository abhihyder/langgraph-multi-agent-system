"""
AutoMem Memory Driver Implementation

Adapter that wraps the existing AutoMem client to conform to the BaseMemoryDriver interface.
"""

from typing import List, Dict, Any, Optional
from .base import BaseMemoryDriver
from ..automem_client import get_default_client


class AutoMemDriver(BaseMemoryDriver):
    """
    AutoMem implementation of the memory driver interface.
    
    Wraps the existing AutoMem client to provide a standardized interface
    for memory operations.
    """
    
    def __init__(self):
        """Initialize AutoMem driver with default client."""
        self._client = None
    
    @property
    def client(self):
        """Lazy-load the AutoMem client."""
        if self._client is None:
            self._client = get_default_client()
        return self._client
    
    def recall(
        self,
        user_id: int,
        conversation_id: Optional[int] = None,
        query: Optional[str] = None,
        top_k: int = 10,
        use_vector: bool = True,
        exclude_tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve user memories using AutoMem.
        
        Args:
            user_id: User identifier
            conversation_id: Optional conversation filter
            query: Search query for semantic retrieval
            top_k: Maximum number of results
            use_vector: Whether to use vector/semantic search
            exclude_tags: Tags to exclude from results
            
        Returns:
            List of memory documents with metadata
        """
        try:
            return self.client.recall(
                user_id=int(user_id),
                conversation_id=int(conversation_id) if conversation_id is not None else None,
                query=query,
                top_k=top_k,
                use_vector=use_vector,
                exclude_tags=exclude_tags
            )
        except Exception as e:
            print(f"[AUTOMEM DRIVER] Recall error: {e}")
            return []
    
    def recall_global_knowledge(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve global knowledge using AutoMem.
        
        Args:
            query: Search query
            top_k: Maximum number of results
            category: Optional category filter
            
        Returns:
            List of knowledge documents with metadata
        """
        try:
            # AutoMem's recall_global_knowledge doesn't have category param
            # Category filtering is handled via tags in the results
            documents = self.client.recall_global_knowledge(
                query=query,
                top_k=top_k
            )
            
            # Apply category filter if specified
            if category:
                category_tag = f"category_{category.lower()}"
                documents = [
                    doc for doc in documents
                    if category_tag in doc.get("memory", {}).get("tags", [])
                ]
            
            return documents
        except Exception as e:
            print(f"[AUTOMEM DRIVER] Recall global knowledge error: {e}")
            return []
    
    def store(
        self,
        user_id: int,
        content: str,
        conversation_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store a new memory using AutoMem.
        
        Args:
            user_id: User identifier
            content: Memory content
            conversation_id: Optional conversation identifier
            tags: Optional tags for categorization
            metadata: Optional additional metadata
            
        Returns:
            Stored memory with generated ID
        """
        try:
            # AutoMem uses store_message instead of store
            result = self.client.store_message(
                user_id=int(user_id),
                conversation_id=int(conversation_id) if conversation_id else None,
                role="user",  # Default role
                content=content,
                scope="conversation",
                metadata=metadata or {}
            )
            return result or {}
        except Exception as e:
            print(f"[AUTOMEM DRIVER] Store error: {e}")
            return {}
    
    def store_global_knowledge(
        self,
        content: str,
        category: str,
        title: Optional[str] = None,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store global knowledge using AutoMem.
        
        Args:
            content: Document content
            category: Category (policies, guidelines, etc.)
            title: Optional document title
            doc_id: Optional document identifier
            metadata: Optional additional metadata
            
        Returns:
            Stored document with generated ID
        """
        try:
            # Build metadata
            full_metadata = metadata or {}
            if title:
                full_metadata["title"] = title
            if doc_id:
                full_metadata["doc_id"] = doc_id
            full_metadata["category"] = category
            
            result = self.client.store_global_knowledge(
                content=content,
                category=category,
                metadata=full_metadata
            )
            return result or {}
        except Exception as e:
            print(f"[AUTOMEM DRIVER] Store global knowledge error: {e}")
            return {}
    
    def delete(
        self,
        memory_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Delete a specific memory using AutoMem.
        
        Args:
            memory_id: Memory identifier
            user_id: Optional user identifier for validation
            
        Returns:
            True if deleted successfully
        """
        try:
            # AutoMem client doesn't have a delete method exposed
            # Make direct HTTP DELETE request to AutoMem API
            url = f"{self.client.base_url}/memory/{memory_id}"
            response = self.client.client.delete(url, headers=self.client._headers())
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"[AUTOMEM DRIVER] Delete error: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check AutoMem connection and configuration.
        
        Returns:
            Dict with status and connection details
        """
        try:
            # Try to initialize client
            _ = self.client
            return {
                "status": "healthy",
                "driver": "automem",
                "connected": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "driver": "automem",
                "connected": False,
                "error": str(e)
            }
