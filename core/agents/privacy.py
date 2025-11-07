"""
Privacy Agent - PII Detection & Anti-Collusion
"""

from typing import Dict, Any, List
from loguru import logger
import re


class PrivacyAgent:
    """
    Privacy Agent - Ensures no PII leakage and detects collusion patterns
    """

    def __init__(self, llm):
        self.llm = llm

        # PII patterns
        self.pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "api_key": r'\b[A-Za-z0-9]{32,}\b',
            "private_key": r'\b0x[a-fA-F0-9]{64}\b'
        }

        logger.info("✓ Privacy agent initialized")

    async def check(
        self,
        messages: List[Dict[str, Any]],
        symbol: str
    ) -> Dict[str, Any]:
        """
        Check for privacy violations

        Args:
            messages: Agent messages to check
            symbol: Trading symbol

        Returns:
            Privacy check result with approval status
        """
        logger.info(f"🔒 Privacy check for {symbol}...")

        try:
            # Check for PII
            pii_found = await self._detect_pii(messages)

            # Check for collusion patterns
            collusion = await self._detect_collusion(messages)

            # Check for insider trading signals
            insider = await self._detect_insider_signals(messages)

            approved = not (pii_found or collusion or insider)

            issues = []
            if pii_found:
                issues.append("PII detected")
            if collusion:
                issues.append("Collusion pattern detected")
            if insider:
                issues.append("Insider trading signals")

            reason = "Privacy check passed" if approved else f"Issues: {', '.join(issues)}"

            return {
                "approved": approved,
                "reason": reason,
                "pii_found": pii_found,
                "collusion": collusion,
                "insider": insider,
                "summary": self._generate_summary(approved, issues)
            }

        except Exception as e:
            logger.error(f"Privacy check error: {e}")
            return {
                "approved": False,
                "reason": f"Privacy check failed: {e}",
                "error": str(e)
            }

    async def _detect_pii(self, messages: List[Dict[str, Any]]) -> bool:
        """Detect personally identifiable information"""

        for message in messages:
            content = message.get("content", "")

            for pii_type, pattern in self.pii_patterns.items():
                if re.search(pattern, content):
                    logger.warning(f"PII detected: {pii_type}")
                    return True

        return False

    async def _detect_collusion(self, messages: List[Dict[str, Any]]) -> bool:
        """Detect collusion patterns"""

        # Check for coordination keywords
        collusion_keywords = [
            "coordinate", "pump together", "dump together",
            "insider", "confidential", "secret signal"
        ]

        for message in messages:
            content = message.get("content", "").lower()
            if any(keyword in content for keyword in collusion_keywords):
                logger.warning("Collusion pattern detected")
                return True

        return False

    async def _detect_insider_signals(
        self,
        messages: List[Dict[str, Any]]
    ) -> bool:
        """Detect potential insider trading signals"""

        insider_keywords = [
            "insider information", "confidential news", "unreleased",
            "before announcement", "early access"
        ]

        for message in messages:
            content = message.get("content", "").lower()
            if any(keyword in content for keyword in insider_keywords):
                logger.warning("Insider trading signal detected")
                return True

        return False

    def _generate_summary(self, approved: bool, issues: List[str]) -> str:
        """Generate privacy check summary"""

        status = "APPROVED ✓" if approved else "REJECTED ✗"

        summary = f"Privacy & Compliance Check: {status}\n\n"

        if issues:
            summary += "Issues Found:\n"
            for issue in issues:
                summary += f"- {issue}\n"
        else:
            summary += "No privacy or compliance issues detected.\n"

        return summary
