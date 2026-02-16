"""
Processing Node - For non-LLM data processing

Handles:
- Data validation
- Format conversion
- Data transformation
- Response formatting
- Business logic
- Filtering and sorting
"""

from typing import Dict, Any, Callable
import logging

from ..utils.node_base import BaseNode, NodeConfig
from ..graphs.base_graph import NodeType, log_node_execution

logger = logging.getLogger(__name__)


class ProcessingNode(BaseNode):
    """
    Processing Node for deterministic data transformations.
    
    Features:
    - Fast execution (no API calls)
    - Deterministic behavior
    - Easy unit testing
    - Pure Python logic
    
    Example:
        def validate_email(state):
            email = state.get("email_address")
            if not email or "@" not in email:
                raise ValueError("Invalid email address")
            state["validated"] = True
            return state
        
        node = ProcessingNode(
            config=NodeConfig(name="validate_params", node_type=NodeType.PROCESSING),
            processing_function=validate_email
        )
    """
    
    def __init__(
        self,
        config: NodeConfig,
        processing_function: Callable[[Dict[str, Any]], Dict[str, Any]]
    ):
        super().__init__(config)
        self.processing_function = processing_function
    
    @log_node_execution(NodeType.PROCESSING)
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute processing node"""
        logger.info(f"Processing Node '{self.name}': Starting processing")
        
        try:
            result_state = self.processing_function(state)
            logger.info(f"Processing Node '{self.name}': Processing complete")
            return result_state
            
        except Exception as e:
            logger.error(f"Processing Node '{self.name}' failed: {str(e)}")
            state["error"] = f"Processing node '{self.name}' failed: {str(e)}"
            state["error_type"] = "ProcessingNodeError"
            raise


__all__ = ["ProcessingNode"]
