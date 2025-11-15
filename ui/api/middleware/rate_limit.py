"""
Rate Limiting Middleware for FastAPI

Implements token bucket / sliding window rate limiting using Redis.

Features:
- Per-IP rate limiting
- Per-endpoint rate limits
- Configurable limits
- Rate limit headers (X-RateLimit-*)
- Redis-backed for distributed systems
- In-memory fallback when Redis unavailable

Usage:
    from middleware.rate_limit import RateLimitMiddleware

    app.add_middleware(
        RateLimitMiddleware,
        redis_client=redis_client,
        requests_per_minute=100
    )
"""

import time
from typing import Dict, Optional, Callable
from fastapi import Request, HTTPException, status, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger

try:
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None  # Type hint placeholder


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis sliding window algorithm

    Default: 100 requests per minute per IP address
    Supports per-endpoint custom limits
    """

    # Endpoints excluded from rate limiting
    EXEMPT_PATHS = [
        "/health",
        "/health/ready",
        "/health/live",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json"
    ]

    # Per-endpoint rate limits (requests per minute)
    ENDPOINT_LIMITS: Dict[str, int] = {
        "/api/v1/analyze": 10,  # Heavy computation
        "/api/v1/trade": 5,  # Critical operations
        "/api/v1/backtest": 5,  # Resource intensive
        "/api/v1/quantum/optimize": 5,  # Quantum optimization
        "/api/v1/agent/debate": 10,  # Multi-agent debate
    }

    def __init__(
        self,
        app: ASGIApp,
        redis_client: Optional[Redis] = None,
        requests_per_minute: int = 100,
        enable_redis: bool = True
    ):
        """
        Initialize rate limiting middleware

        Args:
            app: FastAPI application
            redis_client: Redis client instance (optional)
            requests_per_minute: Default rate limit
            enable_redis: Whether to use Redis (falls back to in-memory if False)
        """
        super().__init__(app)
        self.redis = redis_client if enable_redis and REDIS_AVAILABLE else None
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60

        # In-memory fallback (not distributed, but works without Redis)
        self.memory_store: Dict[str, Dict[str, any]] = {}

        if not self.redis:
            logger.warning("⚠️  Rate limiting using in-memory store (not distributed)")
            logger.warning("   For production, configure Redis for distributed rate limiting")
        else:
            logger.info(f"✓ Rate limiting enabled: {requests_per_minute} req/min (Redis)")

    def _get_endpoint_limit(self, path: str) -> int:
        """Get rate limit for specific endpoint"""
        # Check exact match first
        if path in self.ENDPOINT_LIMITS:
            return self.ENDPOINT_LIMITS[path]

        # Check prefix match (for /api/v1/analyze/BTC, matches /api/v1/analyze)
        for endpoint_path, limit in self.ENDPOINT_LIMITS.items():
            if path.startswith(endpoint_path):
                return limit

        # Default limit
        return self.requests_per_minute

    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from rate limiting"""
        return path in self.EXEMPT_PATHS or path.startswith("/static/")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""

        # Skip rate limiting for exempt paths
        if self._is_exempt(request.url.path):
            return await call_next(request)

        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"

        # Get rate limit for this endpoint
        endpoint_limit = self._get_endpoint_limit(request.url.path)

        # Check rate limit
        key = f"rate_limit:{client_ip}:{request.url.path}"

        try:
            current_count, reset_time = self._check_and_increment(key, endpoint_limit)

            # Rate limit exceeded
            if current_count > endpoint_limit:
                logger.warning(
                    f"Rate limit exceeded for {client_ip} on {request.url.path} "
                    f"({current_count}/{endpoint_limit})"
                )

                retry_after = int(reset_time - time.time())
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "message": f"Maximum {endpoint_limit} requests per minute allowed",
                        "retry_after": retry_after
                    },
                    headers={"Retry-After": str(max(1, retry_after))}
                )

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            remaining = max(0, endpoint_limit - current_count)
            response.headers["X-RateLimit-Limit"] = str(endpoint_limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(reset_time))

            return response

        except HTTPException:
            raise  # Re-raise rate limit errors
        except Exception as e:
            logger.error(f"Rate limiting error: {e}. Allowing request.")
            # Fail open - allow request on errors
            return await call_next(request)

    def _check_and_increment(self, key: str, limit: int) -> tuple[int, float]:
        """
        Check rate limit and increment counter

        Returns:
            Tuple of (current_count, reset_timestamp)
        """
        current_time = time.time()
        reset_time = current_time + self.window_seconds

        if self.redis:
            return self._check_redis(key, reset_time)
        else:
            return self._check_memory(key, current_time, reset_time)

    def _check_redis(self, key: str, reset_time: float) -> tuple[int, float]:
        """Redis-backed rate limiting"""
        try:
            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.window_seconds)
            results = pipe.execute()

            current_count = results[0]
            return current_count, reset_time

        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fallback to memory store
            return self._check_memory(key, time.time(), reset_time)

    def _check_memory(self, key: str, current_time: float, reset_time: float) -> tuple[int, float]:
        """In-memory fallback rate limiting (not distributed!)"""

        # Clean up expired entries
        expired_keys = [
            k for k, v in self.memory_store.items()
            if v["reset_time"] < current_time
        ]
        for k in expired_keys:
            del self.memory_store[k]

        # Get or create entry
        if key not in self.memory_store:
            self.memory_store[key] = {
                "count": 0,
                "reset_time": reset_time
            }

        # Increment and return
        self.memory_store[key]["count"] += 1
        current_count = self.memory_store[key]["count"]
        entry_reset_time = self.memory_store[key]["reset_time"]

        return current_count, entry_reset_time

    def get_stats(self) -> Dict[str, any]:
        """Get rate limiting statistics"""
        if self.redis:
            try:
                # Count all rate limit keys
                keys = self.redis.keys("rate_limit:*")
                return {
                    "backend": "redis",
                    "active_limits": len(keys),
                    "default_limit": self.requests_per_minute,
                    "window_seconds": self.window_seconds,
                    "endpoint_limits": self.ENDPOINT_LIMITS
                }
            except Exception as e:
                logger.error(f"Failed to get Redis stats: {e}")

        return {
            "backend": "memory",
            "active_limits": len(self.memory_store),
            "default_limit": self.requests_per_minute,
            "window_seconds": self.window_seconds,
            "endpoint_limits": self.ENDPOINT_LIMITS
        }


# Decorator for function-level rate limiting
def rate_limit(requests_per_minute: int = 60):
    """
    Decorator for rate limiting specific endpoints

    Usage:
        @app.get("/api/expensive")
        @rate_limit(requests_per_minute=10)
        async def expensive_endpoint():
            return {"status": "ok"}
    """
    def decorator(func):
        # Store limit metadata on function
        func._rate_limit = requests_per_minute
        return func
    return decorator
