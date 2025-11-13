"""
Research Safety Module - Prevents runaway research and manages costs

Inspired by Dexter's step limits, this module ensures:
- Research iterations don't exceed limits
- API calls stay within quotas
- LLM costs are tracked and capped
- Data freshness is enforced
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger
import asyncio


class ResearchSafety:
    """
    Research Safety Module - Prevents excessive research costs and runaway loops

    Features:
    1. Iteration tracking and limits
    2. API call rate limiting
    3. LLM cost tracking and budgets
    4. Data freshness enforcement
    5. Research timeout management
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Research Safety Module

        Args:
            config: Configuration dict with safety limits
        """
        self.config = config or {}

        # Iteration limits
        self.max_research_iterations = self.config.get('max_research_iterations', 5)
        self.max_validation_retries = self.config.get('max_validation_retries', 3)

        # API rate limiting
        self.max_api_calls_per_minute = self.config.get('max_api_calls_per_minute', 30)
        self.max_api_calls_per_hour = self.config.get('max_api_calls_per_hour', 500)

        # Cost limits
        self.max_llm_cost_per_decision = self.config.get('max_llm_cost_per_decision', 0.50)  # $0.50
        self.max_daily_research_cost = self.config.get('max_daily_research_cost', 10.0)  # $10

        # Data freshness
        self.data_freshness_threshold = self.config.get('data_freshness_threshold', 300)  # 5 min

        # Research timeout
        self.max_research_time_seconds = self.config.get('max_research_time_seconds', 120)  # 2 min

        # Tracking
        self.api_calls = defaultdict(list)  # timestamp tracking
        self.llm_costs = defaultdict(float)  # per-decision costs
        self.daily_costs = defaultdict(float)  # date -> total cost
        self.iteration_counts = defaultdict(int)  # symbol -> iteration count

        logger.info("✓ Research Safety module initialized")
        logger.info(f"   Max iterations: {self.max_research_iterations}")
        logger.info(f"   API limit: {self.max_api_calls_per_minute}/min")
        logger.info(f"   Max cost per decision: ${self.max_llm_cost_per_decision}")

    def check_iteration_limit(self, symbol: str, current_iteration: int) -> bool:
        """
        Check if iteration limit has been reached

        Args:
            symbol: Trading symbol
            current_iteration: Current iteration number

        Returns:
            True if safe to continue, False if limit exceeded
        """
        if current_iteration >= self.max_research_iterations:
            logger.warning(f"⚠ Iteration limit reached for {symbol}: {current_iteration}/{self.max_research_iterations}")
            return False

        return True

    async def check_api_rate_limit(self, source: str = "global") -> bool:
        """
        Check if API rate limit allows another call

        Args:
            source: API source identifier

        Returns:
            True if call is allowed, False if rate limited
        """
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        one_hour_ago = now - timedelta(hours=1)

        # Clean old entries
        self.api_calls[source] = [
            ts for ts in self.api_calls[source]
            if ts > one_hour_ago
        ]

        # Count recent calls
        calls_last_minute = len([ts for ts in self.api_calls[source] if ts > one_minute_ago])
        calls_last_hour = len(self.api_calls[source])

        # Check limits
        if calls_last_minute >= self.max_api_calls_per_minute:
            wait_time = 60 - (now - self.api_calls[source][-self.max_api_calls_per_minute]).seconds
            logger.warning(f"⚠ API rate limit reached for {source}: {calls_last_minute}/min. Wait {wait_time}s")
            return False

        if calls_last_hour >= self.max_api_calls_per_hour:
            logger.warning(f"⚠ API hourly limit reached for {source}: {calls_last_hour}/hour")
            return False

        return True

    def record_api_call(self, source: str = "global") -> None:
        """
        Record an API call for rate limiting

        Args:
            source: API source identifier
        """
        self.api_calls[source].append(datetime.now())

    async def wait_for_rate_limit(self, source: str = "global", timeout: float = 60.0) -> bool:
        """
        Wait until rate limit allows another call

        Args:
            source: API source identifier
            timeout: Maximum time to wait in seconds

        Returns:
            True if rate limit cleared, False if timeout
        """
        start_time = datetime.now()

        while not await self.check_api_rate_limit(source):
            elapsed = (datetime.now() - start_time).total_seconds()

            if elapsed >= timeout:
                logger.error(f"⏱ Rate limit timeout for {source} after {timeout}s")
                return False

            await asyncio.sleep(1)

        return True

    def track_llm_cost(self, decision_id: str, cost: float) -> bool:
        """
        Track LLM cost for a decision

        Args:
            decision_id: Unique decision identifier
            cost: Cost in USD

        Returns:
            True if within budget, False if over budget
        """
        # Update decision cost
        self.llm_costs[decision_id] += cost

        # Update daily cost
        today = datetime.now().date().isoformat()
        self.daily_costs[today] += cost

        # Check limits
        if self.llm_costs[decision_id] > self.max_llm_cost_per_decision:
            logger.warning(f"⚠ LLM cost limit exceeded for {decision_id}: ${self.llm_costs[decision_id]:.2f}")
            return False

        if self.daily_costs[today] > self.max_daily_research_cost:
            logger.warning(f"⚠ Daily research cost limit exceeded: ${self.daily_costs[today]:.2f}")
            return False

        return True

    def get_decision_cost(self, decision_id: str) -> float:
        """Get total LLM cost for a decision"""
        return self.llm_costs.get(decision_id, 0.0)

    def get_daily_cost(self, date: Optional[str] = None) -> float:
        """Get total research cost for a date"""
        if date is None:
            date = datetime.now().date().isoformat()
        return self.daily_costs.get(date, 0.0)

    def check_data_freshness(self, data_timestamp: str) -> bool:
        """
        Check if data is fresh enough for trading

        Args:
            data_timestamp: ISO format timestamp

        Returns:
            True if fresh, False if stale
        """
        try:
            data_time = datetime.fromisoformat(data_timestamp)
            age = (datetime.now() - data_time).total_seconds()

            if age > self.data_freshness_threshold:
                logger.warning(f"⚠ Stale data detected: {age:.0f}s old (threshold: {self.data_freshness_threshold}s)")
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking data freshness: {e}")
            return False

    def start_research_timer(self, symbol: str) -> str:
        """
        Start a timer for research timeout tracking

        Args:
            symbol: Trading symbol

        Returns:
            Timer ID
        """
        timer_id = f"{symbol}_{datetime.now().timestamp()}"
        self.iteration_counts[timer_id] = 0
        return timer_id

    def check_research_timeout(self, timer_id: str, start_time: datetime) -> bool:
        """
        Check if research has exceeded timeout

        Args:
            timer_id: Timer identifier
            start_time: Research start time

        Returns:
            True if within timeout, False if exceeded
        """
        elapsed = (datetime.now() - start_time).total_seconds()

        if elapsed > self.max_research_time_seconds:
            logger.warning(f"⚠ Research timeout for {timer_id}: {elapsed:.0f}s > {self.max_research_time_seconds}s")
            return False

        return True

    def get_safety_status(self) -> Dict[str, Any]:
        """
        Get current safety status and metrics

        Returns:
            Dict with safety metrics
        """
        today = datetime.now().date().isoformat()
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        # Calculate API call rates
        total_calls_last_minute = sum(
            len([ts for ts in calls if ts > one_minute_ago])
            for calls in self.api_calls.values()
        )

        return {
            'limits': {
                'max_iterations': self.max_research_iterations,
                'max_api_calls_per_minute': self.max_api_calls_per_minute,
                'max_llm_cost_per_decision': self.max_llm_cost_per_decision,
                'max_daily_research_cost': self.max_daily_research_cost,
                'data_freshness_threshold': self.data_freshness_threshold
            },
            'current': {
                'api_calls_last_minute': total_calls_last_minute,
                'daily_cost': self.daily_costs.get(today, 0.0),
                'active_decisions': len(self.llm_costs),
                'total_api_sources': len(self.api_calls)
            },
            'utilization': {
                'api_rate': f"{total_calls_last_minute}/{self.max_api_calls_per_minute}",
                'daily_budget': f"${self.daily_costs.get(today, 0.0):.2f}/${self.max_daily_research_cost:.2f}",
                'api_rate_pct': (total_calls_last_minute / self.max_api_calls_per_minute) * 100,
                'daily_budget_pct': (self.daily_costs.get(today, 0.0) / self.max_daily_research_cost) * 100
            }
        }

    def reset_daily_stats(self) -> None:
        """Reset daily statistics (call at midnight)"""
        today = datetime.now().date().isoformat()

        # Clean old daily costs (keep last 30 days)
        cutoff_date = (datetime.now() - timedelta(days=30)).date().isoformat()
        old_dates = [date for date in self.daily_costs.keys() if date < cutoff_date]

        for date in old_dates:
            del self.daily_costs[date]

        logger.info(f"✓ Daily stats reset for {today}")

    def get_config(self) -> Dict[str, Any]:
        """Get current safety configuration"""
        return {
            'max_research_iterations': self.max_research_iterations,
            'max_validation_retries': self.max_validation_retries,
            'max_api_calls_per_minute': self.max_api_calls_per_minute,
            'max_api_calls_per_hour': self.max_api_calls_per_hour,
            'max_llm_cost_per_decision': self.max_llm_cost_per_decision,
            'max_daily_research_cost': self.max_daily_research_cost,
            'data_freshness_threshold': self.data_freshness_threshold,
            'max_research_time_seconds': self.max_research_time_seconds
        }

    def update_config(self, config: Dict[str, Any]) -> None:
        """Update safety configuration"""
        for key, value in config.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info(f"✓ Updated {key} = {value}")
