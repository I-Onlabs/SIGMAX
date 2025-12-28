"""
Behavioral Biases Module - Cognitive Bias Modeling for Trading Agents
Inspired by TwinMarket's behavioral finance simulation

Models key behavioral biases that affect investment decisions:
- Disposition Effect: Selling winners too early, holding losers too long
- Lottery Preference: Attraction to high-risk, high-reward assets
- Loss Aversion: Feeling losses ~2.5x stronger than equivalent gains
- Overconfidence: Overestimating prediction accuracy
- Anchoring: Fixating on reference prices
- Herding: Following crowd behavior
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import math
from loguru import logger


class BiasType(Enum):
    """Types of behavioral biases."""
    DISPOSITION = "disposition"
    LOTTERY_PREFERENCE = "lottery_preference"
    LOSS_AVERSION = "loss_aversion"
    OVERCONFIDENCE = "overconfidence"
    ANCHORING = "anchoring"
    HERDING = "herding"
    RECENCY = "recency"
    CONFIRMATION = "confirmation"


@dataclass
class BiasProfile:
    """Profile of an agent's behavioral biases."""
    disposition_strength: float = 0.5  # 0-1, tendency to sell winners/hold losers
    lottery_attraction: float = 0.3  # 0-1, attraction to high-variance assets
    loss_aversion_ratio: float = 2.5  # Kahneman's typical value
    overconfidence_level: float = 0.4  # 0-1, overestimation of ability
    anchoring_weight: float = 0.5  # 0-1, how much to weight reference prices
    herding_susceptibility: float = 0.3  # 0-1, tendency to follow crowd
    recency_weight: float = 0.6  # 0-1, overweighting recent events
    confirmation_strength: float = 0.4  # 0-1, seeking confirming info

    def to_dict(self) -> Dict[str, float]:
        return {
            "disposition_strength": self.disposition_strength,
            "lottery_attraction": self.lottery_attraction,
            "loss_aversion_ratio": self.loss_aversion_ratio,
            "overconfidence_level": self.overconfidence_level,
            "anchoring_weight": self.anchoring_weight,
            "herding_susceptibility": self.herding_susceptibility,
            "recency_weight": self.recency_weight,
            "confirmation_strength": self.confirmation_strength
        }


@dataclass
class BiasAdjustment:
    """Result of applying behavioral biases to a decision."""
    original_action: str
    adjusted_action: str
    original_confidence: float
    adjusted_confidence: float
    original_size: float
    adjusted_size: float
    biases_applied: List[BiasType]
    adjustments: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_action": self.original_action,
            "adjusted_action": self.adjusted_action,
            "original_confidence": round(self.original_confidence, 3),
            "adjusted_confidence": round(self.adjusted_confidence, 3),
            "original_size": round(self.original_size, 4),
            "adjusted_size": round(self.adjusted_size, 4),
            "biases_applied": [b.value for b in self.biases_applied],
            "adjustments": self.adjustments,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class PositionHistory:
    """Track position history for bias calculations."""
    symbol: str
    entry_price: float
    entry_time: datetime
    current_price: float
    quantity: float
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0

    @property
    def pnl_percent(self) -> float:
        """Calculate P&L percentage."""
        if self.entry_price == 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price * 100

    @property
    def holding_days(self) -> float:
        """Days since entry."""
        return (datetime.utcnow() - self.entry_time).total_seconds() / 86400


class BehavioralBiasEngine:
    """
    Engine that applies behavioral biases to trading decisions.

    Usage:
        engine = BehavioralBiasEngine()
        profile = engine.create_profile("moderate")

        # Apply biases to a decision
        adjustment = engine.apply_biases(
            decision={"action": "SELL", "symbol": "AAPL", "confidence": 0.8},
            profile=profile,
            position_history=position,
            market_sentiment=0.6
        )
    """

    # Profile templates
    PROFILE_TEMPLATES = {
        "rational": BiasProfile(
            disposition_strength=0.1,
            lottery_attraction=0.1,
            loss_aversion_ratio=1.5,
            overconfidence_level=0.1,
            anchoring_weight=0.2,
            herding_susceptibility=0.1,
            recency_weight=0.3,
            confirmation_strength=0.1
        ),
        "moderate": BiasProfile(
            disposition_strength=0.4,
            lottery_attraction=0.3,
            loss_aversion_ratio=2.0,
            overconfidence_level=0.3,
            anchoring_weight=0.4,
            herding_susceptibility=0.3,
            recency_weight=0.5,
            confirmation_strength=0.3
        ),
        "emotional": BiasProfile(
            disposition_strength=0.7,
            lottery_attraction=0.5,
            loss_aversion_ratio=3.0,
            overconfidence_level=0.6,
            anchoring_weight=0.6,
            herding_susceptibility=0.6,
            recency_weight=0.7,
            confirmation_strength=0.5
        ),
        "retail_typical": BiasProfile(
            disposition_strength=0.6,
            lottery_attraction=0.6,
            loss_aversion_ratio=2.5,
            overconfidence_level=0.5,
            anchoring_weight=0.5,
            herding_susceptibility=0.5,
            recency_weight=0.6,
            confirmation_strength=0.4
        ),
        "contrarian": BiasProfile(
            disposition_strength=0.2,
            lottery_attraction=0.2,
            loss_aversion_ratio=1.8,
            overconfidence_level=0.4,
            anchoring_weight=0.3,
            herding_susceptibility=-0.3,  # Negative = contrarian
            recency_weight=0.3,
            confirmation_strength=0.2
        )
    }

    def __init__(
        self,
        enable_logging: bool = True,
        randomize_biases: bool = True,
        noise_factor: float = 0.1
    ):
        """
        Initialize behavioral bias engine.

        Args:
            enable_logging: Log bias applications
            randomize_biases: Add noise to bias calculations
            noise_factor: Amount of randomness (0-1)
        """
        self.enable_logging = enable_logging
        self.randomize_biases = randomize_biases
        self.noise_factor = noise_factor

        self._adjustment_history: List[BiasAdjustment] = []
        self._anchor_prices: Dict[str, float] = {}

    def create_profile(
        self,
        template: str = "moderate",
        custom_biases: Optional[Dict[str, float]] = None
    ) -> BiasProfile:
        """
        Create a bias profile from template or custom values.

        Args:
            template: Profile template name
            custom_biases: Override specific bias values

        Returns:
            BiasProfile
        """
        if template not in self.PROFILE_TEMPLATES:
            template = "moderate"

        base_profile = self.PROFILE_TEMPLATES[template]

        if custom_biases:
            profile_dict = base_profile.to_dict()
            profile_dict.update(custom_biases)
            return BiasProfile(**profile_dict)

        return BiasProfile(**base_profile.to_dict())

    def apply_biases(
        self,
        decision: Dict[str, Any],
        profile: BiasProfile,
        position_history: Optional[PositionHistory] = None,
        market_sentiment: Optional[float] = None,
        recent_returns: Optional[List[float]] = None,
        asset_volatility: Optional[float] = None
    ) -> BiasAdjustment:
        """
        Apply behavioral biases to a trading decision.

        Args:
            decision: Trading decision with action, symbol, confidence, size
            profile: Bias profile to apply
            position_history: Current position info if exists
            market_sentiment: Overall market sentiment (-1 to 1)
            recent_returns: Recent return history for recency bias
            asset_volatility: Asset volatility for lottery preference

        Returns:
            BiasAdjustment with modified decision
        """
        original_action = decision.get("action", "HOLD")
        original_confidence = decision.get("confidence", 0.5)
        original_size = decision.get("size", 1.0)

        adjusted_action = original_action
        adjusted_confidence = original_confidence
        adjusted_size = original_size
        biases_applied = []
        adjustments = {}

        # 1. Disposition Effect
        if position_history and profile.disposition_strength > 0:
            disp_result = self._apply_disposition_effect(
                action=adjusted_action,
                position=position_history,
                strength=profile.disposition_strength
            )
            if disp_result["modified"]:
                adjusted_action = disp_result["action"]
                adjusted_confidence *= disp_result["confidence_mult"]
                biases_applied.append(BiasType.DISPOSITION)
                adjustments["disposition"] = disp_result

        # 2. Loss Aversion
        if position_history and profile.loss_aversion_ratio > 1.0:
            loss_result = self._apply_loss_aversion(
                action=adjusted_action,
                confidence=adjusted_confidence,
                position=position_history,
                ratio=profile.loss_aversion_ratio
            )
            if loss_result["modified"]:
                adjusted_confidence = loss_result["confidence"]
                adjusted_size *= loss_result["size_mult"]
                biases_applied.append(BiasType.LOSS_AVERSION)
                adjustments["loss_aversion"] = loss_result

        # 3. Lottery Preference
        if asset_volatility and profile.lottery_attraction > 0:
            lottery_result = self._apply_lottery_preference(
                size=adjusted_size,
                confidence=adjusted_confidence,
                volatility=asset_volatility,
                attraction=profile.lottery_attraction
            )
            if lottery_result["modified"]:
                adjusted_size = lottery_result["size"]
                adjusted_confidence = lottery_result["confidence"]
                biases_applied.append(BiasType.LOTTERY_PREFERENCE)
                adjustments["lottery"] = lottery_result

        # 4. Overconfidence
        if profile.overconfidence_level > 0:
            overconf_result = self._apply_overconfidence(
                confidence=adjusted_confidence,
                size=adjusted_size,
                level=profile.overconfidence_level
            )
            adjusted_confidence = overconf_result["confidence"]
            adjusted_size = overconf_result["size"]
            biases_applied.append(BiasType.OVERCONFIDENCE)
            adjustments["overconfidence"] = overconf_result

        # 5. Anchoring
        symbol = decision.get("symbol", "")
        if symbol and profile.anchoring_weight > 0:
            anchor_result = self._apply_anchoring(
                symbol=symbol,
                current_price=position_history.current_price if position_history else None,
                action=adjusted_action,
                confidence=adjusted_confidence,
                weight=profile.anchoring_weight
            )
            if anchor_result["modified"]:
                adjusted_confidence *= anchor_result["confidence_mult"]
                biases_applied.append(BiasType.ANCHORING)
                adjustments["anchoring"] = anchor_result

        # 6. Herding
        if market_sentiment is not None and profile.herding_susceptibility != 0:
            herd_result = self._apply_herding(
                action=adjusted_action,
                confidence=adjusted_confidence,
                market_sentiment=market_sentiment,
                susceptibility=profile.herding_susceptibility
            )
            if herd_result["modified"]:
                adjusted_action = herd_result["action"]
                adjusted_confidence = herd_result["confidence"]
                biases_applied.append(BiasType.HERDING)
                adjustments["herding"] = herd_result

        # 7. Recency Bias
        if recent_returns and profile.recency_weight > 0:
            recency_result = self._apply_recency_bias(
                action=adjusted_action,
                confidence=adjusted_confidence,
                recent_returns=recent_returns,
                weight=profile.recency_weight
            )
            if recency_result["modified"]:
                adjusted_confidence = recency_result["confidence"]
                biases_applied.append(BiasType.RECENCY)
                adjustments["recency"] = recency_result

        # Add noise if enabled
        if self.randomize_biases:
            noise = (random.random() - 0.5) * 2 * self.noise_factor
            adjusted_confidence = max(0.1, min(1.0, adjusted_confidence + noise * 0.1))
            adjusted_size = max(0.1, adjusted_size * (1 + noise * 0.1))

        # Clamp values
        adjusted_confidence = max(0.1, min(1.0, adjusted_confidence))
        adjusted_size = max(0.0, adjusted_size)

        adjustment = BiasAdjustment(
            original_action=original_action,
            adjusted_action=adjusted_action,
            original_confidence=original_confidence,
            adjusted_confidence=adjusted_confidence,
            original_size=original_size,
            adjusted_size=adjusted_size,
            biases_applied=biases_applied,
            adjustments=adjustments
        )

        self._adjustment_history.append(adjustment)

        if self.enable_logging and biases_applied:
            logger.debug(
                f"Applied biases: {[b.value for b in biases_applied]} "
                f"Action: {original_action}->{adjusted_action}, "
                f"Conf: {original_confidence:.2f}->{adjusted_confidence:.2f}"
            )

        return adjustment

    def _apply_disposition_effect(
        self,
        action: str,
        position: PositionHistory,
        strength: float
    ) -> Dict[str, Any]:
        """
        Apply disposition effect bias.

        Winners: Increased urge to sell (realize gains)
        Losers: Increased urge to hold (avoid realizing loss)
        """
        pnl_pct = position.pnl_percent
        modified = False
        confidence_mult = 1.0

        if pnl_pct > 5.0:  # In profit
            # Increased likelihood to sell winners
            if action == "HOLD":
                # Bias toward selling
                if random.random() < strength * min(pnl_pct / 20, 1.0):
                    action = "SELL"
                    confidence_mult = 0.7 + 0.3 * strength
                    modified = True
            elif action == "SELL":
                # Reinforce sell decision
                confidence_mult = 1.0 + 0.2 * strength
                modified = True

        elif pnl_pct < -5.0:  # In loss
            # Increased likelihood to hold losers
            if action == "SELL":
                # Bias toward holding
                if random.random() < strength * min(abs(pnl_pct) / 20, 1.0):
                    action = "HOLD"
                    confidence_mult = 0.6
                    modified = True
            elif action == "HOLD":
                # Reinforce hold decision
                confidence_mult = 1.0 + 0.1 * strength
                modified = True

        return {
            "modified": modified,
            "action": action,
            "confidence_mult": confidence_mult,
            "pnl_percent": round(pnl_pct, 2),
            "disposition_triggered": pnl_pct > 5.0 or pnl_pct < -5.0
        }

    def _apply_loss_aversion(
        self,
        action: str,
        confidence: float,
        position: PositionHistory,
        ratio: float
    ) -> Dict[str, Any]:
        """
        Apply loss aversion (losses felt ~2.5x stronger than gains).

        Affects position sizing and confidence based on P&L state.
        """
        pnl_pct = position.pnl_percent
        modified = False
        new_confidence = confidence
        size_mult = 1.0

        if pnl_pct < 0:
            # In loss - losses feel stronger
            loss_pain = abs(pnl_pct) * ratio / 100

            # Reduce confidence when in loss
            new_confidence = confidence * (1 - loss_pain * 0.3)

            # Reduce position sizing
            size_mult = 1 - min(loss_pain * 0.5, 0.5)
            modified = True

        elif pnl_pct > 0:
            # In profit - gains feel weaker (asymmetry)
            gain_joy = pnl_pct / 100 / ratio  # Divided by ratio, not multiplied

            # Slightly increase confidence
            new_confidence = confidence * (1 + gain_joy * 0.1)
            modified = True

        return {
            "modified": modified,
            "confidence": new_confidence,
            "size_mult": size_mult,
            "pain_factor": ratio,
            "pnl_percent": round(pnl_pct, 2)
        }

    def _apply_lottery_preference(
        self,
        size: float,
        confidence: float,
        volatility: float,
        attraction: float
    ) -> Dict[str, Any]:
        """
        Apply lottery preference (attraction to high-variance outcomes).

        High volatility assets get oversized positions despite low probability.
        """
        modified = False
        new_size = size
        new_confidence = confidence

        # High volatility triggers lottery effect
        if volatility > 0.3:  # > 30% annualized vol
            vol_factor = min((volatility - 0.3) / 0.5, 1.0)  # Normalize

            # Increase position size for lottery-like assets
            size_boost = 1 + attraction * vol_factor * 0.5
            new_size = size * size_boost

            # Overestimate chances of big win
            new_confidence = confidence * (1 + attraction * vol_factor * 0.3)
            modified = True

        return {
            "modified": modified,
            "size": new_size,
            "confidence": new_confidence,
            "volatility": round(volatility, 3),
            "lottery_boost": new_size / size if modified else 1.0
        }

    def _apply_overconfidence(
        self,
        confidence: float,
        size: float,
        level: float
    ) -> Dict[str, Any]:
        """
        Apply overconfidence bias.

        Overestimate prediction accuracy and increase position sizes.
        """
        # Inflate confidence
        confidence_boost = 1 + level * 0.3
        new_confidence = min(0.95, confidence * confidence_boost)

        # Increase position size
        size_boost = 1 + level * 0.2
        new_size = size * size_boost

        return {
            "confidence": new_confidence,
            "size": new_size,
            "confidence_inflation": round((new_confidence / confidence - 1) * 100, 1),
            "size_inflation": round((new_size / size - 1) * 100, 1)
        }

    def _apply_anchoring(
        self,
        symbol: str,
        current_price: Optional[float],
        action: str,
        confidence: float,
        weight: float
    ) -> Dict[str, Any]:
        """
        Apply anchoring bias (fixating on reference prices).

        Decisions influenced by arbitrary anchor prices (e.g., 52-week high).
        """
        modified = False
        confidence_mult = 1.0

        if current_price is None:
            return {"modified": False}

        # Set anchor if not exists
        if symbol not in self._anchor_prices:
            self._anchor_prices[symbol] = current_price

        anchor = self._anchor_prices[symbol]
        deviation = (current_price - anchor) / anchor

        if abs(deviation) > 0.1:  # >10% from anchor
            if deviation > 0:  # Price above anchor
                if action == "BUY":
                    # Reluctance to buy above anchor
                    confidence_mult = 1 - weight * min(deviation, 0.3)
                    modified = True
                elif action == "SELL":
                    # More willing to sell above anchor
                    confidence_mult = 1 + weight * 0.2
                    modified = True
            else:  # Price below anchor
                if action == "BUY":
                    # Anchoring makes it seem "cheap"
                    confidence_mult = 1 + weight * min(abs(deviation), 0.3)
                    modified = True
                elif action == "SELL":
                    # Reluctance to sell below anchor
                    confidence_mult = 1 - weight * 0.2
                    modified = True

        return {
            "modified": modified,
            "confidence_mult": confidence_mult,
            "anchor_price": round(anchor, 2),
            "current_price": round(current_price, 2),
            "deviation_percent": round(deviation * 100, 2)
        }

    def _apply_herding(
        self,
        action: str,
        confidence: float,
        market_sentiment: float,
        susceptibility: float
    ) -> Dict[str, Any]:
        """
        Apply herding bias (following the crowd).

        Positive susceptibility = follow crowd
        Negative susceptibility = contrarian
        """
        modified = False
        new_action = action
        new_confidence = confidence

        # Strong market sentiment
        if abs(market_sentiment) > 0.3:
            crowd_direction = "BUY" if market_sentiment > 0 else "SELL"

            if susceptibility > 0:  # Herd follower
                if action != crowd_direction:
                    # Consider switching to crowd direction
                    switch_prob = abs(susceptibility) * abs(market_sentiment)
                    if random.random() < switch_prob:
                        new_action = crowd_direction
                        new_confidence = confidence * 0.8
                        modified = True
                else:
                    # Reinforce crowd alignment
                    new_confidence = confidence * (1 + susceptibility * 0.2)
                    modified = True

            elif susceptibility < 0:  # Contrarian
                if action == crowd_direction:
                    # Consider going against crowd
                    contra_prob = abs(susceptibility) * abs(market_sentiment)
                    if random.random() < contra_prob:
                        new_action = "BUY" if crowd_direction == "SELL" else "SELL"
                        new_confidence = confidence * 0.7
                        modified = True

        return {
            "modified": modified,
            "action": new_action,
            "confidence": new_confidence,
            "market_sentiment": round(market_sentiment, 2),
            "crowd_direction": "BUY" if market_sentiment > 0 else "SELL",
            "behavior": "follower" if susceptibility > 0 else "contrarian"
        }

    def _apply_recency_bias(
        self,
        action: str,
        confidence: float,
        recent_returns: List[float],
        weight: float
    ) -> Dict[str, Any]:
        """
        Apply recency bias (overweighting recent events).

        Recent returns disproportionately influence confidence.
        """
        if not recent_returns:
            return {"modified": False}

        modified = False
        new_confidence = confidence

        # Weight recent returns more heavily
        n = len(recent_returns)
        weights = [math.exp(-i / (n * (1 - weight + 0.1))) for i in range(n)]
        weight_sum = sum(weights)
        weights = [w / weight_sum for w in weights]

        weighted_return = sum(r * w for r, w in zip(recent_returns, weights))
        simple_avg = sum(recent_returns) / n

        # Recency-weighted differs from simple average
        recency_signal = weighted_return - simple_avg

        if abs(recency_signal) > 0.01:  # 1% difference
            if recency_signal > 0:  # Recent good
                if action == "BUY":
                    new_confidence = confidence * (1 + weight * recency_signal * 10)
                    modified = True
                elif action == "SELL":
                    new_confidence = confidence * (1 - weight * recency_signal * 5)
                    modified = True
            else:  # Recent bad
                if action == "SELL":
                    new_confidence = confidence * (1 + weight * abs(recency_signal) * 10)
                    modified = True
                elif action == "BUY":
                    new_confidence = confidence * (1 - weight * abs(recency_signal) * 5)
                    modified = True

        return {
            "modified": modified,
            "confidence": max(0.1, min(0.99, new_confidence)),
            "weighted_return": round(weighted_return * 100, 2),
            "simple_avg": round(simple_avg * 100, 2),
            "recency_signal": round(recency_signal * 100, 3)
        }

    def set_anchor_price(self, symbol: str, price: float):
        """Manually set an anchor price for a symbol."""
        self._anchor_prices[symbol] = price

    def clear_anchor(self, symbol: str):
        """Clear anchor price for a symbol."""
        if symbol in self._anchor_prices:
            del self._anchor_prices[symbol]

    def get_statistics(self) -> Dict[str, Any]:
        """Get bias application statistics."""
        if not self._adjustment_history:
            return {"total_adjustments": 0}

        bias_counts = {}
        action_changes = 0
        avg_confidence_change = 0
        avg_size_change = 0

        for adj in self._adjustment_history:
            for bias in adj.biases_applied:
                bias_counts[bias.value] = bias_counts.get(bias.value, 0) + 1

            if adj.original_action != adj.adjusted_action:
                action_changes += 1

            avg_confidence_change += adj.adjusted_confidence - adj.original_confidence
            avg_size_change += adj.adjusted_size - adj.original_size

        n = len(self._adjustment_history)

        return {
            "total_adjustments": n,
            "bias_frequency": bias_counts,
            "action_changes": action_changes,
            "action_change_rate": round(action_changes / n, 3),
            "avg_confidence_change": round(avg_confidence_change / n, 4),
            "avg_size_change": round(avg_size_change / n, 4)
        }

    def clear_history(self):
        """Clear adjustment history."""
        self._adjustment_history.clear()


def calculate_prospect_theory_value(
    outcome: float,
    reference: float = 0.0,
    alpha: float = 0.88,
    beta: float = 0.88,
    lambda_: float = 2.25
) -> float:
    """
    Calculate value using Kahneman & Tversky's Prospect Theory.

    v(x) = x^alpha for gains
    v(x) = -lambda * |x|^beta for losses

    Args:
        outcome: The outcome amount
        reference: Reference point (default 0)
        alpha: Diminishing sensitivity for gains (default 0.88)
        beta: Diminishing sensitivity for losses (default 0.88)
        lambda_: Loss aversion coefficient (default 2.25)

    Returns:
        Prospect theory value
    """
    x = outcome - reference

    if x >= 0:
        return math.pow(x, alpha)
    else:
        return -lambda_ * math.pow(abs(x), beta)


def calculate_probability_weight(
    p: float,
    gamma: float = 0.61
) -> float:
    """
    Calculate probability weighting function from Prospect Theory.

    w(p) = p^gamma / (p^gamma + (1-p)^gamma)^(1/gamma)

    This overweights small probabilities and underweights large ones.

    Args:
        p: Objective probability (0-1)
        gamma: Curvature parameter (default 0.61)

    Returns:
        Weighted probability
    """
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0

    p_gamma = math.pow(p, gamma)
    one_minus_p_gamma = math.pow(1 - p, gamma)

    denominator = math.pow(p_gamma + one_minus_p_gamma, 1 / gamma)

    if denominator == 0:
        return p

    return p_gamma / denominator
