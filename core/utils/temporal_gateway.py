"""
Temporal Data Gateway - Anti-Look-Ahead Controls for Backtesting
Inspired by AI-Trader's strict temporal data boundaries

This module ensures agents can only access data from the current simulation
time and before, preventing future information leakage in backtesting.

Key Features:
- Strict temporal boundaries for all data access
- Point-in-time price queries
- News/events filtered by publication date
- Financial reports filtered by release date
- Audit logging for data access patterns
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import asyncio
from functools import wraps


class DataType(Enum):
    """Types of data that can be accessed through the gateway."""
    PRICE = "price"
    ORDERBOOK = "orderbook"
    OHLCV = "ohlcv"
    NEWS = "news"
    SOCIAL = "social"
    FINANCIALS = "financials"
    FUNDAMENTALS = "fundamentals"
    SENTIMENT = "sentiment"
    ON_CHAIN = "on_chain"


@dataclass
class DataAccessRecord:
    """Record of a data access attempt."""
    timestamp: datetime
    data_type: DataType
    symbol: str
    requested_time: datetime
    simulation_time: datetime
    allowed: bool
    reason: str = ""


@dataclass
class PriceData:
    """Standardized price data structure."""
    symbol: str
    price: float
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume_24h: Optional[float] = None
    change_24h: Optional[float] = None


@dataclass
class OHLCVData:
    """OHLCV candlestick data."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class NewsItem:
    """News item with temporal metadata."""
    title: str
    content: str
    source: str
    published_at: datetime
    symbols: List[str] = field(default_factory=list)
    sentiment: Optional[float] = None
    url: Optional[str] = None


@dataclass
class FinancialReport:
    """Financial report with release date."""
    symbol: str
    report_type: str  # "quarterly", "annual", "8k", etc.
    period_end: datetime
    released_at: datetime
    metrics: Dict[str, Any] = field(default_factory=dict)


class TemporalGateway:
    """
    Temporal Data Gateway for anti-look-ahead backtesting.

    All data access is filtered by the current simulation time,
    ensuring agents cannot "peek into the future."

    Usage:
        gateway = TemporalGateway(simulation_time=datetime(2024, 1, 1))
        price = await gateway.get_price("BTC/USDT")  # Only returns data from before Jan 1, 2024

        # Advance simulation time
        gateway.set_simulation_time(datetime(2024, 1, 2))
    """

    def __init__(
        self,
        simulation_time: Optional[datetime] = None,
        price_service: Optional[Any] = None,
        news_service: Optional[Any] = None,
        financial_service: Optional[Any] = None,
        strict_mode: bool = True,
        log_access: bool = True
    ):
        """
        Initialize Temporal Gateway.

        Args:
            simulation_time: Current simulation time (defaults to now for live trading)
            price_service: External price data provider
            news_service: External news data provider
            financial_service: External financial data provider
            strict_mode: If True, raise errors for future data access attempts
            log_access: If True, log all data access attempts
        """
        self._simulation_time = simulation_time or datetime.utcnow()
        self._is_live = simulation_time is None
        self.price_service = price_service
        self.news_service = news_service
        self.financial_service = financial_service
        self.strict_mode = strict_mode
        self.log_access = log_access

        # Access audit trail
        self._access_log: List[DataAccessRecord] = []

        # Cache for frequently accessed data
        self._price_cache: Dict[str, PriceData] = {}
        self._cache_ttl = timedelta(seconds=10)  # 10 second cache for live mode
        self._cache_timestamps: Dict[str, datetime] = {}

        logger.info(
            f"Temporal Gateway initialized: "
            f"{'LIVE' if self._is_live else 'SIMULATION'} mode, "
            f"time={self._simulation_time.isoformat()}"
        )

    @property
    def simulation_time(self) -> datetime:
        """Get current simulation time."""
        return self._simulation_time

    @property
    def is_live(self) -> bool:
        """Check if gateway is in live mode."""
        return self._is_live

    def set_simulation_time(self, new_time: datetime):
        """
        Set the simulation time boundary.

        Args:
            new_time: New simulation time

        Raises:
            ValueError: If new_time is in the future (for non-live mode)
        """
        if not self._is_live and new_time > datetime.utcnow():
            raise ValueError("Simulation time cannot be in the future")

        old_time = self._simulation_time
        self._simulation_time = new_time

        # Clear cache when time changes significantly
        if abs((new_time - old_time).total_seconds()) > 60:
            self._price_cache.clear()
            self._cache_timestamps.clear()

        logger.debug(f"Simulation time updated: {old_time.isoformat()} → {new_time.isoformat()}")

    def advance_time(self, delta: timedelta):
        """
        Advance simulation time by a delta.

        Args:
            delta: Time to advance by
        """
        self.set_simulation_time(self._simulation_time + delta)

    def _record_access(
        self,
        data_type: DataType,
        symbol: str,
        requested_time: datetime,
        allowed: bool,
        reason: str = ""
    ):
        """Record a data access attempt for audit."""
        if not self.log_access:
            return

        record = DataAccessRecord(
            timestamp=datetime.utcnow(),
            data_type=data_type,
            symbol=symbol,
            requested_time=requested_time,
            simulation_time=self._simulation_time,
            allowed=allowed,
            reason=reason
        )
        self._access_log.append(record)

        # Keep only last 10000 records
        if len(self._access_log) > 10000:
            self._access_log = self._access_log[-10000:]

    def _validate_temporal_access(
        self,
        data_type: DataType,
        symbol: str,
        requested_time: Optional[datetime] = None
    ) -> bool:
        """
        Validate that a data request doesn't violate temporal boundaries.

        Args:
            data_type: Type of data being requested
            symbol: Symbol being queried
            requested_time: Specific time requested (or None for "current")

        Returns:
            True if access is allowed

        Raises:
            TemporalViolationError: If strict_mode and access would leak future data
        """
        max_time = requested_time or self._simulation_time

        if max_time > self._simulation_time:
            reason = f"Requested time {max_time} is after simulation time {self._simulation_time}"
            self._record_access(data_type, symbol, max_time, False, reason)

            if self.strict_mode:
                raise TemporalViolationError(reason)

            logger.warning(f"Temporal violation (non-strict): {reason}")
            return False

        self._record_access(data_type, symbol, max_time, True)
        return True

    async def get_price(
        self,
        symbol: str,
        as_of: Optional[datetime] = None
    ) -> Optional[PriceData]:
        """
        Get price data with temporal constraints.

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            as_of: Point-in-time query (defaults to simulation_time)

        Returns:
            PriceData if available and allowed, None otherwise
        """
        max_time = as_of or self._simulation_time

        if not self._validate_temporal_access(DataType.PRICE, symbol, max_time):
            return None

        # Check cache for live mode
        if self._is_live:
            cache_key = f"{symbol}:{max_time.isoformat()}"
            if cache_key in self._price_cache:
                cache_time = self._cache_timestamps.get(cache_key)
                if cache_time and (datetime.utcnow() - cache_time) < self._cache_ttl:
                    return self._price_cache[cache_key]

        # Fetch from service
        if self.price_service:
            try:
                price_data = await self.price_service.get_price(
                    symbol=symbol,
                    max_time=max_time
                )

                # Cache result
                if self._is_live and price_data:
                    cache_key = f"{symbol}:{max_time.isoformat()}"
                    self._price_cache[cache_key] = price_data
                    self._cache_timestamps[cache_key] = datetime.utcnow()

                return price_data
            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {e}")
                return None

        # Fallback: return mock data for testing
        return PriceData(
            symbol=symbol,
            price=0.0,
            timestamp=max_time,
        )

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        as_of: Optional[datetime] = None
    ) -> List[OHLCVData]:
        """
        Get OHLCV candlestick data with temporal constraints.

        Args:
            symbol: Trading pair
            timeframe: Candle timeframe ("1m", "5m", "1h", "1d", etc.)
            limit: Number of candles to return
            as_of: Point-in-time query

        Returns:
            List of OHLCV candles up to simulation time
        """
        max_time = as_of or self._simulation_time

        if not self._validate_temporal_access(DataType.OHLCV, symbol, max_time):
            return []

        if self.price_service:
            try:
                return await self.price_service.get_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                    max_time=max_time
                )
            except Exception as e:
                logger.error(f"Error fetching OHLCV for {symbol}: {e}")
                return []

        return []

    async def search_news(
        self,
        query: str,
        symbols: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[NewsItem]:
        """
        Search news with temporal constraints.

        Only returns news published BEFORE the simulation time.

        Args:
            query: Search query
            symbols: Filter by symbols
            limit: Max results

        Returns:
            List of news items published before simulation time
        """
        if not self._validate_temporal_access(DataType.NEWS, query):
            return []

        if self.news_service:
            try:
                news = await self.news_service.search(
                    query=query,
                    symbols=symbols,
                    published_before=self._simulation_time,
                    limit=limit
                )
                # Double-check temporal constraints
                return [
                    n for n in news
                    if n.published_at <= self._simulation_time
                ]
            except Exception as e:
                logger.error(f"Error searching news: {e}")
                return []

        return []

    async def get_financials(
        self,
        symbol: str,
        report_type: Optional[str] = None
    ) -> List[FinancialReport]:
        """
        Get financial reports with temporal constraints.

        Only returns reports RELEASED before the simulation time.
        This is important because a company might end a quarter on
        Dec 31 but not release the report until Feb 15.

        Args:
            symbol: Stock/crypto symbol
            report_type: Filter by report type

        Returns:
            List of financial reports released before simulation time
        """
        if not self._validate_temporal_access(DataType.FINANCIALS, symbol):
            return []

        if self.financial_service:
            try:
                reports = await self.financial_service.get_reports(
                    symbol=symbol,
                    report_type=report_type,
                    released_before=self._simulation_time
                )
                # Double-check temporal constraints on release date
                return [
                    r for r in reports
                    if r.released_at <= self._simulation_time
                ]
            except Exception as e:
                logger.error(f"Error fetching financials for {symbol}: {e}")
                return []

        return []

    async def get_sentiment(
        self,
        symbol: str,
        as_of: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Get sentiment score with temporal constraints.

        Args:
            symbol: Symbol to get sentiment for
            as_of: Point-in-time query

        Returns:
            Sentiment score (-1 to 1) or None
        """
        max_time = as_of or self._simulation_time

        if not self._validate_temporal_access(DataType.SENTIMENT, symbol, max_time):
            return None

        # Would integrate with sentiment service
        # For now, return None (no sentiment available)
        return None

    def get_access_log(
        self,
        data_type: Optional[DataType] = None,
        symbol: Optional[str] = None,
        only_violations: bool = False
    ) -> List[DataAccessRecord]:
        """
        Get access audit log with optional filtering.

        Args:
            data_type: Filter by data type
            symbol: Filter by symbol
            only_violations: Only return denied access attempts

        Returns:
            Filtered access records
        """
        records = self._access_log

        if data_type:
            records = [r for r in records if r.data_type == data_type]

        if symbol:
            records = [r for r in records if r.symbol == symbol]

        if only_violations:
            records = [r for r in records if not r.allowed]

        return records

    def get_statistics(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        total = len(self._access_log)
        violations = len([r for r in self._access_log if not r.allowed])

        by_type = {}
        for record in self._access_log:
            type_name = record.data_type.value
            if type_name not in by_type:
                by_type[type_name] = {"total": 0, "violations": 0}
            by_type[type_name]["total"] += 1
            if not record.allowed:
                by_type[type_name]["violations"] += 1

        return {
            "mode": "live" if self._is_live else "simulation",
            "simulation_time": self._simulation_time.isoformat(),
            "strict_mode": self.strict_mode,
            "total_requests": total,
            "violations": violations,
            "violation_rate": violations / total if total > 0 else 0,
            "by_type": by_type,
            "cache_size": len(self._price_cache)
        }

    def reset(self):
        """Reset the gateway state."""
        self._access_log.clear()
        self._price_cache.clear()
        self._cache_timestamps.clear()
        logger.info("Temporal Gateway reset")


class TemporalViolationError(Exception):
    """Raised when a temporal constraint is violated in strict mode."""
    pass


def temporal_guard(data_type: DataType):
    """
    Decorator to add temporal guards to data access methods.

    Usage:
        @temporal_guard(DataType.PRICE)
        async def get_current_price(self, symbol: str) -> float:
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Extract gateway from self or kwargs
            gateway = getattr(self, 'temporal_gateway', None)
            if gateway is None:
                gateway = kwargs.get('gateway')

            if gateway and isinstance(gateway, TemporalGateway):
                # Extract symbol from args or kwargs
                symbol = args[0] if args else kwargs.get('symbol', 'unknown')
                as_of = kwargs.get('as_of')

                if not gateway._validate_temporal_access(data_type, symbol, as_of):
                    return None

            return await func(self, *args, **kwargs)
        return wrapper
    return decorator


class HistoricalReplay:
    """
    Historical replay runner with temporal gateway integration.

    Usage:
        replay = HistoricalReplay(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 6, 30),
            frequency="daily"
        )

        async for step in replay.run():
            decision = await agent.decide(gateway=step.gateway)
            step.record_decision(decision)
    """

    def __init__(
        self,
        start: datetime,
        end: datetime,
        frequency: str = "daily",
        price_service: Optional[Any] = None,
        news_service: Optional[Any] = None
    ):
        """
        Initialize historical replay.

        Args:
            start: Start datetime
            end: End datetime
            frequency: Step frequency ("daily", "hourly", "4h", "15m")
            price_service: Price data provider
            news_service: News data provider
        """
        self.start = start
        self.end = end
        self.frequency = frequency
        self.price_service = price_service
        self.news_service = news_service

        # Calculate step size
        self.step_sizes = {
            "daily": timedelta(days=1),
            "hourly": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "15m": timedelta(minutes=15)
        }
        self.step_size = self.step_sizes.get(frequency, timedelta(days=1))

        # Results tracking
        self.decisions: List[Dict[str, Any]] = []
        self.performance: List[Dict[str, Any]] = []

    async def run(self):
        """
        Run the historical replay.

        Yields:
            ReplayStep objects for each time step
        """
        current = self.start
        step_num = 0

        while current <= self.end:
            # Create gateway for this time step
            gateway = TemporalGateway(
                simulation_time=current,
                price_service=self.price_service,
                news_service=self.news_service,
                strict_mode=True
            )

            step = ReplayStep(
                step_num=step_num,
                simulation_time=current,
                gateway=gateway,
                replay=self
            )

            yield step

            # Move to next step
            current += self.step_size
            step_num += 1

    def record_decision(
        self,
        step_num: int,
        simulation_time: datetime,
        decision: Dict[str, Any]
    ):
        """Record a decision made during replay."""
        self.decisions.append({
            "step": step_num,
            "time": simulation_time.isoformat(),
            **decision
        })

    def get_results(self) -> Dict[str, Any]:
        """Get replay results summary."""
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "frequency": self.frequency,
            "total_steps": len(self.decisions),
            "decisions": self.decisions,
            "performance": self.performance
        }


@dataclass
class ReplayStep:
    """A single step in historical replay."""
    step_num: int
    simulation_time: datetime
    gateway: TemporalGateway
    replay: HistoricalReplay

    def record_decision(self, decision: Dict[str, Any]):
        """Record decision for this step."""
        self.replay.record_decision(
            self.step_num,
            self.simulation_time,
            decision
        )
