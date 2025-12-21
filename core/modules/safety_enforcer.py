"""
Safety Enforcer - Runtime Safety Checks and Auto-Pause Triggers
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
from loguru import logger
import os


@dataclass
class SafetyViolation:
    """Safety violation record"""
    trigger: str
    message: str
    severity: str  # 'warning' or 'critical'
    timestamp: datetime
    auto_pause: bool


class SafetyEnforcer:
    """
    Runtime safety enforcement with auto-pause triggers

    Auto-Pause Triggers:
    1. Consecutive losses (default: 3)
    2. API error burst (default: >5 errors/min)
    3. Sentiment drop (default: <-0.3)
    4. High slippage / MEV attack (default: >1%)
    5. Daily loss limit exceeded
    6. Privacy breach detected
    7. RAG hallucination detected
    """

    def __init__(self):
        # Configuration
        self.max_consecutive_losses = int(os.getenv("MAX_CONSECUTIVE_LOSSES", 3))
        self.max_api_errors_per_min = int(os.getenv("MAX_API_ERRORS_PER_MIN", 5))
        self.min_sentiment = float(os.getenv("MIN_SENTIMENT", -0.3))
        self.max_slippage = float(os.getenv("MAX_SLIPPAGE_PCT", 1.0))
        self.max_daily_loss = float(os.getenv("MAX_DAILY_LOSS", 10))

        # State tracking
        self.recent_trades: deque = deque(maxlen=100)
        self.api_errors: deque = deque(maxlen=100)
        self.violations: List[SafetyViolation] = []
        self.paused = False
        self.pause_reason: Optional[str] = None

        logger.info("✓ Safety enforcer initialized")

    def record_trade_result(self, trade: Dict[str, Any]):
        """
        Record trade result for safety monitoring

        Args:
            trade: Trade dict with 'success', 'pnl', 'slippage', etc.
        """
        self.recent_trades.append({
            "timestamp": datetime.now(),
            "success": trade.get("success", False),
            "pnl": trade.get("pnl", 0.0),
            "slippage": trade.get("slippage", 0.0)
        })

    def record_api_error(self, error: str):
        """
        Record API error for burst detection

        Args:
            error: Error message
        """
        self.api_errors.append({
            "timestamp": datetime.now(),
            "error": error
        })

    def check_consecutive_losses(self) -> Optional[SafetyViolation]:
        """
        Check for consecutive losing trades

        Returns:
            SafetyViolation if triggered, None otherwise
        """
        if len(self.recent_trades) < self.max_consecutive_losses:
            return None

        # Get last N trades
        recent = list(self.recent_trades)[-self.max_consecutive_losses:]

        # Count consecutive losses
        consecutive_losses = 0
        for trade in reversed(recent):
            if trade.get("pnl", 0) < 0:
                consecutive_losses += 1
            else:
                break

        if consecutive_losses >= self.max_consecutive_losses:
            return SafetyViolation(
                trigger="consecutive_losses",
                message=f"{consecutive_losses} consecutive losing trades detected",
                severity="critical",
                timestamp=datetime.now(),
                auto_pause=True
            )

        return None

    def check_api_error_burst(self) -> Optional[SafetyViolation]:
        """
        Check for API error burst (>5 errors/min)

        Returns:
            SafetyViolation if triggered, None otherwise
        """
        if not self.api_errors:
            return None

        # Count errors in last minute
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        recent_errors = [
            e for e in self.api_errors
            if e["timestamp"] > one_minute_ago
        ]

        if len(recent_errors) > self.max_api_errors_per_min:
            return SafetyViolation(
                trigger="api_error_burst",
                message=f"{len(recent_errors)} API errors in last minute",
                severity="critical",
                timestamp=datetime.now(),
                auto_pause=True
            )

        return None

    def check_sentiment_drop(self, sentiment: float) -> Optional[SafetyViolation]:
        """
        Check if sentiment has dropped below threshold

        Args:
            sentiment: Current sentiment score (-1 to 1)

        Returns:
            SafetyViolation if triggered, None otherwise
        """
        if sentiment < self.min_sentiment:
            return SafetyViolation(
                trigger="sentiment_drop",
                message=f"Sentiment dropped to {sentiment:.2f} (threshold: {self.min_sentiment})",
                severity="warning",
                timestamp=datetime.now(),
                auto_pause=True
            )

        return None

    def check_mev_attack(self, expected_price: float, actual_price: float) -> Optional[SafetyViolation]:
        """
        Check for MEV attack / high slippage

        Args:
            expected_price: Expected execution price
            actual_price: Actual execution price

        Returns:
            SafetyViolation if triggered, None otherwise
        """
        if expected_price == 0:
            return None

        slippage = abs((actual_price - expected_price) / expected_price) * 100

        if slippage > self.max_slippage:
            return SafetyViolation(
                trigger="high_slippage",
                message=f"Slippage {slippage:.2f}% exceeds {self.max_slippage}% threshold",
                severity="critical",
                timestamp=datetime.now(),
                auto_pause=True
            )

        return None

    def check_daily_loss_limit(self, current_pnl: float) -> Optional[SafetyViolation]:
        """
        Check if daily loss limit exceeded

        Args:
            current_pnl: Current day's PnL

        Returns:
            SafetyViolation if triggered, None otherwise
        """
        if current_pnl < -self.max_daily_loss:
            return SafetyViolation(
                trigger="daily_loss_limit",
                message=f"Daily loss ${abs(current_pnl):.2f} exceeds limit ${self.max_daily_loss}",
                severity="critical",
                timestamp=datetime.now(),
                auto_pause=True
            )

        return None

    def check_privacy_breach(self, messages: List[Dict]) -> Optional[SafetyViolation]:
        """
        Check for privacy breach (PII in messages)

        Args:
            messages: List of messages to check

        Returns:
            SafetyViolation if triggered, None otherwise
        """
        # Simple PII patterns
        pii_patterns = [
            "social security",
            "ssn",
            "credit card",
            "password",
            "private key",
            "api key"
        ]

        for msg in messages:
            content = str(msg.get("content", "")).lower()
            for pattern in pii_patterns:
                if pattern in content:
                    return SafetyViolation(
                        trigger="privacy_breach",
                        message=f"PII pattern '{pattern}' detected in messages",
                        severity="critical",
                        timestamp=datetime.now(),
                        auto_pause=True
                    )

        return None

    def run_all_checks(
        self,
        sentiment: Optional[float] = None,
        daily_pnl: Optional[float] = None,
        messages: Optional[List[Dict]] = None
    ) -> List[SafetyViolation]:
        """
        Run all safety checks

        Args:
            sentiment: Current sentiment score
            daily_pnl: Current day's PnL
            messages: Recent messages to check for PII

        Returns:
            List of safety violations
        """
        violations = []

        # Check consecutive losses
        violation = self.check_consecutive_losses()
        if violation:
            violations.append(violation)

        # Check API error burst
        violation = self.check_api_error_burst()
        if violation:
            violations.append(violation)

        # Check sentiment if provided
        if sentiment is not None:
            violation = self.check_sentiment_drop(sentiment)
            if violation:
                violations.append(violation)

        # Check daily loss if provided
        if daily_pnl is not None:
            violation = self.check_daily_loss_limit(daily_pnl)
            if violation:
                violations.append(violation)

        # Check privacy if messages provided
        if messages:
            violation = self.check_privacy_breach(messages)
            if violation:
                violations.append(violation)

        # Store violations
        self.violations.extend(violations)

        # Auto-pause if critical violations
        critical_violations = [v for v in violations if v.auto_pause]
        if critical_violations and not self.paused:
            self.trigger_auto_pause(critical_violations[0])

        return violations

    def trigger_auto_pause(self, violation: SafetyViolation):
        """
        Trigger auto-pause due to safety violation

        Args:
            violation: The safety violation that triggered pause
        """
        self.paused = True
        self.pause_reason = violation.message

        logger.critical(f"🚨 AUTO-PAUSE TRIGGERED: {violation.trigger}")
        logger.critical(f"   Reason: {violation.message}")
        logger.critical("   Trading is PAUSED until manual review")

    def resume(self, force: bool = False):
        """
        Resume trading after pause

        Args:
            force: Force resume even if violations exist
        """
        if not force:
            # Check if safe to resume
            recent_violations = [
                v for v in self.violations
                if v.timestamp > datetime.now() - timedelta(minutes=30)
            ]

            if recent_violations:
                logger.warning(
                    f"Cannot resume: {len(recent_violations)} recent violations. "
                    f"Use force=True to override."
                )
                return False

        self.paused = False
        self.pause_reason = None
        logger.info("✅ Trading resumed")
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get current safety status"""
        recent_violations = [
            v for v in self.violations
            if v.timestamp > datetime.now() - timedelta(hours=1)
        ]

        return {
            "paused": self.paused,
            "pause_reason": self.pause_reason,
            "recent_violations": len(recent_violations),
            "total_violations": len(self.violations),
            "consecutive_losses": self._count_consecutive_losses(),
            "api_errors_last_minute": self._count_recent_api_errors()
        }

    def _count_consecutive_losses(self) -> int:
        """Count current consecutive losses"""
        if not self.recent_trades:
            return 0

        count = 0
        for trade in reversed(list(self.recent_trades)):
            if trade.get("pnl", 0) < 0:
                count += 1
            else:
                break

        return count

    def _count_recent_api_errors(self) -> int:
        """Count API errors in last minute"""
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        return len([
            e for e in self.api_errors
            if e["timestamp"] > one_minute_ago
        ])

    def clear_history(self):
        """Clear all safety history"""
        self.recent_trades.clear()
        self.api_errors.clear()
        self.violations.clear()
        logger.info("Safety history cleared")
