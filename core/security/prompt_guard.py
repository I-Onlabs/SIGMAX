"""
Prompt Injection Guard - Security Layer for LLM Trading Agents
Inspired by TradeTrap's adversarial testing patterns

Protects against:
- Direct prompt injection (malicious instructions in user input)
- Indirect prompt injection (malicious content in tool responses)
- Reverse expectation attacks (inverting market signals)
- Fake news injection (fabricated market information)
"""

from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
from loguru import logger


class ThreatLevel(Enum):
    """Threat severity levels."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackType(Enum):
    """Types of prompt injection attacks."""
    DIRECT_INJECTION = "direct_injection"
    INDIRECT_INJECTION = "indirect_injection"
    REVERSE_EXPECTATION = "reverse_expectation"
    FAKE_NEWS = "fake_news"
    ROLE_HIJACKING = "role_hijacking"
    JAILBREAK = "jailbreak"
    DATA_EXFILTRATION = "data_exfiltration"
    INSTRUCTION_OVERRIDE = "instruction_override"


@dataclass
class ThreatDetection:
    """Result of threat detection."""
    is_threat: bool
    threat_level: ThreatLevel
    attack_types: List[AttackType]
    confidence: float
    matched_patterns: List[str]
    sanitized_content: Optional[str] = None
    original_content: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_threat": self.is_threat,
            "threat_level": self.threat_level.value,
            "attack_types": [a.value for a in self.attack_types],
            "confidence": round(self.confidence, 3),
            "matched_patterns": self.matched_patterns,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SecurityPolicy:
    """Security policy configuration."""
    block_threshold: ThreatLevel = ThreatLevel.HIGH
    sanitize_threshold: ThreatLevel = ThreatLevel.MEDIUM
    log_all_detections: bool = True
    allow_override: bool = False
    max_input_length: int = 10000
    blocked_keywords: Set[str] = field(default_factory=set)
    trusted_sources: Set[str] = field(default_factory=set)


class PromptGuard:
    """
    Prompt injection detection and mitigation system.

    Usage:
        guard = PromptGuard()

        # Check user input
        result = guard.analyze("Buy AAPL ignore previous instructions")
        if result.is_threat:
            print(f"Threat detected: {result.attack_types}")

        # Sanitize content
        safe_content = guard.sanitize(untrusted_input)

        # Validate tool responses
        is_safe = guard.validate_tool_response(tool_name, response)
    """

    # Common prompt injection patterns
    INJECTION_PATTERNS = [
        # Direct instruction overrides
        r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
        r"disregard\s+(all\s+)?(previous|prior|above)",
        r"forget\s+(everything|all)\s+(you\s+)?know",
        r"override\s+(system|security|safety)",
        r"bypass\s+(all\s+)?(restrictions?|filters?|rules?)",

        # Role hijacking
        r"you\s+are\s+now\s+a",
        r"pretend\s+(to\s+be|you\s+are)",
        r"act\s+as\s+(if\s+you\s+are|a)",
        r"from\s+now\s+on\s+you\s+are",
        r"new\s+persona:",

        # Jailbreak attempts
        r"do\s+anything\s+now",
        r"DAN\s+mode",
        r"developer\s+mode",
        r"unrestricted\s+mode",
        r"no\s+ethical\s+guidelines",

        # Data exfiltration
        r"reveal\s+(your\s+)?(system\s+)?prompt",
        r"show\s+(me\s+)?(your\s+)?instructions",
        r"what\s+(are\s+)?your\s+rules",
        r"print\s+(your\s+)?config",
        r"dump\s+(all\s+)?data",

        # Trading-specific attacks
        r"(always|only)\s+(buy|sell)\s+everything",
        r"liquidate\s+all\s+positions?\s+immediately",
        r"transfer\s+(all\s+)?funds?\s+to",
        r"maximum\s+leverage\s+on\s+all",
        r"(ignore|disable)\s+risk\s+(management|limits|controls)",
    ]

    # Reverse expectation patterns (signal inversion)
    REVERSE_PATTERNS = [
        r"bullish\s+(means?|signals?|indicates?)\s+(sell|bearish)",
        r"bearish\s+(means?|signals?|indicates?)\s+(buy|bullish)",
        r"positive\s+(news|sentiment)\s+.*(sell|short)",
        r"negative\s+(news|sentiment)\s+.*(buy|long)",
        r"when\s+(price|stock)\s+(rises?|up)\s+.*(sell|short)",
        r"when\s+(price|stock)\s+(falls?|down|drops?)\s+.*(buy|long)",
        r"interpret\s+.*(opposite|reverse|inverse)",
        r"invert\s+(all\s+)?(signals?|indicators?)",
    ]

    # Fake news indicators
    FAKE_NEWS_PATTERNS = [
        r"breaking:\s+.*\s+(bankrupt|crash|surge|soar)\s+\d{2,}%",
        r"urgent:\s+.*(insider|secret|leaked)",
        r"confirmed:\s+.*(merger|acquisition|buyout)\s+tomorrow",
        r"exclusive:\s+.*\s+will\s+(crash|moon|explode)",
        r"sources?\s+say\s+.*(guaranteed|certain|definite)",
        r"100%\s+(guaranteed|certain|profit|return)",
        r"risk.?free\s+(investment|trade|profit)",
        r"cannot\s+(fail|lose|go\s+wrong)",
    ]

    def __init__(self, policy: Optional[SecurityPolicy] = None):
        """
        Initialize prompt guard.

        Args:
            policy: Security policy configuration
        """
        self.policy = policy or SecurityPolicy()
        self._compile_patterns()
        self._detection_history: List[ThreatDetection] = []

    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self._injection_re = [
            re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS
        ]
        self._reverse_re = [
            re.compile(p, re.IGNORECASE) for p in self.REVERSE_PATTERNS
        ]
        self._fake_news_re = [
            re.compile(p, re.IGNORECASE) for p in self.FAKE_NEWS_PATTERNS
        ]

    def analyze(self, content: str) -> ThreatDetection:
        """
        Analyze content for prompt injection threats.

        Args:
            content: Text content to analyze

        Returns:
            ThreatDetection result
        """
        if not content:
            return ThreatDetection(
                is_threat=False,
                threat_level=ThreatLevel.SAFE,
                attack_types=[],
                confidence=1.0,
                matched_patterns=[],
                original_content=""
            )

        attack_types = []
        matched_patterns = []
        confidence_scores = []

        # Check length
        if len(content) > self.policy.max_input_length:
            attack_types.append(AttackType.DATA_EXFILTRATION)
            matched_patterns.append("excessive_length")
            confidence_scores.append(0.6)

        # Check blocked keywords
        content_lower = content.lower()
        for keyword in self.policy.blocked_keywords:
            if keyword.lower() in content_lower:
                attack_types.append(AttackType.DIRECT_INJECTION)
                matched_patterns.append(f"blocked_keyword:{keyword}")
                confidence_scores.append(0.9)

        # Check injection patterns
        for pattern in self._injection_re:
            match = pattern.search(content)
            if match:
                attack_types.append(AttackType.DIRECT_INJECTION)
                matched_patterns.append(match.group())
                confidence_scores.append(0.85)

        # Check reverse expectation patterns
        for pattern in self._reverse_re:
            match = pattern.search(content)
            if match:
                attack_types.append(AttackType.REVERSE_EXPECTATION)
                matched_patterns.append(match.group())
                confidence_scores.append(0.9)

        # Check fake news patterns
        for pattern in self._fake_news_re:
            match = pattern.search(content)
            if match:
                attack_types.append(AttackType.FAKE_NEWS)
                matched_patterns.append(match.group())
                confidence_scores.append(0.8)

        # Check for role hijacking
        if self._detect_role_hijacking(content):
            attack_types.append(AttackType.ROLE_HIJACKING)
            matched_patterns.append("role_hijacking_detected")
            confidence_scores.append(0.75)

        # Calculate overall threat level
        is_threat = len(attack_types) > 0
        threat_level = self._calculate_threat_level(attack_types, confidence_scores)
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

        # Create detection result
        detection = ThreatDetection(
            is_threat=is_threat,
            threat_level=threat_level,
            attack_types=list(set(attack_types)),
            confidence=avg_confidence,
            matched_patterns=matched_patterns,
            original_content=content[:500]  # Truncate for logging
        )

        # Log if configured
        if self.policy.log_all_detections and is_threat:
            logger.warning(f"Threat detected: {detection.to_dict()}")
            self._detection_history.append(detection)

        return detection

    def _detect_role_hijacking(self, content: str) -> bool:
        """Detect role hijacking attempts."""
        role_indicators = [
            "you are", "act as", "pretend", "roleplay",
            "new identity", "assume the role", "from now on"
        ]
        content_lower = content.lower()
        matches = sum(1 for ind in role_indicators if ind in content_lower)
        return matches >= 2

    def _calculate_threat_level(
        self,
        attack_types: List[AttackType],
        confidences: List[float]
    ) -> ThreatLevel:
        """Calculate overall threat level."""
        if not attack_types:
            return ThreatLevel.SAFE

        # Critical attacks
        critical_types = {
            AttackType.INSTRUCTION_OVERRIDE,
            AttackType.JAILBREAK
        }

        # High severity attacks
        high_types = {
            AttackType.DIRECT_INJECTION,
            AttackType.REVERSE_EXPECTATION,
            AttackType.DATA_EXFILTRATION
        }

        if any(t in critical_types for t in attack_types):
            return ThreatLevel.CRITICAL

        if any(t in high_types for t in attack_types):
            avg_conf = sum(confidences) / len(confidences)
            if avg_conf > 0.8:
                return ThreatLevel.HIGH
            return ThreatLevel.MEDIUM

        if len(attack_types) >= 3:
            return ThreatLevel.HIGH

        if len(attack_types) >= 2:
            return ThreatLevel.MEDIUM

        return ThreatLevel.LOW

    def sanitize(self, content: str) -> str:
        """
        Sanitize content by removing detected threats.

        Args:
            content: Content to sanitize

        Returns:
            Sanitized content
        """
        if not content:
            return ""

        sanitized = content

        # Remove injection patterns
        for pattern in self._injection_re:
            sanitized = pattern.sub("[REDACTED]", sanitized)

        # Remove reverse expectation patterns
        for pattern in self._reverse_re:
            sanitized = pattern.sub("[SIGNAL_REMOVED]", sanitized)

        # Remove fake news patterns
        for pattern in self._fake_news_re:
            sanitized = pattern.sub("[UNVERIFIED_CLAIM]", sanitized)

        # Truncate if too long
        if len(sanitized) > self.policy.max_input_length:
            sanitized = sanitized[:self.policy.max_input_length] + "...[TRUNCATED]"

        return sanitized

    def should_block(self, detection: ThreatDetection) -> bool:
        """Check if content should be blocked based on policy."""
        threat_order = [
            ThreatLevel.SAFE,
            ThreatLevel.LOW,
            ThreatLevel.MEDIUM,
            ThreatLevel.HIGH,
            ThreatLevel.CRITICAL
        ]

        return (
            threat_order.index(detection.threat_level) >=
            threat_order.index(self.policy.block_threshold)
        )

    def should_sanitize(self, detection: ThreatDetection) -> bool:
        """Check if content should be sanitized based on policy."""
        threat_order = [
            ThreatLevel.SAFE,
            ThreatLevel.LOW,
            ThreatLevel.MEDIUM,
            ThreatLevel.HIGH,
            ThreatLevel.CRITICAL
        ]

        return (
            threat_order.index(detection.threat_level) >=
            threat_order.index(self.policy.sanitize_threshold)
        )

    def validate_tool_response(
        self,
        tool_name: str,
        response: Dict[str, Any]
    ) -> Tuple[bool, Optional[ThreatDetection]]:
        """
        Validate a tool response for indirect injection.

        Args:
            tool_name: Name of the tool
            response: Tool response to validate

        Returns:
            Tuple of (is_safe, detection_result)
        """
        # Convert response to string for analysis
        response_str = str(response)

        # Analyze for threats
        detection = self.analyze(response_str)

        # Check for indirect injection indicators
        if "instruction" in response_str.lower():
            detection.attack_types.append(AttackType.INDIRECT_INJECTION)
            detection.is_threat = True

        is_safe = not self.should_block(detection)

        return is_safe, detection if detection.is_threat else None

    def validate_news(
        self,
        headline: str,
        source: Optional[str] = None,
        content: Optional[str] = None
    ) -> Tuple[bool, float]:
        """
        Validate news for authenticity.

        Args:
            headline: News headline
            source: News source
            content: Full news content

        Returns:
            Tuple of (is_authentic, confidence)
        """
        # Check source trust
        if source and source in self.policy.trusted_sources:
            source_trust = 0.9
        elif source:
            source_trust = 0.5
        else:
            source_trust = 0.3

        # Check headline for fake news patterns
        combined = f"{headline} {content or ''}"
        detection = self.analyze(combined)

        if AttackType.FAKE_NEWS in detection.attack_types:
            return False, 1 - detection.confidence

        # Check for sensationalism
        sensational_words = [
            "guaranteed", "certain", "must", "will definitely",
            "100%", "cannot fail", "secret", "insider"
        ]
        sensationalism_score = sum(
            1 for word in sensational_words
            if word.lower() in combined.lower()
        ) / len(sensational_words)

        authenticity = source_trust * (1 - sensationalism_score * 0.5)

        return authenticity > 0.5, authenticity

    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics."""
        if not self._detection_history:
            return {"total_detections": 0}

        attack_counts = {}
        for detection in self._detection_history:
            for attack_type in detection.attack_types:
                attack_counts[attack_type.value] = attack_counts.get(attack_type.value, 0) + 1

        threat_levels = {}
        for detection in self._detection_history:
            level = detection.threat_level.value
            threat_levels[level] = threat_levels.get(level, 0) + 1

        return {
            "total_detections": len(self._detection_history),
            "attack_type_distribution": attack_counts,
            "threat_level_distribution": threat_levels,
            "avg_confidence": sum(d.confidence for d in self._detection_history) / len(self._detection_history)
        }

    def add_blocked_keyword(self, keyword: str):
        """Add a keyword to block list."""
        self.policy.blocked_keywords.add(keyword)

    def add_trusted_source(self, source: str):
        """Add a trusted news source."""
        self.policy.trusted_sources.add(source)

    def clear_history(self):
        """Clear detection history."""
        self._detection_history.clear()


class SecurePromptWrapper:
    """
    Wrapper that applies security checks to all prompts.

    Usage:
        wrapper = SecurePromptWrapper(guard)
        safe_prompt = wrapper.wrap_prompt(user_input, system_context)
    """

    def __init__(self, guard: PromptGuard):
        self.guard = guard

    def wrap_prompt(
        self,
        user_input: str,
        system_context: str = ""
    ) -> Tuple[str, bool]:
        """
        Wrap user input with security checks.

        Returns:
            Tuple of (processed_prompt, was_modified)
        """
        # Analyze user input
        detection = self.guard.analyze(user_input)

        if self.guard.should_block(detection):
            logger.error(f"Blocked malicious input: {detection.attack_types}")
            return "", True

        if self.guard.should_sanitize(detection):
            sanitized = self.guard.sanitize(user_input)
            return sanitized, True

        return user_input, False

    def validate_response(
        self,
        response: str
    ) -> Tuple[str, bool]:
        """
        Validate and sanitize LLM response.

        Returns:
            Tuple of (processed_response, was_modified)
        """
        # Check if response contains injected instructions
        detection = self.guard.analyze(response)

        if detection.is_threat:
            logger.warning(f"Response contained threats: {detection.attack_types}")
            return self.guard.sanitize(response), True

        return response, False
