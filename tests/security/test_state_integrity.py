"""
Tests for StateIntegrityVerifier - State Tampering Defense
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.security.state_integrity import (
    StateIntegrityVerifier,
    IntegrityCheck,
    IntegrityStatus,
    TamperType,
    StateSnapshot
)


class TestStateIntegrityVerifier:
    """Test StateIntegrityVerifier for tampering defense."""

    @pytest.fixture
    def verifier(self):
        """Create a verifier instance."""
        return StateIntegrityVerifier(
            max_snapshots=100,
            alert_on_tamper=True
        )

    def test_record_and_verify_valid_state(self, verifier):
        """Test recording and verifying valid state."""
        agent_id = "test_agent"
        positions = {"BTC/USDT": 1.5, "ETH/USDT": 10.0}
        balance = 50000.0

        # Record initial state
        snapshot = verifier.record_state(
            agent_id=agent_id,
            positions=positions,
            cash_balance=balance
        )

        assert snapshot is not None
        assert snapshot.agent_id == agent_id

        # Verify same state
        check = verifier.verify_state(
            agent_id=agent_id,
            current_positions=positions,
            current_balance=balance
        )

        assert check.status == IntegrityStatus.VALID
        assert len(check.tamper_types) == 0

    def test_detect_position_tampering(self, verifier):
        """Test detection of position tampering."""
        agent_id = "test_agent"

        # Record initial state
        verifier.record_state(
            agent_id=agent_id,
            positions={"BTC/USDT": 1.0},
            cash_balance=10000.0
        )

        # Verify with tampered positions (increased without trade)
        check = verifier.verify_state(
            agent_id=agent_id,
            current_positions={"BTC/USDT": 5.0},  # Increased from 1.0
            current_balance=10000.0  # Balance unchanged
        )

        assert check.status != IntegrityStatus.VALID
        assert TamperType.POSITION_MISMATCH in check.tamper_types

    def test_detect_balance_tampering(self, verifier):
        """Test detection of balance tampering."""
        agent_id = "test_agent"

        # Record initial state
        verifier.record_state(
            agent_id=agent_id,
            positions={"BTC/USDT": 1.0},
            cash_balance=10000.0
        )

        # Verify with tampered balance
        check = verifier.verify_state(
            agent_id=agent_id,
            current_positions={"BTC/USDT": 1.0},
            current_balance=100000.0  # 10x increase without trade
        )

        assert check.status != IntegrityStatus.VALID
        assert TamperType.BALANCE_TAMPER in check.tamper_types

    def test_detect_phantom_position(self, verifier):
        """Test detection of phantom (unrecorded) positions."""
        agent_id = "test_agent"

        # Record initial state with only BTC
        verifier.record_state(
            agent_id=agent_id,
            positions={"BTC/USDT": 1.0},
            cash_balance=10000.0
        )

        # Verify with phantom ETH position
        check = verifier.verify_state(
            agent_id=agent_id,
            current_positions={
                "BTC/USDT": 1.0,
                "ETH/USDT": 100.0  # Never recorded
            },
            current_balance=10000.0
        )

        assert check.status != IntegrityStatus.VALID
        assert TamperType.PHANTOM_POSITION in check.tamper_types

    def test_valid_trade_updates_state(self, verifier):
        """Test that recording trades allows state changes."""
        agent_id = "test_agent"

        # Record initial state
        verifier.record_state(
            agent_id=agent_id,
            positions={"BTC/USDT": 1.0},
            cash_balance=10000.0
        )

        # Record a buy trade
        verifier.record_trade(
            agent_id=agent_id,
            trade={
                "symbol": "BTC/USDT",
                "side": "buy",
                "quantity": 0.5,
                "price": 50000.0,
                "total": 25000.0
            }
        )

        # Update state after trade
        verifier.record_state(
            agent_id=agent_id,
            positions={"BTC/USDT": 1.5},  # Increased by 0.5
            cash_balance=10000.0 - 25000.0  # Decreased by trade cost
        )

        # Verify new state
        check = verifier.verify_state(
            agent_id=agent_id,
            current_positions={"BTC/USDT": 1.5},
            current_balance=-15000.0
        )

        assert check.status == IntegrityStatus.VALID

    def test_detect_rollback_attack(self, verifier):
        """Test detection of state rollback attacks."""
        agent_id = "test_agent"

        # Record sequence of states
        verifier.record_state(
            agent_id=agent_id,
            positions={"BTC/USDT": 1.0},
            cash_balance=10000.0
        )

        verifier.record_state(
            agent_id=agent_id,
            positions={"BTC/USDT": 2.0},
            cash_balance=5000.0
        )

        verifier.record_state(
            agent_id=agent_id,
            positions={"BTC/USDT": 3.0},
            cash_balance=0.0
        )

        # Try to verify with old state (rollback)
        check = verifier.verify_state(
            agent_id=agent_id,
            current_positions={"BTC/USDT": 1.0},  # Rolled back
            current_balance=10000.0
        )

        # Should detect something is wrong
        assert check.status != IntegrityStatus.VALID

    def test_multiple_agents_isolated(self, verifier):
        """Test that different agents have isolated state."""
        # Record state for agent 1
        verifier.record_state(
            agent_id="agent1",
            positions={"BTC/USDT": 10.0},
            cash_balance=100000.0
        )

        # Record state for agent 2
        verifier.record_state(
            agent_id="agent2",
            positions={"ETH/USDT": 50.0},
            cash_balance=25000.0
        )

        # Verify agent 1
        check1 = verifier.verify_state(
            agent_id="agent1",
            current_positions={"BTC/USDT": 10.0},
            current_balance=100000.0
        )

        # Verify agent 2
        check2 = verifier.verify_state(
            agent_id="agent2",
            current_positions={"ETH/USDT": 50.0},
            current_balance=25000.0
        )

        assert check1.status == IntegrityStatus.VALID
        assert check2.status == IntegrityStatus.VALID

    def test_statistics_tracking(self, verifier):
        """Test statistics tracking."""
        # Record and verify several states
        verifier.record_state("agent1", {"BTC": 1.0}, 1000.0)
        verifier.verify_state("agent1", {"BTC": 1.0}, 1000.0)
        verifier.verify_state("agent1", {"BTC": 100.0}, 1000.0)  # Tampered

        stats = verifier.get_statistics()
        assert stats["total_snapshots"] >= 1
        assert stats["total_checks"] >= 2

    def test_snapshot_hash_integrity(self, verifier):
        """Test that state hashes are computed correctly."""
        agent_id = "test_agent"
        positions = {"BTC/USDT": 1.0, "ETH/USDT": 10.0}
        balance = 50000.0

        snapshot = verifier.record_state(
            agent_id=agent_id,
            positions=positions,
            cash_balance=balance
        )

        # Hash should be deterministic
        assert snapshot.state_hash is not None
        assert len(snapshot.state_hash) > 0

        # Same state should produce same hash
        snapshot2 = verifier.record_state(
            agent_id=agent_id,
            positions=positions,
            cash_balance=balance
        )

        assert snapshot.state_hash == snapshot2.state_hash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
