"""
Memory Driver Manager - Factory pattern for driver selection

Similar to Laravel's database manager, this provides a centralized way to
access the configured memory driver based on environment settings.
"""

from typing import Optional
from functools import lru_cache

from config.settings import get_settings
from .base import BaseMemoryDriver
from .automem_driver import AutoMemDriver
from .pgvector_driver import PGVectorDriver


class MemoryDriverManager:
    """
    Factory manager for memory drivers.
    
    Handles driver instantiation and caching based on configuration.
    Similar to Laravel's DatabaseManager.
    """
    
    # Registered drivers
    _drivers = {
        "automem": AutoMemDriver,
        "pgvector": PGVectorDriver,
    }
    
    # Cached driver instances
    _instances = {}
    
    @classmethod
    def register_driver(cls, name: str, driver_class: type):
        """
        Register a custom memory driver.
        
        Args:
            name: Driver identifier
            driver_class: Class that implements BaseMemoryDriver
        """
        if not issubclass(driver_class, BaseMemoryDriver):
            raise ValueError(f"Driver {driver_class} must inherit from BaseMemoryDriver")
        
        cls._drivers[name.lower()] = driver_class
        print(f"[MEMORY MANAGER] Registered driver: {name}")
    
    @classmethod
    def get_driver(cls, driver_name: Optional[str] = None) -> BaseMemoryDriver:
        """
        Get or create a memory driver instance.
        
        Args:
            driver_name: Optional driver override (defaults to env config)
            
        Returns:
            Configured memory driver instance
            
        Raises:
            ValueError: If driver is not registered or invalid
        """
        settings = get_settings()
        driver_name = (driver_name or settings.MEMORY_DRIVER).lower()
        
        # Return cached instance if available
        if driver_name in cls._instances:
            return cls._instances[driver_name]
        
        # Validate driver exists
        if driver_name not in cls._drivers:
            available = ", ".join(cls._drivers.keys())
            raise ValueError(
                f"Memory driver '{driver_name}' not found. "
                f"Available drivers: {available}"
            )
        
        # Instantiate driver
        driver_class = cls._drivers[driver_name]
        
        try:
            if driver_name == "pgvector":
                # PGVector needs connection string
                instance = driver_class(connection_string=settings.DATABASE_URL)
            else:
                # Other drivers use default initialization
                instance = driver_class()
            
            # Cache the instance
            cls._instances[driver_name] = instance
            
            print(f"[MEMORY MANAGER] Initialized driver: {driver_name}")
            
            return instance
            
        except Exception as e:
            raise ValueError(f"Failed to initialize driver '{driver_name}': {e}")
    
    @classmethod
    def reset_cache(cls):
        """Clear all cached driver instances. Useful for testing."""
        cls._instances.clear()
        print("[MEMORY MANAGER] Driver cache cleared")
    
    @classmethod
    def get_available_drivers(cls) -> list:
        """Get list of registered driver names."""
        return list(cls._drivers.keys())


@lru_cache(maxsize=1)
def get_memory_driver() -> BaseMemoryDriver:
    """
    Get the configured memory driver instance (singleton).
    
    This is the primary entry point for accessing memory operations.
    The driver is determined by the MEMORY_DRIVER environment variable.
    
    Returns:
        Configured memory driver instance
        
    Example:
        ```python
        from app.core.memory import get_memory_driver
        
        driver = get_memory_driver()
        memories = driver.recall(user_id="123", query="previous conversations")
        ```
    """
    return MemoryDriverManager.get_driver()


def set_memory_driver(driver_name: str) -> BaseMemoryDriver:
    """
    Explicitly set and return a specific memory driver.
    
    Useful for testing or runtime driver switching.
    
    Args:
        driver_name: Name of the driver to use
        
    Returns:
        Configured memory driver instance
    """
    # Clear cache to force new instance
    get_memory_driver.cache_clear()
    return MemoryDriverManager.get_driver(driver_name)
