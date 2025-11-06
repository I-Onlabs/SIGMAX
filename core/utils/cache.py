"""
SIGMAX Caching Layer
Provides Redis-backed caching with fallback to in-memory
"""

import asyncio
import json
import hashlib
from typing import Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
import pickle
import os

from loguru import logger

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache")


class CacheBackend:
    """Abstract cache backend"""

    async def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError

    async def set(self, key: str, value: Any, ttl: int = 300):
        raise NotImplementedError

    async def delete(self, key: str):
        raise NotImplementedError

    async def clear(self):
        raise NotImplementedError

    async def exists(self, key: str) -> bool:
        raise NotImplementedError


class RedisCache(CacheBackend):
    """Redis-backed cache"""

    def __init__(self, host: str = "localhost", port: int = 6379, password: Optional[str] = None, db: int = 0):
        self.redis = aioredis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=False  # We'll handle encoding/decoding
        )
        logger.info(f"✓ Redis cache initialized: {host}:{port}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.redis.get(key)
            if value:
                # Try JSON first, then pickle
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return pickle.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL"""
        try:
            # Try JSON first (faster), fallback to pickle
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                serialized = pickle.dumps(value)

            await self.redis.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def delete(self, key: str):
        """Delete key from cache"""
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")

    async def clear(self):
        """Clear all cache"""
        try:
            await self.redis.flushdb()
            logger.info("Redis cache cleared")
        except Exception as e:
            logger.error(f"Redis clear error: {e}")

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis increment error: {e}")
            return 0

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            info = await self.redis.info()
            return {
                "type": "redis",
                "connected": True,
                "used_memory": info.get("used_memory_human", "unknown"),
                "keys": await self.redis.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {"type": "redis", "connected": False, "error": str(e)}


class MemoryCache(CacheBackend):
    """In-memory cache with TTL support"""

    def __init__(self):
        self.cache: dict = {}
        self.expiry: dict = {}
        self.hits = 0
        self.misses = 0
        logger.info("✓ In-memory cache initialized")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Check expiry
        if key in self.expiry:
            if datetime.now() > self.expiry[key]:
                await self.delete(key)
                self.misses += 1
                return None

        if key in self.cache:
            self.hits += 1
            return self.cache[key]

        self.misses += 1
        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL"""
        self.cache[key] = value
        self.expiry[key] = datetime.now() + timedelta(seconds=ttl)

    async def delete(self, key: str):
        """Delete key from cache"""
        self.cache.pop(key, None)
        self.expiry.pop(key, None)

    async def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.expiry.clear()
        logger.info("Memory cache cleared")

    async def exists(self, key: str) -> bool:
        """Check if key exists and not expired"""
        if key not in self.cache:
            return False

        if key in self.expiry and datetime.now() > self.expiry[key]:
            await self.delete(key)
            return False

        return True

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        current = await self.get(key) or 0
        new_value = current + amount
        await self.set(key, new_value)
        return new_value

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        # Clean expired keys
        now = datetime.now()
        expired_keys = [k for k, v in self.expiry.items() if now > v]
        for key in expired_keys:
            await self.delete(key)

        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "type": "memory",
            "keys": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
        }


class Cache:
    """
    Main cache interface with automatic backend selection
    """

    def __init__(self):
        self.backend: Optional[CacheBackend] = None
        self.enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        self.default_ttl = int(os.getenv("CACHE_TTL", "300"))
        self._initialized = False

    async def initialize(self):
        """Initialize cache backend"""
        if self._initialized:
            return

        if not self.enabled:
            logger.info("Cache disabled")
            return

        # Try Redis first
        if REDIS_AVAILABLE:
            try:
                redis_host = os.getenv("REDIS_HOST", "localhost")
                redis_port = int(os.getenv("REDIS_PORT", "6379"))
                redis_password = os.getenv("REDIS_PASSWORD") or None

                self.backend = RedisCache(
                    host=redis_host,
                    port=redis_port,
                    password=redis_password
                )

                # Test connection
                await self.backend.set("test", "ok", ttl=1)
                test_value = await self.backend.get("test")

                if test_value == "ok":
                    logger.info("✓ Using Redis cache")
                    self._initialized = True
                    return

            except Exception as e:
                logger.warning(f"Redis unavailable, using memory cache: {e}")

        # Fallback to memory
        self.backend = MemoryCache()
        logger.info("✓ Using in-memory cache")
        self._initialized = True

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled or not self.backend:
            return None
        return await self.backend.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        if not self.enabled or not self.backend:
            return
        await self.backend.set(key, value, ttl or self.default_ttl)

    async def delete(self, key: str):
        """Delete from cache"""
        if not self.enabled or not self.backend:
            return
        await self.backend.delete(key)

    async def clear(self):
        """Clear all cache"""
        if not self.enabled or not self.backend:
            return
        await self.backend.clear()

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.enabled or not self.backend:
            return False
        return await self.backend.exists(key)

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled or not self.backend:
            return {"enabled": False}
        return await self.backend.get_stats()

    def make_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from arguments

        Example:
            key = cache.make_key("market_data", symbol="BTC/USDT", timeframe="1h")
            # Returns: "market_data:symbol=BTC/USDT:timeframe=1h:hash"
        """
        parts = [str(arg) for arg in args]

        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}={v}")

        key_str = ":".join(parts)

        # Add hash for long keys
        if len(key_str) > 100:
            hash_suffix = hashlib.md5(key_str.encode()).hexdigest()[:8]
            key_str = f"{key_str[:80]}:{hash_suffix}"

        return key_str


# Global cache instance
cache = Cache()


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator to cache function results

    Usage:
        @cached(ttl=300, key_prefix="market_data")
        async def get_market_data(symbol: str):
            # Expensive operation
            return data

    Args:
        ttl: Time to live in seconds (default: from CACHE_TTL env)
        key_prefix: Prefix for cache key
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip cache if disabled
            if not cache.enabled:
                return await func(*args, **kwargs)

            # Ensure cache is initialized
            if not cache._initialized:
                await cache.initialize()

            # Generate cache key
            cache_key = cache.make_key(
                key_prefix or func.__name__,
                *args,
                **kwargs
            )

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value

            # Cache miss - call function
            logger.debug(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)

            # Store in cache
            await cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


# Example usage
if __name__ == "__main__":
    async def test_cache():
        """Test cache functionality"""
        await cache.initialize()

        print("\n=== Cache Test ===\n")

        # Test set/get
        await cache.set("test_key", {"value": 123}, ttl=10)
        value = await cache.get("test_key")
        print(f"1. Set/Get: {value}")

        # Test exists
        exists = await cache.exists("test_key")
        print(f"2. Exists: {exists}")

        # Test cached decorator
        @cached(ttl=5, key_prefix="example")
        async def expensive_function(x: int, y: int) -> int:
            print(f"   Computing {x} + {y}...")
            await asyncio.sleep(0.1)  # Simulate expensive operation
            return x + y

        print("\n3. Testing cached decorator:")
        result1 = await expensive_function(2, 3)
        print(f"   First call: {result1}")

        result2 = await expensive_function(2, 3)
        print(f"   Second call (cached): {result2}")

        # Test stats
        stats = await cache.get_stats()
        print(f"\n4. Cache stats: {stats}")

        # Cleanup
        await cache.delete("test_key")
        print("\n✓ Cache test complete")

    asyncio.run(test_cache())
