"""
PGVector Memory Driver Implementation

Implementation using PostgreSQL with pgvector extension for vector similarity search.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from .base import BaseMemoryDriver


class PGVectorDriver(BaseMemoryDriver):
    """
    PGVector implementation of the memory driver interface.
    
    Uses PostgreSQL with pgvector extension for storing and retrieving
    memories with vector similarity search capabilities.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize PGVector driver.
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self._connection_string = connection_string
        self._connection = None
        self._embedding_model = None
    
    def _get_connection(self):
        """Get or create database connection."""
        if self._connection is None:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            if not self._connection_string:
                from config.settings import get_settings
                settings = get_settings()
                self._connection_string = settings.DATABASE_URL
            
            self._connection = psycopg2.connect(
                self._connection_string,
                cursor_factory=RealDictCursor
            )
            
            # Ensure pgvector extension is enabled
            with self._connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                self._connection.commit()
        
        return self._connection
    
    def _get_embedding_model(self):
        """Get or create embedding model for vector generation."""
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        return self._embedding_model
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        model = self._get_embedding_model()
        embedding = model.encode(text)
        return embedding.tolist()
    
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
        Retrieve user memories using PGVector.
        
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
            conn = self._get_connection()
            
            if use_vector and query:
                # Vector similarity search
                query_embedding = self._generate_embedding(query)
                embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'
                
                sql = """
                    SELECT id, user_id, conversation_id, content, tags, metadata, 
                           created_at, embedding <=> %s::vector AS distance
                    FROM memories
                    WHERE user_id = %s
                """
                params: List[Any] = [embedding_str, user_id]
                
                if conversation_id:
                    sql += " AND conversation_id = %s"
                    params.append(conversation_id)
                
                if exclude_tags:
                    sql += " AND NOT tags && %s"
                    params.append(exclude_tags)
                
                sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
                params.extend([embedding_str, top_k])
                
            else:
                # Chronological retrieval
                sql = """
                    SELECT id, user_id, conversation_id, content, tags, metadata, created_at
                    FROM memories
                    WHERE user_id = %s
                """
                params: List[Any] = [user_id]
                
                if conversation_id:
                    sql += " AND conversation_id = %s"
                    params.append(conversation_id)
                
                if exclude_tags:
                    sql += " AND NOT tags && %s"
                    params.append(exclude_tags)
                
                sql += " ORDER BY created_at DESC LIMIT %s"
                params.append(top_k)
            
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                results = cursor.fetchall()
            
            # Format results to match AutoMem structure
            formatted_results = []
            for row in results:
                row_dict = dict(row)  # type: ignore
                formatted_results.append({
                    "id": row_dict["id"],
                    "memory": {
                        "content": row_dict["content"],
                        "tags": row_dict["tags"] or [],
                        "metadata": row_dict["metadata"] or {}
                    },
                    "user_id": row_dict["user_id"],
                    "conversation_id": row_dict["conversation_id"],
                    "created_at": row_dict["created_at"].isoformat() if row_dict["created_at"] else None
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"[PGVECTOR DRIVER] Recall error: {e}")
            return []
    
    def recall_global_knowledge(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve global knowledge using PGVector.
        
        Args:
            query: Search query
            top_k: Maximum number of results
            category: Optional category filter
            
        Returns:
            List of knowledge documents with metadata
        """
        try:
            conn = self._get_connection()
            query_embedding = self._generate_embedding(query)
            embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'
            
            sql = """
                SELECT id, content, category, title, doc_id, tags, metadata, 
                       created_at, embedding <=> %s::vector AS distance
                FROM global_knowledge
                WHERE 1=1
            """
            params: List[Any] = [embedding_str]
            
            if category:
                sql += " AND category = %s"
                params.append(category.lower())
            
            sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
            params.extend([embedding_str, top_k])
            
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                results = cursor.fetchall()
            
            # Format results to match AutoMem structure
            formatted_results = []
            for row in results:
                row_dict = dict(row)  # type: ignore
                formatted_results.append({
                    "id": row_dict["id"],
                    "memory": {
                        "content": row_dict["content"],
                        "tags": row_dict["tags"] or [],
                        "metadata": {
                            **(row_dict["metadata"] or {}),
                            "category": row_dict["category"],
                            "title": row_dict["title"],
                            "doc_id": row_dict["doc_id"]
                        }
                    },
                    "category": row_dict["category"],
                    "created_at": row_dict["created_at"].isoformat() if row_dict["created_at"] else None
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"[PGVECTOR DRIVER] Recall global knowledge error: {e}")
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
        Store a new memory using PGVector.
        
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
            conn = self._get_connection()
            embedding = self._generate_embedding(content)
            embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
            
            sql = """
                INSERT INTO memories (user_id, conversation_id, content, tags, metadata, embedding, created_at)
                VALUES (%s, %s, %s, %s, %s, %s::vector, %s)
                RETURNING id, user_id, conversation_id, content, tags, metadata, created_at
            """
            
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    user_id,
                    conversation_id,
                    content,
                    tags or [],
                    json.dumps(metadata or {}),
                    embedding_str,
                    datetime.utcnow()
                ))
                result = cursor.fetchone()
                conn.commit()
            
            if not result:
                return {}
            
            result_dict = dict(result)  # type: ignore
            return {
                "id": result_dict["id"],
                "memory": {
                    "content": result_dict["content"],
                    "tags": result_dict["tags"] or [],
                    "metadata": result_dict["metadata"] or {}
                },
                "user_id": result_dict["user_id"],
                "conversation_id": result_dict["conversation_id"],
                "created_at": result_dict["created_at"].isoformat() if result_dict["created_at"] else None
            }
            
        except Exception as e:
            print(f"[PGVECTOR DRIVER] Store error: {e}")
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
        Store global knowledge using PGVector.
        
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
            conn = self._get_connection()
            embedding = self._generate_embedding(content)
            embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
            
            tags = [f"category_{category.lower()}", "global_knowledge"]
            
            # Check if doc_id exists for upsert logic
            if doc_id:
                # Update existing or insert with doc_id
                sql = """
                    INSERT INTO global_knowledge (content, category, title, doc_id, tags, metadata, embedding, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s)
                    ON CONFLICT (doc_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        category = EXCLUDED.category,
                        title = EXCLUDED.title,
                        tags = EXCLUDED.tags,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding
                    RETURNING id, content, category, title, doc_id, tags, metadata, created_at
                """
            else:
                # Simple insert
                sql = """
                    INSERT INTO global_knowledge (content, category, title, doc_id, tags, metadata, embedding, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s)
                    RETURNING id, content, category, title, doc_id, tags, metadata, created_at
                """
            
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    content,
                    category.lower(),
                    title,
                    doc_id,
                    tags,
                    json.dumps(metadata or {}),
                    embedding_str,
                    datetime.utcnow()
                ))
                result = cursor.fetchone()
                conn.commit()
            
            if not result:
                return {}
            
            result_dict = dict(result)  # type: ignore
            return {
                "id": result_dict["id"],
                "memory": {
                    "content": result_dict["content"],
                    "tags": result_dict["tags"] or [],
                    "metadata": result_dict["metadata"] or {}
                },
                "category": result_dict["category"],
                "created_at": result_dict["created_at"].isoformat() if result_dict["created_at"] else None
            }
            
        except Exception as e:
            print(f"[PGVECTOR DRIVER] Store global knowledge error: {e}")
            return {}
    
    def delete(
        self,
        memory_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Delete a specific memory using PGVector.
        
        Args:
            memory_id: Memory identifier
            user_id: Optional user identifier for validation
            
        Returns:
            True if deleted successfully
        """
        try:
            conn = self._get_connection()
            
            sql = "DELETE FROM memories WHERE id = %s"
            params = [memory_id]
            
            if user_id:
                sql += " AND user_id = %s"
                params.append(user_id)
            
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                conn.commit()
                return cursor.rowcount > 0
            
        except Exception as e:
            print(f"[PGVECTOR DRIVER] Delete error: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check PGVector connection and configuration.
        
        Returns:
            Dict with status and connection details
        """
        try:
            conn = self._get_connection()
            
            # Check if required tables exist
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'memories'
                    ) as memories_exists,
                    EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'global_knowledge'
                    ) as knowledge_exists
                """)
                result = cursor.fetchone()
            
            if not result:
                return {
                    "status": "unhealthy",
                    "driver": "pgvector",
                    "connected": False,
                    "error": "Unable to query table information"
                }
            
            result_dict = dict(result)  # type: ignore
            return {
                "status": "healthy",
                "driver": "pgvector",
                "connected": True,
                "tables": {
                    "memories": result_dict["memories_exists"],
                    "global_knowledge": result_dict["knowledge_exists"]
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "driver": "pgvector",
                "connected": False,
                "error": str(e)
            }
    
    def __del__(self):
        """Clean up database connection."""
        if self._connection:
            self._connection.close()
