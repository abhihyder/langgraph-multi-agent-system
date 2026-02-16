"""
Node Factory Functions

Convenience functions for creating nodes quickly.
Following Single Responsibility Principle - only factory logic here.
"""

from typing import Callable, Optional, Dict, List, Any

from .node_base import NodeConfig
from .llm_node import LLMNode
from .tool_node import ToolNode
from .processing_node import ProcessingNode
from .router_node import RouterNode
from ..graphs.base_graph import NodeType


def create_llm_node(
    name: str,
    prompt_template: str,
    model_name: str = "gpt-4",
    temperature: float = 0.7,
    max_retries: int = 3
) -> LLMNode:
    """Quick factory for LLM nodes"""
    config = NodeConfig(name=name, node_type=NodeType.LLM, max_retries=max_retries)
    return LLMNode(
        config=config,
        prompt_template=prompt_template,
        model_name=model_name,
        temperature=temperature
    )


def create_tool_node(
    name: str,
    tool_function: Callable,
    param_mapping: Optional[Dict[str, str]] = None,
    max_retries: int = 3
) -> ToolNode:
    """Quick factory for Tool nodes"""
    config = NodeConfig(name=name, node_type=NodeType.TOOL, max_retries=max_retries)
    return ToolNode(
        config=config,
        tool_function=tool_function,
        param_mapping=param_mapping
    )


def create_processing_node(
    name: str,
    processing_function: Callable
) -> ProcessingNode:
    """Quick factory for Processing nodes"""
    config = NodeConfig(name=name, node_type=NodeType.PROCESSING)
    return ProcessingNode(config=config, processing_function=processing_function)


def create_router_node(
    name: str,
    routing_function: Callable,
    possible_destinations: Optional[List[str]] = None
) -> RouterNode:
    """Quick factory for Router nodes"""
    config = NodeConfig(name=name, node_type=NodeType.ROUTER)
    return RouterNode(
        config=config,
        routing_function=routing_function,
        possible_destinations=possible_destinations
    )


__all__ = [
    "create_llm_node",
    "create_tool_node",
    "create_processing_node",
    "create_router_node",
]
