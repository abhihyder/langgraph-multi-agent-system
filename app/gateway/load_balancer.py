"""
Load Balancer

Simple load balancer for distributing requests across multiple backend instances.
"""

import logging
from typing import List, Optional
from enum import Enum
import random

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"


class Backend:
    """Represents a backend instance."""
    
    def __init__(self, host: str, port: int, weight: int = 1):
        """
        Initialize backend instance.
        
        Args:
            host: Backend host
            port: Backend port
            weight: Backend weight for weighted load balancing
        """
        self.host = host
        self.port = port
        self.weight = weight
        self.active_connections = 0
        self.total_requests = 0
        self.failed_requests = 0
        self.is_healthy = True
    
    @property
    def url(self) -> str:
        """Get backend URL."""
        return f"http://{self.host}:{self.port}"
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Backend({self.host}:{self.port}, healthy={self.is_healthy})"


class LoadBalancer:
    """
    Load balancer for distributing requests.
    
    Features:
    - Multiple load balancing strategies
    - Health checking
    - Connection tracking
    - Metrics
    """
    
    def __init__(
        self,
        backends: Optional[List[Backend]] = None,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN,
    ):
        """
        Initialize load balancer.
        
        Args:
            backends: List of backend instances
            strategy: Load balancing strategy
        """
        self.backends = backends or []
        self.strategy = strategy
        self.current_index = 0
        
        logger.info(
            f"Load balancer initialized with {len(self.backends)} backends "
            f"using {strategy.value} strategy"
        )
    
    def add_backend(self, backend: Backend) -> None:
        """
        Add a backend instance.
        
        Args:
            backend: Backend to add
        """
        self.backends.append(backend)
        logger.info(f"Added backend: {backend}")
    
    def remove_backend(self, backend: Backend) -> None:
        """
        Remove a backend instance.
        
        Args:
            backend: Backend to remove
        """
        if backend in self.backends:
            self.backends.remove(backend)
            logger.info(f"Removed backend: {backend}")
    
    def get_next_backend(self) -> Optional[Backend]:
        """
        Get next available backend based on strategy.
        
        Returns:
            Next backend to use, or None if no healthy backends
        """
        healthy_backends = [b for b in self.backends if b.is_healthy]
        
        if not healthy_backends:
            logger.error("No healthy backends available")
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin(healthy_backends)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return self._random(healthy_backends)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections(healthy_backends)
        
        return healthy_backends[0]
    
    def _round_robin(self, backends: List[Backend]) -> Backend:
        """
        Round-robin selection.
        
        Args:
            backends: List of healthy backends
            
        Returns:
            Selected backend
        """
        backend = backends[self.current_index % len(backends)]
        self.current_index += 1
        return backend
    
    def _random(self, backends: List[Backend]) -> Backend:
        """
        Random selection.
        
        Args:
            backends: List of healthy backends
            
        Returns:
            Selected backend
        """
        return random.choice(backends)
    
    def _least_connections(self, backends: List[Backend]) -> Backend:
        """
        Least connections selection.
        
        Args:
            backends: List of healthy backends
            
        Returns:
            Backend with least active connections
        """
        return min(backends, key=lambda b: b.active_connections)
    
    def mark_backend_health(self, backend: Backend, is_healthy: bool) -> None:
        """
        Mark backend as healthy or unhealthy.
        
        Args:
            backend: Backend to update
            is_healthy: Health status
        """
        backend.is_healthy = is_healthy
        status = "healthy" if is_healthy else "unhealthy"
        logger.info(f"Backend {backend} marked as {status}")
    
    def get_metrics(self) -> dict:
        """
        Get load balancer metrics.
        
        Returns:
            Dictionary of metrics
        """
        healthy_count = sum(1 for b in self.backends if b.is_healthy)
        total_requests = sum(b.total_requests for b in self.backends)
        total_failures = sum(b.failed_requests for b in self.backends)
        
        return {
            "total_backends": len(self.backends),
            "healthy_backends": healthy_count,
            "unhealthy_backends": len(self.backends) - healthy_count,
            "strategy": self.strategy.value,
            "total_requests": total_requests,
            "total_failures": total_failures,
            "backends": [
                {
                    "url": b.url,
                    "healthy": b.is_healthy,
                    "active_connections": b.active_connections,
                    "total_requests": b.total_requests,
                    "failed_requests": b.failed_requests,
                }
                for b in self.backends
            ],
        }
