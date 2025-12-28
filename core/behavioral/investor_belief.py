"""
Investor Belief System - Personality-Based Trading Agents
Inspired by TwinMarket's behavioral finance modeling

Features:
- Personalized investor personas
- Market outlook/belief generation
- Attitude-based decision modification
- Self-assessment and confidence calibration
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random
from loguru import logger


class MarketAttitude(Enum):
    """Investor attitude towards market."""
    VERY_BULLISH = "very_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    VERY_BEARISH = "very_bearish"


class RiskTolerance(Enum):
    """Investor risk tolerance."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"


class InvestmentStyle(Enum):
    """Investment style preference."""
    VALUE = "value"
    GROWTH = "growth"
    MOMENTUM = "momentum"
    CONTRARIAN = "contrarian"
    QUANTITATIVE = "quantitative"
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"


class TimeHorizon(Enum):
    """Investment time horizon."""
    SCALPER = "scalper"  # Minutes
    DAY_TRADER = "day_trader"  # Hours
    SWING_TRADER = "swing_trader"  # Days-weeks
    POSITION_TRADER = "position_trader"  # Weeks-months
    INVESTOR = "investor"  # Months-years


@dataclass
class InvestorPersona:
    """Complete investor persona/personality."""
    name: str
    attitude: MarketAttitude
    risk_tolerance: RiskTolerance
    style: InvestmentStyle
    time_horizon: TimeHorizon

    # Behavioral traits (0-1)
    overconfidence: float = 0.5
    loss_aversion: float = 0.5
    herd_following: float = 0.5
    news_sensitivity: float = 0.5

    # Experience and track record
    experience_years: int = 3
    historical_win_rate: float = 0.5
    historical_return: float = 0.0

    # Current state
    current_confidence: float = 0.5
    market_belief: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "attitude": self.attitude.value,
            "risk_tolerance": self.risk_tolerance.value,
            "style": self.style.value,
            "time_horizon": self.time_horizon.value,
            "traits": {
                "overconfidence": self.overconfidence,
                "loss_aversion": self.loss_aversion,
                "herd_following": self.herd_following,
                "news_sensitivity": self.news_sensitivity
            },
            "experience_years": self.experience_years,
            "historical_win_rate": self.historical_win_rate,
            "current_confidence": self.current_confidence
        }


@dataclass
class MarketBelief:
    """Agent's belief about market conditions."""
    direction: MarketAttitude  # Expected market direction
    confidence: float  # How confident in this belief
    time_frame: str  # When this belief applies
    reasoning: str  # Why agent believes this
    key_factors: List[str]  # Main factors driving belief
    risk_assessment: str  # Perceived market risk
    self_assessment: str  # Self-evaluation of trading ability
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction.value,
            "confidence": round(self.confidence, 3),
            "time_frame": self.time_frame,
            "reasoning": self.reasoning,
            "key_factors": self.key_factors,
            "risk_assessment": self.risk_assessment,
            "self_assessment": self.self_assessment,
            "timestamp": self.timestamp.isoformat()
        }


class InvestorBeliefSystem:
    """
    System for managing investor beliefs and personalities.

    Usage:
        belief_system = InvestorBeliefSystem()

        # Create investor persona
        persona = belief_system.create_persona(
            name="Aggressive Growth Trader",
            attitude=MarketAttitude.BULLISH,
            style=InvestmentStyle.MOMENTUM
        )

        # Generate market belief
        belief = belief_system.generate_belief(
            persona,
            market_data={...},
            news=[...]
        )

        # Modify decision based on belief
        modified = belief_system.apply_belief_to_decision(
            decision={"action": "buy", "confidence": 0.7},
            belief=belief
        )
    """

    # Persona templates
    PERSONA_TEMPLATES = {
        "conservative_value": {
            "attitude": MarketAttitude.NEUTRAL,
            "risk_tolerance": RiskTolerance.CONSERVATIVE,
            "style": InvestmentStyle.VALUE,
            "time_horizon": TimeHorizon.INVESTOR,
            "overconfidence": 0.3,
            "loss_aversion": 0.8,
            "herd_following": 0.2,
            "news_sensitivity": 0.4
        },
        "aggressive_momentum": {
            "attitude": MarketAttitude.BULLISH,
            "risk_tolerance": RiskTolerance.AGGRESSIVE,
            "style": InvestmentStyle.MOMENTUM,
            "time_horizon": TimeHorizon.SWING_TRADER,
            "overconfidence": 0.7,
            "loss_aversion": 0.3,
            "herd_following": 0.6,
            "news_sensitivity": 0.7
        },
        "quant_neutral": {
            "attitude": MarketAttitude.NEUTRAL,
            "risk_tolerance": RiskTolerance.MODERATE,
            "style": InvestmentStyle.QUANTITATIVE,
            "time_horizon": TimeHorizon.DAY_TRADER,
            "overconfidence": 0.4,
            "loss_aversion": 0.5,
            "herd_following": 0.1,
            "news_sensitivity": 0.3
        },
        "contrarian_bear": {
            "attitude": MarketAttitude.BEARISH,
            "risk_tolerance": RiskTolerance.MODERATE,
            "style": InvestmentStyle.CONTRARIAN,
            "time_horizon": TimeHorizon.POSITION_TRADER,
            "overconfidence": 0.5,
            "loss_aversion": 0.6,
            "herd_following": 0.1,
            "news_sensitivity": 0.5
        },
        "news_driven": {
            "attitude": MarketAttitude.NEUTRAL,
            "risk_tolerance": RiskTolerance.AGGRESSIVE,
            "style": InvestmentStyle.MOMENTUM,
            "time_horizon": TimeHorizon.DAY_TRADER,
            "overconfidence": 0.6,
            "loss_aversion": 0.4,
            "herd_following": 0.8,
            "news_sensitivity": 0.9
        }
    }

    def __init__(self, base_attitude_distribution: Dict[MarketAttitude, float] = None):
        """
        Initialize belief system.

        Args:
            base_attitude_distribution: Probability distribution for random attitudes
        """
        self.attitude_distribution = base_attitude_distribution or {
            MarketAttitude.VERY_BULLISH: 0.1,
            MarketAttitude.BULLISH: 0.25,
            MarketAttitude.NEUTRAL: 0.3,
            MarketAttitude.BEARISH: 0.25,
            MarketAttitude.VERY_BEARISH: 0.1
        }

        self._personas: Dict[str, InvestorPersona] = {}
        self._beliefs: Dict[str, MarketBelief] = {}

    def create_persona(
        self,
        name: str,
        template: str = None,
        attitude: MarketAttitude = None,
        risk_tolerance: RiskTolerance = None,
        style: InvestmentStyle = None,
        time_horizon: TimeHorizon = None,
        **kwargs
    ) -> InvestorPersona:
        """
        Create an investor persona.

        Args:
            name: Persona name
            template: Use predefined template
            attitude: Market attitude override
            risk_tolerance: Risk tolerance override
            style: Investment style override
            time_horizon: Time horizon override
            **kwargs: Additional trait overrides

        Returns:
            Created InvestorPersona
        """
        # Start with template if provided
        if template and template in self.PERSONA_TEMPLATES:
            base = dict(self.PERSONA_TEMPLATES[template])
        else:
            base = {}

        # Apply overrides
        persona = InvestorPersona(
            name=name,
            attitude=attitude or base.get("attitude", self._random_attitude()),
            risk_tolerance=risk_tolerance or base.get("risk_tolerance", RiskTolerance.MODERATE),
            style=style or base.get("style", InvestmentStyle.MOMENTUM),
            time_horizon=time_horizon or base.get("time_horizon", TimeHorizon.SWING_TRADER),
            overconfidence=kwargs.get("overconfidence", base.get("overconfidence", 0.5)),
            loss_aversion=kwargs.get("loss_aversion", base.get("loss_aversion", 0.5)),
            herd_following=kwargs.get("herd_following", base.get("herd_following", 0.5)),
            news_sensitivity=kwargs.get("news_sensitivity", base.get("news_sensitivity", 0.5)),
            experience_years=kwargs.get("experience_years", 3),
            historical_win_rate=kwargs.get("historical_win_rate", 0.5)
        )

        self._personas[name] = persona
        logger.debug(f"Created persona: {name} ({persona.style.value})")

        return persona

    def create_random_persona(self, name: str = None) -> InvestorPersona:
        """Create a persona with randomized traits."""
        name = name or f"Agent_{random.randint(1000, 9999)}"

        return self.create_persona(
            name=name,
            attitude=self._random_attitude(),
            risk_tolerance=random.choice(list(RiskTolerance)),
            style=random.choice(list(InvestmentStyle)),
            time_horizon=random.choice(list(TimeHorizon)),
            overconfidence=random.uniform(0.2, 0.8),
            loss_aversion=random.uniform(0.2, 0.8),
            herd_following=random.uniform(0.1, 0.7),
            news_sensitivity=random.uniform(0.2, 0.8)
        )

    def _random_attitude(self) -> MarketAttitude:
        """Generate random attitude based on distribution."""
        attitudes = list(self.attitude_distribution.keys())
        weights = list(self.attitude_distribution.values())
        return random.choices(attitudes, weights=weights, k=1)[0]

    def generate_belief(
        self,
        persona: InvestorPersona,
        market_data: Dict[str, Any] = None,
        news_items: List[str] = None,
        social_sentiment: float = None
    ) -> MarketBelief:
        """
        Generate market belief based on persona and inputs.

        Args:
            persona: Investor persona
            market_data: Current market data
            news_items: Recent news headlines
            social_sentiment: Social media sentiment (-1 to 1)

        Returns:
            Generated MarketBelief
        """
        market_data = market_data or {}
        news_items = news_items or []

        # Base direction from attitude
        direction = persona.attitude

        # Adjust based on market data
        if market_data:
            direction = self._adjust_for_market(direction, market_data, persona)

        # Adjust based on news (if sensitive)
        if news_items and persona.news_sensitivity > 0.5:
            direction = self._adjust_for_news(direction, news_items, persona)

        # Adjust based on social sentiment (herd following)
        if social_sentiment is not None and persona.herd_following > 0.5:
            direction = self._adjust_for_sentiment(direction, social_sentiment, persona)

        # Calculate confidence
        confidence = self._calculate_belief_confidence(persona, market_data)

        # Generate reasoning
        reasoning = self._generate_reasoning(persona, direction, market_data, news_items)

        # Key factors
        key_factors = self._identify_key_factors(persona, market_data, news_items)

        # Risk assessment
        risk_assessment = self._assess_risk(persona, market_data)

        # Self assessment
        self_assessment = self._generate_self_assessment(persona)

        belief = MarketBelief(
            direction=direction,
            confidence=confidence,
            time_frame=self._get_time_frame(persona),
            reasoning=reasoning,
            key_factors=key_factors,
            risk_assessment=risk_assessment,
            self_assessment=self_assessment
        )

        self._beliefs[persona.name] = belief

        return belief

    def _adjust_for_market(
        self,
        base: MarketAttitude,
        market_data: Dict[str, Any],
        persona: InvestorPersona
    ) -> MarketAttitude:
        """Adjust attitude based on market data."""
        # Get recent price change
        price_change = market_data.get("price_change_pct", 0)

        # Style-based adjustment
        if persona.style == InvestmentStyle.MOMENTUM:
            # Momentum follows trend
            if price_change > 5:
                return self._shift_attitude(base, 1)  # More bullish
            elif price_change < -5:
                return self._shift_attitude(base, -1)  # More bearish

        elif persona.style == InvestmentStyle.CONTRARIAN:
            # Contrarian goes against trend
            if price_change > 5:
                return self._shift_attitude(base, -1)  # More bearish
            elif price_change < -5:
                return self._shift_attitude(base, 1)  # More bullish

        return base

    def _adjust_for_news(
        self,
        base: MarketAttitude,
        news_items: List[str],
        persona: InvestorPersona
    ) -> MarketAttitude:
        """Adjust attitude based on news sentiment."""
        # Simple sentiment analysis
        bullish_words = ["surge", "gain", "rise", "bullish", "growth", "profit"]
        bearish_words = ["crash", "fall", "drop", "bearish", "loss", "decline"]

        combined = " ".join(news_items).lower()

        bull_score = sum(1 for w in bullish_words if w in combined)
        bear_score = sum(1 for w in bearish_words if w in combined)

        sentiment = (bull_score - bear_score) * persona.news_sensitivity

        if sentiment > 1:
            return self._shift_attitude(base, 1)
        elif sentiment < -1:
            return self._shift_attitude(base, -1)

        return base

    def _adjust_for_sentiment(
        self,
        base: MarketAttitude,
        sentiment: float,
        persona: InvestorPersona
    ) -> MarketAttitude:
        """Adjust attitude based on social sentiment."""
        adjustment = sentiment * persona.herd_following

        if adjustment > 0.3:
            return self._shift_attitude(base, 1)
        elif adjustment < -0.3:
            return self._shift_attitude(base, -1)

        return base

    def _shift_attitude(self, attitude: MarketAttitude, shift: int) -> MarketAttitude:
        """Shift attitude by N levels."""
        order = [
            MarketAttitude.VERY_BEARISH,
            MarketAttitude.BEARISH,
            MarketAttitude.NEUTRAL,
            MarketAttitude.BULLISH,
            MarketAttitude.VERY_BULLISH
        ]

        current_idx = order.index(attitude)
        new_idx = max(0, min(len(order) - 1, current_idx + shift))

        return order[new_idx]

    def _calculate_belief_confidence(
        self,
        persona: InvestorPersona,
        market_data: Dict[str, Any]
    ) -> float:
        """Calculate confidence in belief."""
        # Base from overconfidence trait
        base_conf = 0.5 + (persona.overconfidence - 0.5) * 0.3

        # Adjust for experience
        exp_adj = min(persona.experience_years / 10, 0.2)

        # Adjust for historical performance
        perf_adj = (persona.historical_win_rate - 0.5) * 0.2

        confidence = base_conf + exp_adj + perf_adj

        return max(0.1, min(0.95, confidence))

    def _generate_reasoning(
        self,
        persona: InvestorPersona,
        direction: MarketAttitude,
        market_data: Dict[str, Any],
        news_items: List[str]
    ) -> str:
        """Generate reasoning text for belief."""
        style_reasons = {
            InvestmentStyle.MOMENTUM: "following the current market trend",
            InvestmentStyle.CONTRARIAN: "going against the crowd sentiment",
            InvestmentStyle.VALUE: "based on fundamental valuation analysis",
            InvestmentStyle.GROWTH: "focusing on growth potential",
            InvestmentStyle.QUANTITATIVE: "based on statistical analysis",
            InvestmentStyle.TECHNICAL: "based on technical chart patterns",
            InvestmentStyle.FUNDAMENTAL: "considering economic fundamentals"
        }

        direction_text = {
            MarketAttitude.VERY_BULLISH: "strongly positive",
            MarketAttitude.BULLISH: "cautiously optimistic",
            MarketAttitude.NEUTRAL: "balanced and uncertain",
            MarketAttitude.BEARISH: "cautiously pessimistic",
            MarketAttitude.VERY_BEARISH: "strongly negative"
        }

        return (
            f"My outlook is {direction_text[direction]}, "
            f"{style_reasons.get(persona.style, 'based on my analysis')}. "
            f"With {persona.experience_years} years of experience and a "
            f"{persona.historical_win_rate*100:.0f}% historical win rate, "
            f"I maintain this view with measured confidence."
        )

    def _identify_key_factors(
        self,
        persona: InvestorPersona,
        market_data: Dict[str, Any],
        news_items: List[str]
    ) -> List[str]:
        """Identify key factors driving belief."""
        factors = []

        if persona.style in [InvestmentStyle.TECHNICAL, InvestmentStyle.MOMENTUM]:
            factors.append("Price trends and momentum indicators")

        if persona.style in [InvestmentStyle.VALUE, InvestmentStyle.FUNDAMENTAL]:
            factors.append("Fundamental valuation metrics")

        if persona.news_sensitivity > 0.5 and news_items:
            factors.append("Recent market news and events")

        if persona.herd_following > 0.5:
            factors.append("Market sentiment and social signals")

        if market_data.get("volatility"):
            factors.append("Current market volatility levels")

        if not factors:
            factors.append("Overall market conditions")

        return factors[:4]

    def _assess_risk(
        self,
        persona: InvestorPersona,
        market_data: Dict[str, Any]
    ) -> str:
        """Assess market risk from persona perspective."""
        risk_views = {
            RiskTolerance.CONSERVATIVE: "I see elevated risks and prefer capital preservation.",
            RiskTolerance.MODERATE: "I see moderate risks that require careful position sizing.",
            RiskTolerance.AGGRESSIVE: "I see acceptable risks with potential for strong returns.",
            RiskTolerance.VERY_AGGRESSIVE: "I embrace volatility as opportunity for gains."
        }

        return risk_views.get(persona.risk_tolerance, "Risk assessment in progress.")

    def _generate_self_assessment(self, persona: InvestorPersona) -> str:
        """Generate self-assessment text."""
        if persona.historical_win_rate > 0.6:
            performance = "strong track record"
        elif persona.historical_win_rate > 0.5:
            performance = "slightly above average results"
        else:
            performance = "room for improvement"

        overconf_adj = ""
        if persona.overconfidence > 0.7:
            overconf_adj = " though I may sometimes be overconfident in my calls"
        elif persona.overconfidence < 0.3:
            overconf_adj = " and I maintain conservative expectations"

        return (
            f"Based on my experience, I have a {performance}{overconf_adj}. "
            f"My {persona.style.value} approach suits my {persona.time_horizon.value} horizon."
        )

    def _get_time_frame(self, persona: InvestorPersona) -> str:
        """Get time frame description."""
        frames = {
            TimeHorizon.SCALPER: "next few minutes to hours",
            TimeHorizon.DAY_TRADER: "next 1-2 days",
            TimeHorizon.SWING_TRADER: "next 1-2 weeks",
            TimeHorizon.POSITION_TRADER: "next 1-3 months",
            TimeHorizon.INVESTOR: "next 6-12 months"
        }
        return frames.get(persona.time_horizon, "short-term")

    def apply_belief_to_decision(
        self,
        decision: Dict[str, Any],
        belief: MarketBelief
    ) -> Dict[str, Any]:
        """
        Modify a trading decision based on belief.

        Args:
            decision: Original decision {"action": str, "confidence": float, ...}
            belief: Current market belief

        Returns:
            Modified decision
        """
        modified = dict(decision)

        action = decision.get("action", "hold")
        confidence = decision.get("confidence", 0.5)

        # Adjust confidence based on belief alignment
        if action == "buy":
            if belief.direction in [MarketAttitude.BULLISH, MarketAttitude.VERY_BULLISH]:
                # Belief supports buy
                confidence = min(confidence * 1.2, 0.95)
            elif belief.direction in [MarketAttitude.BEARISH, MarketAttitude.VERY_BEARISH]:
                # Belief contradicts buy
                confidence = confidence * 0.7

        elif action == "sell":
            if belief.direction in [MarketAttitude.BEARISH, MarketAttitude.VERY_BEARISH]:
                # Belief supports sell
                confidence = min(confidence * 1.2, 0.95)
            elif belief.direction in [MarketAttitude.BULLISH, MarketAttitude.VERY_BULLISH]:
                # Belief contradicts sell
                confidence = confidence * 0.7

        # Apply belief confidence
        confidence = confidence * belief.confidence

        modified["confidence"] = round(confidence, 3)
        modified["belief_influence"] = {
            "direction": belief.direction.value,
            "belief_confidence": belief.confidence,
            "alignment": "supporting" if confidence > decision.get("confidence", 0) else "opposing"
        }

        return modified

    def get_persona(self, name: str) -> Optional[InvestorPersona]:
        """Get persona by name."""
        return self._personas.get(name)

    def get_belief(self, persona_name: str) -> Optional[MarketBelief]:
        """Get current belief for persona."""
        return self._beliefs.get(persona_name)

    def list_personas(self) -> List[str]:
        """List all persona names."""
        return list(self._personas.keys())

    def get_statistics(self) -> Dict[str, Any]:
        """Get belief system statistics."""
        if not self._personas:
            return {"total_personas": 0}

        attitude_dist = {}
        style_dist = {}
        risk_dist = {}

        for persona in self._personas.values():
            att = persona.attitude.value
            attitude_dist[att] = attitude_dist.get(att, 0) + 1

            sty = persona.style.value
            style_dist[sty] = style_dist.get(sty, 0) + 1

            risk = persona.risk_tolerance.value
            risk_dist[risk] = risk_dist.get(risk, 0) + 1

        return {
            "total_personas": len(self._personas),
            "attitude_distribution": attitude_dist,
            "style_distribution": style_dist,
            "risk_distribution": risk_dist
        }
