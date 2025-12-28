"""
Trading Schedule - Configurable trading frequency support
Inspired by AI-Trader's hourly trading capabilities

Supports:
- Daily trading (default)
- 4-hour intervals
- Hourly trading
- 15-minute intervals (high-frequency)
- Custom schedules
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable
from enum import Enum
from loguru import logger
import asyncio


class TradingFrequency(Enum):
    """Predefined trading frequencies."""
    DAILY = "daily"
    FOUR_HOUR = "4h"
    HOURLY = "1h"
    THIRTY_MIN = "30m"
    FIFTEEN_MIN = "15m"
    CUSTOM = "custom"


class TradingSchedule:
    """
    Configurable trading schedule with support for multiple frequencies.

    Features:
    - Predefined frequency templates
    - Custom checkpoint times
    - Market hours awareness
    - Trading day filtering
    """

    # Predefined frequency schedules (UTC times)
    FREQUENCY_SCHEDULES = {
        TradingFrequency.DAILY: ["00:00"],
        TradingFrequency.FOUR_HOUR: ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
        TradingFrequency.HOURLY: [f"{h:02d}:00" for h in range(24)],
        TradingFrequency.THIRTY_MIN: [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 30]],
        TradingFrequency.FIFTEEN_MIN: [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 15, 30, 45]],
    }

    # A-share market hours (Shanghai time, convert to UTC-8)
    ASTOCK_CHECKPOINTS = ["10:30", "11:30", "14:00", "15:00"]

    # US market hours (Eastern time)
    US_MARKET_HOURS = {"open": "09:30", "close": "16:00"}

    def __init__(
        self,
        frequency: TradingFrequency = TradingFrequency.DAILY,
        custom_checkpoints: Optional[List[str]] = None,
        market: str = "crypto",
        timezone_offset: int = 0
    ):
        """
        Initialize trading schedule.

        Args:
            frequency: Trading frequency enum
            custom_checkpoints: Custom time checkpoints (for CUSTOM frequency)
            market: Market type ("crypto", "us", "cn")
            timezone_offset: UTC offset in hours
        """
        self.frequency = frequency
        self.market = market
        self.timezone_offset = timezone_offset

        # Set checkpoints based on frequency
        if frequency == TradingFrequency.CUSTOM:
            if not custom_checkpoints:
                raise ValueError("Custom frequency requires custom_checkpoints")
            self.checkpoints = custom_checkpoints
        elif market == "cn":
            # A-share market has specific trading hours
            self.checkpoints = self.ASTOCK_CHECKPOINTS
        else:
            self.checkpoints = self.FREQUENCY_SCHEDULES.get(frequency, ["00:00"])

        logger.info(f"Trading schedule initialized: {frequency.value}, {len(self.checkpoints)} checkpoints/day")

    def should_trade(self, current_time: Optional[datetime] = None) -> bool:
        """
        Check if current time is a trading checkpoint.

        Args:
            current_time: Time to check (defaults to now)

        Returns:
            True if current time matches a checkpoint
        """
        if current_time is None:
            current_time = datetime.utcnow()

        # Apply timezone offset
        local_time = current_time + timedelta(hours=self.timezone_offset)
        time_str = local_time.strftime("%H:%M")

        return time_str in self.checkpoints

    def is_trading_day(self, date: Optional[datetime] = None) -> bool:
        """
        Check if given date is a trading day.

        Args:
            date: Date to check (defaults to today)

        Returns:
            True if it's a trading day
        """
        if date is None:
            date = datetime.utcnow()

        # Crypto trades 24/7
        if self.market == "crypto":
            return True

        # Stocks don't trade on weekends
        if date.weekday() >= 5:
            return False

        # TODO: Add holiday calendars for US/CN markets

        return True

    def get_next_checkpoint(self, current_time: Optional[datetime] = None) -> datetime:
        """
        Get the next trading checkpoint time.

        Args:
            current_time: Reference time (defaults to now)

        Returns:
            Datetime of next checkpoint
        """
        if current_time is None:
            current_time = datetime.utcnow()

        local_time = current_time + timedelta(hours=self.timezone_offset)
        current_time_str = local_time.strftime("%H:%M")

        # Find next checkpoint today
        for checkpoint in sorted(self.checkpoints):
            if checkpoint > current_time_str:
                # Found checkpoint later today
                hour, minute = map(int, checkpoint.split(":"))
                next_time = local_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                return next_time - timedelta(hours=self.timezone_offset)

        # No more checkpoints today, return first checkpoint tomorrow
        tomorrow = local_time + timedelta(days=1)
        first_checkpoint = sorted(self.checkpoints)[0]
        hour, minute = map(int, first_checkpoint.split(":"))
        next_time = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)

        return next_time - timedelta(hours=self.timezone_offset)

    def get_checkpoints_in_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[datetime]:
        """
        Get all trading checkpoints in a date range.

        Args:
            start: Start datetime
            end: End datetime

        Returns:
            List of checkpoint datetimes
        """
        checkpoints = []
        current = start

        while current <= end:
            if self.is_trading_day(current):
                for checkpoint in self.checkpoints:
                    hour, minute = map(int, checkpoint.split(":"))
                    checkpoint_time = current.replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    ) - timedelta(hours=self.timezone_offset)

                    if start <= checkpoint_time <= end:
                        checkpoints.append(checkpoint_time)

            current += timedelta(days=1)
            current = current.replace(hour=0, minute=0, second=0, microsecond=0)

        return sorted(checkpoints)

    def seconds_until_next_checkpoint(self, current_time: Optional[datetime] = None) -> float:
        """
        Calculate seconds until next checkpoint.

        Args:
            current_time: Reference time (defaults to now)

        Returns:
            Seconds until next checkpoint
        """
        if current_time is None:
            current_time = datetime.utcnow()

        next_checkpoint = self.get_next_checkpoint(current_time)
        delta = next_checkpoint - current_time

        return max(0, delta.total_seconds())

    async def wait_for_next_checkpoint(
        self,
        callback: Optional[Callable] = None,
        max_wait_seconds: float = 86400
    ) -> datetime:
        """
        Async wait until next trading checkpoint.

        Args:
            callback: Optional callback to run at checkpoint
            max_wait_seconds: Maximum wait time

        Returns:
            The checkpoint datetime reached
        """
        wait_seconds = min(self.seconds_until_next_checkpoint(), max_wait_seconds)

        if wait_seconds > 0:
            logger.info(f"Waiting {wait_seconds:.0f}s for next checkpoint")
            await asyncio.sleep(wait_seconds)

        checkpoint = datetime.utcnow()

        if callback:
            await callback()

        return checkpoint

    def get_schedule_info(self) -> Dict[str, Any]:
        """Get schedule configuration info."""
        return {
            "frequency": self.frequency.value,
            "market": self.market,
            "checkpoints_per_day": len(self.checkpoints),
            "checkpoints": self.checkpoints,
            "timezone_offset": self.timezone_offset,
            "next_checkpoint": self.get_next_checkpoint().isoformat()
        }


class ScheduledTrader:
    """
    Wrapper for running trading sessions on a schedule.

    Usage:
        trader = ScheduledTrader(
            schedule=TradingSchedule(TradingFrequency.HOURLY),
            trade_callback=my_trading_function
        )
        await trader.run()
    """

    def __init__(
        self,
        schedule: TradingSchedule,
        trade_callback: Callable,
        error_callback: Optional[Callable] = None,
        max_consecutive_errors: int = 5
    ):
        """
        Initialize scheduled trader.

        Args:
            schedule: Trading schedule configuration
            trade_callback: Async function to call at each checkpoint
            error_callback: Optional async function to call on errors
            max_consecutive_errors: Stop after this many consecutive errors
        """
        self.schedule = schedule
        self.trade_callback = trade_callback
        self.error_callback = error_callback
        self.max_consecutive_errors = max_consecutive_errors
        self.running = False
        self.consecutive_errors = 0
        self.total_executions = 0

    async def run(self, max_iterations: Optional[int] = None):
        """
        Run the scheduled trading loop.

        Args:
            max_iterations: Optional limit on iterations
        """
        self.running = True
        iterations = 0

        logger.info(f"Starting scheduled trader: {self.schedule.frequency.value}")

        while self.running:
            try:
                # Wait for next checkpoint
                await self.schedule.wait_for_next_checkpoint()

                # Check if we should still run
                if not self.running:
                    break

                # Execute trade callback
                logger.info(f"Executing trading checkpoint #{iterations + 1}")
                await self.trade_callback()

                self.consecutive_errors = 0
                self.total_executions += 1
                iterations += 1

                # Check iteration limit
                if max_iterations and iterations >= max_iterations:
                    logger.info(f"Reached max iterations: {max_iterations}")
                    break

            except Exception as e:
                self.consecutive_errors += 1
                logger.error(f"Trading error ({self.consecutive_errors}/{self.max_consecutive_errors}): {e}")

                if self.error_callback:
                    try:
                        await self.error_callback(e)
                    except Exception:
                        pass

                if self.consecutive_errors >= self.max_consecutive_errors:
                    logger.error("Max consecutive errors reached, stopping")
                    break

                # Wait before retry
                await asyncio.sleep(60)

        self.running = False
        logger.info(f"Scheduled trader stopped after {self.total_executions} executions")

    def stop(self):
        """Stop the scheduled trader."""
        self.running = False
        logger.info("Stop signal received")

    def get_status(self) -> Dict[str, Any]:
        """Get trader status."""
        return {
            "running": self.running,
            "total_executions": self.total_executions,
            "consecutive_errors": self.consecutive_errors,
            "schedule": self.schedule.get_schedule_info()
        }
