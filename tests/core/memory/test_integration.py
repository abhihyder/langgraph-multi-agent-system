"""
Integration Tests for Memory Agents with Driver System

Tests that memory and knowledge agent graphs work correctly with the new driver system.
"""

import pytest
from unittest.mock import Mock, patch
from app.agentic.states.agent_state import AgentState
from app.agentic.graphs.memory_graph import MemoryAgentGraph, create_memory_agent_graph
from app.agentic.graphs.knowledge_graph import KnowledgeAgentGraph, create_knowledge_agent_graph


class TestMemoryAgentGraphIntegration:
    """Integration tests for MemoryAgentGraph with driver system"""
    
    @pytest.fixture
    def mock_driver(self):
        """Mock memory driver"""
        driver = Mock()
        driver.recall.return_value = []
        return driver
    
    @pytest.fixture
    def state(self):
        """Sample agent state"""
        return {
            "user_input": "What did we discuss before?",
            "user_id": "user123",
            "conversation_id": "conv456"
        }
    
    @patch('app.agentic.graphs.memory_graph.get_memory_driver')
    def test_memory_agent_graph_uses_driver(self, mock_get_driver, mock_driver, state):
        """Test that memory agent graph uses the configured driver"""
        mock_get_driver.return_value = mock_driver
        
        # Mock driver responses
        mock_driver.recall.side_effect = [
            # Recent messages
            [{
                "id": "1",
                "memory": {"content": "user: Hello", "tags": ["user"], "metadata": {}},
                "user_id": "user123"
            }],
            # Short-term memories
            [{
                "id": "2",
                "memory": {"content": "assistant: Hi there", "tags": ["assistant"], "metadata": {}},
                "user_id": "user123"
            }],
            # Long-term memories
            [{
                "id": "3",
                "memory": {"content": "Previous conversation", "tags": [], "metadata": {}},
                "user_id": "user123"
            }]
        ]
        
        graph = create_memory_agent_graph()
        result = graph.invoke(state)
        
        # Verify driver was called
        assert mock_get_driver.called
        assert mock_driver.recall.call_count == 3
        
        # Verify result structure
        assert "memory_output" in result
        assert result["memory_output"] is not None
    
    @patch('app.agentic.graphs.memory_graph.get_memory_driver')
    def test_memory_agent_graph_without_user_id(self, mock_get_driver, mock_driver):
        """Test memory agent graph returns None when no user_id"""
        mock_get_driver.return_value = mock_driver
        
        state = {
            "user_input": "test",
            "user_id": None
        }
        
        graph = create_memory_agent_graph()
        result = graph.invoke(state)
        
        assert result["memory_output"] is None
        assert not mock_driver.recall.called
    
    @patch('app.agentic.graphs.memory_graph.get_memory_driver')
    def test_memory_agent_graph_handles_driver_errors(self, mock_get_driver, mock_driver, state):
        """Test memory agent graph handles driver errors gracefully"""
        mock_get_driver.return_value = mock_driver
        mock_driver.recall.side_effect = Exception("Driver error")
        
        graph = create_memory_agent_graph()
        result = graph.invoke(state)
        
        # Should handle error and return error state
        assert "memory_output" in result
    
    @patch('app.agentic.graphs.memory_graph.get_memory_driver')
    def test_memory_agent_graph_formats_output_correctly(self, mock_get_driver, mock_driver, state):
        """Test that memory agent graph formats driver output correctly"""
        mock_get_driver.return_value = mock_driver
        
        # Mock complete memory retrieval
        mock_driver.recall.side_effect = [
            # Recent
            [{
                "id": "1",
                "memory": {"content": "user: How are you?", "tags": ["user"], "metadata": {}},
                "user_id": "user123",
                "created_at": "2024-01-01"
            }],
            # Short-term
            [{
                "id": "2",
                "memory": {"content": "assistant: I'm doing well!", "tags": ["assistant"], "metadata": {}},
                "user_id": "user123",
                "created_at": "2024-01-01"
            }],
            # Long-term
            [{
                "id": "3",
                "memory": {"content": "user: Previous topic", "tags": ["user"], "metadata": {}},
                "user_id": "user123",
                "created_at": "2024-01-01"
            }]
        ]
        
        graph = create_memory_agent_graph()
        result = graph.invoke(state)
        
        output = result["memory_output"]
        
        # Should contain all sections
        assert "RECENT CONVERSATION" in output
        assert "RELEVANT FROM THIS CONVERSATION" in output
        assert "RELEVANT FROM PAST CONVERSATIONS" in output


class TestKnowledgeAgentGraphIntegration:
    """Integration tests for KnowledgeAgentGraph with driver system"""
    
    @pytest.fixture
    def mock_driver(self):
        """Mock memory driver"""
        driver = Mock()
        driver.recall_global_knowledge.return_value = []
        return driver
    
    @pytest.fixture
    def state(self):
        """Sample agent state"""
        return {
            "user_input": "What is our company policy?"
        }
    
    @patch('app.agentic.graphs.knowledge_graph.get_memory_driver')
    def test_knowledge_agent_graph_uses_driver(self, mock_get_driver, mock_driver, state):
        """Test that knowledge agent graph uses the configured driver"""
        mock_get_driver.return_value = mock_driver
        
        # Mock driver response
        mock_driver.recall_global_knowledge.return_value = [
            {
                "id": "doc1",
                "memory": {
                    "content": "Company policy document",
                    "tags": ["category_policies", "global_knowledge"],
                    "metadata": {
                        "title": "HR Policy",
                        "doc_id": "POL-001",
                        "category": "policies"
                    }
                },
                "category": "policies"
            }
        ]
        
        graph = create_knowledge_agent_graph()
        result = graph.invoke(state)
        
        # Verify driver was called
        assert mock_get_driver.called
        mock_driver.recall_global_knowledge.assert_called_once_with(
            query=state["user_input"],
            top_k=5
        )
        
        # Verify result
        assert "knowledge_output" in result
        assert result["knowledge_output"] is not None
        assert "Company policy document" in result["knowledge_output"]
    
    @patch('app.agentic.graphs.knowledge_graph.get_memory_driver')
    def test_knowledge_agent_graph_no_results(self, mock_get_driver, mock_driver, state):
        """Test knowledge agent graph when no documents found"""
        mock_get_driver.return_value = mock_driver
        mock_driver.recall_global_knowledge.return_value = []
        
        graph = create_knowledge_agent_graph()
        result = graph.invoke(state)
        
        assert result["knowledge_output"] is None
    
    @patch('app.agentic.graphs.knowledge_graph.get_memory_driver')
    def test_knowledge_agent_graph_handles_driver_errors(self, mock_get_driver, mock_driver, state):
        """Test knowledge agent graph handles driver errors gracefully"""
        mock_get_driver.return_value = mock_driver
        mock_driver.recall_global_knowledge.side_effect = Exception("Driver error")
        
        graph = create_knowledge_agent_graph()
        result = graph.invoke(state)
        
        # Should handle error and return error state
        assert "knowledge_output" in result
    
    @patch('app.agentic.graphs.knowledge_graph.get_memory_driver')
    def test_knowledge_agent_graph_formats_output_with_metadata(self, mock_get_driver, mock_driver, state):
        """Test that knowledge agent graph formats output with document metadata"""
        mock_get_driver.return_value = mock_driver
        
        mock_driver.recall_global_knowledge.return_value = [
            {
                "id": "doc1",
                "memory": {
                    "content": "Policy content",
                    "tags": ["category_policies"],
                    "metadata": {
                        "title": "Policy Title",
                        "doc_id": "POL-001"
                    }
                },
                "category": "policies"
            }
        ]
        
        graph = create_knowledge_agent_graph()
        result = graph.invoke(state)
        
        output = result["knowledge_output"]
        
        # Should contain category tag
        assert "[POLICIES]" in output
        # Should contain content
        assert "Policy content" in output
    
    @patch('app.agentic.graphs.knowledge_graph.get_memory_driver')
    def test_knowledge_agent_graph_multiple_categories(self, mock_get_driver, mock_driver, state):
        """Test knowledge agent graph with documents from multiple categories"""
        mock_get_driver.return_value = mock_driver
        
        mock_driver.recall_global_knowledge.return_value = [
            {
                "id": "doc1",
                "memory": {
                    "content": "Policy doc",
                    "tags": ["category_policies"],
                    "metadata": {"title": "Policy"}
                },
                "category": "policies"
            },
            {
                "id": "doc2",
                "memory": {
                    "content": "Guide doc",
                    "tags": ["category_guidelines"],
                    "metadata": {"title": "Guide"}
                },
                "category": "guidelines"
            }
        ]
        
        graph = create_knowledge_agent_graph()
        result = graph.invoke(state)
        
        output = result["knowledge_output"]
        
        # Should contain both categories
        assert "[POLICIES]" in output
        assert "[GUIDELINES]" in output


class TestDriverSwitching:
    """Tests for seamless driver switching"""
    
    @patch('app.core.memory.manager.get_settings')
    def test_switching_drivers_via_env(self, mock_settings):
        """Test that changing MEMORY_DRIVER env switches driver implementation"""
        from app.core.memory import get_memory_driver
        from app.core.memory.manager import MemoryDriverManager
        
        # Clear caches
        get_memory_driver.cache_clear()
        MemoryDriverManager.reset_cache()
        
        # Set to automem
        mock_settings.return_value.MEMORY_DRIVER = "automem"
        
        with patch('app.core.memory.automem_driver.get_default_client'):
            driver1 = get_memory_driver()
            driver1_type = type(driver1).__name__
        
        # Clear and switch to pgvector
        get_memory_driver.cache_clear()
        MemoryDriverManager.reset_cache()
        mock_settings.return_value.MEMORY_DRIVER = "pgvector"
        mock_settings.return_value.DATABASE_URL = "postgresql://test"
        
        with patch('psycopg2.connect'):
            driver2 = get_memory_driver()
            driver2_type = type(driver2).__name__
        
        # Should be different driver types
        assert driver1_type == "AutoMemDriver"
        assert driver2_type == "PGVectorDriver"
    
    @patch('app.agentic.graphs.memory_graph.get_memory_driver')
    def test_agent_graphs_work_with_any_driver(self, mock_get_driver):
        """Test that agent graphs work regardless of which driver is configured"""
        
        # Create mock drivers
        mock_automem = Mock()
        mock_automem.recall.return_value = []
        
        mock_pgvector = Mock()
        mock_pgvector.recall.return_value = []
        
        state = {
            "user_input": "test",
            "user_id": "user123",
            "conversation_id": "conv1"
        }
        
        # Test with AutoMem driver
        mock_get_driver.return_value = mock_automem
        graph1 = create_memory_agent_graph()
        result1 = graph1.invoke(state)
        assert "memory_output" in result1
        
        # Test with PGVector driver
        mock_get_driver.return_value = mock_pgvector
        graph2 = create_memory_agent_graph()
        result2 = graph2.invoke(state)
        assert "memory_output" in result2
        
        # Both should work identically
        assert result1.keys() == result2.keys()
