"""
Specialized Agent Graphs

This package contains specialized graphs that compose reusable nodes
for different domains and use cases.

Graph Types:
- EmailAgentGraph: Email operations (send, read, draft, reply)
- GeneralAgentGraph: General conversational AI and queries
- ResearchAgentGraph: Factual research and analysis
- WritingAgentGraph: Content creation and editing
- CodeAgentGraph: Code generation and assistance
- KnowledgeAgentGraph: Knowledge retrieval from company docs
- MemoryAgentGraph: User conversation history retrieval

Usage:
    from app.agentic.graphs import (
        EmailAgentGraph,
        GeneralAgentGraph,
        ResearchAgentGraph,
        WritingAgentGraph,
        CodeAgentGraph,
        KnowledgeAgentGraph,
        MemoryAgentGraph
    )
"""

from .email_graph import EmailAgentGraph, create_email_agent_graph
from .general_graph import GeneralAgentGraph, create_general_agent_graph
from .research_graph import ResearchAgentGraph, create_research_agent_graph
from .writing_graph import WritingAgentGraph, create_writing_agent_graph
from .code_graph import CodeAgentGraph, create_code_agent_graph
from .knowledge_graph import KnowledgeAgentGraph, create_knowledge_agent_graph
from .memory_graph import MemoryAgentGraph, create_memory_agent_graph

__all__ = [
    # Graph classes
    "EmailAgentGraph",
    "GeneralAgentGraph",
    "ResearchAgentGraph",
    "WritingAgentGraph",
    "CodeAgentGraph",
    "KnowledgeAgentGraph",
    "MemoryAgentGraph",
    # Factory functions
    "create_email_agent_graph",
    "create_general_agent_graph",
    "create_research_agent_graph",
    "create_writing_agent_graph",
    "create_code_agent_graph",
    "create_knowledge_agent_graph",
    "create_memory_agent_graph",
]
