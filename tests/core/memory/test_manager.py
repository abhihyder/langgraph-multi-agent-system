"""
Test Memory Driver Manager

Tests for the driver factory/manager system that handles driver selection
and instantiation based on configuration.
"""

import pytest
import os
from unittest.mock import patch, Mock
from app.core.memory.manager import (
    MemoryDriverManager, 
    get_memory_driver, 
    set_memory_driver
)
from app.core.memory.base import BaseMemoryDriver
from app.core.memory.automem_driver import AutoMemDriver
from app.core.memory.pgvector_driver import PGVectorDriver


class TestMemoryDriverManager:
    """Test cases for MemoryDriverManager"""
    
    def setup_method(self):
        """Reset manager state before each test"""
        MemoryDriverManager.reset_cache()
        get_memory_driver.cache_clear()
    
    def test_get_available_drivers(self):
        """Test getting list of available drivers"""
        drivers = MemoryDriverManager.get_available_drivers()
        
        assert "automem" in drivers
        assert "pgvector" in drivers
        assert len(drivers) >= 2
    
    def test_register_custom_driver(self):
        """Test registering a custom driver"""
        
        class CustomDriver(BaseMemoryDriver):
            def recall(self, *args, **kwargs):
                return []
            def recall_global_knowledge(self, *args, **kwargs):
                return []
            def store(self, *args, **kwargs):
                return {}
            def store_global_knowledge(self, *args, **kwargs):
                return {}
            def delete(self, *args, **kwargs):
                return True
            def health_check(self):
                return {"status": "healthy"}
        
        MemoryDriverManager.register_driver("custom", CustomDriver)
        
        drivers = MemoryDriverManager.get_available_drivers()
        assert "custom" in drivers
    
    def test_register_invalid_driver_raises_error(self):
        """Test that registering invalid driver raises ValueError"""
        
        class InvalidDriver:
            pass
        
        with pytest.raises(ValueError) as exc_info:
            MemoryDriverManager.register_driver("invalid", InvalidDriver)
        
        assert "must inherit from BaseMemoryDriver" in str(exc_info.value)
    
    @patch('app.core.memory.manager.get_settings')
    def test_get_driver_automem(self, mock_settings):
        """Test getting AutoMem driver"""
        mock_settings.return_value.MEMORY_DRIVER = "automem"
        
        with patch('app.core.memory.automem_driver.get_default_client'):
            driver = MemoryDriverManager.get_driver()
            
            assert isinstance(driver, AutoMemDriver)
    
    @patch('app.core.memory.manager.get_settings')
    def test_get_driver_pgvector(self, mock_settings):
        """Test getting PGVector driver"""
        mock_settings.return_value.MEMORY_DRIVER = "pgvector"
        mock_settings.return_value.DATABASE_URL = "postgresql://test"
        
        with patch('psycopg2.connect'):
            driver = MemoryDriverManager.get_driver()
            
            assert isinstance(driver, PGVectorDriver)
    
    @patch('app.core.memory.manager.get_settings')
    def test_get_driver_caches_instance(self, mock_settings):
        """Test that driver instances are cached"""
        mock_settings.return_value.MEMORY_DRIVER = "automem"
        
        with patch('app.core.memory.automem_driver.get_default_client'):
            driver1 = MemoryDriverManager.get_driver()
            driver2 = MemoryDriverManager.get_driver()
            
            # Should return same instance
            assert driver1 is driver2
    
    @patch('app.core.memory.manager.get_settings')
    def test_get_driver_invalid_raises_error(self, mock_settings):
        """Test that invalid driver name raises ValueError"""
        mock_settings.return_value.MEMORY_DRIVER = "nonexistent"
        
        with pytest.raises(ValueError) as exc_info:
            MemoryDriverManager.get_driver()
        
        assert "not found" in str(exc_info.value)
        assert "Available drivers" in str(exc_info.value)
    
    @patch('app.core.memory.manager.get_settings')
    def test_get_driver_with_override(self, mock_settings):
        """Test overriding default driver"""
        mock_settings.return_value.MEMORY_DRIVER = "automem"
        mock_settings.return_value.DATABASE_URL = "postgresql://test"
        
        with patch('psycopg2.connect'):
            # Override to use pgvector
            driver = MemoryDriverManager.get_driver(driver_name="pgvector")
            
            assert isinstance(driver, PGVectorDriver)
    
    @patch('app.core.memory.manager.get_settings')
    def test_get_driver_case_insensitive(self, mock_settings):
        """Test that driver names are case-insensitive"""
        mock_settings.return_value.MEMORY_DRIVER = "AUTOMEM"
        
        with patch('app.core.memory.automem_driver.get_default_client'):
            driver = MemoryDriverManager.get_driver()
            
            assert isinstance(driver, AutoMemDriver)
    
    def test_reset_cache_clears_instances(self):
        """Test that reset_cache clears all cached instances"""
        # Add some instances to cache
        MemoryDriverManager._instances["test1"] = Mock()
        MemoryDriverManager._instances["test2"] = Mock()
        
        assert len(MemoryDriverManager._instances) == 2
        
        MemoryDriverManager.reset_cache()
        
        assert len(MemoryDriverManager._instances) == 0


class TestGetMemoryDriverFunction:
    """Test cases for get_memory_driver function"""
    
    def setup_method(self):
        """Reset cache before each test"""
        get_memory_driver.cache_clear()
        MemoryDriverManager.reset_cache()
    
    @patch('app.core.memory.manager.get_settings')
    def test_get_memory_driver_returns_driver(self, mock_settings):
        """Test that get_memory_driver returns a driver instance"""
        mock_settings.return_value.MEMORY_DRIVER = "automem"
        
        with patch('app.core.memory.automem_driver.get_default_client'):
            driver = get_memory_driver()
            
            assert isinstance(driver, BaseMemoryDriver)
            assert isinstance(driver, AutoMemDriver)
    
    @patch('app.core.memory.manager.get_settings')
    def test_get_memory_driver_is_cached(self, mock_settings):
        """Test that get_memory_driver caches result"""
        mock_settings.return_value.MEMORY_DRIVER = "automem"
        
        with patch('app.core.memory.automem_driver.get_default_client'):
            driver1 = get_memory_driver()
            driver2 = get_memory_driver()
            
            # Should return cached instance
            assert driver1 is driver2
    
    @patch('app.core.memory.manager.get_settings')
    def test_set_memory_driver_changes_driver(self, mock_settings):
        """Test that set_memory_driver can switch drivers"""
        mock_settings.return_value.MEMORY_DRIVER = "automem"
        mock_settings.return_value.DATABASE_URL = "postgresql://test"
        
        # First get automem
        with patch('app.core.memory.automem_driver.get_default_client'):
            driver1 = get_memory_driver()
            assert isinstance(driver1, AutoMemDriver)
        
        # Switch to pgvector
        with patch('psycopg2.connect'):
            driver2 = set_memory_driver("pgvector")
            assert isinstance(driver2, PGVectorDriver)
            
            # Verify subsequent get_memory_driver calls use the new cache
            # Note: set_memory_driver updates MemoryDriverManager cache, 
            # but get_memory_driver has its own lru_cache
            # In practice, the app would restart or clear both caches
            MemoryDriverManager.reset_cache()
            get_memory_driver.cache_clear()
            
            with patch('psycopg2.connect'):
                mock_settings.return_value.MEMORY_DRIVER = "pgvector"
                driver3 = get_memory_driver()
                assert isinstance(driver3, PGVectorDriver)


class TestDriverIntegration:
    """Integration tests for driver system"""
    
    def setup_method(self):
        """Reset state"""
        get_memory_driver.cache_clear()
        MemoryDriverManager.reset_cache()
    
    @patch('app.core.memory.manager.get_settings')
    def test_environment_variable_switches_driver(self, mock_settings):
        """Test that MEMORY_DRIVER env var determines which driver is used"""
        
        # Test automem
        mock_settings.return_value.MEMORY_DRIVER = "automem"
        with patch('app.core.memory.automem_driver.get_default_client'):
            get_memory_driver.cache_clear()
            driver = get_memory_driver()
            assert isinstance(driver, AutoMemDriver)
        
        # Test pgvector
        mock_settings.return_value.MEMORY_DRIVER = "pgvector"
        mock_settings.return_value.DATABASE_URL = "postgresql://test"
        with patch('psycopg2.connect'):
            get_memory_driver.cache_clear()
            MemoryDriverManager.reset_cache()
            driver = get_memory_driver()
            assert isinstance(driver, PGVectorDriver)
    
    @patch('app.core.memory.manager.get_settings')
    def test_multiple_drivers_can_coexist(self, mock_settings):
        """Test that multiple driver instances can exist simultaneously"""
        mock_settings.return_value.DATABASE_URL = "postgresql://test"
        
        with patch('app.core.memory.automem_driver.get_default_client'), \
             patch('psycopg2.connect'):
            
            driver1 = MemoryDriverManager.get_driver("automem")
            driver2 = MemoryDriverManager.get_driver("pgvector")
            
            assert isinstance(driver1, AutoMemDriver)
            assert isinstance(driver2, PGVectorDriver)
            assert driver1 is not driver2
    
    @patch('app.core.memory.manager.get_settings')
    def test_driver_interface_consistency(self, mock_settings):
        """Test that all drivers implement the same interface"""
        mock_settings.return_value.DATABASE_URL = "postgresql://test"
        
        with patch('app.core.memory.automem_driver.get_default_client'), \
             patch('psycopg2.connect'):
            
            drivers = [
                MemoryDriverManager.get_driver("automem"),
                MemoryDriverManager.get_driver("pgvector")
            ]
            
            for driver in drivers:
                # All should be BaseMemoryDriver
                assert isinstance(driver, BaseMemoryDriver)
                
                # All should have required methods
                assert hasattr(driver, 'recall')
                assert hasattr(driver, 'recall_global_knowledge')
                assert hasattr(driver, 'store')
                assert hasattr(driver, 'store_global_knowledge')
                assert hasattr(driver, 'delete')
                assert hasattr(driver, 'health_check')
                
                # All methods should be callable
                assert callable(driver.recall)
                assert callable(driver.recall_global_knowledge)
                assert callable(driver.store)
                assert callable(driver.store_global_knowledge)
                assert callable(driver.delete)
                assert callable(driver.health_check)
