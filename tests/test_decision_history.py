"""
Tests for Decision History module
"""

import pytest
from datetime import datetime
from core.utils.decision_history import DecisionHistory


class TestDecisionHistory:
    """Test suite for decision history"""

    @pytest.fixture
    def history(self):
        """Create decision history instance"""
        return DecisionHistory(max_history_per_symbol=5, use_redis=False)

    def test_decision_history_creation(self, history):
        """Test decision history initializes"""
        assert history is not None
        assert history.max_history == 5

    def test_add_and_retrieve_decision(self, history):
        """Test adding and retrieving decisions"""
        decision = {
            "action": "buy",
            "confidence": 0.8,
            "sentiment": 0.5
        }

        debate = {
            "bull_argument": "Strong uptrend",
            "bear_argument": "High volatility risk",
            "research_summary": "Positive fundamentals"
        }

        # Add decision
        history.add_decision("BTC/USDT", decision, debate)

        # Retrieve decision
        last = history.get_last_decision("BTC/USDT")

        assert last is not None
        assert last["symbol"] == "BTC/USDT"
        assert last["decision"]["action"] == "buy"
        assert last["agent_debate"]["bull_argument"] == "Strong uptrend"

    def test_multiple_decisions(self, history):
        """Test storing multiple decisions"""
        for i in range(10):
            decision = {
                "action": "buy" if i % 2 == 0 else "sell",
                "confidence": 0.5 + i * 0.05
            }
            history.add_decision("ETH/USDT", decision)

        # Should only keep last 5 (max_history)
        decisions = history.get_decisions("ETH/USDT", limit=10)
        assert len(decisions) <= 5

    def test_get_last_decision_no_history(self, history):
        """Test retrieving decision when none exists"""
        result = history.get_last_decision("NONEXISTENT/USDT")
        assert result is None

    def test_format_decision_explanation(self, history):
        """Test formatting decision explanation"""
        decision = {
            "symbol": "BTC/USDT",
            "timestamp": datetime.now().isoformat(),
            "action": "buy",
            "confidence": 0.85,
            "sentiment": 0.6,
            "decision": {
                "action": "buy",
                "confidence": 0.85,
                "reasoning": {
                    "technical": "Strong RSI and MACD signals"
                }
            },
            "agent_debate": {
                "bull_argument": "Price breaking resistance with high volume",
                "bear_argument": "Overbought on daily timeframe",
                "research_summary": "Institutional buying increasing"
            }
        }

        explanation = history.format_decision_explanation(decision)

        assert "BTC/USDT" in explanation
        assert "BUY" in explanation
        assert "85.0%" in explanation
        assert "Bull Argument" in explanation
        assert "Bear Argument" in explanation

    def test_get_all_symbols(self, history):
        """Test retrieving all symbols with history"""
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

        for symbol in symbols:
            decision = {"action": "hold", "confidence": 0.5}
            history.add_decision(symbol, decision)

        all_symbols = history.get_all_symbols()

        assert len(all_symbols) == 3
        assert "BTC/USDT" in all_symbols
        assert "ETH/USDT" in all_symbols

    def test_clear_history(self, history):
        """Test clearing decision history"""
        decision = {"action": "buy", "confidence": 0.7}

        history.add_decision("BTC/USDT", decision)
        history.add_decision("ETH/USDT", decision)

        # Clear specific symbol
        history.clear_history("BTC/USDT")
        assert history.get_last_decision("BTC/USDT") is None
        assert history.get_last_decision("ETH/USDT") is not None

        # Clear all
        history.clear_history()
        assert len(history.get_all_symbols()) == 0
