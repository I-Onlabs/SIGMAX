"""
Unit tests for Sentiment Agent
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from core.agents.sentiment import SentimentAgent


class TestSentimentAgent:
    """Tests for SentimentAgent"""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM"""
        llm = Mock()
        llm.ainvoke = AsyncMock()
        return llm

    @pytest.fixture
    def sentiment_agent(self, mock_llm):
        """Create SentimentAgent instance"""
        return SentimentAgent(mock_llm)

    @pytest.mark.asyncio
    async def test_initialization(self, sentiment_agent):
        """Test sentiment agent initialization"""
        assert sentiment_agent is not None
        assert sentiment_agent.bullish_keywords is not None
        assert sentiment_agent.bearish_keywords is not None
        assert len(sentiment_agent.bullish_keywords) > 0
        assert len(sentiment_agent.bearish_keywords) > 0

    @pytest.mark.asyncio
    async def test_analyze_symbol(self, sentiment_agent):
        """Test analyzing a symbol"""
        result = await sentiment_agent.analyze('BTC/USDT', lookback_hours=24)

        assert result is not None
        assert 'aggregate_score' in result
        assert 'confidence' in result
        assert 'sources' in result
        assert 'trending' in result
        assert -1 <= result['aggregate_score'] <= 1
        assert 0 <= result['confidence'] <= 1

    @pytest.mark.asyncio
    async def test_news_sentiment(self, sentiment_agent):
        """Test news sentiment analysis"""
        result = await sentiment_agent._analyze_news('BTC', lookback_hours=24)

        assert 'score' in result
        assert 'confidence' in result
        assert 'article_count' in result
        assert -1 <= result['score'] <= 1

    @pytest.mark.asyncio
    async def test_social_sentiment(self, sentiment_agent):
        """Test social media sentiment analysis"""
        result = await sentiment_agent._analyze_social('BTC', lookback_hours=24)

        assert 'score' in result
        assert 'confidence' in result
        assert 'mention_count' in result
        assert -1 <= result['score'] <= 1

    @pytest.mark.asyncio
    async def test_onchain_metrics(self, sentiment_agent):
        """Test on-chain metrics analysis"""
        result = await sentiment_agent._analyze_onchain('BTC', lookback_hours=24)

        assert 'score' in result
        assert 'confidence' in result
        assert -1 <= result['score'] <= 1

    @pytest.mark.asyncio
    async def test_fear_greed_index(self, sentiment_agent):
        """Test Fear & Greed index"""
        result = await sentiment_agent._get_fear_greed_index()

        assert 'score' in result
        assert 'label' in result
        assert 0 <= result['score'] <= 100

    def test_calculate_sentiment_score_bullish(self, sentiment_agent):
        """Test sentiment calculation with bullish text"""
        text = "Bitcoin showing strong momentum and bullish patterns. Moon soon! Rally expected."
        score = sentiment_agent._calculate_sentiment_score(text)

        assert score > 0  # Should be positive

    def test_calculate_sentiment_score_bearish(self, sentiment_agent):
        """Test sentiment calculation with bearish text"""
        text = "Bitcoin crash imminent. Weak support levels. Bear market confirmed. Dump incoming."
        score = sentiment_agent._calculate_sentiment_score(text)

        assert score < 0  # Should be negative

    def test_calculate_sentiment_score_neutral(self, sentiment_agent):
        """Test sentiment calculation with neutral text"""
        text = "Bitcoin price unchanged. Market moving sideways. No clear direction."
        score = sentiment_agent._calculate_sentiment_score(text)

        assert abs(score) < 0.5  # Should be close to neutral

    def test_calculate_sentiment_score_empty(self, sentiment_agent):
        """Test sentiment calculation with empty text"""
        score = sentiment_agent._calculate_sentiment_score("")

        assert score == 0

    @pytest.mark.asyncio
    async def test_trending_detection(self, sentiment_agent):
        """Test trending detection"""
        # Mock sequential calls that show improvement
        results = []
        for i in range(5):
            result = await sentiment_agent._analyze_news('BTC', lookback_hours=24)
            results.append(result)

        # Trending should be detected
        final_result = await sentiment_agent.analyze('BTC/USDT', lookback_hours=24)
        assert 'trending' in final_result
        assert final_result['trending'] in ['up', 'down', 'neutral']

    @pytest.mark.asyncio
    async def test_symbol_normalization(self, sentiment_agent):
        """Test that symbols are normalized properly"""
        # Different formats should work
        symbols = ['BTC/USDT', 'BTC-USDT', 'BTCUSDT']

        for symbol in symbols:
            result = await sentiment_agent.analyze(symbol, lookback_hours=24)
            assert result is not None

    @pytest.mark.asyncio
    async def test_aggregate_weights(self, sentiment_agent):
        """Test that aggregate calculation uses correct weights"""
        result = await sentiment_agent.analyze('BTC/USDT', lookback_hours=24)

        # Should have contributions from all sources
        assert result['sources']['news']['weight'] > 0
        assert result['sources']['social']['weight'] > 0
        assert result['sources']['onchain']['weight'] > 0
        assert result['sources']['fear_greed']['weight'] > 0

        # Weights should sum to approximately 1
        total_weight = sum(s['weight'] for s in result['sources'].values())
        assert 0.9 <= total_weight <= 1.1

    @pytest.mark.asyncio
    async def test_confidence_calculation(self, sentiment_agent):
        """Test confidence calculation logic"""
        result = await sentiment_agent.analyze('BTC/USDT', lookback_hours=24)

        # Confidence should be based on data availability
        assert 0 <= result['confidence'] <= 1

        # More data sources should increase confidence
        sources_with_data = sum(
            1 for s in result['sources'].values()
            if s.get('article_count', 0) > 0 or s.get('mention_count', 0) > 0
        )

        if sources_with_data > 2:
            assert result['confidence'] > 0.5

    @pytest.mark.asyncio
    async def test_error_handling(self, sentiment_agent):
        """Test error handling for invalid inputs"""
        # Empty symbol
        result = await sentiment_agent.analyze('', lookback_hours=24)
        assert result is not None
        assert result['aggregate_score'] == 0

        # Negative lookback
        result = await sentiment_agent.analyze('BTC/USDT', lookback_hours=-1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_concurrent_analysis(self, sentiment_agent):
        """Test concurrent sentiment analysis"""
        import asyncio

        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        tasks = [sentiment_agent.analyze(symbol, lookback_hours=24) for symbol in symbols]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        for result in results:
            assert 'aggregate_score' in result
            assert 'confidence' in result

    def test_keyword_scoring(self, sentiment_agent):
        """Test keyword scoring system"""
        # Strong bullish keywords should have high scores
        assert sentiment_agent.bullish_keywords.get('moon', 0) >= 2
        assert sentiment_agent.bullish_keywords.get('rally', 0) >= 1

        # Strong bearish keywords should have high negative impact
        assert sentiment_agent.bearish_keywords.get('crash', 0) <= -2
        assert sentiment_agent.bearish_keywords.get('dump', 0) <= -1

    @pytest.mark.asyncio
    async def test_lookback_period_impact(self, sentiment_agent):
        """Test different lookback periods"""
        result_short = await sentiment_agent.analyze('BTC/USDT', lookback_hours=1)
        result_long = await sentiment_agent.analyze('BTC/USDT', lookback_hours=168)

        # Both should return valid results
        assert result_short is not None
        assert result_long is not None

        # Longer period might have different confidence
        assert 'confidence' in result_short
        assert 'confidence' in result_long
