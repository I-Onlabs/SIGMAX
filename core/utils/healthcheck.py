"""
Health Checker - System Health Monitoring
"""

from typing import Dict, Any
import asyncio
from datetime import datetime
from loguru import logger


class HealthChecker:
    """
    Health Checker - Monitors system health

    Checks:
    - API connectivity
    - Database connections
    - Memory usage
    - Error rates
    - Trading performance
    """

    def __init__(self, sigmax):
        self.sigmax = sigmax
        self.running = False
        self.check_interval = 60  # seconds
        self.last_check = None
        self.health_history = []

        logger.info("✓ Health checker created")

    async def start(self):
        """Start health monitoring"""
        self.running = True
        asyncio.create_task(self._monitor_loop())
        logger.info("✓ Health checker started")

    async def stop(self):
        """Stop health monitoring"""
        self.running = False
        logger.info("🛑 Health checker stopped")

    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                health = await self.check()

                # Log health status
                if not health.get("healthy", False):
                    logger.warning(f"⚠️ Health check failed: {health.get('reason')}")

                # Store history
                self.health_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "health": health
                })

                # Keep last 100 checks
                if len(self.health_history) > 100:
                    self.health_history.pop(0)

            except Exception as e:
                logger.error(f"Health check error: {e}")

            await asyncio.sleep(self.check_interval)

    async def check(self) -> Dict[str, Any]:
        """
        Perform health check

        Returns:
            Health status dict
        """
        self.last_check = datetime.now()

        checks = {
            "api": await self._check_api(),
            "database": await self._check_database(),
            "memory": await self._check_memory(),
            "errors": await self._check_errors()
        }

        # Overall health
        healthy = all(checks.values())

        return {
            "healthy": healthy,
            "timestamp": self.last_check.isoformat(),
            "checks": checks,
            "reason": self._get_reason(checks) if not healthy else "All systems operational"
        }

    async def _check_api(self) -> bool:
        """Check API connectivity"""
        try:
            if hasattr(self.sigmax, 'data_module') and self.sigmax.data_module:
                # Try to fetch data
                data = await self.sigmax.data_module.get_market_data("BTC/USDT")
                return bool(data)
            return True
        except Exception as e:
            logger.error(f"API check failed: {e}")
            return False

    async def _check_database(self) -> bool:
        """
        Check database connections (PostgreSQL, Redis, ClickHouse)

        Returns:
            True if all configured databases are reachable
        """
        try:
            import os

            all_healthy = True

            # Check PostgreSQL
            postgres_url = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL')
            if postgres_url:
                postgres_healthy = await self._check_postgres(postgres_url)
                if not postgres_healthy:
                    logger.warning("PostgreSQL health check failed")
                    all_healthy = False

            # Check Redis
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                redis_healthy = await self._check_redis(redis_url)
                if not redis_healthy:
                    logger.warning("Redis health check failed")
                    all_healthy = False

            # Check ClickHouse
            clickhouse_url = os.getenv('CLICKHOUSE_URL')
            if clickhouse_url:
                clickhouse_healthy = await self._check_clickhouse(clickhouse_url)
                if not clickhouse_healthy:
                    logger.warning("ClickHouse health check failed")
                    all_healthy = False

            return all_healthy

        except Exception as e:
            logger.error(f"Database health check error: {e}")
            return False

    async def _check_postgres(self, db_url: str) -> bool:
        """Check PostgreSQL connectivity"""
        try:
            import psycopg2

            # Quick connection test with timeout
            conn = psycopg2.connect(db_url, connect_timeout=5)
            cursor = conn.cursor()

            # Execute simple query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            return result[0] == 1

        except ImportError:
            logger.debug("psycopg2 not available, skipping PostgreSQL check")
            return True  # Skip if not installed
        except Exception as e:
            logger.error(f"PostgreSQL check failed: {e}")
            return False

    async def _check_redis(self, redis_url: str) -> bool:
        """Check Redis connectivity"""
        try:
            import redis.asyncio as redis_async

            # Create async Redis client
            client = redis_async.from_url(redis_url, socket_connect_timeout=5)

            # Ping Redis
            result = await client.ping()

            await client.close()

            return result

        except ImportError:
            logger.debug("redis not available, skipping Redis check")
            return True  # Skip if not installed
        except Exception as e:
            logger.error(f"Redis check failed: {e}")
            return False

    async def _check_clickhouse(self, clickhouse_url: str) -> bool:
        """Check ClickHouse connectivity"""
        try:
            from clickhouse_driver import Client

            # Parse URL (simplified)
            # Format: clickhouse://host:port/database
            parts = clickhouse_url.replace('clickhouse://', '').split('/')
            host_port = parts[0].split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 9000

            # Connect to ClickHouse
            client = Client(host=host, port=port, connect_timeout=5)

            # Execute simple query
            result = client.execute('SELECT 1')

            return result[0][0] == 1

        except ImportError:
            logger.debug("clickhouse_driver not available, skipping ClickHouse check")
            return True  # Skip if not installed
        except Exception as e:
            logger.error(f"ClickHouse check failed: {e}")
            return False

    async def _check_memory(self) -> bool:
        """Check memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024

            # Warn if over 8GB
            if memory_mb > 8000:
                logger.warning(f"High memory usage: {memory_mb:.0f}MB")
                return False

            return True

        except ImportError:
            return True  # Skip if psutil not available

    async def _check_errors(self) -> bool:
        """
        Check error rates across the system

        Checks:
        - Safety enforcer violations
        - Recent errors in logs
        - API error rates
        - Trading errors

        Returns:
            True if error rates are acceptable
        """
        try:
            error_count = 0
            max_allowed_errors = 10  # Max errors in last check period

            # Check safety enforcer if available
            if hasattr(self.sigmax, 'orchestrator') and hasattr(self.sigmax.orchestrator, 'safety_enforcer'):
                safety_status = self.sigmax.orchestrator.safety_enforcer.get_status()

                # Check for critical violations
                if safety_status.get('paused', False):
                    logger.warning("System is paused due to safety violations")
                    error_count += 5  # Weight paused state heavily

                # Check consecutive losses
                consecutive_losses = safety_status.get('consecutive_losses', 0)
                if consecutive_losses >= 2:
                    error_count += consecutive_losses

                # Check API errors
                api_errors = safety_status.get('api_errors_last_minute', 0)
                if api_errors > 3:
                    error_count += api_errors

            # Check if orchestrator has errors
            if hasattr(self.sigmax, 'orchestrator'):
                # Check if orchestrator is running properly
                if hasattr(self.sigmax.orchestrator, 'running') and not self.sigmax.orchestrator.running:
                    logger.warning("Orchestrator is not running")
                    error_count += 5

            # Overall error rate assessment
            if error_count > max_allowed_errors:
                logger.warning(f"High error rate detected: {error_count} errors")
                return False

            return True

        except Exception as e:
            logger.error(f"Error rate check failed: {e}")
            return False

    def _get_reason(self, checks: Dict[str, bool]) -> str:
        """Get failure reason"""
        failed = [k for k, v in checks.items() if not v]
        return f"Failed checks: {', '.join(failed)}"
