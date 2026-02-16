"""
Base Node Abstractions

Defines the base classes and configuration for all node types.
Following Single Responsibility Principle - only base abstractions here.
"""

from typing import Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging

from ..graphs.base_graph import NodeType

logger = logging.getLogger(__name__)


@dataclass
class NodeConfig:
    """Configuration for a node"""
    name: str
    node_type: NodeType
    max_retries: int = 3
    timeout: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseNode(ABC):
    """
    Abstract base class for all node types.
    Provides common functionality and interface.
    """
    
    def __init__(self, config: NodeConfig):
        self.config = config
        self.name = config.name
        self.node_type = config.node_type
        logger.info(f"Initialized {self.node_type.value} node: {self.name}")
    
    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the node logic.
        Must be implemented by each node type.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        pass
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Make node callable"""
        return self.execute(state)


__all__ = ["NodeConfig", "BaseNode"]
