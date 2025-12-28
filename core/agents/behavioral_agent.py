"""
Behavioral Agent - TwinMarket-Inspired Agent with Personality and Biases
Integrates behavioral finance simulation into SIGMAX agents

Features:
- Investor personas with distinct market attitudes
- Behavioral biases that affect decision-making
- Social sentiment influence
- Realistic trading behavior simulation
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from loguru import logger

# Import behavioral modules
from ..behavioral import (
    InvestorPersona,
    InvestorBeliefSystem,
    MarketBelief,
    MarketAttitude,
    InvestmentStyle,
    RiskTolerance,
    BehavioralBiasEngine,
    BiasProfile,
    BiasAdjustment,
    PositionHistory,
    SocialSentimentNetwork,
    SocialAgent,
    SocialRole,
    SentimentType,
    FearGreedIndex
)


@dataclass
class BehavioralDecision:
    """A decision modified by behavioral factors."""
    original_decision: Dict[str, Any]
    behavioral_decision: Dict[str, Any]
    persona: str
    belief: Dict[str, Any]
    bias_adjustment: Dict[str, Any]
    social_influence: Dict[str, Any]
    fear_greed_index: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original": self.original_decision,
            "behavioral": self.behavioral_decision,
            "persona": self.persona,
            "belief": self.belief,
            "bias_adjustment": self.bias_adjustment,
            "social_influence": self.social_influence,
            "fear_greed_index": self.fear_greed_index,
            "timestamp": self.timestamp.isoformat()
        }


class BehavioralAgentWrapper:
    """
    Wrapper that adds behavioral finance simulation to any agent.

    Applies:
    1. Investor persona (market attitude, risk tolerance, style)
    2. Behavioral biases (disposition, loss aversion, etc.)
    3. Social sentiment influence (herd behavior)
    4. Fear & Greed adjustment

    Usage:
        wrapper = BehavioralAgentWrapper(persona_template="aggressive_momentum")
        enhanced_decision = wrapper.apply_behavioral_factors(
            decision={"action": "BUY", "confidence": 0.7},
            position=current_position,
            market_sentiment=0.6
        )
    """

    def __init__(
        self,
        agent_id: str,
        persona_template: str = "moderate",
        bias_profile: str = "moderate",
        social_role: SocialRole = SocialRole.FOLLOWER,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize behavioral wrapper.

        Args:
            agent_id: Unique agent identifier
            persona_template: Investor persona template
            bias_profile: Behavioral bias profile template
            social_role: Role in social network
            config: Additional configuration
        """
        self.agent_id = agent_id
        self.config = config or {}

        # Initialize belief system
        self.belief_system = InvestorBeliefSystem(
            default_confidence=self.config.get("default_confidence", 0.5)
        )

        # Create persona
        self.persona = self.belief_system.create_persona(
            name=f"persona_{agent_id}",
            template=persona_template
        )

        # Initialize bias engine
        self.bias_engine = BehavioralBiasEngine(
            enable_logging=self.config.get("log_biases", True),
            randomize_biases=self.config.get("randomize", True),
            noise_factor=self.config.get("noise", 0.1)
        )

        # Create bias profile
        self.bias_profile = self.bias_engine.create_profile(template=bias_profile)

        # Social network integration
        self.social_role = social_role

        # Current market belief
        self.current_belief: Optional[MarketBelief] = None

        # Decision history
        self._decisions: List[BehavioralDecision] = []

        logger.info(
            f"🧠 Behavioral agent {agent_id} initialized: "
            f"persona={persona_template}, biases={bias_profile}, role={social_role.value}"
        )

    def apply_behavioral_factors(
        self,
        decision: Dict[str, Any],
        position: Optional[Dict[str, Any]] = None,
        market_data: Optional[Dict[str, Any]] = None,
        news_items: Optional[List[Dict]] = None,
        social_sentiment: Optional[float] = None,
        recent_returns: Optional[List[float]] = None,
        fear_greed_value: Optional[float] = None
    ) -> BehavioralDecision:
        """
        Apply behavioral factors to a trading decision.

        Args:
            decision: Base decision (action, symbol, confidence, size)
            position: Current position info
            market_data: Market data for belief generation
            news_items: News for sentiment
            social_sentiment: Overall social sentiment (-1 to 1)
            recent_returns: Recent return history
            fear_greed_value: Fear & Greed index (0-100)

        Returns:
            BehavioralDecision with modified action
        """
        original = dict(decision)
        modified = dict(decision)

        # 1. Generate market belief based on persona
        belief = self.belief_system.generate_belief(
            persona=self.persona,
            market_data=market_data,
            news_items=news_items,
            social_sentiment=social_sentiment
        )
        self.current_belief = belief

        # 2. Apply belief to decision
        belief_modified = self.belief_system.apply_belief_to_decision(
            decision=modified,
            belief=belief
        )
        modified.update(belief_modified)

        # 3. Create position history if position exists
        position_history = None
        if position and position.get("entry_price"):
            position_history = PositionHistory(
                symbol=decision.get("symbol", ""),
                entry_price=position["entry_price"],
                entry_time=datetime.fromisoformat(
                    position.get("entry_time", datetime.utcnow().isoformat())
                ),
                current_price=market_data.get("price", position["entry_price"]) if market_data else position["entry_price"],
                quantity=position.get("quantity", 0),
                unrealized_pnl=position.get("unrealized_pnl", 0)
            )

        # 4. Apply behavioral biases
        asset_volatility = market_data.get("volatility") if market_data else None

        bias_adjustment = self.bias_engine.apply_biases(
            decision=modified,
            profile=self.bias_profile,
            position_history=position_history,
            market_sentiment=social_sentiment,
            recent_returns=recent_returns,
            asset_volatility=asset_volatility
        )

        # Update decision with bias adjustments
        modified["action"] = bias_adjustment.adjusted_action
        modified["confidence"] = bias_adjustment.adjusted_confidence
        modified["size"] = bias_adjustment.adjusted_size

        # 5. Social sentiment influence
        social_influence = self._apply_social_influence(
            decision=modified,
            sentiment=social_sentiment
        )
        modified.update(social_influence.get("adjustments", {}))

        # 6. Fear & Greed adjustment
        fg_value = fear_greed_value or 50.0
        fg_adjustment = self._apply_fear_greed(modified, fg_value)
        modified.update(fg_adjustment)

        # Create behavioral decision
        behavioral_decision = BehavioralDecision(
            original_decision=original,
            behavioral_decision=modified,
            persona=self.persona.name,
            belief=belief.to_dict(),
            bias_adjustment=bias_adjustment.to_dict(),
            social_influence=social_influence,
            fear_greed_index=fg_value,
            timestamp=datetime.utcnow()
        )

        self._decisions.append(behavioral_decision)

        logger.debug(
            f"🧠 Behavioral adjustment: {original.get('action')} -> {modified.get('action')}, "
            f"conf: {original.get('confidence', 0):.2f} -> {modified.get('confidence', 0):.2f}"
        )

        return behavioral_decision

    def _apply_social_influence(
        self,
        decision: Dict[str, Any],
        sentiment: Optional[float]
    ) -> Dict[str, Any]:
        """Apply social network influence to decision."""
        if sentiment is None:
            return {"applied": False, "adjustments": {}}

        adjustments = {}

        # Based on social role
        if self.social_role == SocialRole.FOLLOWER:
            # Followers tend toward crowd sentiment
            if abs(sentiment) > 0.3:
                crowd_action = "BUY" if sentiment > 0 else "SELL"
                if decision.get("action") != crowd_action:
                    # Reduce confidence when going against crowd
                    adjustments["confidence"] = decision.get("confidence", 0.5) * 0.8

        elif self.social_role == SocialRole.CONTRARIAN:
            # Contrarians go against strong sentiment
            if abs(sentiment) > 0.5:
                contra_action = "SELL" if sentiment > 0 else "BUY"
                if decision.get("action") == contra_action:
                    # Increase confidence when being contrarian
                    adjustments["confidence"] = min(
                        decision.get("confidence", 0.5) * 1.2,
                        0.95
                    )

        elif self.social_role == SocialRole.INFLUENCER:
            # Influencers are less affected by sentiment
            pass  # No adjustment

        return {
            "applied": True,
            "role": self.social_role.value,
            "sentiment": sentiment,
            "adjustments": adjustments
        }

    def _apply_fear_greed(
        self,
        decision: Dict[str, Any],
        fear_greed: float
    ) -> Dict[str, Any]:
        """Adjust decision based on Fear & Greed index."""
        adjustments = {}

        # Extreme fear (< 25): Reduce buy confidence, increase sell
        if fear_greed < 25:
            if decision.get("action") == "BUY":
                adjustments["confidence"] = decision.get("confidence", 0.5) * 0.7
                adjustments["size"] = decision.get("size", 1.0) * 0.5
            elif decision.get("action") == "SELL":
                adjustments["confidence"] = min(
                    decision.get("confidence", 0.5) * 1.1,
                    0.95
                )

        # Extreme greed (> 75): Reduce sell confidence, be cautious with buys
        elif fear_greed > 75:
            if decision.get("action") == "SELL":
                adjustments["confidence"] = decision.get("confidence", 0.5) * 0.8
            elif decision.get("action") == "BUY":
                # FOMO can increase buy confidence for emotional traders
                if self.persona.risk_tolerance == RiskTolerance.AGGRESSIVE:
                    adjustments["confidence"] = min(
                        decision.get("confidence", 0.5) * 1.1,
                        0.95
                    )
                else:
                    # Conservative traders are cautious at greed extremes
                    adjustments["confidence"] = decision.get("confidence", 0.5) * 0.9
                    adjustments["size"] = decision.get("size", 1.0) * 0.8

        return adjustments

    def update_persona(
        self,
        attitude: Optional[MarketAttitude] = None,
        risk_tolerance: Optional[RiskTolerance] = None,
        style: Optional[InvestmentStyle] = None
    ):
        """Update persona characteristics."""
        if attitude:
            self.persona.attitude = attitude
        if risk_tolerance:
            self.persona.risk_tolerance = risk_tolerance
        if style:
            self.persona.style = style

        logger.info(f"🧠 Updated persona for {self.agent_id}")

    def update_bias_profile(self, **kwargs):
        """Update bias profile parameters."""
        for key, value in kwargs.items():
            if hasattr(self.bias_profile, key):
                setattr(self.bias_profile, key, value)

    def get_behavioral_summary(self) -> Dict[str, Any]:
        """Get summary of behavioral characteristics."""
        return {
            "agent_id": self.agent_id,
            "persona": {
                "name": self.persona.name,
                "attitude": self.persona.attitude.value,
                "risk_tolerance": self.persona.risk_tolerance.value,
                "style": self.persona.style.value,
                "time_horizon": self.persona.time_horizon.value
            },
            "bias_profile": self.bias_profile.to_dict(),
            "social_role": self.social_role.value,
            "current_belief": self.current_belief.to_dict() if self.current_belief else None,
            "decisions_made": len(self._decisions),
            "bias_statistics": self.bias_engine.get_statistics()
        }

    def get_decision_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent decision history."""
        return [d.to_dict() for d in self._decisions[-limit:]]


class BehavioralAgentPool:
    """
    Pool of behavioral agents with different personalities.

    Creates diverse agent population for realistic simulation.
    """

    # Default agent configurations
    DEFAULT_AGENTS = {
        "conservative_value": {
            "persona": "conservative_value",
            "bias": "rational",
            "role": SocialRole.ANALYST
        },
        "aggressive_momentum": {
            "persona": "aggressive_momentum",
            "bias": "emotional",
            "role": SocialRole.NOISE_TRADER
        },
        "balanced_growth": {
            "persona": "balanced_growth",
            "bias": "moderate",
            "role": SocialRole.FOLLOWER
        },
        "contrarian_deep": {
            "persona": "contrarian_deep",
            "bias": "contrarian",
            "role": SocialRole.CONTRARIAN
        },
        "institutional_steady": {
            "persona": "institutional_steady",
            "bias": "rational",
            "role": SocialRole.INSTITUTIONAL
        },
        "retail_fomo": {
            "persona": "retail_fomo",
            "bias": "retail_typical",
            "role": SocialRole.FOLLOWER
        },
        "influencer_alpha": {
            "persona": "aggressive_momentum",
            "bias": "moderate",
            "role": SocialRole.INFLUENCER
        }
    }

    def __init__(
        self,
        include_defaults: bool = True,
        custom_agents: Optional[Dict[str, Dict]] = None
    ):
        """
        Initialize agent pool.

        Args:
            include_defaults: Include default agent types
            custom_agents: Additional custom agent configurations
        """
        self.agents: Dict[str, BehavioralAgentWrapper] = {}

        # Social network for inter-agent influence
        self.social_network = SocialSentimentNetwork(
            propagation_decay=0.7,
            herd_threshold=0.6
        )

        # Fear & Greed calculator
        self.fear_greed = FearGreedIndex()

        if include_defaults:
            for agent_id, config in self.DEFAULT_AGENTS.items():
                self.add_agent(agent_id, config)

        if custom_agents:
            for agent_id, config in custom_agents.items():
                self.add_agent(agent_id, config)

        logger.info(f"🧠 Agent pool initialized with {len(self.agents)} agents")

    def add_agent(
        self,
        agent_id: str,
        config: Dict[str, Any]
    ) -> BehavioralAgentWrapper:
        """Add an agent to the pool."""
        agent = BehavioralAgentWrapper(
            agent_id=agent_id,
            persona_template=config.get("persona", "moderate"),
            bias_profile=config.get("bias", "moderate"),
            social_role=config.get("role", SocialRole.FOLLOWER)
        )

        self.agents[agent_id] = agent

        # Register in social network
        self.social_network.register_agent(
            agent_id=agent_id,
            role=config.get("role", SocialRole.FOLLOWER)
        )

        return agent

    def get_agent(self, agent_id: str) -> Optional[BehavioralAgentWrapper]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    def get_collective_decision(
        self,
        decision: Dict[str, Any],
        market_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get collective decision from all agents.

        Returns weighted average based on agent influence.
        """
        if not self.agents:
            return decision

        # Calculate current Fear & Greed
        fg = self.fear_greed.calculate(
            social_sentiment=kwargs.get("social_sentiment", 0.0),
            volatility_percentile=kwargs.get("volatility_percentile", 50.0),
            price_momentum=kwargs.get("price_momentum", 0.0),
            volume_ratio=kwargs.get("volume_ratio", 1.0)
        )

        votes = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        total_weight = 0.0
        confidence_sum = 0.0

        for agent_id, agent in self.agents.items():
            behavioral = agent.apply_behavioral_factors(
                decision=decision,
                market_data=market_data,
                fear_greed_value=fg["index"],
                **kwargs
            )

            # Weight by agent influence in social network
            social_agent = self.social_network._agents.get(agent_id)
            weight = social_agent.influence_score if social_agent else 1.0

            action = behavioral.behavioral_decision.get("action", "HOLD")
            confidence = behavioral.behavioral_decision.get("confidence", 0.5)

            votes[action] += weight * confidence
            confidence_sum += confidence * weight
            total_weight += weight

        # Determine collective action
        collective_action = max(votes, key=votes.get)
        collective_confidence = confidence_sum / total_weight if total_weight > 0 else 0.5

        return {
            "action": collective_action,
            "confidence": collective_confidence,
            "symbol": decision.get("symbol"),
            "votes": {k: round(v, 3) for k, v in votes.items()},
            "agent_count": len(self.agents),
            "fear_greed": fg,
            "collective": True
        }

    def get_pool_statistics(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            "agent_count": len(self.agents),
            "agents": {
                agent_id: agent.get_behavioral_summary()
                for agent_id, agent in self.agents.items()
            },
            "social_network": self.social_network.get_network_statistics(),
            "fear_greed_trend": self.fear_greed.get_trend()
        }
