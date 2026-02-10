"""
Base Memory Driver Interface

Defines the abstract interface that all memory drivers must implement.
Similar to Laravel's database driver contract.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseMemoryDriver(ABC):
    """
    Abstract base class for memory drivers.
    
    All memory backends (AutoMem, PGVector, etc.) must implement this interface
    to ensure consistent behavior across different storage systems.
    """
    
    @abstractmethod
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
        Retrieve user memories with optional semantic search.
        
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
        pass
    
    @abstractmethod
    def recall_global_knowledge(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve global knowledge/company documentation.
        
        Args:
            query: Search query
            top_k: Maximum number of results
            category: Optional category filter (policies, guidelines, etc.)
            
        Returns:
            List of knowledge documents with metadata
        """
        pass
    
    @abstractmethod
    def store(
        self,
        user_id: int,
        content: str,
        conversation_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store a new memory.
        
        Args:
            user_id: User identifier
            content: Memory content
            conversation_id: Optional conversation identifier
            tags: Optional tags for categorization
            metadata: Optional additional metadata
            
        Returns:
            Stored memory with generated ID
        """
        pass
    
    @abstractmethod
    def store_global_knowledge(
        self,
        content: str,
        category: str,
        title: Optional[str] = None,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store global knowledge/documentation.
        
        Args:
            content: Document content
            category: Category (policies, guidelines, etc.)
            title: Optional document title
            doc_id: Optional document identifier
            metadata: Optional additional metadata
            
        Returns:
            Stored document with generated ID
        """
        pass
    
    @abstractmethod
    def delete(
        self,
        memory_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Delete a specific memory.
        
        Args:
            memory_id: Memory identifier
            user_id: Optional user identifier for validation
            
        Returns:
            True if deleted successfully
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the driver is properly configured and accessible.
        
        Returns:
            Dict with status and connection details
        """
        pass
