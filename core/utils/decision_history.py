"""
Decision History - Store and retrieve trading decisions for explainability
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque
from loguru import logger
import json
import os
import time


class DecisionHistory:
    """
    Multi-backend decision history storage
    Supports: In-memory (volatile), Redis (TTL), PostgreSQL (persistent)
    """

    def __init__(
        self,
        max_history_per_symbol: int = 10,
        use_redis: bool = False,
        use_postgres: bool = True
    ):
        """
        Initialize decision history

        Args:
            max_history_per_symbol: Max decisions to store per symbol (in-memory only)
            use_redis: Whether to use Redis for caching (7-day TTL)
            use_postgres: Whether to use PostgreSQL for persistent storage (default: True)
        """
        self.max_history = max_history_per_symbol
        self.use_redis = use_redis
        self.use_postgres = use_postgres
        self.redis_client = None
        self.pg_connection = None

        # In-memory storage: {symbol: deque of decisions}
        self.decisions: Dict[str, deque] = {}

        # Initialize Redis
        if use_redis:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    decode_responses=True
                )
                logger.info("✓ Decision history using Redis cache")
            except Exception as e:
                logger.warning(f"Redis unavailable, using in-memory storage: {e}")
                self.use_redis = False

        # Initialize PostgreSQL
        if use_postgres:
            try:
                import psycopg2
                from psycopg2.extras import RealDictCursor

                # Get database connection from environment or use defaults
                db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
                if db_url:
                    self.pg_connection = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
                else:
                    # Fallback to individual parameters
                    self.pg_connection = psycopg2.connect(
                        host=os.getenv("POSTGRES_HOST", "localhost"),
                        port=int(os.getenv("POSTGRES_PORT", "5432")),
                        database=os.getenv("POSTGRES_DB", "sigmax"),
                        user=os.getenv("POSTGRES_USER", "sigmax"),
                        password=os.getenv("POSTGRES_PASSWORD", ""),
                        cursor_factory=RealDictCursor
                    )
                logger.info("✓ Decision history using PostgreSQL persistent storage")
            except Exception as e:
                logger.warning(f"PostgreSQL unavailable, debates will not persist: {e}")
                self.use_postgres = False

        logger.info(f"✓ Decision history created (in-memory max: {self.max_history}, postgres: {self.use_postgres})")

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

        # Store in PostgreSQL if available
        if self.use_postgres and self.pg_connection:
            try:
                self._save_to_postgres(symbol, decision, agent_debate or {})
            except Exception as e:
                logger.warning(f"Failed to store in PostgreSQL: {e}")

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

    def _save_to_postgres(
        self,
        symbol: str,
        decision: Dict[str, Any],
        agent_debate: Dict[str, Any]
    ):
        """
        Save decision and debate to PostgreSQL

        Args:
            symbol: Trading symbol
            decision: Decision dict from orchestrator
            agent_debate: Debate history with bull/bear/research
        """
        try:
            cursor = self.pg_connection.cursor()

            # Extract debate components
            bull_argument = agent_debate.get("bull_argument", "")
            bear_argument = agent_debate.get("bear_argument", "")
            research_summary = agent_debate.get("research_summary", "")

            # Extract decision components
            final_decision = decision.get("action", "hold")
            confidence = decision.get("confidence", 0.0)
            sentiment = decision.get("sentiment", 0.0)

            # Extract agent scores if available
            agent_scores = agent_debate.get("agent_scores", {})
            bull_score = agent_scores.get("bull", None)
            bear_score = agent_scores.get("bear", None)

            # Get reasoning
            reasoning = decision.get("reasoning", {})

            # Get risk validation
            risk_approved = decision.get("risk_approved", True)
            risk_constraints = decision.get("risk_constraints", {})

            # Get nanosecond timestamp
            created_at_ns = time.time_ns()

            # Parse symbol into base/quote (e.g., "BTC/USDT" -> base="BTC", quote="USDT")
            if '/' in symbol:
                base, quote = symbol.split('/', 1)
            else:
                # Fallback for symbols without slash
                base = symbol
                quote = "USDT"

            # First, get or create symbol_id
            # Default exchange to "binance" (most common)
            exchange = "binance"

            cursor.execute(
                "SELECT symbol_id FROM symbols WHERE pair = %s AND exchange = %s",
                (symbol, exchange)
            )
            result = cursor.fetchone()

            if result:
                symbol_id = result['symbol_id']
            else:
                # Insert symbol if it doesn't exist
                cursor.execute(
                    "INSERT INTO symbols (exchange, base, quote, pair) VALUES (%s, %s, %s, %s) RETURNING symbol_id",
                    (exchange, base, quote, symbol)
                )
                symbol_id = cursor.fetchone()['symbol_id']

            # Insert debate record
            cursor.execute("""
                INSERT INTO agent_debates (
                    symbol_id,
                    symbol,
                    bull_argument,
                    bear_argument,
                    research_summary,
                    final_decision,
                    confidence,
                    sentiment,
                    bull_score,
                    bear_score,
                    agent_scores,
                    reasoning,
                    risk_approved,
                    risk_constraints,
                    created_at_ns
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                symbol_id,
                symbol,
                bull_argument,
                bear_argument,
                research_summary,
                final_decision,
                confidence,
                sentiment,
                bull_score,
                bear_score,
                json.dumps(agent_scores) if agent_scores else None,
                json.dumps(reasoning) if reasoning else None,
                risk_approved,
                json.dumps(risk_constraints) if risk_constraints else None,
                created_at_ns
            ))

            self.pg_connection.commit()
            logger.debug(f"Saved debate to PostgreSQL for {symbol}")

        except Exception as e:
            logger.error(f"PostgreSQL save failed: {e}")
            if self.pg_connection:
                self.pg_connection.rollback()
            raise

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
