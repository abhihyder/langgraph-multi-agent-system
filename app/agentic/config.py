"""
Agent Configuration Constants

Centralized configuration for agent types and categories.
Following SOLID principles - single source of truth for agent classification.
"""

from typing import Set


# Agent type classifications
RETRIEVAL_AGENTS: Set[str] = {"knowledge", "memory"}
"""Agents that retrieve data without LLM processing (fast)"""

PROCESSING_AGENTS: Set[str] = {"general", "research", "writing", "code"}
"""Agents that use LLM for processing and generation (slower)"""

INTEGRATION_AGENTS: Set[str] = {"email"}
"""Agents that integrate with external services"""

# All agents combined
ALL_AGENTS: Set[str] = RETRIEVAL_AGENTS | PROCESSING_AGENTS | INTEGRATION_AGENTS

# Agent execution priority order
AGENT_PRIORITY_ORDER = [
    *RETRIEVAL_AGENTS,      # Execute first - provide context
    *PROCESSING_AGENTS,     # Execute second - generate responses
    *INTEGRATION_AGENTS,    # Execute last - external actions
]


__all__ = [
    "RETRIEVAL_AGENTS",
    "PROCESSING_AGENTS", 
    "INTEGRATION_AGENTS",
    "ALL_AGENTS",
    "AGENT_PRIORITY_ORDER",
]
