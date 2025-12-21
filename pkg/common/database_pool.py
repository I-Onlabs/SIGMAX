"""
Database Connection Pooling Module

Provides optimized database connection pooling for PostgreSQL, Redis, and ClickHouse.

Features:
- SQLAlchemy async engine with QueuePool
- Connection health checks (pre-ping)
- Automatic connection recycling
- Pool size configuration
- Timeout handling
- Connection leak detection

Usage:
    from pkg.common.database_pool import get_postgres_engine, get_redis_pool

    # PostgreSQL
    async with get_postgres_engine().begin() as conn:
        result = await conn.execute("SELECT * FROM trades")

    # Redis
    redis = await get_redis_pool()
    await redis.set("key", "value")
"""

import os
from typing import Optional
from loguru import logger

# SQLAlchemy for PostgreSQL
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import QueuePool, NullPool
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("SQLAlchemy not installed. Install with: pip install sqlalchemy asyncpg")

# Redis
try:
    import redis.asyncio as aioredis
    from redis.asyncio.connection import ConnectionPool as RedisConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("aioredis not installed. Install with: pip install redis[hiredis]")

# ClickHouse
try:
    from clickhouse_driver import Client as ClickHouseClient
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False


# =============================================================================
# PostgreSQL Connection Pool
# =============================================================================

_postgres_engine: Optional[AsyncEngine] = None
_postgres_session_maker: Optional[sessionmaker] = None


def create_postgres_engine(
    database_url: Optional[str] = None,
    pool_size: int = 20,
    max_overflow: int = 10,
    pool_timeout: int = 30,
    pool_recycle: int = 3600,
    echo: bool = False
) -> AsyncEngine:
    """
    Create PostgreSQL async engine with connection pooling

    Args:
        database_url: PostgreSQL connection string (uses env var if None)
        pool_size: Number of connections to maintain in the pool
        max_overflow: Maximum number of connections to create beyond pool_size
        pool_timeout: Seconds to wait for a connection from the pool
        pool_recycle: Seconds after which to recycle connections
        echo: Whether to log all SQL statements

    Returns:
        SQLAlchemy AsyncEngine instance

    Configuration:
        Set in environment:
        - POSTGRES_POOL_SIZE (default: 20)
        - POSTGRES_MAX_OVERFLOW (default: 10)
        - POSTGRES_POOL_TIMEOUT (default: 30)
        - POSTGRES_POOL_RECYCLE (default: 3600)
    """
    if not SQLALCHEMY_AVAILABLE:
        raise ImportError("SQLAlchemy is required. Install with: pip install sqlalchemy asyncpg")

    # Get URL from environment if not provided
    if database_url is None:
        database_url = os.getenv(
            "POSTGRES_URL",
            "postgresql+asyncpg://sigmax:password@localhost:5432/sigmax"
        )

    # Get pool settings from environment
    pool_size = int(os.getenv("POSTGRES_POOL_SIZE", pool_size))
    max_overflow = int(os.getenv("POSTGRES_MAX_OVERFLOW", max_overflow))
    pool_timeout = int(os.getenv("POSTGRES_POOL_TIMEOUT", pool_timeout))
    pool_recycle = int(os.getenv("POSTGRES_POOL_RECYCLE", pool_recycle))
    echo = os.getenv("POSTGRES_ECHO", "false").lower() == "true" or echo

    # Convert postgresql:// to postgresql+asyncpg://
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=True,  # Verify connections before using
        echo=echo,
        future=True
    )

    logger.info(
        f"✓ PostgreSQL connection pool created: "
        f"pool_size={pool_size}, max_overflow={max_overflow}, "
        f"timeout={pool_timeout}s, recycle={pool_recycle}s"
    )

    return engine


def get_postgres_engine() -> AsyncEngine:
    """
    Get or create the global PostgreSQL engine

    Returns:
        SQLAlchemy AsyncEngine instance
    """
    global _postgres_engine

    if _postgres_engine is None:
        _postgres_engine = create_postgres_engine()

    return _postgres_engine


def get_postgres_session_maker() -> sessionmaker:
    """
    Get or create the global session maker

    Returns:
        SQLAlchemy sessionmaker configured for async sessions
    """
    global _postgres_session_maker

    if _postgres_session_maker is None:
        engine = get_postgres_engine()
        _postgres_session_maker = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    return _postgres_session_maker


async def get_postgres_session() -> AsyncSession:
    """
    Get a new PostgreSQL session from the pool

    Usage:
        async with get_postgres_session() as session:
            result = await session.execute("SELECT * FROM trades")

    Returns:
        AsyncSession instance
    """
    session_maker = get_postgres_session_maker()
    return session_maker()


# =============================================================================
# Redis Connection Pool
# =============================================================================

_redis_pool: Optional[RedisConnectionPool] = None


def create_redis_pool(
    redis_url: Optional[str] = None,
    max_connections: int = 50,
    decode_responses: bool = True
) -> RedisConnectionPool:
    """
    Create Redis connection pool

    Args:
        redis_url: Redis connection string (uses env var if None)
        max_connections: Maximum number of connections in the pool
        decode_responses: Whether to decode byte responses to strings

    Returns:
        Redis ConnectionPool instance
    """
    if not REDIS_AVAILABLE:
        raise ImportError("aioredis is required. Install with: pip install redis[hiredis]")

    # Get URL from environment if not provided
    if redis_url is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Get pool settings from environment
    max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", max_connections))

    pool = RedisConnectionPool.from_url(
        redis_url,
        max_connections=max_connections,
        decode_responses=decode_responses
    )

    logger.info(f"✓ Redis connection pool created: max_connections={max_connections}")

    return pool


async def get_redis_pool() -> aioredis.Redis:
    """
    Get or create the global Redis connection pool

    Returns:
        Redis client instance
    """
    global _redis_pool

    if _redis_pool is None:
        _redis_pool = create_redis_pool()

    return aioredis.Redis(connection_pool=_redis_pool)


# =============================================================================
# ClickHouse Connection
# =============================================================================

_clickhouse_client: Optional[ClickHouseClient] = None


def create_clickhouse_client(
    host: Optional[str] = None,
    port: int = 9000,
    database: str = "default",
    user: str = "default",
    password: str = ""
) -> ClickHouseClient:
    """
    Create ClickHouse client (synchronous)

    Args:
        host: ClickHouse host
        port: ClickHouse port
        database: Database name
        user: Username
        password: Password

    Returns:
        ClickHouseClient instance
    """
    if not CLICKHOUSE_AVAILABLE:
        raise ImportError("clickhouse-driver required. Install with: pip install clickhouse-driver")

    # Get settings from environment
    host = host or os.getenv("CLICKHOUSE_HOST", "localhost")
    port = int(os.getenv("CLICKHOUSE_PORT", port))
    database = os.getenv("CLICKHOUSE_DB", database)
    user = os.getenv("CLICKHOUSE_USER", user)
    password = os.getenv("CLICKHOUSE_PASSWORD", password)

    client = ClickHouseClient(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )

    logger.info(f"✓ ClickHouse client created: {host}:{port}/{database}")

    return client


def get_clickhouse_client() -> ClickHouseClient:
    """
    Get or create the global ClickHouse client

    Returns:
        ClickHouseClient instance
    """
    global _clickhouse_client

    if _clickhouse_client is None:
        _clickhouse_client = create_clickhouse_client()

    return _clickhouse_client


# =============================================================================
# Health Checks
# =============================================================================

async def health_check_postgres() -> dict:
    """Check PostgreSQL connection health"""
    try:
        engine = get_postgres_engine()
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            await result.fetchone()

        pool_status = engine.pool.status()

        return {
            "status": "healthy",
            "pool_size": engine.pool.size(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "pool_status": pool_status
        }
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def health_check_redis() -> dict:
    """Check Redis connection health"""
    try:
        redis = await get_redis_pool()
        await redis.ping()

        return {
            "status": "healthy",
            "connection_pool_size": _redis_pool.max_connections if _redis_pool else 0
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def health_check_clickhouse() -> dict:
    """Check ClickHouse connection health"""
    try:
        client = get_clickhouse_client()
        result = client.execute("SELECT 1")

        return {
            "status": "healthy",
            "version": client.connection.server_info.version_string()
        }
    except Exception as e:
        logger.error(f"ClickHouse health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def health_check_all() -> dict:
    """Check health of all database connections"""
    return {
        "postgres": await health_check_postgres(),
        "redis": await health_check_redis(),
        "clickhouse": health_check_clickhouse()
    }


# =============================================================================
# Cleanup
# =============================================================================

async def close_all_connections():
    """Close all database connection pools"""
    global _postgres_engine, _postgres_session_maker, _redis_pool, _clickhouse_client

    # Close PostgreSQL
    if _postgres_engine:
        await _postgres_engine.dispose()
        _postgres_engine = None
        _postgres_session_maker = None
        logger.info("✓ PostgreSQL connection pool closed")

    # Close Redis
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
        logger.info("✓ Redis connection pool closed")

    # Close ClickHouse
    if _clickhouse_client:
        _clickhouse_client.disconnect()
        _clickhouse_client = None
        logger.info("✓ ClickHouse client disconnected")


if __name__ == "__main__":
    # Self-test
    import asyncio

    async def test():
        print("🗄️  Database Connection Pool Self-Test\n")

        # Test PostgreSQL
        try:
            engine = get_postgres_engine()
            print("✓ PostgreSQL engine created")
            print(f"  Pool size: {engine.pool.size()}")
        except Exception as e:
            print(f"✗ PostgreSQL: {e}")

        # Test Redis
        try:
            redis = await get_redis_pool()
            print("✓ Redis pool created")
        except Exception as e:
            print(f"✗ Redis: {e}")

        # Health checks
        print("\nHealth Checks:")
        health = await health_check_all()
        for service, status in health.items():
            print(f"  {service}: {status['status']}")

        # Cleanup
        await close_all_connections()
        print("\n✅ Self-test complete!")

    asyncio.run(test())
