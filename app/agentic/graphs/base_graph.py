"""
Base Agent Graph - Foundation for all graph-based agents

This module provides the base class and utilities for creating LangGraph-based agents.
Each agent is a sub-graph with multiple nodes (LLM, Tool, Processing, Router nodes).

Architecture:
- BaseAgentGraph: Abstract base class for all agent graphs
- Node Types: LLMNode, ToolNode, ProcessingNode, RouterNode
- Error handling and retry logic
- LangSmith observability integration
- State management

Usage:
    class EmailAgentGraph(BaseAgentGraph):
        def build_graph(self) -> StateGraph:
            graph = StateGraph(EmailState)
            graph.add_node("parse_intent", self.parse_intent_node)
            # ... add more nodes
            return graph.compile()
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List, Protocol, runtime_checkable
from enum import Enum
import time
import traceback
from functools import wraps

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from ..states import BaseAgentState
from ...exceptions import NodeError, GraphNotBuiltError
from ...utils.tracing import trace_agent
import logging


logger = logging.getLogger(__name__)


@runtime_checkable
class CompiledGraph(Protocol):
    """Protocol for compiled LangGraph graphs"""
    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any: ...
    async def ainvoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any: ...


class NodeType(Enum):
    """Types of nodes in an agent graph"""
    LLM = "llm"  # LLM reasoning/generation nodes
    TOOL = "tool"  # External API/MCP tool invocation nodes
    PROCESSING = "processing"  # Non-LLM data processing nodes
    ROUTER = "router"  # Conditional routing nodes
    ERROR = "error"  # Error handling nodes


def retry_on_failure(max_retries: int = 3, backoff_factor: float = 1.5):
    """
    Decorator to retry node execution on failure with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for delay between retries (exponential backoff)
    
    Usage:
        @retry_on_failure(max_retries=3)
        def my_node(state: AgentState) -> AgentState:
            # node logic
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(first_arg, *args, **kwargs) -> Dict[str, Any]:
            # Determine if this is a method (has self) or a function
            # If first_arg is a dict-like object with state keys, it's the state
            # Otherwise, it's self and the state is in args[0]
            if isinstance(first_arg, dict) or (hasattr(first_arg, 'get') and hasattr(first_arg, '__getitem__')):
                # Regular function: first_arg is state
                state = first_arg
                func_args = args
            else:
                # Instance method: first_arg is self, args[0] is state
                state = args[0] if args else {}
                func_args = args[1:] if len(args) > 1 else ()
                # Include self in the call
                args = (first_arg, state) + func_args
            
            retry_count = state.get("retry_count", 0)
            
            for attempt in range(max_retries):
                try:
                    # Call with all original arguments
                    if isinstance(first_arg, dict) or (hasattr(first_arg, 'get') and hasattr(first_arg, '__getitem__')):
                        result = func(state, *func_args, **kwargs)
                    else:
                        result = func(first_arg, state, *func_args, **kwargs)
                    
                    # Reset retry count on success
                    if isinstance(result, dict):
                        result["retry_count"] = 0
                    return result
                    
                except Exception as e:
                    retry_count += 1
                    logger.warning(
                        f"Node {func.__name__} failed (attempt {attempt + 1}/{max_retries}): {str(e)}"
                    )
                    
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        delay = backoff_factor ** attempt
                        logger.info(f"Retrying in {delay:.2f} seconds...")
                        time.sleep(delay)
                    else:
                        # Final attempt failed
                        logger.error(f"Node {func.__name__} failed after {max_retries} attempts")
                        state["error"] = str(e)
                        state["error_type"] = type(e).__name__
                        state["retry_count"] = retry_count
                        return state
            
            return state
        return wrapper
    return decorator


def log_node_execution(node_type: NodeType):
    """
    Decorator to log node execution and track in state.
    
    Args:
        node_type: Type of node (LLM, TOOL, PROCESSING, ROUTER, ERROR)
    
    Usage:
        @log_node_execution(NodeType.LLM)
        def parse_intent_node(state: AgentState) -> AgentState:
            # node logic
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(first_arg, *args, **kwargs) -> Dict[str, Any]:
            # Determine if this is a method (has self) or a function
            # If first_arg is a dict-like object with state keys, it's the state
            # Otherwise, it's self and the state is in args[0]
            if isinstance(first_arg, dict) or (hasattr(first_arg, 'get') and hasattr(first_arg, '__getitem__')):
                # Regular function: first_arg is state
                state = first_arg
                func_args = args
            else:
                # Instance method: first_arg is self, args[0] is state
                state = args[0] if args else {}
                func_args = args[1:] if len(args) > 1 else ()
            
            node_name = func.__name__
            start_time = time.time()
            
            logger.info(f"[{node_type.value.upper()}] Executing node: {node_name}")
            
            try:
                # Call with all original arguments
                if isinstance(first_arg, dict) or (hasattr(first_arg, 'get') and hasattr(first_arg, '__getitem__')):
                    result = func(state, *func_args, **kwargs)
                else:
                    result = func(first_arg, state, *func_args, **kwargs)
                
                # Track node execution in state
                if isinstance(result, dict):
                    node_history = result.get("node_history", [])
                    node_history.append(node_name)
                    result["node_history"] = node_history
                    
                    execution_time = time.time() - start_time
                    logger.info(f"[{node_type.value.upper()}] {node_name} completed in {execution_time:.3f}s")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"[{node_type.value.upper()}] {node_name} failed after {execution_time:.3f}s: {str(e)}"
                )
                raise NodeError(
                    message=f"Node {node_name} failed: {str(e)}",
                    node_name=node_name,
                    node_type=node_type.value,
                    original_error=e
                )
        
        return wrapper
    return decorator


class BaseAgentGraph(ABC):
    """
    Abstract base class for all agent graphs.
    
    Each agent graph must:
    1. Define its state structure (extend BaseAgentState)
    2. Implement build_graph() to construct the StateGraph
    3. Define node methods with appropriate decorators
    4. Handle errors and edge cases
    
    Example:
        class EmailAgentGraph(BaseAgentGraph):
            def __init__(self, gmail_service, email_composer):
                super().__init__()
                self.gmail_service = gmail_service
                self.email_composer = email_composer
                self.graph = self.build_graph()
            
            def build_graph(self) -> StateGraph:
                graph = StateGraph(EmailState)
                graph.add_node("parse_intent", self.parse_intent_node)
                graph.add_node("validate", self.validate_params_node)
                # ... add more nodes and edges
                graph.set_entry_point("parse_intent")
                return graph.compile()
            
            @log_node_execution(NodeType.LLM)
            @retry_on_failure(max_retries=3)
            def parse_intent_node(self, state: EmailState) -> EmailState:
                # LLM node implementation
                pass
    """
    
    def __init__(self):
        """Initialize base agent graph"""
        self.graph: Optional[CompiledGraph] = None
        self.agent_name = self.__class__.__name__
        logger.info(f"Initializing {self.agent_name}")
    
    @abstractmethod
    def build_graph(self) -> CompiledGraph:
        """
        Build and return the compiled StateGraph for this agent.
        
        Must be implemented by each agent:
        1. Create StateGraph with agent-specific state type
        2. Add all nodes (LLM, Tool, Processing, Router, Error)
        3. Add edges (conditional and regular)
        4. Set entry point
        5. Compile and return the compiled graph
        
        Returns:
            Compiled graph ready for execution (graph.compile())
        """
        pass
    
    def invoke(self, input_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent graph with given input state.
        
        Args:
            input_state: Initial state dictionary
            
        Returns:
            Final state after graph execution
        """
        if not self.graph:
            raise GraphNotBuiltError(self.agent_name)
        
        logger.info(f"{self.agent_name}: Starting graph execution")
        
        try:
            # Initialize tracking fields
            input_state.setdefault("node_history", [])
            input_state.setdefault("retry_count", 0)
            input_state.setdefault("error", None)
            
            # Execute graph
            result = self.graph.invoke(input_state)
            
            logger.info(
                f"{self.agent_name}: Graph execution complete. "
                f"Nodes executed: {result.get('node_history', [])}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Graph execution failed: {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                **input_state,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def ainvoke(self, input_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Async version of invoke (for streaming/async execution).
        
        Args:
            input_state: Initial state dictionary
            
        Returns:
            Final state after graph execution
        """
        if not self.graph:
            raise GraphNotBuiltError(self.agent_name)
        
        logger.info(f"{self.agent_name}: Starting async graph execution")
        
        try:
            input_state.setdefault("node_history", [])
            input_state.setdefault("retry_count", 0)
            input_state.setdefault("error", None)
            
            result = await self.graph.ainvoke(input_state)
            
            logger.info(
                f"{self.agent_name}: Async graph execution complete. "
                f"Nodes executed: {result.get('node_history', [])}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Async graph execution failed: {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                **input_state,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def create_error_handler_node(self) -> Callable:
        """
        Create a generic error handler node for the graph.
        
        Returns:
            Error handler function that can be added as a node
        """
        @log_node_execution(NodeType.ERROR)
        def handle_error(state: Dict[str, Any]) -> Dict[str, Any]:
            """Generic error handler node"""
            error_msg = state.get("error", "Unknown error")
            error_type = state.get("error_type", "Exception")
            
            logger.error(f"{self.agent_name}: Handling error - {error_type}: {error_msg}")
            
            # Format error response
            state["formatted_result"] = {
                "success": False,
                "error": error_msg,
                "error_type": error_type,
                "agent": self.agent_name
            }
            
            return state
        
        return handle_error
    
    def create_router_node(
        self,
        routing_logic: Callable[[Dict[str, Any]], str],
        node_name: str = "router"
    ) -> Callable:
        """
        Create a router node with custom routing logic.
        
        Args:
            routing_logic: Function that takes state and returns next node name
            node_name: Name for the router node
            
        Returns:
            Router node function
        """
        @log_node_execution(NodeType.ROUTER)
        def router(state: Dict[str, Any]) -> str:
            """Router node with custom logic"""
            try:
                next_node = routing_logic(state)
                logger.info(f"{self.agent_name}: Router '{node_name}' -> {next_node}")
                return next_node
            except Exception as e:
                logger.error(f"{self.agent_name}: Router '{node_name}' failed: {str(e)}")
                return "error"
        
        return router
