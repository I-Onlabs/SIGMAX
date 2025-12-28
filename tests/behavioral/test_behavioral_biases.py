"""
Tests for BehavioralBiasEngine - Cognitive Bias Modeling
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.behavioral.behavioral_biases import (
    BehavioralBiasEngine,
    BiasProfile,
    BiasAdjustment,
    BiasType,
    PositionHistory,
    calculate_prospect_theory_value,
    calculate_probability_weight
)


class TestBehavioralBiasEngine:
    """Test BehavioralBiasEngine for cognitive bias modeling."""

    @pytest.fixture
    def engine(self):
        """Create a bias engine."""
        return BehavioralBiasEngine(
            enable_logging=False,
            randomize_biases=False,
            noise_factor=0.0
        )

    @pytest.fixture
    def emotional_profile(self):
        """Create an emotional investor profile."""
        return BiasProfile(
            disposition_strength=0.8,
            lottery_attraction=0.6,
            loss_aversion_ratio=3.0,
            overconfidence_level=0.7,
            anchoring_weight=0.6,
            herding_susceptibility=0.7,
            recency_weight=0.8,
            confirmation_strength=0.6
        )

    @pytest.fixture
    def rational_profile(self):
        """Create a rational investor profile."""
        return BiasProfile(
            disposition_strength=0.1,
            lottery_attraction=0.1,
            loss_aversion_ratio=1.5,
            overconfidence_level=0.1,
            anchoring_weight=0.2,
            herding_susceptibility=0.1,
            recency_weight=0.3,
            confirmation_strength=0.1
        )

    def test_create_profile_from_template(self, engine):
        """Test creating profiles from templates."""
        templates = ["rational", "moderate", "emotional", "retail_typical", "contrarian"]

        for template in templates:
            profile = engine.create_profile(template=template)
            assert isinstance(profile, BiasProfile)
            assert 0 <= profile.disposition_strength <= 1
            assert profile.loss_aversion_ratio >= 1

    def test_disposition_effect_winners(self, engine, emotional_profile):
        """Test disposition effect on winning positions."""
        # Create a winning position
        position = PositionHistory(
            symbol="BTC/USDT",
            entry_price=40000.0,
            entry_time=datetime.utcnow() - timedelta(days=7),
            current_price=50000.0,  # 25% profit
            quantity=1.0
        )

        decision = {
            "action": "HOLD",
            "symbol": "BTC/USDT",
            "confidence": 0.6,
            "size": 1.0
        }

        adjustment = engine.apply_biases(
            decision=decision,
            profile=emotional_profile,
            position_history=position
        )

        # Disposition effect should push toward selling winners
        assert BiasType.DISPOSITION in adjustment.biases_applied
        # Either action changed to SELL or confidence was adjusted
        assert adjustment.adjusted_action == "SELL" or \
               adjustment.adjusted_confidence != decision["confidence"]

    def test_disposition_effect_losers(self, engine, emotional_profile):
        """Test disposition effect on losing positions."""
        # Create a losing position
        position = PositionHistory(
            symbol="BTC/USDT",
            entry_price=50000.0,
            entry_time=datetime.utcnow() - timedelta(days=7),
            current_price=40000.0,  # 20% loss
            quantity=1.0
        )

        decision = {
            "action": "SELL",
            "symbol": "BTC/USDT",
            "confidence": 0.7,
            "size": 1.0
        }

        adjustment = engine.apply_biases(
            decision=decision,
            profile=emotional_profile,
            position_history=position
        )

        # Disposition effect should push toward holding losers
        assert BiasType.DISPOSITION in adjustment.biases_applied

    def test_loss_aversion(self, engine, emotional_profile):
        """Test loss aversion reduces confidence in losing positions."""
        position = PositionHistory(
            symbol="ETH/USDT",
            entry_price=3000.0,
            entry_time=datetime.utcnow() - timedelta(days=3),
            current_price=2500.0,  # Loss
            quantity=10.0
        )

        decision = {
            "action": "BUY",
            "symbol": "ETH/USDT",
            "confidence": 0.8,
            "size": 1.0
        }

        adjustment = engine.apply_biases(
            decision=decision,
            profile=emotional_profile,
            position_history=position
        )

        # Loss aversion should reduce confidence/size when in loss
        assert BiasType.LOSS_AVERSION in adjustment.biases_applied
        assert adjustment.adjusted_confidence <= decision["confidence"] or \
               adjustment.adjusted_size <= decision["size"]

    def test_lottery_preference(self, engine, emotional_profile):
        """Test lottery preference for high-volatility assets."""
        decision = {
            "action": "BUY",
            "symbol": "MEME/USDT",
            "confidence": 0.5,
            "size": 0.5
        }

        adjustment = engine.apply_biases(
            decision=decision,
            profile=emotional_profile,
            asset_volatility=0.8  # 80% annualized volatility
        )

        # Lottery preference should increase size/confidence for volatile assets
        assert BiasType.LOTTERY_PREFERENCE in adjustment.biases_applied
        assert adjustment.adjusted_size >= decision["size"]

    def test_overconfidence(self, engine, emotional_profile):
        """Test overconfidence inflates confidence."""
        decision = {
            "action": "BUY",
            "symbol": "BTC/USDT",
            "confidence": 0.6,
            "size": 1.0
        }

        adjustment = engine.apply_biases(
            decision=decision,
            profile=emotional_profile
        )

        # Overconfidence should inflate confidence
        assert BiasType.OVERCONFIDENCE in adjustment.biases_applied
        assert adjustment.adjusted_confidence > decision["confidence"]

    def test_herding_follows_crowd(self, engine, emotional_profile):
        """Test herding behavior follows market sentiment."""
        decision = {
            "action": "SELL",
            "symbol": "BTC/USDT",
            "confidence": 0.6,
            "size": 1.0
        }

        adjustment = engine.apply_biases(
            decision=decision,
            profile=emotional_profile,
            market_sentiment=0.8  # Strong bullish sentiment
        )

        # Herding should potentially flip action to follow crowd
        assert BiasType.HERDING in adjustment.biases_applied

    def test_contrarian_goes_against_crowd(self, engine):
        """Test contrarian behavior goes against sentiment."""
        contrarian_profile = engine.create_profile(template="contrarian")

        decision = {
            "action": "BUY",
            "symbol": "BTC/USDT",
            "confidence": 0.6,
            "size": 1.0
        }

        adjustment = engine.apply_biases(
            decision=decision,
            profile=contrarian_profile,
            market_sentiment=0.8  # Strong bullish sentiment
        )

        # Contrarian might switch or reduce confidence when following crowd
        assert BiasType.HERDING in adjustment.biases_applied

    def test_recency_bias(self, engine, emotional_profile):
        """Test recency bias affects confidence."""
        decision = {
            "action": "BUY",
            "symbol": "BTC/USDT",
            "confidence": 0.6,
            "size": 1.0
        }

        # Recent positive returns
        recent_returns = [0.02, 0.03, 0.01, 0.025, 0.015]  # Good recent performance

        adjustment = engine.apply_biases(
            decision=decision,
            profile=emotional_profile,
            recent_returns=recent_returns
        )

        # Good recent returns should boost buy confidence
        assert BiasType.RECENCY in adjustment.biases_applied

    def test_rational_profile_minimal_adjustment(self, engine, rational_profile):
        """Test that rational profile makes minimal adjustments."""
        decision = {
            "action": "BUY",
            "symbol": "BTC/USDT",
            "confidence": 0.7,
            "size": 1.0
        }

        adjustment = engine.apply_biases(
            decision=decision,
            profile=rational_profile,
            market_sentiment=0.5
        )

        # Rational profile should have smaller adjustments
        confidence_change = abs(adjustment.adjusted_confidence - decision["confidence"])
        size_change = abs(adjustment.adjusted_size - decision["size"])

        # Changes should be relatively small
        assert confidence_change < 0.3
        assert size_change < 0.5

    def test_anchoring_effect(self, engine, emotional_profile):
        """Test anchoring to reference prices."""
        engine.set_anchor_price("BTC/USDT", 45000.0)

        position = PositionHistory(
            symbol="BTC/USDT",
            entry_price=45000.0,
            entry_time=datetime.utcnow() - timedelta(days=30),
            current_price=55000.0,  # Above anchor
            quantity=1.0
        )

        decision = {
            "action": "BUY",
            "symbol": "BTC/USDT",
            "confidence": 0.7,
            "size": 1.0
        }

        adjustment = engine.apply_biases(
            decision=decision,
            profile=emotional_profile,
            position_history=position
        )

        # Anchoring should affect confidence when price is far from anchor
        assert BiasType.ANCHORING in adjustment.biases_applied

    def test_statistics_tracking(self, engine, emotional_profile):
        """Test bias application statistics."""
        # Apply biases multiple times
        for _ in range(5):
            engine.apply_biases(
                decision={"action": "BUY", "confidence": 0.5, "size": 1.0},
                profile=emotional_profile,
                market_sentiment=0.3
            )

        stats = engine.get_statistics()
        assert stats["total_adjustments"] == 5
        assert "bias_frequency" in stats


class TestProspectTheory:
    """Test Prospect Theory utility functions."""

    def test_gains_concave(self):
        """Test that gains have diminishing marginal utility."""
        v1 = calculate_prospect_theory_value(100)
        v2 = calculate_prospect_theory_value(200)

        # Second 100 should add less value than first
        assert v2 < v1 * 2

    def test_losses_steeper(self):
        """Test that losses loom larger than gains."""
        gain_value = calculate_prospect_theory_value(100)
        loss_value = calculate_prospect_theory_value(-100)

        # Loss should have larger magnitude
        assert abs(loss_value) > abs(gain_value)

    def test_reference_point(self):
        """Test that reference point matters."""
        # Gain of 50 from reference 0
        v1 = calculate_prospect_theory_value(50, reference=0)

        # Gain of 50 from reference 50 (same absolute outcome)
        v2 = calculate_prospect_theory_value(100, reference=50)

        # Should be similar
        assert abs(v1 - v2) < 0.1

    def test_probability_weighting_small_probs(self):
        """Test that small probabilities are overweighted."""
        # Objective probability
        p = 0.01

        # Weighted probability
        w = calculate_probability_weight(p)

        # Small probs should be overweighted
        assert w > p

    def test_probability_weighting_large_probs(self):
        """Test that large probabilities are underweighted."""
        # Objective probability
        p = 0.95

        # Weighted probability
        w = calculate_probability_weight(p)

        # Large probs should be underweighted
        assert w < p


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
