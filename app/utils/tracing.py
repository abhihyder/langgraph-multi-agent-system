"""
LangSmith Tracing Utilities

This module provides utilities for tracing and monitoring the agentic AI system
using LangSmith. It includes functions for:
- Initializing LangSmith tracing
- Creating traced contexts
- Adding metadata and tags to traces
- Custom run decorators for agents
"""

import os
import functools
from typing import Any, Callable, Dict, Optional, TypeVar, Literal
from contextlib import contextmanager

from langsmith import Client
from langsmith.run_helpers import traceable
from config.settings import get_settings

settings = get_settings()

# Type variable for generic decorator
F = TypeVar('F', bound=Callable[..., Any])

# Type for run types
RunType = Literal["tool", "chain", "llm", "retriever", "embedding", "prompt", "parser"]


def initialize_langsmith() -> None:
    """
    Initialize LangSmith tracing by setting environment variables.
    Call this at application startup.
    """
    if settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT


def get_langsmith_client() -> Optional[Client]:
    """
    Get a LangSmith client instance.
    
    Returns:
        LangSmith Client if API key is available, None otherwise
    """
    if settings.LANGCHAIN_API_KEY:
        return Client(
            api_key=settings.LANGCHAIN_API_KEY,
            api_url=settings.LANGCHAIN_ENDPOINT
        )
    return None


@contextmanager
def trace_context(
    name: str,
    run_type: RunType = "chain",
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[list] = None
):
    """
    Context manager for creating traced execution contexts.
    
    Args:
        name: Name of the traced operation
        run_type: Type of run (chain, llm, tool, retriever, etc.)
        metadata: Additional metadata to attach to the trace
        tags: Tags for categorizing the trace
        
    Example:
        with trace_context("process_chat", metadata={"user_id": 123}):
            # Your code here
            result = process_message(message)
    """
    from langsmith import trace as langsmith_trace
    
    if settings.LANGCHAIN_TRACING_V2:
        with langsmith_trace(
            name=name,
            run_type=run_type,
            metadata=metadata or {},
            tags=tags or []
        ):
            yield
    else:
        yield


def trace_agent(
    agent_name: str,
    run_type: RunType = "chain",
    tags: Optional[list] = None
) -> Callable[[F], F]:
    """
    Decorator for tracing agent execution with LangSmith.
    
    Args:
        agent_name: Name of the agent (e.g., "orchestrator", "research_agent")
        run_type: Type of run (chain, llm, tool, etc.)
        tags: Tags to add to the trace
        
    Example:
        @trace_agent("research_agent", tags=["agent", "research"])
        def research_agent(state: AgentState) -> Dict[str, Any]:
            # Agent implementation
            pass
    """
    def decorator(func: F) -> F:
        if not settings.LANGCHAIN_TRACING_V2:
            return func
            
        @functools.wraps(func)
        @traceable(
            name=f"{agent_name}.{func.__name__}",
            run_type=run_type,
            tags=tags or [agent_name, "agent"]
        )
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper  # type: ignore
    return decorator


def trace_service(
    service_name: str,
    operation: Optional[str] = None,
    tags: Optional[list] = None
) -> Callable[[F], F]:
    """
    Decorator for tracing service methods with LangSmith.
    
    Args:
        service_name: Name of the service (e.g., "chat_service")
        operation: Specific operation name (optional)
        tags: Tags to add to the trace
        
    Example:
        @trace_service("chat_service", operation="process_chat")
        def process_chat(self, user_input: str) -> Dict[str, Any]:
            # Service implementation
            pass
    """
    def decorator(func: F) -> F:
        if not settings.LANGCHAIN_TRACING_V2:
            return func
            
        op_name = operation or func.__name__
        
        @functools.wraps(func)
        @traceable(
            name=f"{service_name}.{op_name}",
            run_type="chain",
            tags=tags or [service_name, "service"]
        )
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper  # type: ignore
    return decorator


def add_trace_metadata(
    metadata: Dict[str, Any]
) -> None:
    """
    Add metadata to the current trace context.
    
    Args:
        metadata: Dictionary of metadata to add
        
    Example:
        add_trace_metadata({
            "user_id": 123,
            "conversation_id": 456,
            "intent": "research"
        })
    """
    if not settings.LANGCHAIN_TRACING_V2:
        return
    
    try:
        from langsmith import get_current_run_tree
        
        run = get_current_run_tree()
        if run:
            run.add_metadata(metadata)
    except Exception:
        pass  # Silently handle errors


def add_trace_tags(tags: list) -> None:
    """
    Add tags to the current trace context.
    
    Args:
        tags: List of tags to add
        
    Example:
        add_trace_tags(["high-priority", "complex-query"])
    """
    if not settings.LANGCHAIN_TRACING_V2:
        return
    
    try:
        from langsmith import get_current_run_tree
        
        run = get_current_run_tree()
        if run:
            run.add_tags(tags)
    except Exception:
        pass  # Silently handle errors


def log_trace_feedback(
    run_id: str,
    score: float,
    feedback_type: str = "user_rating",
    comment: Optional[str] = None
) -> None:
    """
    Log feedback for a specific trace run.
    
    Args:
        run_id: The run ID to attach feedback to
        score: Numerical score (0.0 to 1.0)
        feedback_type: Type of feedback (e.g., "user_rating", "accuracy")
        comment: Optional text comment
        
    Example:
        log_trace_feedback(
            run_id="abc-123",
            score=0.9,
            feedback_type="user_rating",
            comment="Great response!"
        )
    """
    client = get_langsmith_client()
    if not client:
        return
    
    try:
        client.create_feedback(
            run_id=run_id,
            key=feedback_type,
            score=score,
            comment=comment
        )
    except Exception:
        pass  # Silently handle errors
