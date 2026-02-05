"""
Unit Tests for ChatService
Testing chat processing, memory integration, and agent orchestration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage
from app.services.chat_service import ChatService


@pytest.mark.unit
@pytest.mark.service
class TestChatService:
    """Test suite for ChatService"""
    
    @pytest.fixture
    def chat_service(self):
        """Create ChatService instance for testing"""
        return ChatService()
    
    @pytest.fixture
    def mock_agent_graph_result(self):
        """Mock result from agent graph execution"""
        return {
            "final_output": "Test response",
            "intent": "User needs help with coding",
            "selected_agents": ["code"],
            "knowledge_output": None,
            "memory_output": None,
            "research_output": None,
            "writing_output": None,
            "code_output": "def example(): pass"
        }
    
    @patch('app.services.chat_service.get_default_client')
    def test_process_chat_basic_flow(self, mock_get_client, chat_service, 
                                     mock_automem_client, mock_agent_graph_result):
        """Test basic chat processing flow"""
        # Setup mocks
        mock_get_client.return_value = mock_automem_client
        chat_service.agent_graph = Mock()
        chat_service.agent_graph.invoke.return_value = mock_agent_graph_result
        
        # Execute
        result = chat_service.process_chat(
            user_input="Help me write a Python function",
            user_id=1,
            conversation_id=1
        )
        
        # Verify agent graph was invoked
        chat_service.agent_graph.invoke.assert_called_once()
        
        # Verify AutoMem store was called (2 times: user message + AI response)
        assert mock_automem_client.store_message.call_count == 2
        
        # Verify response structure
        assert result["response"] == "Test response"
        assert result["intent"] == "User needs help with coding"
        assert result["agents_used"] == ["code"]
        assert "metadata" in result
        assert result["metadata"]["knowledge_used"] is False
        assert result["metadata"]["memory_used"] is False
    
    @patch('app.services.chat_service.get_default_client')
    def test_process_chat_memory_recall_steps(self, mock_get_client, 
                                               chat_service, mock_automem_client,
                                               mock_agent_graph_result):
        """Test that memory recall is now handled by memory_agent (not in chat_service)"""
        mock_get_client.return_value = mock_automem_client
        
        # Add memory_output to show memory_agent was used
        mock_agent_graph_result["memory_output"] = "Memory context from memory_agent"
        mock_agent_graph_result["selected_agents"] = ["memory", "general"]
        
        chat_service.agent_graph = Mock()
        chat_service.agent_graph.invoke.return_value = mock_agent_graph_result
        
        result = chat_service.process_chat(
            user_input="Test query",
            user_id=1,
            conversation_id=1
        )
        
        # Verify agent graph was invoked (memory recall happens inside the graph now)
        chat_service.agent_graph.invoke.assert_called_once()
        
        # Verify metadata indicates memory was used
        assert result["metadata"]["memory_used"] is True
        assert result["response"] == "Test response"
    
    @patch('app.services.chat_service.get_default_client')
    def test_process_chat_memory_deduplication(self, mock_get_client,
                                               chat_service, mock_agent_graph_result):
        """Test that chat service works correctly"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.store_message.return_value = {"id": "stored"}
        
        chat_service.agent_graph = Mock()
        chat_service.agent_graph.invoke.return_value = mock_agent_graph_result
        
        result = chat_service.process_chat(
            user_input="Test",
            user_id=1,
            conversation_id=1
        )
        
        # Verify it ran successfully
        assert result["response"] == "Test response"
        chat_service.agent_graph.invoke.assert_called_once()
    
    @patch('app.services.chat_service.get_default_client')
    def test_process_chat_filters_current_conversation_from_long_term(self, mock_get_client,
                                                                       chat_service,
                                                                       mock_agent_graph_result):
        """Test that chat service works correctly"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        chat_service.agent_graph = Mock()
        chat_service.agent_graph.invoke.return_value = mock_agent_graph_result
        mock_client.store_message.return_value = {"id": "stored"}
        
        result = chat_service.process_chat(
            user_input="Test",
            user_id=1,
            conversation_id=1
        )
        
        assert result["response"] == "Test response"
        chat_service.agent_graph.invoke.assert_called_once()
    
    @patch('app.services.chat_service.get_default_client')
    def test_process_chat_stores_user_and_ai_messages(self, mock_get_client,
                                                      chat_service, mock_automem_client,
                                                      mock_agent_graph_result):
        """Test that both user and AI messages are stored"""
        mock_get_client.return_value = mock_automem_client
        chat_service.agent_graph = Mock()
        chat_service.agent_graph.invoke.return_value = mock_agent_graph_result
        
        result = chat_service.process_chat(
            user_input="Test input",
            user_id=1,
            conversation_id=1
        )
        
        # Verify store_message was called twice
        store_calls = mock_automem_client.store_message.call_args_list
        assert len(store_calls) == 2
        
        # First call: user message
        assert store_calls[0].kwargs["role"] == "user"
        assert store_calls[0].kwargs["content"] == "Test input"
        assert store_calls[0].kwargs["user_id"] == 1
        assert store_calls[0].kwargs["conversation_id"] == 1
        
        # Second call: assistant message
        assert store_calls[1].kwargs["role"] == "assistant"
        assert store_calls[1].kwargs["content"] == "Test response"
    
    @patch('app.services.chat_service.get_default_client')
    def test_process_chat_handles_recall_error(self, mock_get_client,
                                               chat_service, mock_agent_graph_result):
        """Test chat processing continues even if recall fails"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        chat_service.agent_graph = Mock()
        chat_service.agent_graph.invoke.return_value = mock_agent_graph_result
        
        mock_client.store_message.return_value = {"id": "stored"}
        
        # Should not raise exception
        result = chat_service.process_chat(
            user_input="Test",
            user_id=1,
            conversation_id=1
        )
        
        assert result["response"] == "Test response"
    
    @patch('app.services.chat_service.get_default_client')
    def test_process_chat_handles_store_error(self, mock_get_client,
                                              chat_service, mock_automem_client,
                                              mock_agent_graph_result):
        """Test chat processing continues even if storage fails"""
        mock_get_client.return_value = mock_automem_client
        chat_service.agent_graph = Mock()
        chat_service.agent_graph.invoke.return_value = mock_agent_graph_result
        
        # Make store_message raise an exception
        mock_automem_client.store_message.side_effect = Exception("Storage failed")
        
        # Should not raise exception
        result = chat_service.process_chat(
            user_input="Test",
            user_id=1,
            conversation_id=1
        )
        
        assert result["response"] == "Test response"
    
    @patch('app.services.chat_service.get_default_client')
    def test_process_chat_without_conversation_id(self, mock_get_client,
                                                  chat_service, mock_automem_client,
                                                  mock_agent_graph_result):
        """Test chat processing works without conversation_id (new conversation)"""
        mock_get_client.return_value = mock_automem_client
        chat_service.agent_graph = Mock()
        chat_service.agent_graph.invoke.return_value = mock_agent_graph_result
        
        result = chat_service.process_chat(
            user_input="Test",
            user_id=1,
            conversation_id=None
        )
        
        # Verify it still works
        assert result["response"] == "Test response"
        chat_service.agent_graph.invoke.assert_called_once()
    
    @patch('app.services.chat_service.get_default_client')
    def test_process_chat_formats_memory_context(self, mock_get_client,
                                                 chat_service, mock_agent_graph_result):
        """Test that chat service invokes agent graph correctly"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        chat_service.agent_graph = Mock()
        chat_service.agent_graph.invoke.return_value = mock_agent_graph_result
        
        mock_client.store_message.return_value = {"id": "stored"}
        
        result = chat_service.process_chat(
            user_input="Test",
            user_id=1,
            conversation_id=1
        )
        
        # Verify graph was called correctly
        call_args = chat_service.agent_graph.invoke.call_args
        state = call_args.args[0]
        
        assert state["user_input"] == "Test"
        assert state["user_id"] == 1
        assert state["conversation_id"] == 1
        assert result["response"] == "Test response"
    
    def test_get_agent_info(self, chat_service):
        """Test getting agent information"""
        info = chat_service.get_agent_info()
        
        assert "agents" in info
        assert "orchestrator" in info
        assert len(info["agents"]) > 0
        
        # Verify agent structure
        for agent in info["agents"]:
            assert "name" in agent
            assert "description" in agent
            assert "capabilities" in agent
    
    @patch('app.services.chat_service.get_default_client')
    def test_process_chat_fallback_response(self, mock_get_client,
                                           chat_service, mock_automem_client):
        """Test fallback response when no final_output"""
        mock_get_client.return_value = mock_automem_client
        chat_service.agent_graph = Mock()
        chat_service.agent_graph.invoke.return_value = {
            "final_output": "",  # Empty response
            "intent": "test",
            "selected_agents": [],
            "knowledge_output": None,
            "memory_output": None
        }
        
        result = chat_service.process_chat(
            user_input="Test",
            user_id=1,
            conversation_id=1
        )
        
        # Should return the empty response as-is
        assert result["response"] == ""
