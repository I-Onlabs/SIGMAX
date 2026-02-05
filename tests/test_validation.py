"""
Test suite for ValidationAgent and Research Safety

Tests the Phase 1 enhancements inspired by Dexter
"""

import pytest
from datetime import datetime, timedelta
from core.agents.validator import ValidationAgent
from core.modules.research_safety import ResearchSafety


class TestValidationAgent:
    """Test ValidationAgent functionality"""

    @pytest.fixture
    def validator(self):
        """Create a ValidationAgent for testing"""
        config = {
            'validation_threshold': 0.7,
            'data_freshness_seconds': 300,
            'required_data_sources': ['news', 'social', 'onchain', 'technical']
        }
        return ValidationAgent(llm=None, config=config)

    @pytest.mark.asyncio
    async def test_validation_passes_with_complete_data(self, validator):
        """Test that validation passes with complete, fresh data"""
        research_data = {
            'news': {'score': 0.5, 'articles': []},
            'social': {'score': 0.3, 'trending': False},
            'onchain': {'whale_activity': 'neutral'},
            'technical': {'summary': 'RSI at 50'},
            'sentiment': 0.4,
            'timestamp': datetime.now().isoformat()
        }

        result = await validator.validate(
            research_summary="Comprehensive market analysis completed",
            technical_analysis="Technical indicators show neutral trend",
            research_data=research_data
        )

        assert result['passed'] == True
        assert result['score'] >= 0.7
        assert len(result['gaps']) == 0

    @pytest.mark.asyncio
    async def test_validation_fails_with_missing_data(self, validator):
        """Test that validation fails when required data is missing"""
        research_data = {
            'news': {'score': 0.5},
            # Missing: social, onchain, technical
            'timestamp': datetime.now().isoformat()
        }

        result = await validator.validate(
            research_summary="Incomplete research",
            research_data=research_data
        )

        assert result['passed'] == False
        assert len(result['gaps']) > 0
        assert any('Missing' in gap for gap in result['gaps'])

    @pytest.mark.asyncio
    async def test_validation_detects_stale_data(self, validator):
        """Test that validation detects stale data"""
        old_timestamp = (datetime.now() - timedelta(minutes=10)).isoformat()

        research_data = {
            'news': {'score': 0.5},
            'social': {'score': 0.3},
            'onchain': {'whale_activity': 'neutral'},
            'technical': {'summary': 'Analysis'},
            'timestamp': old_timestamp
        }

        result = await validator.validate(
            research_summary="Old research",
            research_data=research_data
        )

        assert result['passed'] == False
        assert any('stale' in gap.lower() for gap in result.get('gaps', []))

    @pytest.mark.asyncio
    async def test_validation_detects_stale_onchain_rpc(self, validator):
        """Test that validation detects stale on-chain RPC snapshot"""
        research_data = {
            'news': {'score': 0.5},
            'social': {'score': 0.3},
            'onchain': {
                'whale_activity': 'neutral',
                'rpc_snapshot': {
                    'evm': {'block_age_sec': 9999}
                }
            },
            'technical': {'summary': 'Analysis'},
            'sentiment': 0.2,
            'timestamp': datetime.now().isoformat()
        }

        result = await validator.validate(
            research_summary="Research includes stale on-chain snapshot",
            technical_analysis="Technical indicators available",
            research_data=research_data
        )

        assert result['passed'] == False
        assert any('rpc' in gap.lower() for gap in result.get('gaps', []))

    @pytest.mark.asyncio
    async def test_validation_checks_summary_quality(self, validator):
        """Test that validation checks summary quality"""
        research_data = {
            'news': {'score': 0.5},
            'social': {'score': 0.3},
            'onchain': {'whale_activity': 'neutral'},
            'technical': {'summary': 'Analysis'},
            'timestamp': datetime.now().isoformat()
        }

        # Test with too short summary
        result = await validator.validate(
            research_summary="Short",  # Too short
            technical_analysis="Also short",
            research_data=research_data
        )

        assert result['passed'] == False
        assert result['checks']['completeness'] < 1.0


class TestSentimentAgent:
    """Test SentimentAgent handling of rpc_snapshot"""

    @pytest.mark.asyncio
    async def test_onchain_rpc_snapshot_non_dict(self):
        """Non-dict rpc_snapshot should be ignored safely."""
        from core.agents.sentiment import SentimentAgent

        agent = SentimentAgent(llm=None)
        result = await agent._analyze_onchain("BTC/USDT", rpc_snapshot="invalid")

        assert isinstance(result, dict)
        assert result.get("rpc_snapshot") == {}


class TestResearchSafety:
    """Test ResearchSafety functionality"""

    @pytest.fixture
    def safety(self):
        """Create a ResearchSafety module for testing"""
        config = {
            'max_research_iterations': 5,
            'max_api_calls_per_minute': 30,
            'max_llm_cost_per_decision': 0.50,
            'max_daily_research_cost': 10.0,
            'data_freshness_threshold': 300
        }
        return ResearchSafety(config=config)

    def test_iteration_limit_check(self, safety):
        """Test iteration limit checking"""
        symbol = "BTC/USDT"

        # Should pass for iterations below limit
        assert safety.check_iteration_limit(symbol, 0) == True
        assert safety.check_iteration_limit(symbol, 3) == True

        # Should fail at limit
        assert safety.check_iteration_limit(symbol, 5) == False
        assert safety.check_iteration_limit(symbol, 10) == False

    @pytest.mark.asyncio
    async def test_api_rate_limiting(self, safety):
        """Test API rate limit tracking"""
        source = "test_api"

        # First call should succeed
        assert await safety.check_api_rate_limit(source) == True

        # Record calls up to limit
        for i in range(30):
            safety.record_api_call(source)

        # Next call should fail (at limit)
        assert await safety.check_api_rate_limit(source) == False

    def test_llm_cost_tracking(self, safety):
        """Test LLM cost tracking and limits"""
        decision_id = "test_decision_1"

        # Track cost within limit
        assert safety.track_llm_cost(decision_id, 0.20) == True
        assert safety.get_decision_cost(decision_id) == 0.20

        # Add more cost within limit
        assert safety.track_llm_cost(decision_id, 0.20) == True
        assert safety.get_decision_cost(decision_id) == 0.40

        # Exceed per-decision limit
        assert safety.track_llm_cost(decision_id, 0.20) == False
        assert safety.get_decision_cost(decision_id) == 0.60

    def test_data_freshness_check(self, safety):
        """Test data freshness validation"""
        # Fresh data
        fresh_timestamp = datetime.now().isoformat()
        assert safety.check_data_freshness(fresh_timestamp) == True

        # Stale data (10 minutes old)
        stale_timestamp = (datetime.now() - timedelta(minutes=10)).isoformat()
        assert safety.check_data_freshness(stale_timestamp) == False

    def test_safety_status(self, safety):
        """Test safety status reporting"""
        status = safety.get_safety_status()

        assert 'limits' in status
        assert 'current' in status
        assert 'utilization' in status

        assert status['limits']['max_iterations'] == 5
        assert status['limits']['max_api_calls_per_minute'] == 30


class TestIntegration:
    """Integration tests for validation workflow"""

    @pytest.mark.asyncio
    async def test_validation_workflow(self):
        """Test complete validation workflow"""
        validator = ValidationAgent(llm=None, config={
            'validation_threshold': 0.7,
            'data_freshness_seconds': 300,
            'required_data_sources': ['news', 'social', 'onchain', 'technical']
        })

        safety = ResearchSafety(config={
            'max_research_iterations': 3,
            'max_api_calls_per_minute': 30,
            'max_llm_cost_per_decision': 0.50
        })

        # Simulate research iteration 1 - incomplete data
        research_data_v1 = {
            'news': {'score': 0.5},
            'timestamp': datetime.now().isoformat()
        }

        result_v1 = await validator.validate(
            research_summary="Initial research",
            research_data=research_data_v1
        )

        assert result_v1['passed'] == False
        assert safety.check_iteration_limit("BTC/USDT", 0) == True

        # Simulate research iteration 2 - complete data
        research_data_v2 = {
            'news': {'score': 0.5, 'articles': []},
            'social': {'score': 0.3, 'trending': False},
            'onchain': {'whale_activity': 'neutral'},
            'technical': {'summary': 'Comprehensive technical analysis'},
            'sentiment': 0.4,
            'timestamp': datetime.now().isoformat()
        }

        result_v2 = await validator.validate(
            research_summary="Comprehensive research with all sources analyzed",
            technical_analysis="Complete technical analysis with RSI, MACD, and patterns",
            research_data=research_data_v2
        )

        assert result_v2['passed'] == True
        assert result_v2['score'] >= 0.7


def test_configuration_loading():
    """Test that configuration can be loaded"""
    config = {
        'validation_threshold': 0.8,
        'data_freshness_seconds': 600,
        'max_research_iterations': 5
    }

    validator = ValidationAgent(config=config)
    assert validator.validation_threshold == 0.8
    assert validator.data_freshness_seconds == 600

    safety = ResearchSafety(config=config)
    assert safety.max_research_iterations == 5


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
