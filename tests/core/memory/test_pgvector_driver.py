"""
Test PGVector Driver Implementation

Tests for PGVectorDriver to ensure proper PostgreSQL + pgvector integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
from app.core.memory.pgvector_driver import PGVectorDriver


class TestPGVectorDriver:
    """Test cases for PGVectorDriver"""
    
    @pytest.fixture
    def mock_connection(self):
        """Mock database connection"""
        conn = Mock()
        cursor = Mock()
        cursor.__enter__ = Mock(return_value=cursor)
        cursor.__exit__ = Mock(return_value=False)
        conn.cursor.return_value = cursor
        return conn, cursor
    
    @pytest.fixture
    def mock_embedding_model(self):
        """Mock embedding model"""
        model = Mock()
        model.encode.return_value = Mock(tolist=Mock(return_value=[0.1, 0.2, 0.3]))
        return model
    
    @pytest.fixture
    def driver(self, mock_connection, mock_embedding_model):
        """Create driver with mocked dependencies"""
        conn, cursor = mock_connection
        
        # Mock both psycopg2 and sentence_transformers at module level
        import sys
        mock_sentence_transformers = Mock()
        mock_sentence_transformers.SentenceTransformer = Mock(return_value=mock_embedding_model)
        sys.modules['sentence_transformers'] = mock_sentence_transformers
        
        with patch('psycopg2.connect', return_value=conn):
            driver = PGVectorDriver(connection_string="postgresql://test")
            # Force connection initialization with our mock
            driver._connection = conn
            driver._embedding_model = mock_embedding_model
            return driver
    
    def test_initialization(self):
        """Test driver initialization"""
        driver = PGVectorDriver(connection_string="postgresql://test")
        assert driver is not None
        assert driver._connection_string == "postgresql://test"
        assert driver._connection is None
        assert driver._embedding_model is None
    
    def test_get_connection_creates_extension(self, mock_connection):
        """Test that connection setup creates pgvector extension"""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            driver = PGVectorDriver(connection_string="postgresql://test")
            connection = driver._get_connection()
            
            # Verify extension was created
            cursor.execute.assert_called_with("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit.assert_called()
            assert connection is conn
    
    def test_get_connection_uses_settings_if_no_string(self, mock_connection):
        """Test that connection uses settings when no string provided"""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn), \
             patch('config.settings.get_settings') as mock_settings:
            mock_settings.return_value.DATABASE_URL = "postgresql://from_settings"
            
            driver = PGVectorDriver()
            driver._get_connection()
            
            # Should use settings URL
            mock_settings.assert_called_once()
    
    def test_generate_embedding(self, driver, mock_embedding_model):
        """Test embedding generation"""
        embedding = driver._generate_embedding("test text")
        
        mock_embedding_model.encode.assert_called_once_with("test text")
        assert embedding == [0.1, 0.2, 0.3]
    
    def test_recall_with_vector_search(self, driver, mock_connection, mock_embedding_model):
        """Test recalling memories with vector similarity search"""
        conn, cursor = mock_connection
        
        # Mock database results
        cursor.fetchall.return_value = [
            {
                "id": "mem1",
                "user_id": "user123",
                "conversation_id": "conv1",
                "content": "Test memory",
                "tags": ["user"],
                "metadata": {},
                "created_at": datetime(2026, 1, 1),
                "distance": 0.1
            }
        ]
        
        result = driver.recall(
            user_id="user123",
            conversation_id="conv1",
            query="test query",
            top_k=5,
            use_vector=True
        )
        
        # Verify SQL was executed
        cursor.execute.assert_called_once()
        sql_call = cursor.execute.call_args[0][0]
        params = cursor.execute.call_args[0][1]
        
        assert "embedding <=> %s::vector" in sql_call
        assert "user_id = %s" in sql_call
        assert "conversation_id = %s" in sql_call
        assert params[1] == "user123"
        assert params[2] == "conv1"
        
        # Verify result format
        assert len(result) == 1
        assert result[0]["id"] == "mem1"
        assert result[0]["memory"]["content"] == "Test memory"
        assert result[0]["user_id"] == "user123"
    
    def test_recall_chronological(self, driver, mock_connection):
        """Test recalling memories chronologically without vector search"""
        conn, cursor = mock_connection
        
        cursor.fetchall.return_value = [
            {
                "id": "mem1",
                "user_id": "user123",
                "conversation_id": None,
                "content": "Recent memory",
                "tags": [],
                "metadata": {},
                "created_at": datetime(2026, 1, 1)
            }
        ]
        
        result = driver.recall(
            user_id="user123",
            query=None,
            use_vector=False,
            top_k=10
        )
        
        # Verify SQL doesn't use vector search
        sql_call = cursor.execute.call_args[0][0]
        assert "embedding" not in sql_call
        assert "ORDER BY created_at DESC" in sql_call
        
        assert len(result) == 1
    
    def test_recall_with_exclude_tags(self, driver, mock_connection, mock_embedding_model):
        """Test recalling with tag exclusion"""
        conn, cursor = mock_connection
        cursor.fetchall.return_value = []
        
        driver.recall(
            user_id="user123",
            query="test",
            use_vector=True,
            exclude_tags=["conversation_conv1", "archived"]
        )
        
        sql_call = cursor.execute.call_args[0][0]
        params = cursor.execute.call_args[0][1]
        
        assert "NOT tags && %s" in sql_call
        assert ["conversation_conv1", "archived"] in params
    
    def test_recall_global_knowledge(self, driver, mock_connection, mock_embedding_model):
        """Test recalling global knowledge documents"""
        conn, cursor = mock_connection
        
        cursor.fetchall.return_value = [
            {
                "id": "doc1",
                "content": "Policy document",
                "category": "policies",
                "title": "Policy 1",
                "doc_id": "POL-001",
                "tags": ["category_policies"],
                "metadata": {},
                "created_at": datetime(2026, 1, 1),
                "distance": 0.2
            }
        ]
        
        result = driver.recall_global_knowledge(
            query="company policies",
            top_k=3,
            category="policies"
        )
        
        # Verify SQL
        sql_call = cursor.execute.call_args[0][0]
        params = cursor.execute.call_args[0][1]
        
        assert "FROM global_knowledge" in sql_call
        assert "category = %s" in sql_call
        assert "policies" in params
        
        # Verify result
        assert len(result) == 1
        assert result[0]["memory"]["content"] == "Policy document"
        assert result[0]["memory"]["metadata"]["category"] == "policies"
        assert result[0]["memory"]["metadata"]["title"] == "Policy 1"
    
    def test_store_memory(self, driver, mock_connection, mock_embedding_model):
        """Test storing a new memory"""
        conn, cursor = mock_connection
        
        cursor.fetchone.return_value = {
            "id": "mem123",
            "user_id": "user123",
            "conversation_id": "conv1",
            "content": "New memory",
            "tags": ["user"],
            "metadata": {"key": "value"},
            "created_at": datetime(2026, 1, 1)
        }
        
        result = driver.store(
            user_id="user123",
            content="New memory",
            conversation_id="conv1",
            tags=["user"],
            metadata={"key": "value"}
        )
        
        # Verify INSERT was called
        sql_call = cursor.execute.call_args[0][0]
        params = cursor.execute.call_args[0][1]
        
        assert "INSERT INTO memories" in sql_call
        assert "user123" in params
        assert "New memory" in params
        assert ["user"] in params
        
        # Verify commit
        conn.commit.assert_called_once()
        
        # Verify result
        assert result["id"] == "mem123"
        assert result["memory"]["content"] == "New memory"
    
    def test_store_global_knowledge(self, driver, mock_connection, mock_embedding_model):
        """Test storing global knowledge"""
        conn, cursor = mock_connection
        
        cursor.fetchone.return_value = {
            "id": "doc1",
            "content": "Policy doc",
            "category": "policies",
            "title": "New Policy",
            "doc_id": "POL-001",
            "tags": ["category_policies", "global_knowledge"],
            "metadata": {},
            "created_at": datetime(2026, 1, 1)
        }
        
        result = driver.store_global_knowledge(
            content="Policy doc",
            category="policies",
            title="New Policy",
            doc_id="POL-001"
        )
        
        # Verify INSERT/UPSERT
        sql_call = cursor.execute.call_args[0][0]
        params = cursor.execute.call_args[0][1]
        
        assert "INSERT INTO global_knowledge" in sql_call
        assert "ON CONFLICT (doc_id) DO UPDATE" in sql_call  # Changed from (id) to (doc_id)
        assert "POL-001" in params
        assert "policies" in params
        
        assert result["id"] == "doc1"
    
    def test_delete_memory(self, driver, mock_connection):
        """Test deleting a memory"""
        conn, cursor = mock_connection
        cursor.rowcount = 1
        
        result = driver.delete(memory_id="mem123", user_id="user123")
        
        # Verify DELETE was called
        sql_call = cursor.execute.call_args[0][0]
        params = cursor.execute.call_args[0][1]
        
        assert "DELETE FROM memories" in sql_call
        assert "id = %s" in sql_call
        assert "user_id = %s" in sql_call
        assert "mem123" in params
        assert "user123" in params
        
        conn.commit.assert_called_once()
        assert result is True
    
    def test_delete_memory_not_found(self, driver, mock_connection):
        """Test deleting non-existent memory"""
        conn, cursor = mock_connection
        cursor.rowcount = 0
        
        result = driver.delete(memory_id="nonexistent")
        
        assert result is False
    
    def test_health_check_success(self, driver, mock_connection):
        """Test health check when database is accessible"""
        conn, cursor = mock_connection
        
        cursor.fetchone.return_value = {
            "memories_exists": True,
            "knowledge_exists": True
        }
        
        result = driver.health_check()
        
        assert result["status"] == "healthy"
        assert result["driver"] == "pgvector"
        assert result["connected"] is True
        assert result["tables"]["memories"] is True
        assert result["tables"]["global_knowledge"] is True
    
    def test_health_check_failure(self):
        """Test health check when connection fails"""
        with patch('psycopg2.connect', side_effect=Exception("Connection failed")):
            driver = PGVectorDriver(connection_string="postgresql://invalid")
            result = driver.health_check()
            
            assert result["status"] == "unhealthy"
            assert result["driver"] == "pgvector"
            assert result["connected"] is False
            assert "Connection failed" in result["error"]
    
    def test_recall_handles_errors(self, driver, mock_connection):
        """Test that recall handles database errors gracefully"""
        conn, cursor = mock_connection
        cursor.execute.side_effect = Exception("Database error")
        
        result = driver.recall(user_id="user123")
        
        assert result == []
    
    def test_store_handles_errors(self, driver, mock_connection):
        """Test that store handles errors gracefully"""
        conn, cursor = mock_connection
        cursor.execute.side_effect = Exception("Insert failed")
        
        result = driver.store(user_id="user123", content="test")
        
        assert result == {}
