"""
Compliance Module - Regulatory Compliance & Policy Enforcement
"""

from typing import Dict, Any, Optional
from loguru import logger
import aiohttp
import json
import os


class ComplianceModule:
    """
    Compliance Module - Ensures regulatory compliance

    Standards:
    - EU AI Act
    - SEC regulations
    - KYC/AML
    - Anti-market manipulation

    OPA Integration:
    - HTTP API communication with OPA server
    - Policy-as-Code using Rego
    - Fallback to embedded policies when OPA unavailable
    """

    def __init__(self, opa_url: Optional[str] = None):
        self.opa_url = opa_url or os.getenv("OPA_URL", "http://localhost:8181")
        self.opa_available = False
        self.policies = {}
        self.embedded_policies = self._get_embedded_policies()
        logger.info("✓ Compliance module created")

    def _get_embedded_policies(self) -> Dict[str, Any]:
        """Get embedded policies (fallback when OPA unavailable)"""
        return {
            "max_position_size": float(os.getenv("MAX_POSITION_SIZE", "15")),
            "max_leverage": float(os.getenv("MAX_LEVERAGE", "1")),
            "max_daily_loss": float(os.getenv("MAX_DAILY_LOSS", "10")),
            "allowed_assets": [
                "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT",
                "AVAX/USDT", "MATIC/USDT", "DOT/USDT", "LINK/USDT"
            ],
            "blacklisted_assets": [],
            "risk_limits": {
                "conservative": {
                    "max_position_pct": 10,
                    "max_correlation": 0.7,
                    "min_liquidity_score": 60
                },
                "balanced": {
                    "max_position_pct": 15,
                    "max_correlation": 0.8,
                    "min_liquidity_score": 50
                },
                "aggressive": {
                    "max_position_pct": 25,
                    "max_correlation": 0.9,
                    "min_liquidity_score": 40
                }
            },
            "trading_hours": {
                "enabled": False,  # 24/7 crypto trading by default
                "start_hour": 0,
                "end_hour": 24
            }
        }

    async def initialize(self):
        """Load compliance policies from OPA or embedded"""
        # Try to connect to OPA server
        try:
            await self._check_opa_health()
            self.policies = await self._load_policies()
            logger.info(f"✓ Compliance module initialized with OPA at {self.opa_url}")
        except Exception as e:
            logger.warning(f"OPA unavailable: {e}. Using embedded policies.")
            self.policies = self.embedded_policies.copy()
            logger.info("✓ Compliance module initialized with embedded policies")

    async def _check_opa_health(self):
        """Check if OPA server is available"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.opa_url}/health",
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as response:
                    if response.status == 200:
                        self.opa_available = True
                        logger.info(f"✓ OPA server available at {self.opa_url}")
                    else:
                        raise Exception(f"OPA health check failed with status {response.status}")
        except Exception as e:
            self.opa_available = False
            raise Exception(f"Cannot connect to OPA: {e}")

    async def _load_policies(self) -> Dict[str, Any]:
        """
        Load policy rules from OPA server

        Queries OPA for policy data and parses the response
        """
        if not self.opa_available:
            return self.embedded_policies.copy()

        try:
            async with aiohttp.ClientSession() as session:
                # Query OPA for trading policies
                async with session.post(
                    f"{self.opa_url}/v1/data/trading/policies",
                    json={"input": {}},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get("result", {})

                        if result:
                            logger.info("✓ Loaded policies from OPA")
                            return result
                        else:
                            logger.warning("Empty result from OPA, using embedded policies")
                            return self.embedded_policies.copy()
                    else:
                        logger.warning(f"OPA query failed: {response.status}")
                        return self.embedded_policies.copy()

        except Exception as e:
            logger.error(f"Failed to load policies from OPA: {e}")
            return self.embedded_policies.copy()

    async def check_compliance(
        self,
        trade: Dict[str, Any],
        risk_profile: str = "conservative"
    ) -> Dict[str, Any]:
        """
        Check trade against compliance policies

        Can use either OPA server or embedded policies
        """
        # If OPA is available, query it for decision
        if self.opa_available:
            return await self._check_with_opa(trade, risk_profile)
        else:
            return await self._check_with_embedded_policies(trade, risk_profile)

    async def _check_with_opa(
        self,
        trade: Dict[str, Any],
        risk_profile: str
    ) -> Dict[str, Any]:
        """Check compliance using OPA server"""
        try:
            async with aiohttp.ClientSession() as session:
                # Send trade data to OPA for policy evaluation
                input_data = {
                    "input": {
                        "trade": trade,
                        "risk_profile": risk_profile
                    }
                }

                async with session.post(
                    f"{self.opa_url}/v1/data/trading/allow",
                    json=input_data,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get("result", {})

                        # OPA returns {allow: true/false, reason: "..."}
                        return {
                            "compliant": result.get("allow", False),
                            "reason": result.get("reason", "Policy decision from OPA"),
                            "violations": result.get("violations", [])
                        }
                    else:
                        logger.error(f"OPA query failed: {response.status}")
                        # Fallback to embedded policies
                        return await self._check_with_embedded_policies(trade, risk_profile)

        except Exception as e:
            logger.error(f"OPA check failed: {e}, falling back to embedded policies")
            return await self._check_with_embedded_policies(trade, risk_profile)

    async def _check_with_embedded_policies(
        self,
        trade: Dict[str, Any],
        risk_profile: str
    ) -> Dict[str, Any]:
        """Check compliance using embedded policies"""
        violations = []

        # Check position size
        max_size = self.policies.get("max_position_size", 15)
        if trade.get("size", 0) > max_size:
            violations.append(f"Position size {trade.get('size')} exceeds limit {max_size}")

        # Check leverage
        max_leverage = self.policies.get("max_leverage", 1)
        if trade.get("leverage", 1) > max_leverage:
            violations.append(f"Leverage {trade.get('leverage')} exceeds limit {max_leverage}")

        # Check blacklist
        blacklisted = self.policies.get("blacklisted_assets", [])
        if trade.get("symbol") in blacklisted:
            violations.append(f"Asset {trade.get('symbol')} is blacklisted")

        # Check allowed assets (if whitelist exists)
        allowed = self.policies.get("allowed_assets", [])
        if allowed and trade.get("symbol") not in allowed:
            violations.append(f"Asset {trade.get('symbol')} not in whitelist")

        # Check risk limits for profile
        risk_limits = self.policies.get("risk_limits", {}).get(risk_profile, {})
        if risk_limits:
            # Check position percentage
            max_position_pct = risk_limits.get("max_position_pct", 100)
            if trade.get("position_pct", 0) > max_position_pct:
                violations.append(f"Position {trade.get('position_pct'):.1f}% exceeds {risk_profile} limit {max_position_pct}%")

        compliant = len(violations) == 0

        return {
            "compliant": compliant,
            "reason": "All compliance checks passed" if compliant else f"{len(violations)} violation(s) found",
            "violations": violations
        }

    async def evaluate_policy(
        self,
        policy_path: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a specific OPA policy path

        Args:
            policy_path: OPA policy path (e.g., "trading/allow")
            input_data: Input data for policy evaluation

        Returns:
            Policy evaluation result
        """
        if not self.opa_available:
            logger.warning("OPA not available, cannot evaluate policy")
            return {"error": "OPA not available"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.opa_url}/v1/data/{policy_path}",
                    json={"input": input_data},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("result", {})
                    else:
                        logger.error(f"Policy evaluation failed: {response.status}")
                        return {"error": f"HTTP {response.status}"}

        except Exception as e:
            logger.error(f"Policy evaluation error: {e}")
            return {"error": str(e)}

    def get_policies(self) -> Dict[str, Any]:
        """Get current policies"""
        return self.policies.copy()
