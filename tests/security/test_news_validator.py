"""
Tests for NewsValidator - Fake News Defense
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.security.news_validator import (
    NewsValidator,
    NewsValidation,
    CredibilityLevel,
    ManipulationIndicator,
    SourceProfile
)


class TestNewsValidator:
    """Test NewsValidator for fake news defense."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return NewsValidator(
            require_source=False,
            min_credibility=CredibilityLevel.MEDIUM
        )

    @pytest.fixture
    def strict_validator(self):
        """Create a strict validator."""
        return NewsValidator(
            require_source=True,
            min_credibility=CredibilityLevel.HIGH
        )

    def test_valid_news_from_trusted_source(self, validator):
        """Test validation of legitimate news."""
        result = validator.validate(
            headline="Bitcoin ETF sees record inflows",
            source="reuters.com",
            content="Spot Bitcoin ETFs recorded $1 billion in net inflows."
        )

        assert result.credibility in [CredibilityLevel.HIGH, CredibilityLevel.VERY_HIGH]
        assert len(result.manipulation_indicators) == 0

    def test_detect_sensational_language(self, validator):
        """Test detection of sensational language."""
        result = validator.validate(
            headline="BREAKING URGENT ALERT: Bitcoin to crash 99% TODAY!!!",
            content="Shocking exclusive revelation about crypto market collapse."
        )

        assert ManipulationIndicator.SENSATIONAL_LANGUAGE in result.manipulation_indicators
        assert result.credibility.value in ["low", "very_low", "medium"]

    def test_detect_unrealistic_claims(self, validator):
        """Test detection of unrealistic price claims."""
        result = validator.validate(
            headline="Bitcoin surges 500% in one hour",
            content="Cryptocurrency rises 500 percent in unprecedented move."
        )

        assert ManipulationIndicator.UNREALISTIC_CLAIMS in result.manipulation_indicators

    def test_detect_price_manipulation(self, validator):
        """Test detection of price manipulation attempts."""
        result = validator.validate(
            headline="Buy now before it's too late - insider tip",
            content="This is your last chance to buy. FOMO guaranteed 1000x returns."
        )

        assert ManipulationIndicator.PUMP_DUMP_LANGUAGE in result.manipulation_indicators

    def test_unknown_source_lower_credibility(self, validator):
        """Test that unknown sources have lower credibility."""
        result = validator.validate(
            headline="Market update",
            source="unknown-crypto-news.xyz",
            content="Regular market commentary."
        )

        # Unknown source should lower credibility
        assert result.credibility.value in ["low", "medium", "unknown"]

    def test_trusted_sources_recognized(self, validator):
        """Test that trusted sources are recognized."""
        trusted_sources = [
            "reuters.com",
            "bloomberg.com",
            "wsj.com",
            "ft.com",
            "coindesk.com"
        ]

        for source in trusted_sources:
            result = validator.validate(
                headline="Market analysis",
                source=source,
                content="Regular market analysis."
            )

            assert result.credibility in [
                CredibilityLevel.HIGH,
                CredibilityLevel.VERY_HIGH,
                CredibilityLevel.MEDIUM
            ], f"Trusted source {source} not recognized"

    def test_strict_mode_requires_source(self, strict_validator):
        """Test that strict mode requires a source."""
        result = strict_validator.validate(
            headline="Important market news",
            content="Some content without source."
        )

        # Without source in strict mode, should fail or have low credibility
        assert ManipulationIndicator.NO_SOURCE in result.manipulation_indicators or \
               result.credibility.value in ["low", "very_low", "unknown"]

    def test_detect_urgency_pressure(self, validator):
        """Test detection of urgency/pressure tactics."""
        result = validator.validate(
            headline="Act NOW or miss out forever",
            content="Limited time offer. Buy immediately before price explodes."
        )

        assert ManipulationIndicator.URGENCY_PRESSURE in result.manipulation_indicators

    def test_detect_anonymous_sources(self, validator):
        """Test detection of suspicious anonymous sourcing."""
        result = validator.validate(
            headline="Secret insider reveals market crash",
            source="anonymous-leaks.com",
            content="Anonymous sources confirm major developments."
        )

        assert ManipulationIndicator.ANONYMOUS_SOURCE in result.manipulation_indicators or \
               result.credibility.value in ["low", "very_low"]

    def test_validation_with_metadata(self, validator):
        """Test validation with additional metadata."""
        result = validator.validate(
            headline="Quarterly earnings report",
            source="wsj.com",
            content="Company reports Q3 earnings.",
            metadata={
                "publish_date": "2024-01-15",
                "author": "John Smith",
                "category": "earnings"
            }
        )

        assert result.source_profile is not None
        assert result.timestamp is not None

    def test_multiple_manipulation_indicators(self, validator):
        """Test detection of multiple manipulation indicators."""
        result = validator.validate(
            headline="BREAKING URGENT: Anonymous insider says BUY NOW - 1000% gains guaranteed!!!",
            content="Secret sources reveal massive gains. Act immediately or miss out forever."
        )

        # Should detect multiple indicators
        assert len(result.manipulation_indicators) >= 2
        assert result.credibility.value in ["low", "very_low"]

    def test_clean_news_no_indicators(self, validator):
        """Test that clean news has no manipulation indicators."""
        result = validator.validate(
            headline="Federal Reserve holds interest rates steady",
            source="reuters.com",
            content="The Federal Reserve announced it will maintain current interest rates following its latest meeting."
        )

        # Clean news from trusted source should have no indicators
        assert len(result.manipulation_indicators) == 0 or \
               all(i == ManipulationIndicator.NONE for i in result.manipulation_indicators)

    def test_credibility_score(self, validator):
        """Test credibility score calculation."""
        # High credibility
        high = validator.validate(
            headline="Market update",
            source="reuters.com",
            content="Regular market news."
        )

        # Low credibility
        low = validator.validate(
            headline="URGENT BUY NOW 1000x!!!",
            content="Guaranteed returns act fast."
        )

        assert high.credibility_score > low.credibility_score

    def test_source_profile_lookup(self, validator):
        """Test source profile lookup."""
        result = validator.validate(
            headline="Tech earnings",
            source="bloomberg.com"
        )

        assert result.source_profile is not None
        assert result.source_profile.name == "Bloomberg"
        assert result.source_profile.credibility >= 0.8

    def test_register_custom_source(self, validator):
        """Test registering custom trusted sources."""
        custom_source = SourceProfile(
            name="Custom Finance News",
            credibility=0.85,
            domain="customfinance.com",
            category="financial"
        )

        validator.register_source(custom_source)

        result = validator.validate(
            headline="Market update",
            source="customfinance.com"
        )

        assert result.source_profile.name == "Custom Finance News"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
