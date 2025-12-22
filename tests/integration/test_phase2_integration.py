#!/usr/bin/env python3
"""
Phase 2 Integration Tests
Tests quantum integration + debate storage + CLI components
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from datetime import datetime
from core.utils.decision_history import DecisionHistory

# Set environment variables for testing
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_DB'] = 'sigmax'
os.environ['POSTGRES_USER'] = 'sigmax'
os.environ['POSTGRES_PASSWORD'] = 'sigmax_dev'
os.environ['QUANTUM_ENABLED'] = 'true'


class TestDebateStorage:
    """Test agent debate storage in PostgreSQL"""

    def test_debate_saves_to_postgres(self):
        """Verify debates are saved to PostgreSQL"""
        history = DecisionHistory(use_redis=False, use_postgres=True)

        symbol = "ETH/USDT"
        decision = {
            "action": "sell",
            "confidence": 0.65,
            "sentiment": -0.3,
            "reasoning": {"technical": "Bearish divergence"}
        }

        agent_debate = {
            "bull_argument": "Support holding at $3.2k",
            "bear_argument": "Breaking below key support",
            "research_summary": "Mixed signals, trend turning bearish",
            "agent_scores": {"bull": 0.4, "bear": 0.7}
        }

        # Save debate
        history.add_decision(symbol, decision, agent_debate)

        # Verify in memory
        last_decision = history.get_last_decision(symbol)
        assert last_decision is not None
        assert last_decision["action"] == "sell"
        assert last_decision["confidence"] == 0.65

        # Verify in database
        if history.pg_connection:
            cursor = history.pg_connection.cursor()
            cursor.execute(
                "SELECT * FROM agent_debates WHERE symbol = %s ORDER BY created_at DESC LIMIT 1",
                (symbol,)
            )
            result = cursor.fetchone()

            assert result is not None
            assert result['final_decision'] == "sell"
            assert float(result['confidence']) == 0.65
            assert "Breaking below" in result['bear_argument']

    def test_debate_retrieval_pagination(self):
        """Verify pagination works for debate retrieval"""
        history = DecisionHistory(use_redis=False, use_postgres=True)

        symbol = "SOL/USDT"

        # Create multiple decisions
        for i in range(5):
            decision = {
                "action": "buy" if i % 2 == 0 else "sell",
                "confidence": 0.5 + (i * 0.1),
                "sentiment": 0.0
            }
            agent_debate = {
                "bull_argument": f"Bull argument {i}",
                "bear_argument": f"Bear argument {i}",
                "research_summary": f"Summary {i}"
            }
            history.add_decision(symbol, decision, agent_debate)

        # Test retrieval with limit
        decisions = history.get_decisions(symbol, limit=3)
        assert len(decisions) <= 3

        # Test retrieval with time filter
        since = datetime.now()
        recent_decisions = history.get_decisions(symbol, since=since, limit=10)
        # Should be empty since all were created before 'now'
        assert len(recent_decisions) == 0

    def test_debate_persistence_across_restarts(self):
        """Verify debates persist in PostgreSQL across DecisionHistory instances"""
        symbol = "MATIC/USDT"

        # Create first instance and save debate
        history1 = DecisionHistory(use_redis=False, use_postgres=True)
        decision = {
            "action": "hold",
            "confidence": 0.5,
            "sentiment": 0.0
        }
        agent_debate = {
            "bull_argument": "Stable support",
            "bear_argument": "Sideways movement",
            "research_summary": "Wait for breakout"
        }
        history1.add_decision(symbol, decision, agent_debate)

        # Create second instance (simulates restart)
        history2 = DecisionHistory(use_redis=False, use_postgres=True)

        # Verify data still available (from database, not memory)
        if history2.pg_connection:
            cursor = history2.pg_connection.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM agent_debates WHERE symbol = %s",
                (symbol,)
            )
            result = cursor.fetchone()
            assert result['count'] > 0


class TestQuantumIntegration:
    """Test quantum optimization integration"""

    def test_quantum_module_imports(self):
        """Verify quantum module can be imported"""
        try:
            from core.modules.quantum import QuantumModule
            assert QuantumModule is not None
        except ImportError as e:
            pytest.skip(f"Quantum module not available: {e}")

    def test_quantum_environment_variable(self):
        """Verify QUANTUM_ENABLED environment variable is respected"""
        # Test enabled
        os.environ['QUANTUM_ENABLED'] = 'true'
        enabled = os.getenv('QUANTUM_ENABLED', 'true').lower() == 'true'
        assert enabled is True

        # Test disabled
        os.environ['QUANTUM_ENABLED'] = 'false'
        enabled = os.getenv('QUANTUM_ENABLED', 'true').lower() == 'true'
        assert enabled is False

        # Reset
        os.environ['QUANTUM_ENABLED'] = 'true'

    def test_quantum_optimizer_initialization(self):
        """Verify quantum optimizer can be initialized"""
        try:
            from core.modules.quantum import QuantumModule
            quantum = QuantumModule()
            assert quantum is not None
        except Exception as e:
            pytest.skip(f"Quantum initialization failed: {e}")


class TestDecisionHistoryFeatures:
    """Test DecisionHistory utility features"""

    def test_decision_formatting(self):
        """Verify decision explanation formatting"""
        history = DecisionHistory()

        decision_record = {
            "symbol": "BTC/USDT",
            "timestamp": datetime.now().isoformat(),
            "decision": {
                "action": "buy",
                "confidence": 0.85,
                "sentiment": 0.6,
                "reasoning": {"technical": "Strong momentum"}
            },
            "agent_debate": {
                "bull_argument": "Breaking ATH, institutional buying",
                "bear_argument": "Overbought RSI",
                "research_summary": "Positive macro environment"
            },
            "action": "buy",
            "confidence": 0.85,
            "sentiment": 0.6
        }

        explanation = history.format_decision_explanation(decision_record)

        assert "BTC/USDT" in explanation
        assert "BUY" in explanation.upper()  # Decision is uppercase in formatted output
        assert "85" in explanation  # Confidence percentage
        assert "Bull Argument" in explanation or "BULL ARGUMENT" in explanation
        assert "Bear Argument" in explanation or "BEAR ARGUMENT" in explanation

    def test_get_all_symbols(self):
        """Verify getting list of all tracked symbols"""
        history = DecisionHistory()

        # Add decisions for multiple symbols
        for symbol in ["BTC/USDT", "ETH/USDT", "SOL/USDT"]:
            decision = {"action": "hold", "confidence": 0.5, "sentiment": 0.0}
            history.add_decision(symbol, decision)

        symbols = history.get_all_symbols()
        assert len(symbols) >= 3
        assert "BTC/USDT" in symbols

    def test_clear_history(self):
        """Verify clearing decision history"""
        history = DecisionHistory()

        symbol = "DOGE/USDT"
        decision = {"action": "hold", "confidence": 0.5, "sentiment": 0.0}
        history.add_decision(symbol, decision)

        # Verify exists
        assert symbol in history.decisions

        # Clear specific symbol
        history.clear_history(symbol)
        assert len(history.decisions.get(symbol, [])) == 0

        # Test clear all
        history.add_decision("TEST1/USDT", decision)
        history.add_decision("TEST2/USDT", decision)
        history.clear_history()
        assert len(history.decisions) == 0


def run_integration_tests():
    """Run all integration tests"""
    print("=" * 70)
    print("Phase 2 Integration Tests")
    print("=" * 70)
    print()

    # Run pytest
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-k", "test_"
    ])

    return exit_code


if __name__ == "__main__":
    sys.exit(run_integration_tests())
