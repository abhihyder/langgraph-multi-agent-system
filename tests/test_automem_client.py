"""
Unit Tests for AutoMemClient
Testing memory storage, recall, and association functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.core.automem_client import AutoMemClient, get_default_client


@pytest.mark.unit
@pytest.mark.service
class TestAutoMemClient:
    """Test suite for AutoMemClient"""
    
    def test_client_initialization(self):
        """Test client initializes with correct defaults"""
        client = AutoMemClient()
        
        assert client.base_url == "http://localhost:8001"
        assert client.timeout == 10
        assert client.client is not None
    
    def test_client_initialization_with_custom_params(self):
        """Test client initializes with custom parameters"""
        client = AutoMemClient(
            base_url="http://custom:9000",
            api_token="test_token",
            timeout=20
        )
        
        assert client.base_url == "http://custom:9000"
        assert client.api_token == "test_token"
        assert client.timeout == 20
    
    @patch('app.core.automem_client.get_settings')
    def test_headers_without_token(self, mock_get_settings):
        """Test headers generation without API token"""
        # Mock settings to return None for API token
        mock_settings = Mock()
        mock_settings.AUTOMEM_URL = "http://localhost:8001"
        mock_settings.AUTOMEM_API_TOKEN = None
        mock_settings.AUTOMEM_TIMEOUT = 10
        mock_get_settings.return_value = mock_settings
        
        client = AutoMemClient()
        headers = client._headers()
        
        assert headers["Content-Type"] == "application/json"
        # Should not have Authorization header when no token in settings
        assert "Authorization" not in headers
    
    def test_headers_with_token(self):
        """Test headers generation with API token"""
        client = AutoMemClient(api_token="test_token")
        headers = client._headers()
        
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test_token"
    
    @patch('httpx.Client.get')
    def test_recall_with_conversation_id(self, mock_get):
        """Test recall with conversation_id filtering"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "mem1",
                    "memory": {"content": "Test memory", "tags": ["conversation_1"]},
                    "relations": []
                }
            ],
            "vector_search": {"matched": True}
        }
        mock_get.return_value = mock_response
        
        client = AutoMemClient()
        results = client.recall(
            user_id=1,
            conversation_id=1,
            query="test query",
            top_k=5
        )
        
        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "params" in call_args.kwargs
        assert call_args.kwargs["params"]["tags"] == "conversation_1"
        assert call_args.kwargs["params"]["query"] == "test query"
        assert call_args.kwargs["params"]["limit"] == 5
        
        # Verify results
        assert len(results) == 1
        assert results[0]["id"] == "mem1"
    
    @patch('httpx.Client.get')
    def test_recall_without_conversation_id(self, mock_get):
        """Test recall with only user_id (cross-conversation)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [],
            "vector_search": {"matched": False}
        }
        mock_get.return_value = mock_response
        
        client = AutoMemClient()
        results = client.recall(
            user_id=1,
            conversation_id=None,
            query="test query",
            top_k=10
        )
        
        # Verify tags use user_id when no conversation_id
        call_args = mock_get.call_args
        assert call_args.kwargs["params"]["tags"] == "user_1"
        assert results == []
    
    @patch('httpx.Client.get')
    def test_recall_without_vector_search(self, mock_get):
        """Test recall with tag-only mode (no vector search)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"id": "mem1", "memory": {"content": "Tag match"}}],
            "vector_search": {"matched": False}
        }
        mock_get.return_value = mock_response
        
        client = AutoMemClient()
        results = client.recall(
            user_id=1,
            conversation_id=1,
            query="test",
            use_vector=False
        )
        
        # Verify query is not included in params (tag-only mode)
        call_args = mock_get.call_args
        assert "query" not in call_args.kwargs["params"]
        assert len(results) == 1
    
    @patch('httpx.Client.get')
    def test_recall_handles_api_error(self, mock_get):
        """Test recall handles API errors gracefully"""
        mock_get.side_effect = Exception("API Error")
        
        client = AutoMemClient()
        results = client.recall(user_id=1, conversation_id=1, query="test")
        
        # Should return empty list on error
        assert results == []
    
    @patch('httpx.Client.post')
    @patch('time.sleep')
    def test_store_message_with_conversation_id(self, mock_sleep, mock_post):
        """Test storing message with conversation context"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "new_mem", "status": "stored"}
        mock_post.return_value = mock_response
        
        client = AutoMemClient()
        result = client.store_message(
            user_id=1,
            conversation_id=1,
            role="user",
            content="Test message",
            scope="conversation"
        )
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        
        assert payload["content"] == "Test message"
        assert payload["type"] == "conversation"
        assert "user_1" in payload["tags"]
        assert "user" in payload["tags"]
        assert "conversation_1" in payload["tags"]
        assert payload["importance"] == 0.7  # user messages have higher importance
        
        # Verify sleep was called
        mock_sleep.assert_called_once_with(0.5)
        
        assert result["id"] == "new_mem"  # type: ignore
    
    @patch('httpx.Client.post')
    def test_store_message_without_conversation_id(self, mock_post):
        """Test storing message without conversation context"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "new_mem"}
        mock_post.return_value = mock_response
        
        client = AutoMemClient()
        result = client.store_message(
            user_id=1,
            conversation_id=None,
            role="assistant",
            content="Test response"
        )
        
        payload = mock_post.call_args.kwargs["json"]
        
        assert "user_1" in payload["tags"]
        assert "assistant" in payload["tags"]
        assert payload["importance"] == 0.5  # assistant messages have lower importance
        # No conversation tag
        assert not any(tag.startswith("conversation_") for tag in payload["tags"])
    
    @patch('httpx.Client.post')
    def test_store_message_with_metadata(self, mock_post):
        """Test storing message with custom metadata"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "new_mem"}
        mock_post.return_value = mock_response
        
        client = AutoMemClient()
        metadata = {"source": "test", "timestamp": "2024-01-01"}
        
        result = client.store_message(
            user_id=1,
            conversation_id=1,
            role="user",
            content="Test",
            metadata=metadata
        )
        
        payload = mock_post.call_args.kwargs["json"]
        assert payload["metadata"] == metadata
    
    @patch('httpx.Client.post')
    def test_store_message_handles_error(self, mock_post):
        """Test store_message handles API errors"""
        mock_post.side_effect = Exception("API Error")
        
        client = AutoMemClient()
        result = client.store_message(
            user_id=1,
            conversation_id=1,
            role="user",
            content="Test"
        )
        
        assert result is None
    
    @patch('httpx.Client.post')
    def test_associate_memories(self, mock_post):
        """Test associating two memories"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "associated"}
        mock_post.return_value = mock_response
        
        client = AutoMemClient()
        result = client.associate(
            memory1_id="mem1",
            memory2_id="mem2",
            relation_type="RELATED_TO"
        )
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "/associate" in call_args.args[0]
        
        payload = call_args.kwargs["json"]
        assert payload["memory1_id"] == "mem1"
        assert payload["memory2_id"] == "mem2"
        assert payload["type"] == "RELATED_TO"
        
        assert result is True
    
    @patch('httpx.Client.post')
    def test_associate_handles_error(self, mock_post):
        """Test associate handles API errors"""
        mock_post.side_effect = Exception("API Error")
        
        client = AutoMemClient()
        result = client.associate(memory1_id="mem1", memory2_id="mem2", relation_type="RELATED_TO")
        
        assert result is False
    
    @patch('app.core.automem_client.get_settings')
    def test_get_default_client_from_env(self, mock_get_settings):
        """Test getting default client uses settings from configuration"""
        # Mock settings to return custom values
        mock_settings = Mock()
        mock_settings.AUTOMEM_URL = "http://custom:9000"
        mock_settings.AUTOMEM_API_TOKEN = "env_token"
        mock_settings.AUTOMEM_TIMEOUT = 10
        mock_get_settings.return_value = mock_settings
        
        client = get_default_client()
        
        assert client.base_url == "http://custom:9000"
        assert client.api_token == "env_token"
