"""
Agentic AI System Core Module

This module contains the multi-agent orchestration system:
- Orchestrator: Routes queries to appropriate agents
- Agents: Specialized agents (research, writing, code)
- Aggregator: Synthesizes agent outputs
- Graph: LangGraph workflow definition
- State: Shared state schema
"""

from .graph import app
from .state import AgentState

__all__ = ["app", "AgentState"]
