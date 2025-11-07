"""
Tests for Runtime Safety Enforcer
"""

import pytest
from datetime import datetime, timedelta
from core.modules.safety_enforcer import SafetyEnforcer, SafetyViolation


class TestSafetyEnforcer:
    """Test suite for runtime safety enforcement"""

    @pytest.fixture
    def enforcer(self):
        """Create safety enforcer instance"""
        return SafetyEnforcer()

    def test_enforcer_initialization(self, enforcer):
        """Test safety enforcer initializes correctly"""
        assert enforcer is not None
        assert enforcer.max_consecutive_losses == 3
        assert not enforcer.paused

    def test_consecutive_losses_trigger(self, enforcer):
        """Test consecutive losses trigger auto-pause"""
        # Record 3 losing trades
        for i in range(3):
            enforcer.record_trade_result({
                "success": True,
                "pnl": -5.0,  # Loss
                "slippage": 0.1
            })

        # Check should trigger
        violation = enforcer.check_consecutive_losses()

        assert violation is not None
        assert violation.trigger == "consecutive_losses"
        assert violation.auto_pause is True
        assert "3 consecutive" in violation.message

    def test_consecutive_losses_not_triggered_by_wins(self, enforcer):
        """Test winning trades break consecutive loss streak"""
        # 2 losses, 1 win, 2 losses
        enforcer.record_trade_result({"pnl": -5.0})
        enforcer.record_trade_result({"pnl": -3.0})
        enforcer.record_trade_result({"pnl": +10.0})  # Win breaks streak
        enforcer.record_trade_result({"pnl": -2.0})
        enforcer.record_trade_result({"pnl": -4.0})

        # Should not trigger (only 2 consecutive losses)
        violation = enforcer.check_consecutive_losses()
        assert violation is None

    def test_api_error_burst_trigger(self, enforcer):
        """Test API error burst triggers auto-pause"""
        # Record 6 errors in quick succession
        for i in range(6):
            enforcer.record_api_error(f"Connection timeout {i}")

        # Check should trigger (>5 errors/min)
        violation = enforcer.check_api_error_burst()

        assert violation is not None
        assert violation.trigger == "api_error_burst"
        assert violation.auto_pause is True
        assert "6 API errors" in violation.message

    def test_api_errors_old_errors_ignored(self, enforcer):
        """Test old API errors don't trigger burst"""
        # Manually add old errors
        old_time = datetime.now() - timedelta(minutes=5)
        for i in range(10):
            enforcer.api_errors.append({
                "timestamp": old_time,
                "error": f"Old error {i}"
            })

        # Should not trigger (errors are too old)
        violation = enforcer.check_api_error_burst()
        assert violation is None

    def test_sentiment_drop_trigger(self, enforcer):
        """Test sentiment drop triggers auto-pause"""
        # Sentiment drops below -0.3
        violation = enforcer.check_sentiment_drop(-0.5)

        assert violation is not None
        assert violation.trigger == "sentiment_drop"
        assert violation.auto_pause is True
        assert "-0.50" in violation.message

    def test_sentiment_drop_not_triggered_above_threshold(self, enforcer):
        """Test sentiment above threshold doesn't trigger"""
        violation = enforcer.check_sentiment_drop(-0.2)
        assert violation is None

        violation = enforcer.check_sentiment_drop(0.5)
        assert violation is None

    def test_mev_attack_high_slippage(self, enforcer):
        """Test high slippage / MEV attack detection"""
        expected_price = 100.0
        actual_price = 102.5  # 2.5% slippage

        violation = enforcer.check_mev_attack(expected_price, actual_price)

        assert violation is not None
        assert violation.trigger == "high_slippage"
        assert "2.50%" in violation.message

    def test_mev_attack_acceptable_slippage(self, enforcer):
        """Test acceptable slippage doesn't trigger"""
        expected_price = 100.0
        actual_price = 100.5  # 0.5% slippage (within 1% limit)

        violation = enforcer.check_mev_attack(expected_price, actual_price)
        assert violation is None

    def test_daily_loss_limit_trigger(self, enforcer):
        """Test daily loss limit triggers auto-pause"""
        # Daily loss exceeds $10 limit
        violation = enforcer.check_daily_loss_limit(-15.0)

        assert violation is not None
        assert violation.trigger == "daily_loss_limit"
        assert violation.auto_pause is True
        assert "$15" in violation.message

    def test_daily_loss_within_limit(self, enforcer):
        """Test daily loss within limit doesn't trigger"""
        violation = enforcer.check_daily_loss_limit(-5.0)
        assert violation is None

        violation = enforcer.check_daily_loss_limit(+10.0)  # Profit
        assert violation is None

    def test_privacy_breach_detection(self, enforcer):
        """Test PII detection triggers auto-pause"""
        messages = [
            {"content": "Trading BTC/USDT"},
            {"content": "My API key is abc123"},  # PII detected
            {"content": "Bullish signal"}
        ]

        violation = enforcer.check_privacy_breach(messages)

        assert violation is not None
        assert violation.trigger == "privacy_breach"
        assert "api key" in violation.message

    def test_privacy_breach_no_pii(self, enforcer):
        """Test no PII doesn't trigger"""
        messages = [
            {"content": "Trading BTC/USDT"},
            {"content": "Strong uptrend"},
            {"content": "Risk assessment complete"}
        ]

        violation = enforcer.check_privacy_breach(messages)
        assert violation is None

    def test_run_all_checks(self, enforcer):
        """Test running all checks at once"""
        # Set up multiple violations
        enforcer.record_trade_result({"pnl": -5.0})
        enforcer.record_trade_result({"pnl": -3.0})
        enforcer.record_trade_result({"pnl": -2.0})

        for i in range(6):
            enforcer.record_api_error(f"Error {i}")

        violations = enforcer.run_all_checks(
            sentiment=-0.5,
            daily_pnl=-12.0,
            messages=[{"content": "password: secret123"}]
        )

        # Should have multiple violations
        assert len(violations) >= 3
        trigger_types = [v.trigger for v in violations]
        assert "consecutive_losses" in trigger_types
        assert "api_error_burst" in trigger_types
        assert "sentiment_drop" in trigger_types

    def test_auto_pause_trigger(self, enforcer):
        """Test auto-pause is triggered on critical violation"""
        assert not enforcer.paused

        # Create critical violation
        violation = SafetyViolation(
            trigger="test_trigger",
            message="Test critical violation",
            severity="critical",
            timestamp=datetime.now(),
            auto_pause=True
        )

        enforcer.trigger_auto_pause(violation)

        assert enforcer.paused is True
        assert enforcer.pause_reason == "Test critical violation"

    def test_resume_with_recent_violations(self, enforcer):
        """Test cannot resume with recent violations"""
        # Trigger pause
        enforcer.paused = True
        enforcer.violations.append(SafetyViolation(
            trigger="test",
            message="Recent violation",
            severity="critical",
            timestamp=datetime.now(),
            auto_pause=True
        ))

        # Should not be able to resume
        result = enforcer.resume(force=False)
        assert result is False
        assert enforcer.paused is True

    def test_resume_force_override(self, enforcer):
        """Test force resume overrides violations"""
        # Trigger pause with recent violations
        enforcer.paused = True
        enforcer.violations.append(SafetyViolation(
            trigger="test",
            message="Recent violation",
            severity="critical",
            timestamp=datetime.now(),
            auto_pause=True
        ))

        # Force resume should work
        result = enforcer.resume(force=True)
        assert result is True
        assert enforcer.paused is False

    def test_resume_after_old_violations(self, enforcer):
        """Test can resume after old violations expire"""
        # Add old violations (>30 minutes ago)
        old_time = datetime.now() - timedelta(minutes=45)
        enforcer.paused = True
        enforcer.violations.append(SafetyViolation(
            trigger="test",
            message="Old violation",
            severity="critical",
            timestamp=old_time,
            auto_pause=True
        ))

        # Should be able to resume (violations are old)
        result = enforcer.resume(force=False)
        assert result is True
        assert enforcer.paused is False

    def test_get_status(self, enforcer):
        """Test getting safety status"""
        # Add some test data
        enforcer.record_trade_result({"pnl": -5.0})
        enforcer.record_trade_result({"pnl": -3.0})
        enforcer.record_api_error("Test error")

        status = enforcer.get_status()

        assert "paused" in status
        assert "consecutive_losses" in status
        assert "api_errors_last_minute" in status
        assert status["consecutive_losses"] == 2
        assert status["api_errors_last_minute"] == 1

    def test_clear_history(self, enforcer):
        """Test clearing safety history"""
        # Add test data
        enforcer.record_trade_result({"pnl": -5.0})
        enforcer.record_api_error("Error")
        enforcer.violations.append(SafetyViolation(
            trigger="test",
            message="Test",
            severity="warning",
            timestamp=datetime.now(),
            auto_pause=False
        ))

        assert len(enforcer.recent_trades) > 0
        assert len(enforcer.api_errors) > 0
        assert len(enforcer.violations) > 0

        # Clear
        enforcer.clear_history()

        assert len(enforcer.recent_trades) == 0
        assert len(enforcer.api_errors) == 0
        assert len(enforcer.violations) == 0
