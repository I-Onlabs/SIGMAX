"""
Tests for SocialSentimentNetwork - Herd Behavior Modeling
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.behavioral.social_sentiment import (
    SocialSentimentNetwork,
    SocialAgent,
    SocialRole,
    SentimentSignal,
    SentimentType,
    HerdEvent,
    FearGreedIndex
)


class TestSocialSentimentNetwork:
    """Test SocialSentimentNetwork for herd behavior."""

    @pytest.fixture
    def network(self):
        """Create a social network."""
        return SocialSentimentNetwork(
            propagation_decay=0.7,
            herd_threshold=0.6,
            enable_logging=False
        )

    def test_register_agent(self, network):
        """Test agent registration."""
        agent = network.register_agent(
            agent_id="trader1",
            role=SocialRole.INFLUENCER,
            influence=0.9
        )

        assert agent.agent_id == "trader1"
        assert agent.role == SocialRole.INFLUENCER
        assert agent.influence_score == 0.9

    def test_add_follow_relationship(self, network):
        """Test creating follow relationships."""
        network.register_agent("influencer", SocialRole.INFLUENCER)
        network.register_agent("follower", SocialRole.FOLLOWER)

        network.add_follow("follower", "influencer")

        influencer = network._agents["influencer"]
        follower = network._agents["follower"]

        assert "follower" in influencer.followers
        assert "influencer" in follower.following

    def test_emit_signal(self, network):
        """Test emitting sentiment signals."""
        network.register_agent("trader1", SocialRole.ANALYST)

        signal = network.emit_signal(
            agent_id="trader1",
            sentiment=SentimentType.BULLISH,
            strength=0.8,
            symbol="BTC/USDT"
        )

        assert signal.source_id == "trader1"
        assert signal.sentiment == SentimentType.BULLISH
        assert signal.strength > 0

    def test_sentiment_propagation(self, network):
        """Test sentiment propagates through network."""
        network.register_agent("influencer", SocialRole.INFLUENCER, influence=0.9)
        network.register_agent("follower1", SocialRole.FOLLOWER, susceptibility=0.8)
        network.register_agent("follower2", SocialRole.FOLLOWER, susceptibility=0.7)

        network.add_follow("follower1", "influencer")
        network.add_follow("follower2", "influencer")

        signal = network.emit_signal(
            agent_id="influencer",
            sentiment=SentimentType.BULLISH,
            strength=0.9,
            symbol="BTC/USDT"
        )

        result = network.propagate_sentiment(signal)

        assert result["source"] == "influencer"
        assert result["affected_count"] >= 0

    def test_aggregate_sentiment_bullish(self, network):
        """Test aggregate sentiment calculation."""
        for i in range(5):
            agent = network.register_agent(f"bull{i}", SocialRole.ANALYST)
            network.emit_signal(f"bull{i}", SentimentType.BULLISH, 0.7, "BTC")

        network.register_agent("bear", SocialRole.ANALYST)
        network.emit_signal("bear", SentimentType.BEARISH, 0.5, "BTC")

        agg = network.get_aggregate_sentiment(symbol="BTC")

        assert agg["sentiment"] in ["bullish", "slightly_bullish"]
        assert agg["score"] > 0

    def test_aggregate_sentiment_bearish(self, network):
        """Test aggregate sentiment for bearish market."""
        for i in range(5):
            agent = network.register_agent(f"bear{i}", SocialRole.ANALYST)
            network.emit_signal(f"bear{i}", SentimentType.BEARISH, 0.8, "ETH")

        agg = network.get_aggregate_sentiment(symbol="ETH")

        assert agg["sentiment"] in ["bearish", "slightly_bearish"]
        assert agg["score"] < 0

    def test_influencer_sentiment(self, network):
        """Test getting sentiment from influencers only."""
        network.register_agent("inf1", SocialRole.INFLUENCER, influence=0.9)
        network.register_agent("inf2", SocialRole.INFLUENCER, influence=0.85)

        network._agents["inf1"].sentiment = SentimentType.BULLISH
        network._agents["inf2"].sentiment = SentimentType.BULLISH

        for i in range(10):
            agent = network.register_agent(f"fol{i}", SocialRole.FOLLOWER, influence=0.2)
            agent.sentiment = SentimentType.BEARISH

        inf_sentiment = network.get_influencer_sentiment(min_influence=0.6)

        assert inf_sentiment["sentiment"] == "bullish"
        assert inf_sentiment["influencer_count"] == 2

    def test_network_statistics(self, network):
        """Test network statistics."""
        network.register_agent("a1", SocialRole.INFLUENCER)
        network.register_agent("a2", SocialRole.FOLLOWER)
        network.register_agent("a3", SocialRole.ANALYST)

        network.add_follow("a2", "a1")
        network.emit_signal("a1", SentimentType.NEUTRAL, 0.5)

        stats = network.get_network_statistics()

        assert stats["agent_count"] == 3
        assert "role_distribution" in stats
        assert stats["total_signals"] >= 1


class TestFearGreedIndex:
    """Test Fear and Greed Index calculation."""

    @pytest.fixture
    def fg_index(self):
        """Create Fear and Greed calculator."""
        return FearGreedIndex()

    def test_extreme_fear(self, fg_index):
        """Test extreme fear calculation."""
        result = fg_index.calculate(
            social_sentiment=-0.8,
            volatility_percentile=90,
            price_momentum=-0.7,
            volume_ratio=1.5
        )

        assert result["label"] == "extreme_fear"
        assert result["index"] < 25

    def test_extreme_greed(self, fg_index):
        """Test extreme greed calculation."""
        result = fg_index.calculate(
            social_sentiment=0.9,
            volatility_percentile=20,
            price_momentum=0.8,
            volume_ratio=2.0
        )

        assert result["label"] == "extreme_greed"
        assert result["index"] > 75

    def test_neutral_market(self, fg_index):
        """Test neutral market calculation."""
        result = fg_index.calculate(
            social_sentiment=0.0,
            volatility_percentile=50,
            price_momentum=0.0,
            volume_ratio=1.0
        )

        assert result["label"] == "neutral"
        assert 40 <= result["index"] <= 60

    def test_components_included(self, fg_index):
        """Test that components are included in result."""
        result = fg_index.calculate(
            social_sentiment=0.5,
            volatility_percentile=40,
            price_momentum=0.3,
            volume_ratio=1.2
        )

        assert "components" in result
        assert "social" in result["components"]
        assert "volatility" in result["components"]

    def test_trend_tracking(self, fg_index):
        """Test trend tracking over time."""
        for _ in range(10):
            fg_index.calculate(
                social_sentiment=0.3,
                volatility_percentile=40,
                price_momentum=0.2,
                volume_ratio=1.1
            )

        trend = fg_index.get_trend(periods=5)

        assert trend["trend"] in ["increasing_greed", "increasing_fear", "stable"]
        assert trend["periods"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
