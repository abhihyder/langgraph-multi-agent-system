"""
LLM Node - For reasoning, planning, generation tasks

Handles:
- Intent parsing
- Content generation
- Reasoning and planning
- Natural language understanding
"""

from typing import Dict, Any, Optional, List
import logging

from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_core.language_models import BaseChatModel

from ..utils.node_base import BaseNode, NodeConfig
from ..graphs.base_graph import NodeType, log_node_execution, retry_on_failure
from ...utils.llm_factory import get_llm
from ...utils.helpers import load_prompt

logger = logging.getLogger(__name__)


class LLMNode(BaseNode):
    """
    LLM Node for AI-powered reasoning and generation.
    
    Features:
    - Configurable temperature per node
    - Prompt template support
    - System and user message handling
    - Token usage tracking
    
    Example:
        node = LLMNode(
            config=NodeConfig(name="parse_intent", node_type=NodeType.LLM),
            prompt_template="email_intent.md",
            model_name="gpt-4",
            temperature=0.3
        )
    """
    
    def __init__(
        self,
        config: NodeConfig,
        prompt_template: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model_name: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ):
        super().__init__(config)
        self.prompt_template = prompt_template
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.llm: Optional[BaseChatModel] = None
    
    def _get_llm(self) -> BaseChatModel:
        """Lazy load LLM"""
        if not self.llm:
            llm_config = f"openai:{self.model_name}"
            self.llm = get_llm(
                llm_config=llm_config,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        if not self.llm:
            raise ValueError("Failed to initialize LLM")
        return self.llm
    
    def _prepare_messages(self, state: Dict[str, Any]) -> List[BaseMessage]:
        """Prepare messages for LLM from state and prompts"""
        messages = []
        
        # Add system prompt
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))
        elif self.prompt_template:
            prompt_content = load_prompt(self.prompt_template)
            messages.append(SystemMessage(content=prompt_content))
        
        # Add user input
        user_input = state.get("user_input") or state.get("user_request", "")
        if user_input:
            messages.append(HumanMessage(content=user_input))
        
        # Add any additional context from state
        if "additional_context" in state:
            context = state["additional_context"]
            messages.append(HumanMessage(content=f"Context: {context}"))
        
        return messages
    
    @log_node_execution(NodeType.LLM)
    @retry_on_failure(max_retries=3)
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM node"""
        logger.info(f"LLM Node '{self.name}': Preparing LLM call (model={self.model_name}, temp={self.temperature})")
        
        try:
            llm = self._get_llm()
            messages = self._prepare_messages(state)
            
            # Invoke LLM
            response = llm.invoke(messages)
            
            # Extract content
            content = str(response.content) if hasattr(response, "content") else str(response)
            
            logger.info(f"LLM Node '{self.name}': Received response ({len(content)} chars)")
            
            # Store response in state
            state[f"{self.name}_response"] = content
            
            # If this is a parsing node, try to extract structured data
            if "parse" in self.name.lower():
                import json
                try:
                    parsed = json.loads(content)
                    state["parsed_intent"] = parsed
                except:
                    state["parsed_intent"] = {"raw": content}
            
            return state
            
        except Exception as e:
            logger.error(f"LLM Node '{self.name}' failed: {str(e)}")
            state["error"] = f"LLM node '{self.name}' failed: {str(e)}"
            state["error_type"] = "LLMNodeError"
            raise


__all__ = ["LLMNode"]
