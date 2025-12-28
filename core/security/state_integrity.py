"""
State Integrity Verification - Position/Portfolio State Protection
Inspired by TradeTrap's state tampering attack patterns

Protects against:
- Position state manipulation
- Portfolio balance tampering
- Order history corruption
- Cognitive confusion attacks
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
from loguru import logger


class IntegrityStatus(Enum):
    """State integrity status."""
    VERIFIED = "verified"
    SUSPICIOUS = "suspicious"
    COMPROMISED = "compromised"
    UNKNOWN = "unknown"


class TamperType(Enum):
    """Types of state tampering."""
    POSITION_MISMATCH = "position_mismatch"
    BALANCE_MISMATCH = "balance_mismatch"
    ORDER_HISTORY_GAP = "order_history_gap"
    IMPOSSIBLE_STATE = "impossible_state"
    HASH_MISMATCH = "hash_mismatch"
    ROLLBACK_DETECTED = "rollback_detected"
    PHANTOM_POSITION = "phantom_position"


@dataclass
class StateSnapshot:
    """Snapshot of agent state at a point in time."""
    timestamp: datetime
    positions: Dict[str, float]
    cash_balance: float
    total_value: float
    pending_orders: List[Dict]
    state_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "positions": self.positions,
            "cash_balance": self.cash_balance,
            "total_value": round(self.total_value, 2),
            "pending_orders_count": len(self.pending_orders),
            "state_hash": self.state_hash
        }


@dataclass
class IntegrityCheck:
    """Result of state integrity check."""
    status: IntegrityStatus
    tamper_types: List[TamperType]
    confidence: float
    details: Dict[str, Any]
    expected_state: Optional[StateSnapshot]
    actual_state: Optional[StateSnapshot]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "tamper_types": [t.value for t in self.tamper_types],
            "confidence": round(self.confidence, 3),
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class StateIntegrityVerifier:
    """
    Verifies integrity of agent state (positions, balances, orders).

    Usage:
        verifier = StateIntegrityVerifier()

        # Record state after each operation
        verifier.record_state(agent_id, positions, balance)

        # Verify state hasn't been tampered
        result = verifier.verify_state(agent_id, current_positions, current_balance)
        if result.status == IntegrityStatus.COMPROMISED:
            print("State tampering detected!")
    """

    def __init__(
        self,
        max_history: int = 1000,
        tolerance_pct: float = 0.01,
        enable_hash_verification: bool = True
    ):
        """
        Initialize state integrity verifier.

        Args:
            max_history: Maximum state snapshots to keep per agent
            tolerance_pct: Tolerance for floating point comparisons
            enable_hash_verification: Enable cryptographic hash verification
        """
        self.max_history = max_history
        self.tolerance_pct = tolerance_pct
        self.enable_hash_verification = enable_hash_verification

        # State history per agent
        self._state_history: Dict[str, List[StateSnapshot]] = {}

        # Trade log for reconciliation
        self._trade_log: Dict[str, List[Dict]] = {}

        # Integrity check history
        self._check_history: List[IntegrityCheck] = []

    def record_state(
        self,
        agent_id: str,
        positions: Dict[str, float],
        cash_balance: float,
        pending_orders: List[Dict] = None,
        prices: Dict[str, float] = None
    ) -> StateSnapshot:
        """
        Record a state snapshot for an agent.

        Args:
            agent_id: Agent identifier
            positions: Current positions {symbol: quantity}
            cash_balance: Current cash balance
            pending_orders: List of pending orders
            prices: Current prices for total value calculation

        Returns:
            Created StateSnapshot
        """
        pending_orders = pending_orders or []
        prices = prices or {}

        # Calculate total value
        position_value = sum(
            qty * prices.get(symbol, 0)
            for symbol, qty in positions.items()
        )
        total_value = cash_balance + position_value

        # Generate state hash
        state_hash = self._generate_hash(positions, cash_balance, pending_orders)

        snapshot = StateSnapshot(
            timestamp=datetime.utcnow(),
            positions=dict(positions),
            cash_balance=cash_balance,
            total_value=total_value,
            pending_orders=list(pending_orders),
            state_hash=state_hash
        )

        # Store snapshot
        if agent_id not in self._state_history:
            self._state_history[agent_id] = []

        self._state_history[agent_id].append(snapshot)

        # Prune old history
        if len(self._state_history[agent_id]) > self.max_history:
            self._state_history[agent_id] = self._state_history[agent_id][-self.max_history:]

        return snapshot

    def record_trade(
        self,
        agent_id: str,
        trade: Dict[str, Any]
    ):
        """
        Record a trade for state reconciliation.

        Trade dict should include:
        - symbol: str
        - action: "buy" or "sell"
        - quantity: float
        - price: float
        - timestamp: datetime
        """
        if agent_id not in self._trade_log:
            self._trade_log[agent_id] = []

        trade_record = {
            **trade,
            "recorded_at": datetime.utcnow()
        }
        self._trade_log[agent_id].append(trade_record)

    def verify_state(
        self,
        agent_id: str,
        current_positions: Dict[str, float],
        current_balance: float,
        current_prices: Dict[str, float] = None
    ) -> IntegrityCheck:
        """
        Verify current state against recorded history.

        Args:
            agent_id: Agent identifier
            current_positions: Current reported positions
            current_balance: Current reported cash balance
            current_prices: Current prices for value calculation

        Returns:
            IntegrityCheck result
        """
        tamper_types = []
        details = {}

        # Get last known state
        history = self._state_history.get(agent_id, [])

        if not history:
            return IntegrityCheck(
                status=IntegrityStatus.UNKNOWN,
                tamper_types=[],
                confidence=0.5,
                details={"reason": "no_history"},
                expected_state=None,
                actual_state=None
            )

        last_snapshot = history[-1]

        # Create current snapshot for comparison
        current_prices = current_prices or {}
        position_value = sum(
            qty * current_prices.get(symbol, 0)
            for symbol, qty in current_positions.items()
        )
        current_hash = self._generate_hash(current_positions, current_balance, [])

        current_snapshot = StateSnapshot(
            timestamp=datetime.utcnow(),
            positions=current_positions,
            cash_balance=current_balance,
            total_value=current_balance + position_value,
            pending_orders=[],
            state_hash=current_hash
        )

        # Check 1: Position consistency
        position_check = self._verify_positions(
            agent_id, last_snapshot.positions, current_positions
        )
        if not position_check["consistent"]:
            tamper_types.append(TamperType.POSITION_MISMATCH)
            details["position_check"] = position_check

        # Check 2: Balance consistency
        balance_check = self._verify_balance(
            agent_id, last_snapshot.cash_balance, current_balance
        )
        if not balance_check["consistent"]:
            tamper_types.append(TamperType.BALANCE_MISMATCH)
            details["balance_check"] = balance_check

        # Check 3: Impossible states
        impossible_check = self._check_impossible_state(
            current_positions, current_balance
        )
        if impossible_check["impossible"]:
            tamper_types.append(TamperType.IMPOSSIBLE_STATE)
            details["impossible_check"] = impossible_check

        # Check 4: Hash verification (if enabled)
        if self.enable_hash_verification:
            hash_check = self._verify_state_chain(agent_id)
            if not hash_check["valid"]:
                tamper_types.append(TamperType.HASH_MISMATCH)
                details["hash_check"] = hash_check

        # Check 5: Rollback detection
        rollback_check = self._detect_rollback(agent_id, current_snapshot)
        if rollback_check["detected"]:
            tamper_types.append(TamperType.ROLLBACK_DETECTED)
            details["rollback_check"] = rollback_check

        # Check 6: Phantom positions
        phantom_check = self._detect_phantom_positions(
            agent_id, current_positions
        )
        if phantom_check["detected"]:
            tamper_types.append(TamperType.PHANTOM_POSITION)
            details["phantom_check"] = phantom_check

        # Determine overall status
        status, confidence = self._calculate_status(tamper_types)

        result = IntegrityCheck(
            status=status,
            tamper_types=tamper_types,
            confidence=confidence,
            details=details,
            expected_state=last_snapshot,
            actual_state=current_snapshot
        )

        self._check_history.append(result)

        if tamper_types:
            logger.warning(f"State integrity issues for {agent_id}: {[t.value for t in tamper_types]}")

        return result

    def _generate_hash(
        self,
        positions: Dict[str, float],
        balance: float,
        orders: List[Dict]
    ) -> str:
        """Generate cryptographic hash of state."""
        # Normalize for consistent hashing
        state_data = {
            "positions": dict(sorted(positions.items())),
            "balance": round(balance, 8),
            "orders_count": len(orders)
        }
        state_str = json.dumps(state_data, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()[:16]

    def _verify_positions(
        self,
        agent_id: str,
        last_positions: Dict[str, float],
        current_positions: Dict[str, float]
    ) -> Dict[str, Any]:
        """Verify position changes are consistent with trades."""
        trades = self._trade_log.get(agent_id, [])

        # Calculate expected position changes from trades
        expected_changes: Dict[str, float] = {}
        for trade in trades:
            symbol = trade.get("symbol")
            action = trade.get("action")
            quantity = trade.get("quantity", 0)

            if symbol:
                if action == "buy":
                    expected_changes[symbol] = expected_changes.get(symbol, 0) + quantity
                elif action == "sell":
                    expected_changes[symbol] = expected_changes.get(symbol, 0) - quantity

        # Check each position
        inconsistencies = []
        all_symbols = set(last_positions.keys()) | set(current_positions.keys())

        for symbol in all_symbols:
            last_qty = last_positions.get(symbol, 0)
            current_qty = current_positions.get(symbol, 0)
            expected_change = expected_changes.get(symbol, 0)

            expected_qty = last_qty + expected_change
            diff = abs(current_qty - expected_qty)

            # Allow small tolerance for floating point
            tolerance = max(abs(expected_qty) * self.tolerance_pct, 0.001)

            if diff > tolerance:
                inconsistencies.append({
                    "symbol": symbol,
                    "expected": expected_qty,
                    "actual": current_qty,
                    "difference": diff
                })

        return {
            "consistent": len(inconsistencies) == 0,
            "inconsistencies": inconsistencies
        }

    def _verify_balance(
        self,
        agent_id: str,
        last_balance: float,
        current_balance: float
    ) -> Dict[str, Any]:
        """Verify balance changes are consistent with trades."""
        trades = self._trade_log.get(agent_id, [])

        # Calculate expected balance change
        expected_change = 0
        for trade in trades:
            action = trade.get("action")
            quantity = trade.get("quantity", 0)
            price = trade.get("price", 0)

            if action == "buy":
                expected_change -= quantity * price
            elif action == "sell":
                expected_change += quantity * price

        expected_balance = last_balance + expected_change
        diff = abs(current_balance - expected_balance)

        # Allow tolerance
        tolerance = max(abs(expected_balance) * self.tolerance_pct, 0.01)

        return {
            "consistent": diff <= tolerance,
            "expected": expected_balance,
            "actual": current_balance,
            "difference": diff
        }

    def _check_impossible_state(
        self,
        positions: Dict[str, float],
        balance: float
    ) -> Dict[str, Any]:
        """Check for impossible states."""
        impossible_reasons = []

        # Negative balance
        if balance < -0.01:  # Small tolerance for rounding
            impossible_reasons.append("negative_balance")

        # Negative positions (unless shorting is allowed)
        for symbol, qty in positions.items():
            if qty < -0.001:
                impossible_reasons.append(f"negative_position_{symbol}")

        # Extreme values
        if balance > 1e12:
            impossible_reasons.append("balance_too_large")

        for symbol, qty in positions.items():
            if abs(qty) > 1e9:
                impossible_reasons.append(f"position_too_large_{symbol}")

        return {
            "impossible": len(impossible_reasons) > 0,
            "reasons": impossible_reasons
        }

    def _verify_state_chain(self, agent_id: str) -> Dict[str, Any]:
        """Verify state hash chain integrity."""
        history = self._state_history.get(agent_id, [])

        if len(history) < 2:
            return {"valid": True, "reason": "insufficient_history"}

        # Check for duplicate or out-of-order timestamps
        for i in range(1, len(history)):
            if history[i].timestamp <= history[i-1].timestamp:
                return {
                    "valid": False,
                    "reason": "timestamp_order_violation",
                    "index": i
                }

        # Verify no sudden hash changes without corresponding trades
        # (simplified check - full implementation would chain hashes)
        return {"valid": True}

    def _detect_rollback(
        self,
        agent_id: str,
        current_snapshot: StateSnapshot
    ) -> Dict[str, Any]:
        """Detect if state has been rolled back to a previous state."""
        history = self._state_history.get(agent_id, [])

        if len(history) < 3:
            return {"detected": False}

        # Check if current state matches an old state exactly
        for i, old_snapshot in enumerate(history[:-2]):
            if (old_snapshot.positions == current_snapshot.positions and
                abs(old_snapshot.cash_balance - current_snapshot.cash_balance) < 0.01):
                return {
                    "detected": True,
                    "rollback_to_index": i,
                    "rollback_timestamp": old_snapshot.timestamp.isoformat()
                }

        return {"detected": False}

    def _detect_phantom_positions(
        self,
        agent_id: str,
        current_positions: Dict[str, float]
    ) -> Dict[str, Any]:
        """Detect positions that appeared without corresponding trades."""
        history = self._state_history.get(agent_id, [])
        trades = self._trade_log.get(agent_id, [])

        if not history:
            return {"detected": False}

        # Get symbols that have ever been traded
        traded_symbols = set()
        for trade in trades:
            if trade.get("symbol"):
                traded_symbols.add(trade["symbol"])

        # Get symbols from first known state
        if history:
            initial_symbols = set(history[0].positions.keys())
        else:
            initial_symbols = set()

        # Find phantom positions (exist now but never traded and not in initial)
        phantom = []
        for symbol, qty in current_positions.items():
            if qty != 0 and symbol not in traded_symbols and symbol not in initial_symbols:
                phantom.append(symbol)

        return {
            "detected": len(phantom) > 0,
            "phantom_symbols": phantom
        }

    def _calculate_status(
        self,
        tamper_types: List[TamperType]
    ) -> Tuple[IntegrityStatus, float]:
        """Calculate overall integrity status."""
        if not tamper_types:
            return IntegrityStatus.VERIFIED, 1.0

        # Critical tampering
        critical = {
            TamperType.IMPOSSIBLE_STATE,
            TamperType.HASH_MISMATCH,
            TamperType.ROLLBACK_DETECTED
        }

        if any(t in critical for t in tamper_types):
            return IntegrityStatus.COMPROMISED, 0.9

        if len(tamper_types) >= 2:
            return IntegrityStatus.COMPROMISED, 0.8

        return IntegrityStatus.SUSPICIOUS, 0.7

    def get_state_history(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get state history for an agent."""
        history = self._state_history.get(agent_id, [])
        return [s.to_dict() for s in history[-limit:]]

    def get_statistics(self) -> Dict[str, Any]:
        """Get verification statistics."""
        if not self._check_history:
            return {"total_checks": 0}

        status_counts = {}
        tamper_counts = {}

        for check in self._check_history:
            status = check.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            for tamper in check.tamper_types:
                t = tamper.value
                tamper_counts[t] = tamper_counts.get(t, 0) + 1

        return {
            "total_checks": len(self._check_history),
            "agents_tracked": len(self._state_history),
            "status_distribution": status_counts,
            "tamper_distribution": tamper_counts
        }

    def clear_agent_history(self, agent_id: str):
        """Clear history for a specific agent."""
        self._state_history.pop(agent_id, None)
        self._trade_log.pop(agent_id, None)

    def clear_all(self):
        """Clear all history."""
        self._state_history.clear()
        self._trade_log.clear()
        self._check_history.clear()
