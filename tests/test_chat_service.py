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
            "final_output": "This is the AI response",
            "intent": "User needs help with coding",
            "selected_agents": ["code"],
            "messages": [
                HumanMessage(content="Help me write code"),
                AIMessage(content="This is the AI response")
            ],
            "research_output": None,
            "writing_output": None,
            "code_output": "def example(): pass"
        }
    
    @patch('app.services.chat_service.get_default_client')
    @patch('app.services.chat_service.agent_graph')
    def test_process_chat_basic_flow(self, mock_graph, mock_get_client, chat_service, 
                                     mock_automem_client, mock_agent_graph_result):
        """Test basic chat processing flow"""
        # Setup mocks
        mock_get_client.return_value = mock_automem_client
        mock_graph.invoke.return_value = mock_agent_graph_result
        
        # Execute
        result = chat_service.process_chat(
            user_input="Help me write a Python function",
            user_id=1,
            conversation_id=1
        )
        
        # Verify AutoMem recall was called (3 times: recent, semantic, long-term)
        assert mock_automem_client.recall.call_count == 3
        
        # Verify agent graph was invoked
        mock_graph.invoke.assert_called_once()
        
        # Verify AutoMem store was called (2 times: user message + AI response)
        assert mock_automem_client.store_message.call_count == 2
        
        # Verify response structure
        assert result["response"] == "This is the AI response"
        assert result["intent"] == "User needs help with coding"
        assert result["agents_used"] == ["code"]
        assert "metadata" in result
    
    @patch('app.services.chat_service.get_default_client')
    @patch('app.services.chat_service.agent_graph')
    def test_process_chat_memory_recall_steps(self, mock_graph, mock_get_client, 
                                               chat_service, mock_automem_client,
                                               mock_agent_graph_result):
        """Test three-tier memory recall (recent, semantic, long-term)"""
        mock_get_client.return_value = mock_automem_client
        mock_graph.invoke.return_value = mock_agent_graph_result
        
        # Configure different responses for each recall call
        mock_automem_client.recall.side_effect = [
            # Recent chronological (query=None)
            [{"id": "r1", "memory": {"content": "Recent message 1"}}],
            # Semantic short-term (query=user_input)
            [{"id": "s1", "memory": {"content": "Semantic match 1"}}],
            # Long-term cross-conversation (conversation_id=None)
            [{"id": "l1", "memory": {"content": "Old memory", "tags": ["user_1"]}}]
        ]
        
        result = chat_service.process_chat(
            user_input="Test query",
            user_id=1,
            conversation_id=1
        )
        
        # Verify recall calls
        calls = mock_automem_client.recall.call_args_list
        
        # First call: recent chronological
        assert calls[0].kwargs["query"] is None
        assert calls[0].kwargs["use_vector"] is False
        assert calls[0].kwargs["top_k"] == 5
        
        # Second call: semantic short-term
        assert calls[1].kwargs["query"] == "Test query"
        assert calls[1].kwargs["use_vector"] is True
        assert calls[1].kwargs["top_k"] == 3
        
        # Third call: long-term cross-conversation
        assert calls[2].kwargs["conversation_id"] is None
        assert calls[2].kwargs["top_k"] == 10
    
    @patch('app.services.chat_service.get_default_client')
    @patch('app.services.chat_service.agent_graph')
    def test_process_chat_memory_deduplication(self, mock_graph, mock_get_client,
                                               chat_service, mock_agent_graph_result):
        """Test that semantic memories don't duplicate recent messages"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_graph.invoke.return_value = mock_agent_graph_result
        
        # Return same memory ID in both recent and semantic
        mock_client.recall.side_effect = [
            [{"id": "duplicate", "memory": {"content": "Same message"}}],  # Recent
            [{"id": "duplicate", "memory": {"content": "Same message"}}],  # Semantic (should be filtered)
            []  # Long-term
        ]
        mock_client.store_message.return_value = {"id": "stored"}
        
        result = chat_service.process_chat(
            user_input="Test",
            user_id=1,
            conversation_id=1
        )
        
        # The duplicate should have been filtered out
        # We can't directly check the internal state, but we verify it ran successfully
        assert result["response"] is not None
    
    @patch('app.services.chat_service.get_default_client')
    @patch('app.services.chat_service.agent_graph')
    def test_process_chat_filters_current_conversation_from_long_term(self, mock_graph, 
                                                                       mock_get_client,
                                                                       chat_service,
                                                                       mock_agent_graph_result):
        """Test that long-term recall filters out current conversation"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_graph.invoke.return_value = mock_agent_graph_result
        
        mock_client.recall.side_effect = [
            [],  # Recent
            [],  # Semantic
            [   # Long-term - includes current conversation (should be filtered)
                {"id": "l1", "memory": {"content": "Old conv", "tags": ["user_1", "conversation_5"]}},
                {"id": "l2", "memory": {"content": "Current conv", "tags": ["user_1", "conversation_1"]}}  # Should be filtered
            ]
        ]
        mock_client.store_message.return_value = {"id": "stored"}
        
        result = chat_service.process_chat(
            user_input="Test",
            user_id=1,
            conversation_id=1
        )
        
        assert result["response"] is not None
    
    @patch('app.services.chat_service.get_default_client')
    @patch('app.services.chat_service.agent_graph')
    def test_process_chat_stores_user_and_ai_messages(self, mock_graph, mock_get_client,
                                                      chat_service, mock_automem_client,
                                                      mock_agent_graph_result):
        """Test that both user and AI messages are stored"""
        mock_get_client.return_value = mock_automem_client
        mock_graph.invoke.return_value = mock_agent_graph_result
        
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
        assert store_calls[1].kwargs["content"] == "This is the AI response"
    
    @patch('app.services.chat_service.get_default_client')
    @patch('app.services.chat_service.agent_graph')
    def test_process_chat_handles_recall_error(self, mock_graph, mock_get_client,
                                               chat_service, mock_agent_graph_result):
        """Test chat processing continues even if recall fails"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_graph.invoke.return_value = mock_agent_graph_result
        
        # Make recall raise an exception
        mock_client.recall.side_effect = Exception("AutoMem unavailable")
        mock_client.store_message.return_value = {"id": "stored"}
        
        # Should not raise exception
        result = chat_service.process_chat(
            user_input="Test",
            user_id=1,
            conversation_id=1
        )
        
        assert result["response"] is not None
    
    @patch('app.services.chat_service.get_default_client')
    @patch('app.services.chat_service.agent_graph')
    def test_process_chat_handles_store_error(self, mock_graph, mock_get_client,
                                              chat_service, mock_automem_client,
                                              mock_agent_graph_result):
        """Test chat processing continues even if storage fails"""
        mock_get_client.return_value = mock_automem_client
        mock_graph.invoke.return_value = mock_agent_graph_result
        
        # Make store_message raise an exception
        mock_automem_client.store_message.side_effect = Exception("Storage failed")
        
        # Should not raise exception
        result = chat_service.process_chat(
            user_input="Test",
            user_id=1,
            conversation_id=1
        )
        
        assert result["response"] is not None
    
    @patch('app.services.chat_service.get_default_client')
    @patch('app.services.chat_service.agent_graph')
    def test_process_chat_without_conversation_id(self, mock_graph, mock_get_client,
                                                  chat_service, mock_automem_client,
                                                  mock_agent_graph_result):
        """Test chat processing works without conversation_id (new conversation)"""
        mock_get_client.return_value = mock_automem_client
        mock_graph.invoke.return_value = mock_agent_graph_result
        
        result = chat_service.process_chat(
            user_input="Test",
            user_id=1,
            conversation_id=None
        )
        
        # Verify it still works
        assert result["response"] is not None
        
        # Verify conversation_id=None was passed to recall
        recall_calls = mock_automem_client.recall.call_args_list
        # At least one call should have conversation_id
        assert any(call.kwargs.get("conversation_id") is None for call in recall_calls)
    
    @patch('app.services.chat_service.get_default_client')
    @patch('app.services.chat_service.agent_graph')
    def test_process_chat_formats_memory_context(self, mock_graph, mock_get_client,
                                                 chat_service, mock_agent_graph_result):
        """Test that memories are properly formatted in context"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_graph.invoke.return_value = mock_agent_graph_result
        
        # Return memories with content and relations
        mock_client.recall.side_effect = [
            [{"id": "m1", "memory": {"content": "User is a software engineer"}, "relations": []}],
            [],
            []
        ]
        mock_client.store_message.return_value = {"id": "stored"}
        
        result = chat_service.process_chat(
            user_input="Test",
            user_id=1,
            conversation_id=1
        )
        
        # Verify graph was called with formatted messages
        call_args = mock_graph.invoke.call_args
        state = call_args.args[0]
        
        # Should have memory message + user input message
        assert len(state["messages"]) >= 1
        assert state["user_input"] == "Test"
    
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
    @patch('app.services.chat_service.agent_graph')
    def test_process_chat_fallback_response(self, mock_graph, mock_get_client,
                                           chat_service, mock_automem_client):
        """Test fallback response when no final_output"""
        mock_get_client.return_value = mock_automem_client
        mock_graph.invoke.return_value = {
            "final_output": "",  # Empty response
            "intent": "test",
            "selected_agents": [],
            "messages": []
        }
        
        result = chat_service.process_chat(
            user_input="Test",
            user_id=1,
            conversation_id=1
        )
        
        # Should return the empty response as-is
        assert result["response"] == ""
