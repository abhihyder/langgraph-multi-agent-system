"""
Test Memory Driver Base Interface

Tests for the BaseMemoryDriver abstract class to ensure proper interface definition.
"""

import pytest
from app.core.memory.base import BaseMemoryDriver


class TestBaseMemoryDriver:
    """Test cases for BaseMemoryDriver abstract interface"""
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseMemoryDriver cannot be instantiated directly"""
        with pytest.raises(TypeError) as exc_info:
            BaseMemoryDriver()
        
        assert "Can't instantiate abstract class" in str(exc_info.value)
    
    def test_must_implement_all_methods(self):
        """Test that subclasses must implement all abstract methods"""
        
        class IncompleteDriver(BaseMemoryDriver):
            """Incomplete implementation missing required methods"""
            pass
        
        with pytest.raises(TypeError) as exc_info:
            IncompleteDriver()
        
        error_msg = str(exc_info.value)
        assert "Can't instantiate abstract class" in error_msg
        
        # Check that all required methods are mentioned
        required_methods = [
            'recall', 'recall_global_knowledge', 'store',
            'store_global_knowledge', 'delete', 'health_check'
        ]
        
        # At least some methods should be mentioned as missing
        assert any(method in error_msg for method in required_methods)
    
    def test_complete_implementation_works(self):
        """Test that a complete implementation can be instantiated"""
        
        class CompleteDriver(BaseMemoryDriver):
            """Complete driver implementation for testing"""
            
            def recall(self, user_id, conversation_id=None, query=None, 
                      top_k=10, use_vector=True, exclude_tags=None):
                return []
            
            def recall_global_knowledge(self, query, top_k=5, category=None):
                return []
            
            def store(self, user_id, content, conversation_id=None, 
                     tags=None, metadata=None):
                return {}
            
            def store_global_knowledge(self, content, category, title=None, 
                                      doc_id=None, metadata=None):
                return {}
            
            def delete(self, memory_id, user_id=None):
                return True
            
            def health_check(self):
                return {"status": "healthy"}
        
        # Should not raise any errors
        driver = CompleteDriver()
        assert driver is not None
        assert isinstance(driver, BaseMemoryDriver)
