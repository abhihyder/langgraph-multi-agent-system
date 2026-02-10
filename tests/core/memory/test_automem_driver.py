"""
Test AutoMem Driver Implementation

Tests for AutoMemDriver to ensure proper wrapping of AutoMem client.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.core.memory.automem_driver import AutoMemDriver


class TestAutoMemDriver:
    """Test cases for AutoMemDriver"""
    
    @pytest.fixture
    def mock_automem_client(self):
        """Mock AutoMem client for testing"""
        return Mock()
    
    @pytest.fixture
    def driver(self, mock_automem_client):
        """Create driver with mocked client"""
        with patch('app.core.memory.automem_driver.get_default_client', 
                  return_value=mock_automem_client):
            driver = AutoMemDriver()
            # Force client initialization
            _ = driver.client
            return driver
    
    def test_initialization(self):
        """Test driver initialization"""
        driver = AutoMemDriver()
        assert driver is not None
        assert driver._client is None  # Lazy loading
    
    def test_lazy_client_loading(self, mock_automem_client):
        """Test that client is loaded lazily"""
        with patch('app.core.memory.automem_driver.get_default_client', 
                  return_value=mock_automem_client) as mock_get_client:
            driver = AutoMemDriver()
            
            # Client not loaded yet
            assert mock_get_client.call_count == 0
            
            # Access client
            client = driver.client
            
            # Client loaded
            assert mock_get_client.call_count == 1
            assert client is mock_automem_client
            
            # Second access doesn't reload
            client2 = driver.client
            assert mock_get_client.call_count == 1
            assert client2 is client
    
    def test_recall_user_memories(self, driver, mock_automem_client):
        """Test recalling user memories"""
        # Mock return data
        mock_automem_client.recall.return_value = [
            {
                "id": "mem1",
                "memory": {"content": "Test memory", "tags": ["user"], "metadata": {}},
                "user_id": 123
            }
        ]
        
        # Call recall
        result = driver.recall(
            user_id="123",
            conversation_id="456",
            query="test query",
            top_k=5,
            use_vector=True,
            exclude_tags=["tag1"]
        )
        
        # Verify client was called correctly
        mock_automem_client.recall.assert_called_once_with(
            user_id=123,
            conversation_id=456,
            query="test query",
            top_k=5,
            use_vector=True,
            exclude_tags=["tag1"]
        )
        
        # Verify result
        assert len(result) == 1
        assert result[0]["id"] == "mem1"
        assert result[0]["memory"]["content"] == "Test memory"
    
    def test_recall_handles_errors(self, driver, mock_automem_client):
        """Test that recall handles errors gracefully"""
        mock_automem_client.recall.side_effect = Exception("Connection error")
        
        result = driver.recall(user_id="123")
        
        # Should return empty list on error
        assert result == []
    
    def test_recall_global_knowledge(self, driver, mock_automem_client):
        """Test recalling global knowledge"""
        mock_automem_client.recall_global_knowledge.return_value = [
            {
                "id": "doc1",
                "memory": {
                    "content": "Company policy",
                    "tags": ["category_policies", "global_knowledge"],
                    "metadata": {"title": "Policy 1"}
                }
            }
        ]
        
        result = driver.recall_global_knowledge(query="policies", top_k=3)
        
        mock_automem_client.recall_global_knowledge.assert_called_once_with(
            query="policies",
            top_k=3
        )
        
        assert len(result) == 1
        assert result[0]["memory"]["content"] == "Company policy"
    
    def test_recall_global_knowledge_with_category_filter(self, driver, mock_automem_client):
        """Test recalling global knowledge with category filter"""
        mock_automem_client.recall_global_knowledge.return_value = [
            {
                "id": "doc1",
                "memory": {
                    "content": "Policy doc",
                    "tags": ["category_policies"],
                    "metadata": {}
                }
            },
            {
                "id": "doc2",
                "memory": {
                    "content": "Guide doc",
                    "tags": ["category_guidelines"],
                    "metadata": {}
                }
            }
        ]
        
        # Filter by category
        result = driver.recall_global_knowledge(
            query="documentation",
            category="policies"
        )
        
        # Should only return policies
        assert len(result) == 1
        assert result[0]["id"] == "doc1"
    
    def test_store_memory(self, driver, mock_automem_client):
        """Test storing a memory"""
        mock_automem_client.store_message.return_value = {
            "id": "new_mem",
            "memory": {"content": "New memory", "tags": ["user"], "metadata": {}}
        }
        
        result = driver.store(
            user_id="123",
            content="New memory",
            conversation_id="456",
            tags=["user"],
            metadata={"key": "value"}
        )
        
        mock_automem_client.store_message.assert_called_once_with(
            user_id=123,
            conversation_id=456,
            role="user",
            content="New memory",
            scope="conversation",
            metadata={"key": "value"}
        )
        
        assert result["id"] == "new_mem"
    
    def test_store_memory_with_defaults(self, driver, mock_automem_client):
        """Test storing memory with default values"""
        mock_automem_client.store_message.return_value = {"id": "mem"}
        
        driver.store(user_id="123", content="Memory")
        
        # Should pass empty dict for metadata
        mock_automem_client.store_message.assert_called_once()
        call_args = mock_automem_client.store_message.call_args
        assert call_args[1]["metadata"] == {}
    
    def test_store_global_knowledge(self, driver, mock_automem_client):
        """Test storing global knowledge"""
        mock_automem_client.store_global_knowledge.return_value = {
            "id": "doc1",
            "memory": {"content": "Policy", "tags": ["category_policies"], "metadata": {}}
        }
        
        result = driver.store_global_knowledge(
            content="Policy document",
            category="policies",
            title="New Policy",
            doc_id="POL-001"
        )
        
        # Verify call
        mock_automem_client.store_global_knowledge.assert_called_once()
        call_args = mock_automem_client.store_global_knowledge.call_args[1]
        
        assert call_args["content"] == "Policy document"
        assert call_args["category"] == "policies"
        assert call_args["metadata"]["title"] == "New Policy"
        assert call_args["metadata"]["doc_id"] == "POL-001"
        assert call_args["metadata"]["category"] == "policies"
    
    def test_delete_memory(self, driver, mock_automem_client):
        """Test deleting a memory"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_automem_client.client.delete.return_value = mock_response
        mock_automem_client.base_url = "http://localhost:8001"
        
        result = driver.delete(memory_id="mem123", user_id="123")
        
        mock_automem_client.client.delete.assert_called_once()
        assert result is True
    
    def test_delete_handles_errors(self, driver, mock_automem_client):
        """Test delete error handling"""
        mock_automem_client.client.delete.side_effect = Exception("Delete failed")
        mock_automem_client.base_url = "http://localhost:8001"
        
        result = driver.delete(memory_id="mem123")
        
        assert result is False
    
    def test_health_check_success(self, driver, mock_automem_client):
        """Test health check when client is healthy"""
        result = driver.health_check()
        
        assert result["status"] == "healthy"
        assert result["driver"] == "automem"
        assert result["connected"] is True
    
    def test_health_check_failure(self):
        """Test health check when client initialization fails"""
        with patch('app.core.memory.automem_driver.get_default_client', 
                  side_effect=Exception("Connection failed")):
            driver = AutoMemDriver()
            result = driver.health_check()
            
            assert result["status"] == "unhealthy"
            assert result["driver"] == "automem"
            assert result["connected"] is False
            assert "Connection failed" in result["error"]
