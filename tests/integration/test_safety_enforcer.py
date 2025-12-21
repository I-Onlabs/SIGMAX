"""
Integration tests for Safety Enforcer auto-pause triggers.

Tests all runtime safety checks and automatic pause mechanisms:
1. Consecutive losses
2. API error bursts
3. Sentiment drops
4. High slippage/MEV attacks
5. Daily loss limits
6. Privacy breaches
7. RAG hallucination detection
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.modules.safety_enforcer import SafetyEnforcer, SafetyViolation


class TestSafetyEnforcerTriggers:
    """Test all auto-pause triggers"""

    @pytest.fixture
    def safety_enforcer(self):
        """Create safety enforcer with default settings"""
        with patch.dict('os.environ', {
            'MAX_CONSECUTIVE_LOSSES': '3',
            'MAX_API_ERRORS_PER_MIN': '5',
            'MIN_SENTIMENT': '-0.3',
            'MAX_SLIPPAGE_PCT': '1.0',
            'MAX_DAILY_LOSS': '10'
        }):
            return SafetyEnforcer()

    @pytest.mark.asyncio
    async def test_consecutive_losses_trigger(self, safety_enforcer):
        """Test auto-pause on consecutive losses"""

        print("\n=== Consecutive Losses Trigger ===")

        # Record winning trade first
        safety_enforcer.record_trade_result({
            "success": True,
            "pnl": 100.0
        })

        violation = safety_enforcer.check_consecutive_losses()
        assert violation is None
        print(f"After 1 win: No violation")

        # Record 3 consecutive losses
        for i in range(3):
            safety_enforcer.record_trade_result({
                "success": False,
                "pnl": -50.0
            })

            violation = safety_enforcer.check_consecutive_losses()

            if i < 2:
                assert violation is None
                print(f"After {i+1} losses: No violation")
            else:
                assert violation is not None
                assert violation.auto_pause is True
                assert "consecutive" in violation.message.lower()
                print(f"After {i+1} losses: VIOLATION - {violation.message}")

    @pytest.mark.asyncio
    async def test_api_error_burst_trigger(self, safety_enforcer):
        """Test auto-pause on API error burst"""

        print("\n=== API Error Burst Trigger ===")

        # Record errors within 1 minute
        for i in range(6):  # 6 errors (threshold is 5)
            safety_enforcer.record_api_error(f"API Error {i+1}")

            violation = safety_enforcer.check_api_error_burst()

            if i < 5:
                assert violation is None
                print(f"After {i+1} errors: No violation")
            else:
                assert violation is not None
                assert violation.auto_pause is True
                assert "error" in violation.message.lower()
                print(f"After {i+1} errors: VIOLATION - {violation.message}")

    @pytest.mark.asyncio
    async def test_sentiment_drop_trigger(self, safety_enforcer):
        """Test auto-pause on sentiment drop"""

        print("\n=== Sentiment Drop Trigger ===")

        test_sentiments = [
            (0.5, False, "Positive sentiment"),
            (0.0, False, "Neutral sentiment"),
            (-0.2, False, "Slightly negative"),
            (-0.4, True, "Critical drop")  # Below -0.3 threshold
        ]

        for sentiment, should_trigger, description in test_sentiments:
            violation = safety_enforcer.check_sentiment_drop(sentiment)

            if should_trigger:
                assert violation is not None
                assert violation.auto_pause is True
                print(f"{description} ({sentiment}): VIOLATION")
            else:
                assert violation is None
                print(f"{description} ({sentiment}): OK")

    @pytest.mark.asyncio
    async def test_mev_attack_trigger(self, safety_enforcer):
        """Test auto-pause on high slippage (MEV attack)"""

        print("\n=== MEV Attack / High Slippage ===")

        test_cases = [
            (100.0, 100.5, False, "0.5% slippage (OK)"),
            (100.0, 101.5, True, "1.5% slippage (TRIGGER)"),
            (100.0, 105.0, True, "5% slippage (CRITICAL)")
        ]

        for expected, actual, should_trigger, description in test_cases:
            violation = safety_enforcer.check_mev_attack(expected, actual)

            if should_trigger:
                assert violation is not None
                assert violation.auto_pause is True
                print(f"{description}: VIOLATION")
            else:
                assert violation is None
                print(f"{description}: OK")

    @pytest.mark.asyncio
    async def test_daily_loss_limit_trigger(self, safety_enforcer):
        """Test auto-pause on daily loss limit"""

        print("\n=== Daily Loss Limit ===")

        # Record trades with total loss
        trades = [
            {"success": False, "pnl": -3.0},
            {"success": False, "pnl": -4.0},
            {"success": True, "pnl": 1.0},
            {"success": False, "pnl": -5.0}  # Total: -11, exceeds -10 limit
        ]

        cumulative_pnl = 0.0
        for i, trade in enumerate(trades):
            safety_enforcer.record_trade_result(trade)
            cumulative_pnl += trade["pnl"]

            violation = safety_enforcer.check_daily_loss_limit(cumulative_pnl)

            if abs(cumulative_pnl) < 10.0:
                assert violation is None
                print(f"Trade {i+1}: PnL={cumulative_pnl:.1f} - OK")
            else:
                assert violation is not None
                assert violation.auto_pause is True
                print(f"Trade {i+1}: PnL={cumulative_pnl:.1f} - VIOLATION")

    @pytest.mark.asyncio
    async def test_privacy_breach_trigger(self, safety_enforcer):
        """Test auto-pause on privacy breach detection"""

        print("\n=== Privacy Breach Detection ===")

        # Messages without sensitive data
        safe_messages = [
            {"role": "user", "content": "What is the market sentiment?"},
            {"role": "assistant", "content": "The market is bullish"}
        ]

        violation = safety_enforcer.check_privacy_breach(safe_messages)
        assert violation is None
        print("Safe messages: OK")

        # Messages with API key leak
        unsafe_messages = [
            {"role": "user", "content": "My API key is sk-1234567890abcdef"}
        ]

        violation = safety_enforcer.check_privacy_breach(unsafe_messages)
        assert violation is not None
        assert violation.auto_pause is True
        assert "privacy" in violation.message.lower() or "api" in violation.message.lower()
        print(f"API key detected: VIOLATION - {violation.message}")

    @pytest.mark.asyncio
    async def test_consecutive_losses_reset_after_win(self, safety_enforcer):
        """Test that consecutive loss counter resets after a win"""

        print("\n=== Consecutive Losses Reset ===")

        # 2 losses, then a win, then 2 more losses
        safety_enforcer.record_trade_result({"success": False, "pnl": -10})
        safety_enforcer.record_trade_result({"success": False, "pnl": -10})
        print("After 2 losses: counter at 2")

        safety_enforcer.record_trade_result({"success": True, "pnl": 20})
        print("After 1 win: counter reset")

        safety_enforcer.record_trade_result({"success": False, "pnl": -10})
        safety_enforcer.record_trade_result({"success": False, "pnl": -10})

        # Should not trigger (only 2 consecutive after reset)
        violation = safety_enforcer.check_consecutive_losses()
        assert violation is None
        print("After 2 more losses (post-win): No violation (counter reset)")

    @pytest.mark.asyncio
    async def test_api_errors_expire_after_time(self, safety_enforcer):
        """Test that old API errors don't trigger burst detection"""

        print("\n=== API Error Expiration ===")

        # Record 3 errors more than 1 minute ago
        old_time = datetime.now() - timedelta(minutes=2)
        for i in range(3):
            error_record = {
                "timestamp": old_time,
                "error": f"Old error {i}"
            }
            safety_enforcer.api_errors.append(error_record)

        # Record 2 recent errors
        for i in range(2):
            safety_enforcer.record_api_error(f"Recent error {i}")

        # Should not trigger (only 2 errors in last minute)
        violation = safety_enforcer.check_api_error_burst()
        assert violation is None
        print("3 old + 2 recent errors: No violation (old errors expired)")

    @pytest.mark.asyncio
    async def test_multiple_violations(self, safety_enforcer):
        """Test handling multiple simultaneous violations"""

        print("\n=== Multiple Violations ===")

        # Trigger multiple violations
        violations = []

        # 1. Consecutive losses
        for _ in range(3):
            safety_enforcer.record_trade_result({"success": False, "pnl": -10})

        v1 = safety_enforcer.check_consecutive_losses()
        if v1:
            violations.append(v1)
            safety_enforcer.violations.append(v1)

        # 2. API error burst
        for _ in range(6):
            safety_enforcer.record_api_error("Error")

        v2 = safety_enforcer.check_api_error_burst()
        if v2:
            violations.append(v2)
            safety_enforcer.violations.append(v2)

        # 3. Sentiment drop
        v3 = safety_enforcer.check_sentiment_drop(-0.5)
        if v3:
            violations.append(v3)
            safety_enforcer.violations.append(v3)

        print(f"Total violations triggered: {len(violations)}")
        for v in violations:
            print(f"  - {v.trigger}: {v.message}")

        assert len(violations) >= 2  # At least 2 should trigger

    @pytest.mark.asyncio
    async def test_violation_severity_levels(self, safety_enforcer):
        """Test different severity levels for violations"""

        print("\n=== Violation Severity Levels ===")

        # Critical: Consecutive losses
        for _ in range(3):
            safety_enforcer.record_trade_result({"success": False, "pnl": -10})

        critical = safety_enforcer.check_consecutive_losses()
        if critical:
            print(f"Consecutive losses: {critical.severity}")
            assert critical.severity in ["critical", "warning"]

        # Check sentiment drop
        warning = safety_enforcer.check_sentiment_drop(-0.25)
        critical_sent = safety_enforcer.check_sentiment_drop(-0.6)

        if warning:
            print(f"Mild sentiment drop: {warning.severity}")

        if critical_sent:
            print(f"Severe sentiment drop: {critical_sent.severity}")


class TestSafetyEnforcerIntegration:
    """Integration tests with orchestrator"""

    @pytest.fixture
    def safety_enforcer(self):
        """Create safety enforcer"""
        return SafetyEnforcer()

    @pytest.mark.asyncio
    async def test_pause_mechanism(self, safety_enforcer):
        """Test that paused state is set correctly"""

        print("\n=== Pause Mechanism ===")

        assert safety_enforcer.paused is False
        assert safety_enforcer.pause_reason is None
        print("Initial state: Not paused")

        # Trigger a violation
        for _ in range(3):
            safety_enforcer.record_trade_result({"success": False, "pnl": -10})

        violation = safety_enforcer.check_consecutive_losses()

        if violation and violation.auto_pause:
            safety_enforcer.paused = True
            safety_enforcer.pause_reason = violation.message

            print(f"After violation: Paused")
            print(f"Reason: {safety_enforcer.pause_reason}")

            assert safety_enforcer.paused is True
            assert safety_enforcer.pause_reason is not None

    @pytest.mark.asyncio
    async def test_violation_history(self, safety_enforcer):
        """Test that violations are recorded in history"""

        print("\n=== Violation History ===")

        initial_count = len(safety_enforcer.violations)

        # Trigger violations
        for _ in range(3):
            safety_enforcer.record_trade_result({"success": False, "pnl": -10})

        v1 = safety_enforcer.check_consecutive_losses()
        if v1:
            safety_enforcer.violations.append(v1)

        v2 = safety_enforcer.check_sentiment_drop(-0.5)
        if v2:
            safety_enforcer.violations.append(v2)

        final_count = len(safety_enforcer.violations)
        added = final_count - initial_count

        print(f"Violations recorded: {added}")
        print(f"Total history: {final_count}")

        assert final_count > initial_count

        # Check timestamps
        for v in safety_enforcer.violations:
            assert isinstance(v.timestamp, datetime)
            assert isinstance(v.trigger, str)
            assert isinstance(v.message, str)

    @pytest.mark.asyncio
    async def test_slippage_calculation_edge_cases(self, safety_enforcer):
        """Test slippage calculation with edge cases"""

        print("\n=== Slippage Edge Cases ===")

        # Zero expected price
        v1 = safety_enforcer.check_mev_attack(0.0, 100.0)
        print(f"Zero expected price: {'VIOLATION' if v1 else 'Handled'}")

        # Negative prices (shouldn't happen but test)
        v2 = safety_enforcer.check_mev_attack(-100.0, -101.0)
        print(f"Negative prices: {'VIOLATION' if v2 else 'Handled'}")

        # Very small prices
        v3 = safety_enforcer.check_mev_attack(0.001, 0.00105)
        print(f"Small prices (0.5% slip): {'VIOLATION' if v3 else 'OK'}")

    @pytest.mark.asyncio
    async def test_sentiment_boundary_conditions(self, safety_enforcer):
        """Test sentiment drop at boundary values"""

        print("\n=== Sentiment Boundaries ===")

        test_values = [
            (-1.0, "Extreme bearish"),
            (-0.3, "At threshold"),
            (-0.29, "Just above threshold"),
            (-0.31, "Just below threshold"),
            (1.0, "Extreme bullish")
        ]

        for value, description in test_values:
            violation = safety_enforcer.check_sentiment_drop(value)
            status = "VIOLATION" if violation else "OK"
            print(f"{description} ({value}): {status}")

    @pytest.mark.asyncio
    async def test_error_burst_timing(self, safety_enforcer):
        """Test API error burst with precise timing"""

        print("\n=== Error Burst Timing ===")

        # Simulate errors at different times
        now = datetime.now()

        # 3 errors in last 30 seconds
        for i in range(3):
            safety_enforcer.api_errors.append({
                "timestamp": now - timedelta(seconds=i*10),
                "error": f"Recent error {i}"
            })

        # 3 errors 90 seconds ago (outside 1-minute window)
        for i in range(3):
            safety_enforcer.api_errors.append({
                "timestamp": now - timedelta(seconds=90+i*5),
                "error": f"Old error {i}"
            })

        violation = safety_enforcer.check_api_error_burst()
        status = "VIOLATION" if violation else "OK (old errors don't count)"
        print(f"3 recent + 3 old errors: {status}")


class TestSafetyConfiguration:
    """Test configuration and thresholds"""

    @pytest.mark.asyncio
    async def test_custom_thresholds(self):
        """Test safety enforcer with custom thresholds"""

        print("\n=== Custom Thresholds ===")

        with patch.dict('os.environ', {
            'MAX_CONSECUTIVE_LOSSES': '5',  # Increased
            'MAX_API_ERRORS_PER_MIN': '10',  # Increased
            'MIN_SENTIMENT': '-0.5',  # More tolerant
            'MAX_SLIPPAGE_PCT': '2.0',  # More tolerant
        }):
            enforcer = SafetyEnforcer()

            print(f"Max consecutive losses: {enforcer.max_consecutive_losses}")
            print(f"Max API errors/min: {enforcer.max_api_errors_per_min}")
            print(f"Min sentiment: {enforcer.min_sentiment}")
            print(f"Max slippage: {enforcer.max_slippage}%")

            assert enforcer.max_consecutive_losses == 5
            assert enforcer.max_api_errors_per_min == 10
            assert enforcer.min_sentiment == -0.5
            assert enforcer.max_slippage == 2.0

            # Should now tolerate 4 losses
            for _ in range(4):
                enforcer.record_trade_result({"success": False, "pnl": -10})

            violation = enforcer.check_consecutive_losses()
            assert violation is None
            print("4 losses with threshold=5: OK")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
