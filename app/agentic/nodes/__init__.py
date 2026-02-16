"""
Node Types Package

Actual LangGraph nodes (method-based functions used directly in graph.add_node()):
- general_nodes.py: General agent node function
- knowledge_nodes.py: Knowledge retrieval node function
- memory_nodes.py: Memory management node function
- email_nodes.py: Email agent node function
- code_nodes.py: Code generation node function
- research_nodes.py: Research agent node function
- writing_nodes.py: Writing agent node function

Note: Node class abstractions (LLMNode, ToolNode, etc.) are in app/agentic/utils/
They are re-exported here for backward compatibility.
"""

# Re-export node utilities from utils for backward compatibility
from ..utils.node_base import NodeConfig, BaseNode
from ..utils.llm_node import LLMNode
from ..utils.tool_node import ToolNode
from ..utils.processing_node import ProcessingNode
from ..utils.router_node import RouterNode
from ..utils.node_factories import (
    create_llm_node,
    create_tool_node,
    create_processing_node,
    create_router_node,
)

# Legacy agent nodes (backward compatibility)
from .general_nodes import general_agent
from .knowledge_nodes import knowledge_agent
from .memory_nodes import memory_agent
from .email_nodes import email_agent
from .code_nodes import code_agent
from .research_nodes import research_agent
from .writing_nodes import writing_agent

__all__ = [
    # Modern node types (following SRP)
    "NodeConfig",
    "BaseNode",
    "LLMNode",
    "ToolNode",
    "ProcessingNode",
    "RouterNode",
    "create_llm_node",
    "create_tool_node",
    "create_processing_node",
    "create_router_node",
    # Legacy agent nodes
    "general_agent",
    "knowledge_agent",
    "memory_agent",
    "email_agent",
    "code_agent",
    "research_agent",
    "writing_agent",
]
