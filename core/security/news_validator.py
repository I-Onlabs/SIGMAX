"""
News Source Validator - Fake News Detection for Trading Agents
Inspired by TradeTrap's fake news injection attacks

Validates news for:
- Source authenticity
- Content credibility
- Manipulation indicators
- Cross-reference verification
"""

from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re
from loguru import logger


class CredibilityLevel(Enum):
    """News credibility levels."""
    VERIFIED = "verified"
    LIKELY_AUTHENTIC = "likely_authentic"
    UNCERTAIN = "uncertain"
    SUSPICIOUS = "suspicious"
    LIKELY_FAKE = "likely_fake"


class ManipulationIndicator(Enum):
    """Indicators of news manipulation."""
    SENSATIONAL_LANGUAGE = "sensational_language"
    UNREALISTIC_CLAIMS = "unrealistic_claims"
    UNKNOWN_SOURCE = "unknown_source"
    MISSING_ATTRIBUTION = "missing_attribution"
    PRICE_MANIPULATION = "price_manipulation"
    URGENCY_PRESSURE = "urgency_pressure"
    CONTRADICTS_CONSENSUS = "contradicts_consensus"
    SUSPICIOUS_TIMING = "suspicious_timing"
    GRAMMATICAL_ISSUES = "grammatical_issues"
    EXCESSIVE_PUNCTUATION = "excessive_punctuation"


@dataclass
class NewsValidation:
    """Result of news validation."""
    headline: str
    source: Optional[str]
    credibility: CredibilityLevel
    confidence: float
    indicators: List[ManipulationIndicator]
    risk_score: float  # 0-1, higher = more risky
    details: Dict[str, Any]
    recommendation: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "headline": self.headline[:100],
            "source": self.source,
            "credibility": self.credibility.value,
            "confidence": round(self.confidence, 3),
            "indicators": [i.value for i in self.indicators],
            "risk_score": round(self.risk_score, 3),
            "recommendation": self.recommendation,
            "timestamp": self.timestamp.isoformat()
        }

    @property
    def is_safe_to_use(self) -> bool:
        return self.credibility in [
            CredibilityLevel.VERIFIED,
            CredibilityLevel.LIKELY_AUTHENTIC
        ]


@dataclass
class SourceProfile:
    """Profile of a news source."""
    name: str
    trust_score: float  # 0-1
    domain: Optional[str] = None
    category: str = "general"  # financial, tech, mainstream, social
    verification_level: str = "unverified"  # verified, trusted, unverified
    historical_accuracy: float = 0.5
    bias_score: float = 0.0  # -1 (bearish bias) to 1 (bullish bias)


class NewsValidator:
    """
    Validates news articles for authenticity and manipulation.

    Usage:
        validator = NewsValidator()

        # Validate a news article
        result = validator.validate(
            headline="BREAKING: Stock XYZ to surge 500%!",
            source="unknown_blog.com",
            content="..."
        )

        if not result.is_safe_to_use:
            print(f"Suspicious news: {result.indicators}")
    """

    # Known trusted sources
    DEFAULT_TRUSTED_SOURCES = {
        "reuters.com": SourceProfile("Reuters", 0.95, "reuters.com", "financial", "verified", 0.92),
        "bloomberg.com": SourceProfile("Bloomberg", 0.95, "bloomberg.com", "financial", "verified", 0.91),
        "wsj.com": SourceProfile("Wall Street Journal", 0.9, "wsj.com", "financial", "verified", 0.89),
        "ft.com": SourceProfile("Financial Times", 0.9, "ft.com", "financial", "verified", 0.88),
        "cnbc.com": SourceProfile("CNBC", 0.85, "cnbc.com", "financial", "trusted", 0.82),
        "sec.gov": SourceProfile("SEC", 0.99, "sec.gov", "regulatory", "verified", 0.99),
        "federalreserve.gov": SourceProfile("Federal Reserve", 0.99, "federalreserve.gov", "regulatory", "verified", 0.99),
    }

    # Sensational language patterns
    SENSATIONAL_PATTERNS = [
        r"\b(breaking|urgent|alert|exclusive|shocking|bombshell)\b",
        r"\b(skyrocket|plummet|crash|explode|moon|tank)\b",
        r"\b(guaranteed|certain|definite|100%|risk.?free)\b",
        r"\b(secret|insider|leaked|confidential|hidden)\b",
        r"\b(must\s+buy|must\s+sell|act\s+now|don't\s+miss)\b",
    ]

    # Unrealistic claim patterns
    UNREALISTIC_PATTERNS = [
        r"\b\d{3,}%\s*(gain|return|increase|growth|profit)\b",
        r"\b(will|going\s+to)\s+(definitely|certainly|absolutely)\b",
        r"\b(cannot|can't|won't)\s+(fail|lose|go\s+wrong)\b",
        r"\b(overnight|instant|immediate)\s+(wealth|rich|millionaire)\b",
        r"\bguaranteed\s+(returns?|profit|success)\b",
    ]

    # Price manipulation patterns
    MANIPULATION_PATTERNS = [
        r"\bbuy\s+(now|immediately|before|while)\b",
        r"\blast\s+chance\s+to\s+(buy|invest)\b",
        r"\bonly\s+\d+\s+(shares|spots|seats)\s+(left|remaining)\b",
        r"\bprice\s+will\s+(never|not)\s+be\s+this\s+low\b",
        r"\binsider\s+(tip|information|knowledge)\b",
    ]

    def __init__(
        self,
        trusted_sources: Dict[str, SourceProfile] = None,
        strict_mode: bool = False,
        min_confidence_threshold: float = 0.6
    ):
        """
        Initialize news validator.

        Args:
            trusted_sources: Additional trusted sources
            strict_mode: Apply stricter validation rules
            min_confidence_threshold: Minimum confidence for uncertain status
        """
        self._sources = dict(self.DEFAULT_TRUSTED_SOURCES)
        if trusted_sources:
            self._sources.update(trusted_sources)

        self.strict_mode = strict_mode
        self.min_confidence_threshold = min_confidence_threshold

        self._compile_patterns()
        self._validation_history: List[NewsValidation] = []

        # Cache for cross-reference
        self._recent_news: List[Dict[str, Any]] = []

    def _compile_patterns(self):
        """Compile regex patterns."""
        self._sensational_re = [
            re.compile(p, re.IGNORECASE) for p in self.SENSATIONAL_PATTERNS
        ]
        self._unrealistic_re = [
            re.compile(p, re.IGNORECASE) for p in self.UNREALISTIC_PATTERNS
        ]
        self._manipulation_re = [
            re.compile(p, re.IGNORECASE) for p in self.MANIPULATION_PATTERNS
        ]

    def validate(
        self,
        headline: str,
        source: Optional[str] = None,
        content: Optional[str] = None,
        published_at: Optional[datetime] = None,
        symbols_mentioned: List[str] = None
    ) -> NewsValidation:
        """
        Validate a news article.

        Args:
            headline: News headline
            source: Source domain or name
            content: Full article content
            published_at: Publication timestamp
            symbols_mentioned: Stock/crypto symbols mentioned

        Returns:
            NewsValidation result
        """
        indicators = []
        details = {}
        confidence_scores = []

        combined_text = f"{headline} {content or ''}"

        # Check source credibility
        source_result = self._check_source(source)
        if source_result["indicators"]:
            indicators.extend(source_result["indicators"])
        details["source_analysis"] = source_result
        confidence_scores.append(source_result["trust_score"])

        # Check for sensational language
        sensational_result = self._check_sensational(combined_text)
        if sensational_result["detected"]:
            indicators.append(ManipulationIndicator.SENSATIONAL_LANGUAGE)
            details["sensational_analysis"] = sensational_result
            confidence_scores.append(1 - sensational_result["severity"])

        # Check for unrealistic claims
        unrealistic_result = self._check_unrealistic(combined_text)
        if unrealistic_result["detected"]:
            indicators.append(ManipulationIndicator.UNREALISTIC_CLAIMS)
            details["unrealistic_analysis"] = unrealistic_result
            confidence_scores.append(0.3)

        # Check for price manipulation language
        manipulation_result = self._check_manipulation(combined_text)
        if manipulation_result["detected"]:
            indicators.append(ManipulationIndicator.PRICE_MANIPULATION)
            details["manipulation_analysis"] = manipulation_result
            confidence_scores.append(0.2)

        # Check for urgency pressure
        urgency_result = self._check_urgency(combined_text)
        if urgency_result["detected"]:
            indicators.append(ManipulationIndicator.URGENCY_PRESSURE)
            details["urgency_analysis"] = urgency_result

        # Check timing if provided
        if published_at:
            timing_result = self._check_timing(published_at, symbols_mentioned)
            if timing_result["suspicious"]:
                indicators.append(ManipulationIndicator.SUSPICIOUS_TIMING)
                details["timing_analysis"] = timing_result

        # Check writing quality
        quality_result = self._check_quality(combined_text)
        if quality_result["issues"]:
            if "grammar" in quality_result["issues"]:
                indicators.append(ManipulationIndicator.GRAMMATICAL_ISSUES)
            if "punctuation" in quality_result["issues"]:
                indicators.append(ManipulationIndicator.EXCESSIVE_PUNCTUATION)
            details["quality_analysis"] = quality_result

        # Cross-reference check
        crossref_result = self._cross_reference(headline, symbols_mentioned)
        if crossref_result["contradicts"]:
            indicators.append(ManipulationIndicator.CONTRADICTS_CONSENSUS)
            details["crossref_analysis"] = crossref_result

        # Calculate credibility and risk
        credibility, confidence = self._calculate_credibility(indicators, confidence_scores)
        risk_score = self._calculate_risk(indicators, source_result["trust_score"])

        # Generate recommendation
        recommendation = self._generate_recommendation(credibility, risk_score, indicators)

        result = NewsValidation(
            headline=headline,
            source=source,
            credibility=credibility,
            confidence=confidence,
            indicators=list(set(indicators)),
            risk_score=risk_score,
            details=details,
            recommendation=recommendation
        )

        # Cache for cross-reference
        self._recent_news.append({
            "headline": headline,
            "symbols": symbols_mentioned or [],
            "credibility": credibility,
            "timestamp": datetime.utcnow()
        })
        if len(self._recent_news) > 1000:
            self._recent_news = self._recent_news[-500:]

        self._validation_history.append(result)

        if indicators:
            logger.info(f"News validation: {credibility.value} - {[i.value for i in indicators]}")

        return result

    def _check_source(self, source: Optional[str]) -> Dict[str, Any]:
        """Check source credibility."""
        if not source:
            return {
                "trust_score": 0.3,
                "indicators": [ManipulationIndicator.UNKNOWN_SOURCE],
                "verified": False
            }

        source_lower = source.lower()

        # Check against known sources
        for domain, profile in self._sources.items():
            if domain in source_lower or profile.name.lower() in source_lower:
                return {
                    "trust_score": profile.trust_score,
                    "indicators": [],
                    "verified": profile.verification_level == "verified",
                    "profile": profile.name
                }

        # Unknown source
        return {
            "trust_score": 0.4,
            "indicators": [ManipulationIndicator.UNKNOWN_SOURCE],
            "verified": False
        }

    def _check_sensational(self, text: str) -> Dict[str, Any]:
        """Check for sensational language."""
        matches = []
        for pattern in self._sensational_re:
            found = pattern.findall(text)
            matches.extend(found)

        severity = min(len(matches) * 0.15, 0.9)

        return {
            "detected": len(matches) > 0,
            "matches": matches[:5],
            "count": len(matches),
            "severity": severity
        }

    def _check_unrealistic(self, text: str) -> Dict[str, Any]:
        """Check for unrealistic claims."""
        matches = []
        for pattern in self._unrealistic_re:
            found = pattern.findall(text)
            matches.extend(found)

        return {
            "detected": len(matches) > 0,
            "matches": matches[:5],
            "count": len(matches)
        }

    def _check_manipulation(self, text: str) -> Dict[str, Any]:
        """Check for price manipulation language."""
        matches = []
        for pattern in self._manipulation_re:
            found = pattern.findall(text)
            matches.extend(found)

        return {
            "detected": len(matches) > 0,
            "matches": matches[:5],
            "count": len(matches)
        }

    def _check_urgency(self, text: str) -> Dict[str, Any]:
        """Check for artificial urgency."""
        urgency_words = [
            "now", "immediately", "urgent", "hurry", "quick",
            "last chance", "limited time", "act fast", "don't wait"
        ]

        text_lower = text.lower()
        found = [w for w in urgency_words if w in text_lower]

        return {
            "detected": len(found) >= 2,
            "words": found
        }

    def _check_timing(
        self,
        published_at: datetime,
        symbols: List[str] = None
    ) -> Dict[str, Any]:
        """Check for suspicious timing."""
        now = datetime.utcnow()

        # Future dated
        if published_at > now + timedelta(hours=1):
            return {"suspicious": True, "reason": "future_dated"}

        # Very old but presented as breaking
        if published_at < now - timedelta(days=7):
            return {"suspicious": True, "reason": "stale_news"}

        # TODO: Check against known events for suspicious timing

        return {"suspicious": False}

    def _check_quality(self, text: str) -> Dict[str, Any]:
        """Check writing quality indicators."""
        issues = []

        # Excessive punctuation
        exclamation_count = text.count("!")
        if exclamation_count > 3:
            issues.append("punctuation")

        # ALL CAPS words (more than 3)
        caps_words = re.findall(r"\b[A-Z]{4,}\b", text)
        if len(caps_words) > 3:
            issues.append("excessive_caps")

        # Very short content for a news article
        word_count = len(text.split())
        if word_count < 20:
            issues.append("too_short")

        return {
            "issues": issues,
            "exclamation_count": exclamation_count,
            "caps_words": len(caps_words),
            "word_count": word_count
        }

    def _cross_reference(
        self,
        headline: str,
        symbols: List[str] = None
    ) -> Dict[str, Any]:
        """Cross-reference against recent news."""
        if not symbols or not self._recent_news:
            return {"contradicts": False}

        # Find recent news about same symbols
        related = []
        for news in self._recent_news[-100:]:
            if any(s in news["symbols"] for s in symbols):
                related.append(news)

        if not related:
            return {"contradicts": False}

        # Simple contradiction check
        headline_lower = headline.lower()
        bullish_words = ["surge", "gain", "rise", "up", "bullish", "positive"]
        bearish_words = ["crash", "fall", "drop", "down", "bearish", "negative"]

        is_bullish = any(w in headline_lower for w in bullish_words)
        is_bearish = any(w in headline_lower for w in bearish_words)

        # Check if majority of recent news has opposite sentiment
        if is_bullish or is_bearish:
            # This is simplified - full implementation would use NLP
            pass

        return {"contradicts": False, "related_count": len(related)}

    def _calculate_credibility(
        self,
        indicators: List[ManipulationIndicator],
        confidence_scores: List[float]
    ) -> Tuple[CredibilityLevel, float]:
        """Calculate overall credibility."""
        if not indicators:
            avg_conf = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.7
            if avg_conf > 0.85:
                return CredibilityLevel.VERIFIED, avg_conf
            return CredibilityLevel.LIKELY_AUTHENTIC, avg_conf

        # Critical indicators
        critical = {
            ManipulationIndicator.UNREALISTIC_CLAIMS,
            ManipulationIndicator.PRICE_MANIPULATION
        }

        if any(i in critical for i in indicators):
            return CredibilityLevel.LIKELY_FAKE, 0.85

        if len(indicators) >= 4:
            return CredibilityLevel.LIKELY_FAKE, 0.8

        if len(indicators) >= 2:
            return CredibilityLevel.SUSPICIOUS, 0.7

        avg_conf = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        return CredibilityLevel.UNCERTAIN, avg_conf

    def _calculate_risk(
        self,
        indicators: List[ManipulationIndicator],
        source_trust: float
    ) -> float:
        """Calculate risk score (0-1)."""
        base_risk = 1 - source_trust

        # Add risk for each indicator
        indicator_risks = {
            ManipulationIndicator.UNREALISTIC_CLAIMS: 0.3,
            ManipulationIndicator.PRICE_MANIPULATION: 0.25,
            ManipulationIndicator.SENSATIONAL_LANGUAGE: 0.1,
            ManipulationIndicator.UNKNOWN_SOURCE: 0.15,
            ManipulationIndicator.URGENCY_PRESSURE: 0.1,
            ManipulationIndicator.SUSPICIOUS_TIMING: 0.15,
        }

        for indicator in indicators:
            base_risk += indicator_risks.get(indicator, 0.05)

        return min(base_risk, 1.0)

    def _generate_recommendation(
        self,
        credibility: CredibilityLevel,
        risk_score: float,
        indicators: List[ManipulationIndicator]
    ) -> str:
        """Generate actionable recommendation."""
        if credibility == CredibilityLevel.VERIFIED:
            return "Safe to use for trading decisions"

        if credibility == CredibilityLevel.LIKELY_AUTHENTIC:
            return "Generally reliable, verify with additional sources for major decisions"

        if credibility == CredibilityLevel.UNCERTAIN:
            return "Exercise caution, cross-reference with trusted sources before acting"

        if credibility == CredibilityLevel.SUSPICIOUS:
            return "High risk - do not use for trading without independent verification"

        if credibility == CredibilityLevel.LIKELY_FAKE:
            return "DANGER - Likely manipulated content, do not act on this information"

        return "Unable to assess - treat with extreme caution"

    def add_trusted_source(self, domain: str, profile: SourceProfile):
        """Add a trusted source."""
        self._sources[domain] = profile

    def get_statistics(self) -> Dict[str, Any]:
        """Get validation statistics."""
        if not self._validation_history:
            return {"total_validations": 0}

        credibility_counts = {}
        indicator_counts = {}

        for result in self._validation_history:
            cred = result.credibility.value
            credibility_counts[cred] = credibility_counts.get(cred, 0) + 1

            for indicator in result.indicators:
                ind = indicator.value
                indicator_counts[ind] = indicator_counts.get(ind, 0) + 1

        safe_count = sum(1 for r in self._validation_history if r.is_safe_to_use)

        return {
            "total_validations": len(self._validation_history),
            "safe_news_pct": safe_count / len(self._validation_history) * 100,
            "credibility_distribution": credibility_counts,
            "indicator_distribution": indicator_counts,
            "avg_risk_score": sum(r.risk_score for r in self._validation_history) / len(self._validation_history)
        }

    def clear_history(self):
        """Clear validation history."""
        self._validation_history.clear()
        self._recent_news.clear()
