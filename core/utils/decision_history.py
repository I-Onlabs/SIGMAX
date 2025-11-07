"""
Decision History - Store and retrieve trading decisions for explainability
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque
from loguru import logger
import json


class DecisionHistory:
    """
    In-memory decision history with optional Redis backend
    Stores the last N decisions for each symbol
    """

    def __init__(self, max_history_per_symbol: int = 10, use_redis: bool = False):
        """
        Initialize decision history

        Args:
            max_history_per_symbol: Max decisions to store per symbol
            use_redis: Whether to use Redis for persistence
        """
        self.max_history = max_history_per_symbol
        self.use_redis = use_redis
        self.redis_client = None

        # In-memory storage: {symbol: deque of decisions}
        self.decisions: Dict[str, deque] = {}

        if use_redis:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    decode_responses=True
                )
                logger.info("✓ Decision history using Redis")
            except Exception as e:
                logger.warning(f"Redis unavailable, using in-memory storage: {e}")
                self.use_redis = False

        logger.info(f"✓ Decision history created (max per symbol: {self.max_history})")

    def add_decision(
        self,
        symbol: str,
        decision: Dict[str, Any],
        agent_debate: Optional[Dict[str, Any]] = None
    ):
        """
        Add a decision to history

        Args:
            symbol: Trading symbol
            decision: Decision dict from orchestrator
            agent_debate: Optional debate history with bull/bear/research
        """
        # Create full decision record
        record = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "agent_debate": agent_debate or {},
            "action": decision.get("action", "hold"),
            "confidence": decision.get("confidence", 0.0),
            "sentiment": decision.get("sentiment", 0.0)
        }

        # Store in memory
        if symbol not in self.decisions:
            self.decisions[symbol] = deque(maxlen=self.max_history)

        self.decisions[symbol].append(record)

        # Store in Redis if available
        if self.use_redis and self.redis_client:
            try:
                key = f"sigmax:decisions:{symbol}"
                self.redis_client.lpush(key, json.dumps(record))
                self.redis_client.ltrim(key, 0, self.max_history - 1)
                self.redis_client.expire(key, 86400 * 7)  # 7 days TTL
            except Exception as e:
                logger.warning(f"Failed to store in Redis: {e}")

        logger.debug(f"Stored decision for {symbol}: {decision.get('action')}")

    def get_last_decision(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent decision for a symbol

        Args:
            symbol: Trading symbol

        Returns:
            Last decision record or None
        """
        # Try in-memory first
        if symbol in self.decisions and self.decisions[symbol]:
            return self.decisions[symbol][-1]

        # Try Redis
        if self.use_redis and self.redis_client:
            try:
                key = f"sigmax:decisions:{symbol}"
                data = self.redis_client.lindex(key, 0)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Failed to retrieve from Redis: {e}")

        return None

    def get_decisions(
        self,
        symbol: str,
        limit: int = 10,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get decision history for a symbol

        Args:
            symbol: Trading symbol
            limit: Max number of decisions to return
            since: Only return decisions after this time

        Returns:
            List of decision records
        """
        decisions = []

        # Get from in-memory storage
        if symbol in self.decisions:
            for decision in reversed(self.decisions[symbol]):
                if since:
                    decision_time = datetime.fromisoformat(decision["timestamp"])
                    if decision_time < since:
                        continue

                decisions.append(decision)

                if len(decisions) >= limit:
                    break

        return decisions

    def get_all_symbols(self) -> List[str]:
        """Get list of all symbols with decision history"""
        return list(self.decisions.keys())

    def format_decision_explanation(self, decision: Dict[str, Any]) -> str:
        """
        Format a decision into a human-readable explanation

        Args:
            decision: Decision record

        Returns:
            Formatted explanation string
        """
        symbol = decision.get("symbol", "Unknown")
        timestamp = decision.get("timestamp", "Unknown")
        action = decision.get("action", "hold").upper()
        confidence = decision.get("confidence", 0.0) * 100
        sentiment = decision.get("sentiment", 0.0)

        debate = decision.get("agent_debate", {})
        bull = debate.get("bull_argument", "N/A")[:200]
        bear = debate.get("bear_argument", "N/A")[:200]
        research = debate.get("research_summary", "N/A")[:200]

        explanation = f"""
🔍 **Decision Explanation for {symbol}**
⏰ Time: {timestamp}

📊 **Decision: {action}**
✅ Confidence: {confidence:.1f}%
💭 Sentiment: {sentiment:+.2f}

🐂 **Bull Argument:**
{bull}...

🐻 **Bear Argument:**
{bear}...

📚 **Research Summary:**
{research}...
"""

        # Add reasoning if available
        reasoning = decision.get("decision", {}).get("reasoning", {})
        if reasoning:
            explanation += f"""
🎯 **Key Factors:**
• Technical: {reasoning.get('technical', 'N/A')[:100]}...
"""

        return explanation

    def clear_history(self, symbol: Optional[str] = None):
        """
        Clear decision history

        Args:
            symbol: If provided, clear only this symbol. Otherwise clear all.
        """
        if symbol:
            if symbol in self.decisions:
                self.decisions[symbol].clear()

            if self.use_redis and self.redis_client:
                try:
                    self.redis_client.delete(f"sigmax:decisions:{symbol}")
                except Exception as e:
                    logger.warning(f"Failed to clear Redis: {e}")
        else:
            self.decisions.clear()

            if self.use_redis and self.redis_client:
                try:
                    keys = self.redis_client.keys("sigmax:decisions:*")
                    if keys:
                        self.redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Failed to clear Redis: {e}")

        logger.info(f"Cleared decision history{f' for {symbol}' if symbol else ''}")
