"""
Unit Tests for Orchestrator Agent
Testing intent detection and agent routing
"""

import pytest
import json
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage
from app.agentic.orchestrator import orchestrator_router, should_route_to_agents


@pytest.mark.unit
@pytest.mark.agent
class TestOrchestratorRouter:
    """Test suite for Orchestrator routing logic"""
    
    @patch('app.agentic.orchestrator.get_llm')
    @patch('app.agentic.orchestrator.load_prompt')
    def test_orchestrator_routes_to_code_agent(self, mock_load_prompt, mock_llm_class):
        """Test orchestrator routes coding requests to code agent"""
        # Setup mocks
        mock_load_prompt.return_value = "You are an orchestrator"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = json.dumps({
            "intent": "User needs help with Python coding",
            "selected_agents": ["code"]
        })
        mock_llm.invoke.return_value = mock_response
        
        # Create state
        state = {
            "user_input": "Help me write a Python function",
            "messages": [],
            "selected_agents": []
        }
        
        # Execute
        result = orchestrator_router(state)  # type: ignore  # type: ignore
        
        # Verify
        assert result["intent"] == "User needs help with Python coding"
        assert result["selected_agents"] == ["code"]
        mock_llm.invoke.assert_called_once()
    
    @patch('app.agentic.orchestrator.get_llm')
    @patch('app.agentic.orchestrator.load_prompt')
    def test_orchestrator_routes_to_research_agent(self, mock_load_prompt, mock_llm_class):
        """Test orchestrator routes research requests to research agent"""
        mock_load_prompt.return_value = "You are an orchestrator"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = json.dumps({
            "intent": "User needs to research AI trends",
            "selected_agents": ["research"]
        })
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_input": "What are the latest AI trends?",
            "messages": [],
            "selected_agents": []
        }
        
        result = orchestrator_router(state)  # type: ignore  # type: ignore
        
        assert result["intent"] == "User needs to research AI trends"
        assert result["selected_agents"] == ["research"]
    
    @patch('app.agentic.orchestrator.get_llm')
    @patch('app.agentic.orchestrator.load_prompt')
    def test_orchestrator_routes_to_writing_agent(self, mock_load_prompt, mock_llm_class):
        """Test orchestrator routes writing requests to writing agent"""
        mock_load_prompt.return_value = "You are an orchestrator"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = json.dumps({
            "intent": "User wants to write an article",
            "selected_agents": ["writing"]
        })
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_input": "Write an article about climate change",
            "messages": [],
            "selected_agents": []
        }
        
        result = orchestrator_router(state)  # type: ignore  # type: ignore
        
        assert result["intent"] == "User wants to write an article"
        assert result["selected_agents"] == ["writing"]
    
    @patch('app.agentic.orchestrator.get_llm')
    @patch('app.agentic.orchestrator.load_prompt')
    def test_orchestrator_routes_to_general_agent(self, mock_load_prompt, mock_llm_class):
        """Test orchestrator routes general questions to general agent"""
        mock_load_prompt.return_value = "You are an orchestrator"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = json.dumps({
            "intent": "General conversation",
            "selected_agents": ["general"]
        })
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_input": "What's your name?",
            "messages": [],
            "selected_agents": []
        }
        
        result = orchestrator_router(state)  # type: ignore  # type: ignore
        
        assert result["intent"] == "General conversation"
        assert result["selected_agents"] == ["general"]
    
    @patch('app.agentic.orchestrator.get_llm')
    @patch('app.agentic.orchestrator.load_prompt')
    def test_orchestrator_routes_to_multiple_agents(self, mock_load_prompt, mock_llm_class):
        """Test orchestrator can route to multiple agents"""
        mock_load_prompt.return_value = "You are an orchestrator"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = json.dumps({
            "intent": "Research and write an article",
            "selected_agents": ["research", "writing"]
        })
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_input": "Research AI trends and write an article about them",
            "messages": [],
            "selected_agents": []
        }
        
        result = orchestrator_router(state)  # type: ignore  # type: ignore
        
        assert result["intent"] == "Research and write an article"
        assert "research" in result["selected_agents"]
        assert "writing" in result["selected_agents"]
    
    @patch('app.agentic.orchestrator.get_llm')
    @patch('app.agentic.orchestrator.load_prompt')
    def test_orchestrator_handles_json_in_code_block(self, mock_load_prompt, mock_llm_class):
        """Test orchestrator parses JSON wrapped in markdown code blocks"""
        mock_load_prompt.return_value = "You are an orchestrator"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        # Response with markdown code block
        mock_response = Mock()
        mock_response.content = """```json
{
    "intent": "User needs coding help",
    "selected_agents": ["code"]
}
```"""
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_input": "Write Python code",
            "messages": [],
            "selected_agents": []
        }
        
        result = orchestrator_router(state)  # type: ignore  # type: ignore
        
        # Should successfully parse despite markdown wrapper
        assert result["intent"] == "User needs coding help"
        assert result["selected_agents"] == ["code"]
    
    @patch('app.agentic.orchestrator.get_llm')
    @patch('app.agentic.orchestrator.load_prompt')
    def test_orchestrator_handles_invalid_json(self, mock_load_prompt, mock_llm_class):
        """Test orchestrator handles invalid JSON gracefully"""
        mock_load_prompt.return_value = "You are an orchestrator"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = "This is not valid JSON"
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_input": "Test",
            "messages": [],
            "selected_agents": []
        }
        
        result = orchestrator_router(state)  # type: ignore  # type: ignore
        
        # Should fallback to writing agent
        assert "fallback" in result["intent"]
        assert result["selected_agents"] == ["writing"]
    
    @patch('app.agentic.orchestrator.get_llm')
    @patch('app.agentic.orchestrator.load_prompt')
    def test_orchestrator_uses_correct_model(self, mock_load_prompt, mock_llm_class):
        """Test orchestrator uses correct model and temperature"""
        mock_load_prompt.return_value = "You are an orchestrator"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = json.dumps({
            "intent": "test",
            "selected_agents": ["general"]
        })
        mock_llm.invoke.return_value = mock_response
        
        state = {"user_input": "test", "messages": [], "selected_agents": []}
        
        orchestrator_router(state)  # type: ignore  # type: ignore
        
        # Verify LLM was initialized with correct params
        mock_llm_class.assert_called_once()
        call_args = mock_llm_class.call_args
        assert call_args[1]['temperature'] == 0.0
    
    def test_should_route_to_agents_returns_selected_agents(self):
        """Test should_route_to_agents returns correct agent list"""
        state = {
            "selected_agents": ["code", "research"]
        }
        
        result = should_route_to_agents(state)  # type: ignore  # type: ignore
        
        assert result == ["code", "research"]
    
    def test_should_route_to_agents_returns_empty_list(self):
        """Test should_route_to_agents handles empty state"""
        state = {}
        
        result = should_route_to_agents(state)  # type: ignore  # type: ignore
        
        assert result == []
    
    @patch('app.agentic.orchestrator.get_llm')
    @patch('app.agentic.orchestrator.load_prompt')
    def test_orchestrator_includes_user_input_in_prompt(self, mock_load_prompt, mock_llm_class):
        """Test orchestrator includes user input in LLM prompt"""
        mock_load_prompt.return_value = "System prompt"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = json.dumps({"intent": "test", "selected_agents": ["general"]})
        mock_llm.invoke.return_value = mock_response
        
        user_input_text = "What is machine learning?"
        state = {
            "user_input": user_input_text,
            "messages": [],
            "selected_agents": []
        }
        
        orchestrator_router(state)  # type: ignore  # type: ignore
        
        # Verify user input was included in messages
        call_args = mock_llm.invoke.call_args
        messages = call_args.args[0]
        
        # Should have SystemMessage and HumanMessage
        assert len(messages) == 2
        assert user_input_text in str(messages[1].content)
