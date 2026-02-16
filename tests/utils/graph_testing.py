"""
Graph Testing Utilities - Testing framework for agent graphs

Provides utilities for testing agent graphs and nodes:
- Mock nodes for testing
- State builders for test data
- Graph execution testing
- Node isolation testing
- Edge validation testing

Usage:
    from tests.utils.graph_testing import MockLLMNode, GraphTestRunner
    
    # Create mock node
    mock_node = MockLLMNode(return_value={"parsed_intent": {"action": "send"}})
    
    # Test graph
    runner = GraphTestRunner(my_agent_graph)
    result = runner.run_test(input_state={"user_input": "Send email"})
    assert result["success"]
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from unittest.mock import Mock, MagicMock

from .base_agent_graph import BaseAgentState, NodeType, BaseAgentGraph
from .node_types import LLMNode, ToolNode, ProcessingNode, RouterNode
import logging


logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a graph or node test"""
    success: bool
    final_state: Dict[str, Any]
    node_history: List[str]
    errors: List[str]
    execution_time: float
    metadata: Dict[str, Any]


class MockLLMNode:
    """
    Mock LLM node for testing.
    Returns predefined responses without calling actual LLM.
    
    Example:
        mock = MockLLMNode(return_value={
            "parsed_intent": {"action": "send", "to": "test@example.com"}
        })
        state = mock({"user_input": "Send email"})
    """
    
    def __init__(
        self,
        return_value: Optional[Dict[str, Any]] = None,
        side_effect: Optional[Callable] = None,
        should_fail: bool = False
    ):
        self.return_value = return_value or {}
        self.side_effect = side_effect
        self.should_fail = should_fail
        self.call_count = 0
        self.call_history = []
    
    def __call__(self, state: BaseAgentState) -> BaseAgentState:
        """Execute mock node"""
        self.call_count += 1
        self.call_history.append(state.copy())
        
        if self.should_fail:
            raise Exception("Mock LLM node intentionally failed")
        
        if self.side_effect:
            return self.side_effect(state)
        
        # Merge return value into state
        updated_state = {**state, **self.return_value}
        return updated_state


class MockToolNode:
    """
    Mock Tool node for testing.
    Returns predefined results without calling actual external APIs.
    
    Example:
        mock = MockToolNode(return_value={
            "result": {"message_id": "12345", "success": True}
        })
        state = mock({"params": {"to": "test@example.com"}})
    """
    
    def __init__(
        self,
        return_value: Optional[Dict[str, Any]] = None,
        side_effect: Optional[Callable] = None,
        should_fail: bool = False,
        delay: float = 0.0
    ):
        self.return_value = return_value or {}
        self.side_effect = side_effect
        self.should_fail = should_fail
        self.delay = delay
        self.call_count = 0
        self.call_history = []
    
    def __call__(self, state: BaseAgentState) -> BaseAgentState:
        """Execute mock node"""
        self.call_count += 1
        self.call_history.append(state.copy())
        
        if self.delay > 0:
            import time
            time.sleep(self.delay)
        
        if self.should_fail:
            raise Exception("Mock Tool node intentionally failed")
        
        if self.side_effect:
            return self.side_effect(state)
        
        updated_state = {**state, **self.return_value}
        return updated_state


class StateBuilder:
    """
    Builder for creating test states with common patterns.
    
    Example:
        state = (StateBuilder()
            .with_user_input("Send email to john@example.com")
            .with_params({"to": "john@example.com", "subject": "Test"})
            .with_action("send")
            .build())
    """
    
    def __init__(self):
        self.state: Dict[str, Any] = {
            "node_history": [],
            "retry_count": 0,
            "error": None
        }
    
    def with_user_input(self, user_input: str) -> 'StateBuilder':
        """Add user input"""
        self.state["user_input"] = user_input
        return self
    
    def with_user_request(self, user_request: str) -> 'StateBuilder':
        """Add user request"""
        self.state["user_request"] = user_request
        return self
    
    def with_params(self, params: Dict[str, Any]) -> 'StateBuilder':
        """Add parameters"""
        self.state["params"] = params
        return self
    
    def with_action(self, action: str) -> 'StateBuilder':
        """Add action"""
        self.state["action"] = action
        return self
    
    def with_parsed_intent(self, parsed_intent: Dict[str, Any]) -> 'StateBuilder':
        """Add parsed intent"""
        self.state["parsed_intent"] = parsed_intent
        return self
    
    def with_error(self, error: str, error_type: str = "TestError") -> 'StateBuilder':
        """Add error"""
        self.state["error"] = error
        self.state["error_type"] = error_type
        return self
    
    def with_field(self, key: str, value: Any) -> 'StateBuilder':
        """Add custom field"""
        self.state[key] = value
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build final state"""
        return self.state.copy()


class GraphTestRunner:
    """
    Test runner for agent graphs.
    Provides utilities for testing complete graph execution.
    
    Example:
        runner = GraphTestRunner(email_agent_graph)
        
        # Run single test
        result = runner.run_test(
            input_state={"user_input": "Send email"},
            expected_nodes=["parse_intent", "validate", "gmail_api", "format"]
        )
        
        # Run multiple test cases
        results = runner.run_test_suite([
            {"input": {"user_input": "Send email"}, "expected_success": True},
            {"input": {"user_input": "Invalid"}, "expected_success": False}
        ])
    """
    
    def __init__(self, agent_graph: BaseAgentGraph):
        self.agent_graph = agent_graph
        self.test_results: List[TestResult] = []
    
    def run_test(
        self,
        input_state: Dict[str, Any],
        expected_nodes: Optional[List[str]] = None,
        expected_fields: Optional[List[str]] = None,
        should_succeed: bool = True
    ) -> TestResult:
        """
        Run a single test case.
        
        Args:
            input_state: Initial state for graph
            expected_nodes: Expected nodes that should execute
            expected_fields: Expected fields in final state
            should_succeed: Whether test should succeed
            
        Returns:
            TestResult with test outcome
        """
        import time
        
        logger.info(f"Running test for {self.agent_graph.agent_name}")
        start_time = time.time()
        
        try:
            # Execute graph
            final_state = self.agent_graph.invoke(input_state)
            execution_time = time.time() - start_time
            
            errors = []
            
            # Check for execution errors
            if final_state.get("error") and should_succeed:
                errors.append(f"Graph execution failed: {final_state['error']}")
            
            # Validate expected nodes
            if expected_nodes:
                actual_nodes = final_state.get("node_history", [])
                for expected in expected_nodes:
                    if expected not in actual_nodes:
                        errors.append(f"Expected node '{expected}' not in execution history")
            
            # Validate expected fields
            if expected_fields:
                for field in expected_fields:
                    if field not in final_state:
                        errors.append(f"Expected field '{field}' not in final state")
            
            success = len(errors) == 0
            
            result = TestResult(
                success=success,
                final_state=final_state,
                node_history=final_state.get("node_history", []),
                errors=errors,
                execution_time=execution_time,
                metadata={"agent": self.agent_graph.agent_name}
            )
            
            self.test_results.append(result)
            
            if success:
                logger.info(f"Test PASSED in {execution_time:.3f}s")
            else:
                logger.error(f"Test FAILED: {errors}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Test execution failed: {str(e)}")
            
            result = TestResult(
                success=False,
                final_state=input_state,
                node_history=[],
                errors=[f"Test execution failed: {str(e)}"],
                execution_time=execution_time,
                metadata={"agent": self.agent_graph.agent_name}
            )
            
            self.test_results.append(result)
            return result
    
    def run_test_suite(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> List[TestResult]:
        """
        Run multiple test cases.
        
        Args:
            test_cases: List of test case dictionaries with:
                - input: Input state
                - expected_nodes: Expected nodes (optional)
                - expected_fields: Expected fields (optional)
                - should_succeed: Expected success (default True)
                
        Returns:
            List of TestResult objects
        """
        logger.info(f"Running test suite with {len(test_cases)} test cases")
        
        results = []
        for i, test_case in enumerate(test_cases):
            logger.info(f"Running test case {i+1}/{len(test_cases)}")
            
            result = self.run_test(
                input_state=test_case["input"],
                expected_nodes=test_case.get("expected_nodes"),
                expected_fields=test_case.get("expected_fields"),
                should_succeed=test_case.get("should_succeed", True)
            )
            
            results.append(result)
        
        # Summary
        passed = sum(1 for r in results if r.success)
        logger.info(f"Test suite complete: {passed}/{len(results)} passed")
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all test results"""
        if not self.test_results:
            return {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0.0}
        
        passed = sum(1 for r in self.test_results if r.success)
        total = len(self.test_results)
        
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0.0,
            "avg_execution_time": sum(r.execution_time for r in self.test_results) / total
        }


class NodeTester:
    """
    Utility for testing individual nodes in isolation.
    
    Example:
        tester = NodeTester()
        
        # Test LLM node
        result = tester.test_node(
            node=parse_intent_node,
            input_state={"user_input": "Send email"},
            expected_output_keys=["parsed_intent"]
        )
    """
    
    @staticmethod
    def test_node(
        node: Callable,
        input_state: Dict[str, Any],
        expected_output_keys: Optional[List[str]] = None,
        should_succeed: bool = True
    ) -> TestResult:
        """
        Test a single node in isolation.
        
        Args:
            node: Node function to test
            input_state: Input state
            expected_output_keys: Keys expected in output
            should_succeed: Whether node should succeed
            
        Returns:
            TestResult
        """
        import time
        
        start_time = time.time()
        errors = []
        
        try:
            # Execute node
            output_state = node(input_state)
            execution_time = time.time() - start_time
            
            # Validate output keys
            if expected_output_keys:
                for key in expected_output_keys:
                    if key not in output_state:
                        errors.append(f"Expected key '{key}' not in output")
            
            # Check for errors
            if output_state.get("error") and should_succeed:
                errors.append(f"Node execution failed: {output_state['error']}")
            
            success = len(errors) == 0
            
            return TestResult(
                success=success,
                final_state=output_state,
                node_history=[node.__name__],
                errors=errors,
                execution_time=execution_time,
                metadata={"node": node.__name__}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return TestResult(
                success=False if should_succeed else True,
                final_state=input_state,
                node_history=[],
                errors=[f"Node execution failed: {str(e)}"],
                execution_time=execution_time,
                metadata={"node": node.__name__}
            )


def assert_node_executed(result: TestResult, node_name: str):
    """Assert that a specific node was executed"""
    if node_name not in result.node_history:
        raise AssertionError(
            f"Node '{node_name}' not in execution history. "
            f"Executed nodes: {result.node_history}"
        )


def assert_field_exists(result: TestResult, field_name: str):
    """Assert that a field exists in final state"""
    if field_name not in result.final_state:
        raise AssertionError(
            f"Field '{field_name}' not in final state. "
            f"Available fields: {list(result.final_state.keys())}"
        )


def assert_no_errors(result: TestResult):
    """Assert that execution had no errors"""
    if result.final_state.get("error"):
        raise AssertionError(f"Execution had error: {result.final_state['error']}")
    
    if result.errors:
        raise AssertionError(f"Test had errors: {result.errors}")
