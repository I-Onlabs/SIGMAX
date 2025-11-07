"""
Risk Agent - Policy Validation & Risk Management
"""

from typing import Dict, Any, Optional
from loguru import logger
import os
import numpy as np


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
        risk_profile: str,
        trade_size: float = 0.0
    ) -> Dict[str, Any]:
        """
        Check policies using compliance module (OPA integration)

        The compliance module handles OPA communication and falls back
        to embedded policies when OPA is unavailable
        """
        # Build trade data for compliance check
        trade_data = {
            "symbol": symbol,
            "size": trade_size,
            "leverage": self.max_leverage,
            "action": "analyze",  # Pre-trade analysis
            "risk_profile": risk_profile
        }

        # Check with compliance module (uses OPA if available)
        compliance_result = await self.compliance_module.check_compliance(
            trade=trade_data,
            risk_profile=risk_profile
        )

        # Convert compliance result to policy check format
        checks = {
            "compliant": compliance_result.get("compliant", False),
            "position_size_ok": trade_size <= self.max_position_size,
            "leverage_ok": self.max_leverage <= float(os.getenv("MAX_LEVERAGE", "1")),
            "blacklist_ok": symbol not in compliance_result.get("violations", []),
            "policy_approved": compliance_result.get("compliant", False)
        }

        approved = all(checks.values())

        return {
            "approved": approved,
            "checks": checks,
            "compliance_reason": compliance_result.get("reason", ""),
            "violations": compliance_result.get("violations", [])
        }

    async def _assess_market_risk(self, symbol: str, market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Assess market-specific risks with actual calculations

        Args:
            symbol: Trading pair (e.g., BTC/USDT)
            market_data: Optional dictionary containing:
                - prices: List of historical prices for volatility calculation
                - volumes: List of trading volumes for liquidity assessment
                - market_cap: Market capitalization (if available)

        Returns:
            Risk assessment with volatility, liquidity, and correlation metrics
        """
        volatility_value = 0.0
        volatility_level = "unknown"
        liquidity_value = 0.0
        liquidity_level = "unknown"
        risk_level = "medium"

        # Extract base asset from symbol (e.g., BTC from BTC/USDT)
        base_asset = symbol.split('/')[0] if '/' in symbol else symbol

        # Calculate volatility if historical prices are provided
        if market_data and 'prices' in market_data and len(market_data['prices']) > 1:
            prices = np.array(market_data['prices'])

            # Calculate returns
            returns = np.diff(prices) / prices[:-1]

            # Annualized volatility (assuming daily prices)
            volatility_value = float(np.std(returns) * np.sqrt(365) * 100)

            # Classify volatility
            if volatility_value < 30:
                volatility_level = "low"
            elif volatility_value < 60:
                volatility_level = "medium"
            elif volatility_value < 100:
                volatility_level = "high"
            else:
                volatility_level = "extreme"

        else:
            # Use heuristics based on asset type
            major_assets = ['BTC', 'ETH', 'BNB', 'SOL', 'USDT', 'USDC']
            mid_cap_assets = ['AVAX', 'MATIC', 'DOT', 'LINK', 'UNI', 'ATOM']

            if base_asset in major_assets:
                volatility_value = 45.0  # Typical for major crypto
                volatility_level = "medium"
            elif base_asset in mid_cap_assets:
                volatility_value = 70.0  # Higher for mid-cap
                volatility_level = "high"
            else:
                volatility_value = 120.0  # Very high for small-cap/unknown
                volatility_level = "extreme"

        # Calculate liquidity if volume data is provided
        if market_data and 'volumes' in market_data and len(market_data['volumes']) > 0:
            volumes = np.array(market_data['volumes'])

            # Average daily volume
            avg_volume = float(np.mean(volumes))

            # Liquidity score based on average volume
            if avg_volume > 1_000_000_000:  # $1B+
                liquidity_level = "very_high"
                liquidity_value = 95.0
            elif avg_volume > 100_000_000:  # $100M+
                liquidity_level = "high"
                liquidity_value = 80.0
            elif avg_volume > 10_000_000:  # $10M+
                liquidity_level = "medium"
                liquidity_value = 60.0
            elif avg_volume > 1_000_000:  # $1M+
                liquidity_level = "low"
                liquidity_value = 35.0
            else:
                liquidity_level = "very_low"
                liquidity_value = 15.0

        else:
            # Use heuristics based on asset type
            major_assets = ['BTC', 'ETH', 'BNB', 'SOL']
            mid_cap_assets = ['AVAX', 'MATIC', 'DOT', 'LINK']

            if base_asset in major_assets:
                liquidity_level = "very_high"
                liquidity_value = 90.0
            elif base_asset in mid_cap_assets:
                liquidity_level = "high"
                liquidity_value = 75.0
            else:
                liquidity_level = "medium"
                liquidity_value = 50.0

        # Determine overall risk level
        if volatility_level == "extreme" or liquidity_level == "very_low":
            risk_level = "high"
        elif volatility_level in ["high", "medium"] and liquidity_level in ["high", "very_high"]:
            risk_level = "medium"
        elif volatility_level == "low" and liquidity_level in ["high", "very_high"]:
            risk_level = "low"
        else:
            risk_level = "medium"

        # Calculate correlation (placeholder - would need market-wide data)
        correlation = 0.5  # Default moderate correlation with market

        return {
            "level": risk_level,
            "volatility": volatility_level,
            "volatility_value": volatility_value,
            "liquidity": liquidity_level,
            "liquidity_value": liquidity_value,
            "correlation": correlation,
            "details": {
                "asset": base_asset,
                "data_source": "historical" if market_data else "heuristic"
            }
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
