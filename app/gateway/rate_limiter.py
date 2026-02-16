"""
Rate Limiter

Implements token bucket algorithm for rate limiting.
"""

import logging
import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter.
    
    Features:
    - Per-user rate limiting
    - Per-endpoint rate limiting
    - Configurable limits
    - Metrics tracking
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst size
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        
        # Token buckets: key -> (tokens, last_refill_time)
        self.buckets: Dict[str, tuple[float, float]] = defaultdict(
            lambda: (float(burst_size), time.time())
        )
        
        # Metrics
        self.total_requests = 0
        self.blocked_requests = 0
        self.lock = asyncio.Lock()
        
        logger.info(
            f"Rate limiter initialized: {requests_per_minute} req/min, "
            f"burst: {burst_size}"
        )
    
    def _get_bucket_key(self, request: Request) -> str:
        """
        Generate bucket key from request.
        
        Args:
            request: FastAPI request
            
        Returns:
            Bucket key (user_id or IP)
        """
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to client IP
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    def _refill_bucket(self, key: str) -> tuple[float, float]:
        """
        Refill token bucket based on elapsed time.
        
        Args:
            key: Bucket key
            
        Returns:
            Updated (tokens, last_refill_time) tuple
        """
        tokens, last_refill = self.buckets[key]
        now = time.time()
        elapsed = now - last_refill
        
        # Add tokens based on elapsed time
        new_tokens = min(
            self.burst_size,
            tokens + (elapsed * self.refill_rate)
        )
        
        return (new_tokens, now)
    
    async def check_rate_limit(self, request: Request) -> None:
        """
        Check if request should be rate limited.
        
        Args:
            request: FastAPI request
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        async with self.lock:
            self.total_requests += 1
            
            key = self._get_bucket_key(request)
            
            # Refill bucket
            tokens, _ = self._refill_bucket(key)
            
            # Check if tokens available
            if tokens < 1.0:
                self.blocked_requests += 1
                logger.warning(f"Rate limit exceeded for {key}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": "60"},
                )
            
            # Consume one token
            self.buckets[key] = (tokens - 1.0, time.time())
            
            logger.debug(f"Rate limit check passed for {key}, tokens remaining: {tokens - 1.0}")
    
    def get_metrics(self) -> Dict:
        """
        Get rate limiter metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "block_rate": (
                self.blocked_requests / self.total_requests
                if self.total_requests > 0
                else 0
            ),
            "active_buckets": len(self.buckets),
        }
    
    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        self.total_requests = 0
        self.blocked_requests = 0
    
    def clear_buckets(self) -> None:
        """Clear all token buckets (for testing)."""
        self.buckets.clear()
