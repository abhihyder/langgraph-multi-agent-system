"""
Router Node - For conditional routing between nodes

Handles:
- Action-based routing (send/read/search)
- Condition-based routing (if/else logic)
- Error routing (success/error paths)
- Feature flags and A/B testing
"""

from typing import Dict, Any, Callable, Optional, List
import logging

from ..utils.node_base import BaseNode, NodeConfig
from ..graphs.base_graph import NodeType, log_node_execution

logger = logging.getLogger(__name__)


class RouterNode(BaseNode):
    """
    Router Node for conditional flow control.
    
    Features:
    - Fast decision making
    - Clear routing logic
    - Easy debugging
    - Supports multiple output paths
    
    Example:
        def route_by_action(state):
            action = state.get("action")
            if action == "send":
                return "compose"
            elif action == "read":
                return "gmail_api"
            else:
                return "error"
        
        node = RouterNode(
            config=NodeConfig(name="route_action", node_type=NodeType.ROUTER),
            routing_function=route_by_action,
            possible_destinations=["compose", "gmail_api", "error"]
        )
    """
    
    def __init__(
        self,
        config: NodeConfig,
        routing_function: Callable[[Dict[str, Any]], str],
        possible_destinations: Optional[List[str]] = None
    ):
        super().__init__(config)
        self.routing_function = routing_function
        self.possible_destinations = possible_destinations or []
    
    @log_node_execution(NodeType.ROUTER)
    def execute(self, state: Dict[str, Any]) -> str:
        """Execute router node"""
        logger.info(f"Router Node '{self.name}': Evaluating routing logic")
        
        try:
            next_node = self.routing_function(state)
            
            # Validate destination if list provided
            if self.possible_destinations and next_node not in self.possible_destinations:
                logger.warning(
                    f"Router Node '{self.name}': Unexpected destination '{next_node}'. "
                    f"Expected one of: {self.possible_destinations}"
                )
            
            logger.info(f"Router Node '{self.name}': Routing to '{next_node}'")
            return next_node
            
        except Exception as e:
            logger.error(f"Router Node '{self.name}' failed: {str(e)}")
            return "error"


__all__ = ["RouterNode"]
