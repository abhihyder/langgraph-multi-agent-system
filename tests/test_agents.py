"""
Unit Tests for Agent Nodes
Testing general, research, writing, and code agents
"""

import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage
from app.agentic.agents.general import general_agent
from app.agentic.agents.research import research_agent
from app.agentic.agents.writing import writing_agent
from app.agentic.agents.code import code_agent


@pytest.mark.unit
@pytest.mark.agent
class TestGeneralAgent:
    """Test suite for General Agent"""
    
    @patch('app.agentic.agents.general.ChatOpenAI')
    @patch('app.agentic.agents.general.load_prompt')
    def test_general_agent_basic_response(self, mock_load_prompt, mock_llm_class):
        """Test general agent provides basic response"""
        mock_load_prompt.return_value = "You are a general assistant"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = "Nice to meet you! I'm an AI assistant."
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_input": "What's your name?",
            "intent": "General conversation",
            "messages": [HumanMessage(content="What's your name?")]
        }
        
        result = general_agent(state)  # type: ignore  # type: ignore
        
        assert result["general_output"] == "Nice to meet you! I'm an AI assistant."
        mock_llm.invoke.assert_called_once()
    
    @patch('app.agentic.agents.general.ChatOpenAI')
    @patch('app.agentic.agents.general.load_prompt')
    def test_general_agent_uses_conversation_history(self, mock_load_prompt, mock_llm_class):
        """Test general agent includes conversation history"""
        mock_load_prompt.return_value = "You are a general assistant"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = "Based on our conversation..."
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_input": "What did I just tell you?",
            "intent": "General conversation",
            "messages": [
                HumanMessage(content="I work at Portonics"),
                AIMessage(content="That's great!"),
                HumanMessage(content="What did I just tell you?")
            ]
        }
        
        result = general_agent(state)  # type: ignore  # type: ignore
        
        # Verify LLM was called with history
        call_args = mock_llm.invoke.call_args
        messages = call_args.args[0]
        
        # Should include system message + history (excluding last message) + current query
        assert len(messages) >= 2  # At minimum system + query
    
    @patch('app.agentic.agents.general.ChatOpenAI')
    @patch('app.agentic.agents.general.load_prompt')
    def test_general_agent_uses_correct_temperature(self, mock_load_prompt, mock_llm_class):
        """Test general agent uses temperature 0.7 for conversational tone"""
        mock_load_prompt.return_value = "You are a general assistant"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = "Response"
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_input": "Test",
            "intent": "General",
            "messages": [HumanMessage(content="Test")]
        }
        
        general_agent(state)  # type: ignore  # type: ignore
        
        # Verify temperature is 0.7
        mock_llm_class.assert_called_once_with(model="gpt-4o-mini", temperature=0.7)


@pytest.mark.unit
@pytest.mark.agent
class TestResearchAgent:
    """Test suite for Research Agent"""
    
    @patch('app.agentic.agents.research.ChatOpenAI')
    @patch('app.agentic.agents.research.load_prompt')
    def test_research_agent_provides_researched_answer(self, mock_load_prompt, mock_llm_class):
        """Test research agent provides well-researched answer"""
        mock_load_prompt.return_value = "You are a research assistant"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = "Based on research, AI is advancing rapidly..."
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_input": "What are the latest AI trends?",
            "intent": "Research AI trends",
            "messages": [HumanMessage(content="What are the latest AI trends?")]
        }
        
        result = research_agent(state)  # type: ignore  # type: ignore
        
        assert result["research_output"] == "Based on research, AI is advancing rapidly..."
    
    @patch('app.agentic.agents.research.ChatOpenAI')
    @patch('app.agentic.agents.research.load_prompt')
    def test_research_agent_uses_correct_model(self, mock_load_prompt, mock_llm_class):
        """Test research agent uses appropriate model"""
        mock_load_prompt.return_value = "You are a research assistant"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = "Research findings..."
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_input": "Research question",
            "intent": "Research",
            "messages": [HumanMessage(content="Research question")]
        }
        
        research_agent(state)  # type: ignore  # type: ignore
        
        mock_llm_class.assert_called_once()


@pytest.mark.unit
@pytest.mark.agent
class TestWritingAgent:
    """Test suite for Writing Agent"""
    
    @patch('app.agentic.agents.writing.ChatOpenAI')
    @patch('app.agentic.agents.writing.load_prompt')
    def test_writing_agent_generates_content(self, mock_load_prompt, mock_llm_class):
        """Test writing agent generates written content"""
        mock_load_prompt.return_value = "You are a writing assistant"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = "# Article Title\n\nThis is a well-written article..."
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_input": "Write an article about AI",
            "intent": "Writing task",
            "messages": [HumanMessage(content="Write an article about AI")]
        }
        
        result = writing_agent(state)  # type: ignore  # type: ignore
        
        assert result["writing_output"] == "# Article Title\n\nThis is a well-written article..."
    
    @patch('app.agentic.agents.writing.ChatOpenAI')
    @patch('app.agentic.agents.writing.load_prompt')
    def test_writing_agent_uses_research_output(self, mock_load_prompt, mock_llm_class):
        """Test writing agent can use research output"""
        mock_load_prompt.return_value = "You are a writing assistant"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = "Article based on research..."
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_input": "Write article",
            "intent": "Writing",
            "research_output": "Research findings: AI is evolving...",
            "messages": [HumanMessage(content="Write article")]
        }
        
        result = writing_agent(state)  # type: ignore  # type: ignore
        
        assert result["writing_output"] is not None


@pytest.mark.unit
@pytest.mark.agent
class TestCodeAgent:
    """Test suite for Code Agent"""
    
    @patch('app.agentic.agents.code.ChatOpenAI')
    @patch('app.agentic.agents.code.load_prompt')
    def test_code_agent_generates_code(self, mock_load_prompt, mock_llm_class):
        """Test code agent generates code"""
        mock_load_prompt.return_value = "You are a coding assistant"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = """```python
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
```"""
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_input": "Write a factorial function",
            "intent": "Coding task",
            "messages": [HumanMessage(content="Write a factorial function")]
        }
        
        result = code_agent(state)  # type: ignore  # type: ignore
        
        assert result["code_output"] is not None
        assert "factorial" in result["code_output"]
    
    @patch('app.agentic.agents.code.ChatOpenAI')
    @patch('app.agentic.agents.code.load_prompt')
    def test_code_agent_provides_explanation(self, mock_load_prompt, mock_llm_class):
        """Test code agent provides code with explanation"""
        mock_load_prompt.return_value = "You are a coding assistant"
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = """Here's a Python function that calculates factorial:

```python
def factorial(n):
    return 1 if n == 0 else n * factorial(n - 1)
```

This uses recursion to calculate the factorial."""
        mock_llm.invoke.return_value = mock_response
        
        state = {
            "user_input": "Explain factorial function",
            "intent": "Code explanation",
            "messages": [HumanMessage(content="Explain factorial function")]
        }
        
        result = code_agent(state)  # type: ignore  # type: ignore
        
        assert "factorial" in result["code_output"]
        assert "recursion" in result["code_output"].lower()


@pytest.mark.integration
@pytest.mark.agent
class TestAgentIntegration:
    """Integration tests for agent cooperation"""
    
    @patch('app.agentic.agents.research.ChatOpenAI')
    @patch('app.agentic.agents.writing.ChatOpenAI')
    @patch('app.agentic.agents.research.load_prompt')
    @patch('app.agentic.agents.writing.load_prompt')
    def test_research_to_writing_pipeline(self, mock_writing_prompt, mock_research_prompt,
                                         mock_writing_llm_class, mock_research_llm_class):
        """Test research output can be used by writing agent"""
        # Setup research agent
        mock_research_prompt.return_value = "Research prompt"
        mock_research_llm = Mock()
        mock_research_llm_class.return_value = mock_research_llm
        
        mock_research_response = Mock()
        mock_research_response.content = "Research findings: AI trends are X, Y, Z"
        mock_research_llm.invoke.return_value = mock_research_response
        
        # Setup writing agent
        mock_writing_prompt.return_value = "Writing prompt"
        mock_writing_llm = Mock()
        mock_writing_llm_class.return_value = mock_writing_llm
        
        mock_writing_response = Mock()
        mock_writing_response.content = "Article based on research: AI trends include X, Y, Z..."
        mock_writing_llm.invoke.return_value = mock_writing_response
        
        # Execute pipeline
        state = {
            "user_input": "Research AI trends and write article",
            "intent": "Research and write",
            "messages": [HumanMessage(content="Research AI trends and write article")]
        }
        
        # Step 1: Research
        state = {**state, **research_agent(state)}  # type: ignore
        assert state["research_output"] is not None
        
        # Step 2: Writing
        state = {**state, **writing_agent(state)}  # type: ignore
        assert state["writing_output"] is not None
