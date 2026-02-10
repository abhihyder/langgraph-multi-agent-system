"""
Memory Driver System - Configurable memory layer abstraction

This module provides a Laravel-like driver pattern for memory management.
Supports multiple backends (AutoMem, PGVector, etc.) with seamless switching via env config.
"""

from .manager import get_memory_driver

__all__ = ["get_memory_driver"]
