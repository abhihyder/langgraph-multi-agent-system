"""
Tool Node - For external API calls and MCP tool invocations

Handles:
- Gmail API calls
- SMS API calls  
- Drive API calls
- MCP tool invocations
- Database queries
- Any external service integration
"""

from typing import Dict, Any, Optional, Callable
import logging

from ..utils.node_base import BaseNode, NodeConfig
from ..graphs.base_graph import NodeType, log_node_execution, retry_on_failure

logger = logging.getLogger(__name__)


class ToolNode(BaseNode):
    """
    Tool Node for external API and service calls.
    
    Features:
    - Retry logic with exponential backoff
    - Error handling and fallback
    - Timeout handling
    - Result validation
    
    Example:
        node = ToolNode(
            config=NodeConfig(name="call_gmail_api", node_type=NodeType.TOOL),
            tool_function=gmail_service.send_email,
            param_mapping={"to": "recipient", "subject": "email_subject"}
        )
    """
    
    def __init__(
        self,
        config: NodeConfig,
        tool_function: Callable,
        param_mapping: Optional[Dict[str, str]] = None,
        validate_response: Optional[Callable] = None
    ):
        super().__init__(config)
        self.tool_function = tool_function
        self.param_mapping = param_mapping or {}
        self.validate_response = validate_response
    
    def _extract_params(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters for tool from state"""
        params = state.get("params", {})
        
        # Apply parameter mapping if provided
        if self.param_mapping:
            mapped_params = {}
            for tool_param, state_key in self.param_mapping.items():
                if state_key in state:
                    mapped_params[tool_param] = state[state_key]
                elif state_key in params:
                    mapped_params[tool_param] = params[state_key]
            return mapped_params
        
        return params
    
    @log_node_execution(NodeType.TOOL)
    @retry_on_failure(max_retries=3)
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool node"""
        logger.info(f"Tool Node '{self.name}': Extracting parameters")
        
        try:
            params = self._extract_params(state)
            logger.info(f"Tool Node '{self.name}': Invoking tool with params: {list(params.keys())}")
            
            # Invoke the tool
            result = self.tool_function(**params)
            
            # Validate response if validator provided
            if self.validate_response and not self.validate_response(result):
                raise ValueError(f"Tool response validation failed for '{self.name}'")
            
            logger.info(f"Tool Node '{self.name}': Tool invocation successful")
            
            # Store result in state
            state[f"{self.name}_result"] = result
            state["result"] = result
            
            return state
            
        except Exception as e:
            logger.error(f"Tool Node '{self.name}' failed: {str(e)}")
            state["error"] = f"Tool node '{self.name}' failed: {str(e)}"
            state["error_type"] = "ToolNodeError"
            raise


__all__ = ["ToolNode"]
