"""
Sentiment analysis validation tests.
Tests sentiment scoring accuracy and LLM output analysis.
"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Direct import to avoid pulling in all agent dependencies
import importlib.util
# Fixed: Use relative path from project root instead of hardcoded /home/user
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sentiment_path = os.path.join(project_root, 'core/agents/sentiment.py')
spec = importlib.util.spec_from_file_location("sentiment", sentiment_path)
sentiment_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sentiment_module)
SentimentAgent = sentiment_module.SentimentAgent


class MockLLM:
    """Mock LLM for testing"""
    async def ainvoke(self, prompt):
        class MockResponse:
            content = "Sentiment analysis suggests neutral market conditions."
        return MockResponse()


class TestSentimentValidation:
    """Validate sentiment analysis accuracy"""

    @pytest.mark.asyncio
    async def test_sentiment_analysis_basic(self):
        """Test basic sentiment analysis for a symbol"""

        agent = SentimentAgent(llm=MockLLM())
        result = await agent.analyze("BTC/USDT", lookback_hours=24)

        print("\n=== Basic Sentiment Analysis ===")
        print("Symbol: BTC/USDT")
        print(f"Aggregate Score: {result['aggregate_score']:.3f}")
        print(f"Classification: {result['classification']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"News Score: {result['sources']['news']['score']:.3f}")
        print(f"Social Score: {result['sources']['social']['score']:.3f}")

        # Validate structure
        assert 'aggregate_score' in result
        assert 'classification' in result
        assert 'confidence' in result
        assert 'sources' in result
        assert 'summary' in result

        # Validate ranges
        assert -1 <= result['aggregate_score'] <= 1
        assert 0 <= result['confidence'] <= 1

        # Validate classification
        valid_classifications = ['very_bearish', 'bearish', 'neutral', 'bullish', 'very_bullish']
        assert result['classification'] in valid_classifications

    @pytest.mark.asyncio
    async def test_sentiment_sources(self):
        """Test individual sentiment sources"""

        agent = SentimentAgent(llm=MockLLM())
        result = await agent.analyze("ETH/USDT", lookback_hours=24)

        print("\n=== Sentiment Sources ===")

        # News sentiment
        news = result['sources']['news']
        print("News:")
        print(f"  Score: {news['score']:.3f}")
        print(f"  Articles: {news['article_count']}")
        print(f"  Headlines: {news.get('top_headlines', [])[:2]}")

        # Social sentiment
        social = result['sources']['social']
        print("Social:")
        print(f"  Score: {social['score']:.3f}")
        print(f"  Mentions: {social['mention_count']}")
        print(f"  Trending: {social['trending']}")

        # On-chain sentiment
        onchain = result['sources']['onchain']
        print("On-chain:")
        print(f"  Score: {onchain['score']:.3f}")
        print(f"  Inflow: ${onchain['exchange_flow']['inflow']:,.0f}")
        print(f"  Outflow: ${onchain['exchange_flow']['outflow']:,.0f}")

        # Fear & Greed
        fear_greed = result['sources']['fear_greed']
        print("Fear & Greed:")
        print(f"  Index: {fear_greed['index']}")
        print(f"  Classification: {fear_greed['classification']}")

        # Validate all sources have scores
        assert -1 <= news['score'] <= 1
        assert -1 <= social['score'] <= 1
        assert -1 <= onchain['score'] <= 1
        assert 0 <= fear_greed['index'] <= 100

    @pytest.mark.asyncio
    async def test_sentiment_classification_mapping(self):
        """Test that sentiment scores map to correct classifications"""

        agent = SentimentAgent(llm=MockLLM())

        # Test classification logic with known scores
        test_cases = [
            (0.7, 'very_bullish'),
            (0.3, 'bullish'),
            (0.0, 'neutral'),
            (-0.3, 'bearish'),
            (-0.7, 'very_bearish'),
        ]

        print("\n=== Sentiment Classification Mapping ===")

        for score, expected_class in test_cases:
            classification = agent._classify_sentiment(score)
            print(f"Score {score:+.1f} -> {classification}")
            assert classification == expected_class

    @pytest.mark.asyncio
    async def test_text_sentiment_scoring(self):
        """Test text-based sentiment scoring"""

        agent = SentimentAgent(llm=MockLLM())

        test_texts = [
            ("Bitcoin surges to new all-time high! Strong bullish momentum!", "positive"),
            ("Market crash imminent, sell everything now!", "negative"),
            ("Price remains stable with low volatility", "neutral"),
            ("Rally continues with strong buying pressure and breakout!", "positive"),
            ("Weak fundamentals lead to bearish breakdown", "negative"),
        ]

        print("\n=== Text Sentiment Scoring ===")

        for text, expected_sentiment in test_texts:
            score = agent._score_text(text)
            sentiment_type = "positive" if score > 0.1 else ("negative" if score < -0.1 else "neutral")

            print(f"Text: {text[:50]}...")
            print(f"  Score: {score:+.3f} ({sentiment_type})")

            assert sentiment_type == expected_sentiment

    @pytest.mark.asyncio
    async def test_confidence_calculation(self):
        """Test sentiment confidence calculation"""

        agent = SentimentAgent(llm=MockLLM())
        result = await agent.analyze("BTC/USDT", lookback_hours=24)

        confidence = result['confidence']

        print("\n=== Confidence Calculation ===")
        print(f"Aggregate Score: {result['aggregate_score']:.3f}")
        print(f"Confidence: {confidence:.3f}")
        print(f"News articles: {result['sources']['news']['article_count']}")
        print(f"Social mentions: {result['sources']['social']['mention_count']}")

        # Confidence should be between 0 and 1
        assert 0 <= confidence <= 1

        # With mock data, we should have reasonable confidence
        assert confidence > 0.3  # At least moderate confidence

    @pytest.mark.asyncio
    async def test_sentiment_trend_analysis(self):
        """Test sentiment trend over time"""

        agent = SentimentAgent(llm=MockLLM())

        # Generate sentiment history by analyzing multiple times
        for i in range(5):
            await agent.analyze("BTC/USDT", lookback_hours=24)
            await asyncio.sleep(0.1)  # Small delay

        # Get trend
        if hasattr(agent, 'get_sentiment_trend'):
            trend = await agent.get_sentiment_trend(periods=5)

            print("\n=== Sentiment Trend ===")
            print(f"History length: {len(agent.sentiment_history)}")
            if trend:
                print(f"Trend direction: {trend.get('direction', 'N/A')}")
                print(f"Recent scores: {[h['aggregate_score'] for h in agent.sentiment_history[-3:]]}")

        # Validate history is being tracked
        assert len(agent.sentiment_history) >= 5

    @pytest.mark.asyncio
    async def test_multiple_symbols(self):
        """Test sentiment analysis for multiple symbols"""

        agent = SentimentAgent(llm=MockLLM())
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

        results = {}
        for symbol in symbols:
            result = await agent.analyze(symbol, lookback_hours=24)
            results[symbol] = result

        print("\n=== Multi-Symbol Sentiment ===")
        for symbol, result in results.items():
            print(f"{symbol}:")
            print(f"  Score: {result['aggregate_score']:+.3f}")
            print(f"  Class: {result['classification']}")
            print(f"  Confidence: {result['confidence']:.3f}")

        # All results should have valid structure
        for result in results.values():
            assert 'aggregate_score' in result
            assert 'classification' in result
            assert -1 <= result['aggregate_score'] <= 1

    @pytest.mark.asyncio
    async def test_lookback_period_variation(self):
        """Test sentiment with different lookback periods"""

        agent = SentimentAgent(llm=MockLLM())

        lookback_periods = [6, 12, 24, 48]
        results = []

        for hours in lookback_periods:
            result = await agent.analyze("BTC/USDT", lookback_hours=hours)
            results.append((hours, result))

        print("\n=== Lookback Period Variation ===")
        for hours, result in results:
            print(f"{hours}h lookback:")
            print(f"  Score: {result['aggregate_score']:+.3f}")
            print(f"  Articles: {result['sources']['news']['article_count']}")

        # All should produce valid results
        for _, result in results:
            assert -1 <= result['aggregate_score'] <= 1

    @pytest.mark.asyncio
    async def test_sentiment_summary_generation(self):
        """Test sentiment summary text generation"""

        agent = SentimentAgent(llm=MockLLM())
        result = await agent.analyze("BTC/USDT", lookback_hours=24)

        summary = result.get('summary', '')

        print("\n=== Sentiment Summary ===")
        print(f"Summary: {summary}")

        # Summary should exist and be non-empty
        assert summary is not None
        assert len(summary) > 0

        # Summary should mention key aspects
        # (The actual content depends on LLM, so we just check it exists)

    @pytest.mark.asyncio
    async def test_weighted_aggregation(self):
        """Test that sentiment sources are weighted correctly"""

        agent = SentimentAgent(llm=MockLLM())
        result = await agent.analyze("BTC/USDT", lookback_hours=24)

        # Extract individual scores
        news_score = result['sources']['news']['score']
        social_score = result['sources']['social']['score']
        onchain_score = result['sources']['onchain']['score']
        fg_score = result['sources']['fear_greed']['normalized_score']

        # Expected weights from agent: news=0.3, social=0.25, onchain=0.25, fg=0.2
        expected_aggregate = (
            news_score * 0.3 +
            social_score * 0.25 +
            onchain_score * 0.25 +
            fg_score * 0.2
        )

        actual_aggregate = result['aggregate_score']

        print("\n=== Weighted Aggregation ===")
        print(f"News: {news_score:+.3f} (weight 0.30)")
        print(f"Social: {social_score:+.3f} (weight 0.25)")
        print(f"On-chain: {onchain_score:+.3f} (weight 0.25)")
        print(f"Fear/Greed: {fg_score:+.3f} (weight 0.20)")
        print(f"Expected aggregate: {expected_aggregate:+.3f}")
        print(f"Actual aggregate: {actual_aggregate:+.3f}")

        # Should be approximately equal (allowing for floating point errors)
        assert abs(expected_aggregate - actual_aggregate) < 0.01

    @pytest.mark.asyncio
    async def test_extreme_sentiment_cases(self):
        """Test handling of extreme sentiment cases"""

        agent = SentimentAgent(llm=MockLLM())

        # Analyze multiple times to potentially hit different random scenarios
        results = []
        for _ in range(10):
            result = await agent.analyze("BTC/USDT", lookback_hours=24)
            results.append(result)

        print("\n=== Extreme Sentiment Cases ===")

        # Find most bullish and bearish
        most_bullish = max(results, key=lambda r: r['aggregate_score'])
        most_bearish = min(results, key=lambda r: r['aggregate_score'])

        print(f"Most Bullish: {most_bullish['aggregate_score']:+.3f} ({most_bullish['classification']})")
        print(f"Most Bearish: {most_bearish['aggregate_score']:+.3f} ({most_bearish['classification']})")

        # All should still be in valid range
        for result in results:
            assert -1 <= result['aggregate_score'] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
