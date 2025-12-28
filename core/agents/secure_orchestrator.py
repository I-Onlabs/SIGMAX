"""
Secure Orchestrator - Security-Enhanced Trading Pipeline
Integrates TradeTrap-inspired security defenses into SIGMAX orchestrator

Features:
- Prompt injection detection on all inputs
- Tool response validation (MCP hijacking defense)
- State integrity verification
- News source authenticity validation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

# Import base orchestrator
from .orchestrator import SIGMAXOrchestrator, AgentState

# Import security modules
from ..security import (
    PromptGuard,
    SecurePromptWrapper,
    ThreatLevel,
    ToolResponseValidator,
    SecureToolWrapper,
    ValidationStatus,
    StateIntegrityVerifier,
    NewsValidator,
    CredibilityLevel
)


class SecureOrchestrator:
    """
    Security-enhanced wrapper around SIGMAXOrchestrator.

    Applies defense layers:
    1. Input sanitization (prompt injection defense)
    2. Tool response validation (MCP hijacking defense)
    3. State integrity checks (tampering defense)
    4. News validation (fake news defense)

    Usage:
        secure_orch = SecureOrchestrator(base_orchestrator)
        await secure_orch.initialize()
        result = await secure_orch.analyze_symbol_secure("BTC/USDT")
    """

    def __init__(
        self,
        orchestrator: SIGMAXOrchestrator,
        security_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize secure orchestrator.

        Args:
            orchestrator: Base SIGMAX orchestrator
            security_config: Optional security configuration
        """
        self.orchestrator = orchestrator
        self.config = security_config or {}

        # Initialize security components
        self.prompt_guard = PromptGuard(
            sensitivity=self.config.get("prompt_sensitivity", "medium"),
            block_on_threat=self.config.get("block_on_threat", True)
        )

        self.tool_validator = ToolResponseValidator(
            enable_anomaly_detection=self.config.get("anomaly_detection", True),
            max_price_change_pct=self.config.get("max_price_change", 50.0),
            stale_data_threshold_sec=self.config.get("stale_threshold", 300)
        )

        self.state_verifier = StateIntegrityVerifier(
            max_snapshots=self.config.get("max_snapshots", 100),
            alert_on_tamper=self.config.get("alert_on_tamper", True)
        )

        self.news_validator = NewsValidator(
            require_source=self.config.get("require_news_source", False),
            min_credibility=CredibilityLevel(
                self.config.get("min_credibility", "medium")
            )
        )

        # Security metrics
        self._security_metrics = {
            "prompts_scanned": 0,
            "threats_blocked": 0,
            "tools_validated": 0,
            "anomalies_detected": 0,
            "state_checks": 0,
            "tampering_detected": 0,
            "news_validated": 0,
            "fake_news_blocked": 0
        }

        # Security event log
        self._security_events: List[Dict[str, Any]] = []

        logger.info("🛡️ Secure orchestrator initialized")

    async def initialize(self):
        """Initialize underlying orchestrator."""
        await self.orchestrator.initialize()
        logger.info("🛡️ Secure orchestrator ready")

    async def analyze_symbol_secure(
        self,
        symbol: str,
        market_data: Optional[Dict[str, Any]] = None,
        user_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze symbol with full security pipeline.

        Args:
            symbol: Trading symbol
            market_data: Optional market data
            user_prompt: Optional user input to sanitize

        Returns:
            Analysis result with security metadata
        """
        security_report = {
            "checks_passed": True,
            "threats_detected": [],
            "anomalies": [],
            "warnings": []
        }

        # 1. Sanitize user input if provided
        if user_prompt:
            sanitized, threat = await self._check_prompt(user_prompt)
            if threat:
                security_report["threats_detected"].append(threat)
                if threat.get("level") == "critical":
                    security_report["checks_passed"] = False
                    return {
                        "action": "blocked",
                        "reason": "Security threat detected in input",
                        "security": security_report
                    }

        # 2. Validate market data if provided
        if market_data:
            validated_data, validation = await self._validate_market_data(
                symbol, market_data
            )
            if validation.get("anomalies"):
                security_report["anomalies"].extend(validation["anomalies"])
                security_report["warnings"].append("Market data anomalies detected")
            market_data = validated_data

        # 3. Record pre-analysis state
        await self._record_state("pre_analysis", symbol)

        # 4. Run analysis
        try:
            result = await self.orchestrator.analyze_symbol(symbol, market_data)
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {
                "action": "error",
                "error": str(e),
                "security": security_report
            }

        # 5. Verify state integrity after analysis
        integrity = await self._verify_state("post_analysis", symbol)
        if not integrity.get("valid", True):
            security_report["warnings"].append("State integrity warning")
            security_report["tampering"] = integrity.get("issues", [])

        # 6. Validate any news in the result
        if result.get("reasoning", {}).get("research"):
            news_check = await self._validate_news(
                result["reasoning"]["research"]
            )
            if news_check.get("suspicious"):
                security_report["warnings"].append("Suspicious news detected")
                security_report["news_issues"] = news_check.get("issues", [])

        # Add security metadata
        result["security"] = security_report
        result["security_score"] = self._calculate_security_score(security_report)

        return result

    async def _check_prompt(
        self,
        prompt: str
    ) -> tuple[str, Optional[Dict[str, Any]]]:
        """Check prompt for injection attacks."""
        self._security_metrics["prompts_scanned"] += 1

        threat = self.prompt_guard.analyze(prompt)

        if threat.level != ThreatLevel.NONE:
            self._security_metrics["threats_blocked"] += 1
            self._log_security_event("prompt_threat", {
                "level": threat.level.value,
                "attack_types": [a.value for a in threat.attack_types],
                "confidence": threat.confidence
            })

            # Sanitize if not blocking
            sanitized = self.prompt_guard.sanitize(prompt)

            return sanitized, {
                "level": threat.level.value,
                "types": [a.value for a in threat.attack_types],
                "confidence": threat.confidence
            }

        return prompt, None

    async def _validate_market_data(
        self,
        symbol: str,
        data: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Validate market data for anomalies."""
        self._security_metrics["tools_validated"] += 1

        result = self.tool_validator.validate("get_price", data)

        validation_info = {
            "status": result.status.value,
            "anomalies": [a.value for a in result.anomalies],
            "confidence": result.confidence
        }

        if result.anomalies:
            self._security_metrics["anomalies_detected"] += len(result.anomalies)
            self._log_security_event("data_anomaly", {
                "symbol": symbol,
                "anomalies": validation_info["anomalies"]
            })

        # Return sanitized data if needed
        if result.sanitized_response:
            return result.sanitized_response, validation_info

        return data, validation_info

    async def _record_state(self, checkpoint: str, symbol: str):
        """Record state for integrity verification."""
        try:
            # Get current portfolio state from execution module
            portfolio = await self.orchestrator.execution_module.get_portfolio()
            positions = portfolio.get("positions", {})
            balance = portfolio.get("balance", 0.0)

            self.state_verifier.record_state(
                agent_id=f"orchestrator_{symbol}",
                positions=positions,
                cash_balance=balance,
                metadata={"checkpoint": checkpoint}
            )

            self._security_metrics["state_checks"] += 1

        except Exception as e:
            logger.warning(f"State recording failed: {e}")

    async def _verify_state(
        self,
        checkpoint: str,
        symbol: str
    ) -> Dict[str, Any]:
        """Verify state integrity."""
        try:
            portfolio = await self.orchestrator.execution_module.get_portfolio()
            positions = portfolio.get("positions", {})
            balance = portfolio.get("balance", 0.0)

            check = self.state_verifier.verify_state(
                agent_id=f"orchestrator_{symbol}",
                current_positions=positions,
                current_balance=balance
            )

            if check.status.value != "valid":
                self._security_metrics["tampering_detected"] += 1
                self._log_security_event("state_integrity", {
                    "checkpoint": checkpoint,
                    "status": check.status.value,
                    "issues": [t.value for t in check.tamper_types]
                })

                return {
                    "valid": False,
                    "issues": [t.value for t in check.tamper_types],
                    "details": check.details
                }

            return {"valid": True}

        except Exception as e:
            logger.warning(f"State verification failed: {e}")
            return {"valid": True, "error": str(e)}

    async def _validate_news(
        self,
        research_content: str
    ) -> Dict[str, Any]:
        """Validate news content for manipulation."""
        self._security_metrics["news_validated"] += 1

        # Extract headlines/claims from research
        validation = self.news_validator.validate(
            headline=research_content[:500],  # First 500 chars as headline
            content=research_content
        )

        if validation.credibility.value in ["low", "very_low"]:
            self._security_metrics["fake_news_blocked"] += 1
            self._log_security_event("suspicious_news", {
                "credibility": validation.credibility.value,
                "indicators": [i.value for i in validation.manipulation_indicators]
            })

            return {
                "suspicious": True,
                "credibility": validation.credibility.value,
                "issues": [i.value for i in validation.manipulation_indicators]
            }

        return {"suspicious": False}

    def _calculate_security_score(
        self,
        report: Dict[str, Any]
    ) -> float:
        """Calculate overall security score (0-1)."""
        score = 1.0

        # Deduct for threats
        score -= len(report.get("threats_detected", [])) * 0.3

        # Deduct for anomalies
        score -= len(report.get("anomalies", [])) * 0.1

        # Deduct for warnings
        score -= len(report.get("warnings", [])) * 0.05

        return max(0.0, min(1.0, score))

    def _log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any]
    ):
        """Log security event."""
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        }
        self._security_events.append(event)

        # Keep only last 1000 events
        if len(self._security_events) > 1000:
            self._security_events = self._security_events[-1000:]

        logger.warning(f"🛡️ Security event: {event_type} - {details}")

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics summary."""
        return {
            **self._security_metrics,
            "recent_events": self._security_events[-10:],
            "prompt_guard_stats": self.prompt_guard.get_statistics(),
            "tool_validator_stats": self.tool_validator.get_statistics(),
            "state_verifier_stats": self.state_verifier.get_statistics()
        }

    def get_recent_threats(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent security threats."""
        threat_events = [
            e for e in self._security_events
            if e["type"] in ["prompt_threat", "data_anomaly", "state_integrity", "suspicious_news"]
        ]
        return threat_events[-limit:]

    # Delegate other methods to base orchestrator
    async def start(self):
        await self.orchestrator.start()

    async def stop(self):
        await self.orchestrator.stop()

    async def pause(self):
        await self.orchestrator.pause()

    async def resume(self):
        await self.orchestrator.resume()

    async def get_status(self) -> Dict[str, Any]:
        base_status = await self.orchestrator.get_status()
        base_status["security"] = {
            "enabled": True,
            "metrics": self._security_metrics,
            "recent_threats": len([
                e for e in self._security_events[-100:]
                if e["type"] == "prompt_threat"
            ])
        }
        return base_status
