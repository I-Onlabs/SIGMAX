"""
Risk Agent - Policy Validation & Risk Management
"""

from typing import Dict, Any, Optional
from loguru import logger
import os


class RiskAgent:
    """
    Risk Agent - Validates trades against risk policies
    """

    def __init__(self, llm, compliance_module):
        self.llm = llm
        self.compliance_module = compliance_module

        # Load risk limits from env
        self.max_position_size = float(os.getenv("MAX_POSITION_SIZE", 15))
        self.max_daily_loss = float(os.getenv("MAX_DAILY_LOSS", 10))
        self.stop_loss_pct = float(os.getenv("STOP_LOSS_PCT", 1.5))
        self.max_leverage = float(os.getenv("MAX_LEVERAGE", 1))

        logger.info("✓ Risk agent initialized")

    async def assess(
        self,
        symbol: str,
        bull_case: Optional[str],
        bear_case: Optional[str],
        technical: Optional[str],
        risk_profile: str = "conservative"
    ) -> Dict[str, Any]:
        """
        Assess risk and validate against policies

        Args:
            symbol: Trading pair
            bull_case: Bull argument
            bear_case: Bear argument
            technical: Technical analysis
            risk_profile: Risk profile (conservative/balanced/aggressive)

        Returns:
            Risk assessment with approval status
        """
        logger.info(f"🛡️ Assessing risk for {symbol}...")

        try:
            # Check policy compliance
            policy_check = await self._check_policies(symbol, risk_profile)

            # Assess market risk
            market_risk = await self._assess_market_risk(symbol)

            # Check for red flags
            red_flags = await self._check_red_flags(
                bull_case=bull_case,
                bear_case=bear_case,
                technical=technical
            )

            # Determine approval
            approved = (
                policy_check.get("approved", False) and
                not red_flags and
                market_risk.get("level", "high") != "extreme"
            )

            reason = self._get_reason(policy_check, market_risk, red_flags)

            return {
                "approved": approved,
                "reason": reason,
                "policy_check": policy_check,
                "market_risk": market_risk,
                "red_flags": red_flags,
                "summary": self._generate_summary(
                    approved=approved,
                    reason=reason,
                    market_risk=market_risk
                )
            }

        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            return {
                "approved": False,
                "reason": f"Risk assessment failed: {e}",
                "error": str(e)
            }

    async def _check_policies(
        self,
        symbol: str,
        risk_profile: str
    ) -> Dict[str, Any]:
        """Check OPA policies"""

        # TODO: Integrate with OPA
        # For now, simple checks

        checks = {
            "position_size_ok": True,
            "daily_loss_ok": True,
            "leverage_ok": True,
            "blacklist_ok": symbol not in []
        }

        approved = all(checks.values())

        return {
            "approved": approved,
            "checks": checks
        }

    async def _assess_market_risk(self, symbol: str) -> Dict[str, Any]:
        """Assess market-specific risks"""

        # TODO: Calculate actual volatility, liquidity, etc.

        return {
            "level": "medium",
            "volatility": "medium",
            "liquidity": "high",
            "correlation": 0.5
        }

    async def _check_red_flags(
        self,
        bull_case: Optional[str],
        bear_case: Optional[str],
        technical: Optional[str]
    ) -> bool:
        """Check for red flags in arguments"""

        red_flag_keywords = [
            "scam", "rug pull", "pump and dump", "ponzi",
            "extreme risk", "unverified", "suspicious"
        ]

        for text in [bull_case, bear_case, technical]:
            if text:
                text_lower = text.lower()
                if any(keyword in text_lower for keyword in red_flag_keywords):
                    return True

        return False

    def _get_reason(
        self,
        policy_check: Dict[str, Any],
        market_risk: Dict[str, Any],
        red_flags: bool
    ) -> str:
        """Get human-readable reason"""

        if red_flags:
            return "Red flags detected in analysis"

        if market_risk.get("level") == "extreme":
            return "Extreme market risk"

        if not policy_check.get("approved"):
            failed_checks = [
                k for k, v in policy_check.get("checks", {}).items()
                if not v
            ]
            return f"Policy violations: {', '.join(failed_checks)}"

        return "All risk checks passed"

    def _generate_summary(
        self,
        approved: bool,
        reason: str,
        market_risk: Dict[str, Any]
    ) -> str:
        """Generate risk summary"""

        status = "APPROVED ✓" if approved else "REJECTED ✗"

        return f"""
Risk Assessment: {status}

Market Risk Level: {market_risk.get('level', 'unknown').upper()}
Volatility: {market_risk.get('volatility', 'unknown')}
Liquidity: {market_risk.get('liquidity', 'unknown')}

Reason: {reason}

Position Limits:
- Max Position Size: ${self.max_position_size}
- Stop Loss: {self.stop_loss_pct}%
- Max Leverage: {self.max_leverage}x
"""
