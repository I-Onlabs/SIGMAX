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
        """Check database connections"""
        # TODO: Implement database connectivity check
        return True

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
        """Check error rates"""
        # TODO: Implement error rate checking
        return True

    def _get_reason(self, checks: Dict[str, bool]) -> str:
        """Get failure reason"""
        failed = [k for k, v in checks.items() if not v]
        return f"Failed checks: {', '.join(failed)}"
