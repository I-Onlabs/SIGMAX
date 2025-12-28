"""
Social Sentiment Integration - Herd Behavior and Social Network Effects
Inspired by TwinMarket's social sentiment simulation

Models how agents influence each other through:
- Social networks (who influences whom)
- Information propagation (news/rumor spreading)
- Herd behavior (following influential agents)
- Sentiment contagion (emotional spread)
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import math
from collections import defaultdict
from loguru import logger


class SocialRole(Enum):
    """Roles agents can have in the social network."""
    INFLUENCER = "influencer"  # High follower count, sets trends
    FOLLOWER = "follower"  # Follows influencers
    CONTRARIAN = "contrarian"  # Goes against the crowd
    ANALYST = "analyst"  # Provides analysis, medium influence
    NOISE_TRADER = "noise_trader"  # Random, adds noise
    INSTITUTIONAL = "institutional"  # Large positions, slow to act


class SentimentType(Enum):
    """Types of sentiment signals."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    FEAR = "fear"
    GREED = "greed"
    FOMO = "fomo"  # Fear of missing out
    PANIC = "panic"


@dataclass
class SocialAgent:
    """An agent in the social network."""
    agent_id: str
    role: SocialRole
    influence_score: float  # 0-1, how influential
    susceptibility: float  # 0-1, how easily influenced
    credibility: float  # 0-1, how trusted
    sentiment: SentimentType = SentimentType.NEUTRAL
    sentiment_strength: float = 0.5  # 0-1
    followers: Set[str] = field(default_factory=set)
    following: Set[str] = field(default_factory=set)
    last_signal: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "influence_score": round(self.influence_score, 3),
            "susceptibility": round(self.susceptibility, 3),
            "credibility": round(self.credibility, 3),
            "sentiment": self.sentiment.value,
            "sentiment_strength": round(self.sentiment_strength, 3),
            "follower_count": len(self.followers),
            "following_count": len(self.following)
        }


@dataclass
class SentimentSignal:
    """A sentiment signal in the network."""
    source_id: str
    sentiment: SentimentType
    strength: float  # 0-1
    symbol: Optional[str] = None
    message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reach: int = 0  # How many agents saw this
    engagement: float = 0.0  # Interaction level

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "sentiment": self.sentiment.value,
            "strength": round(self.strength, 3),
            "symbol": self.symbol,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "reach": self.reach,
            "engagement": round(self.engagement, 3)
        }


@dataclass
class HerdEvent:
    """A detected herd behavior event."""
    event_type: str  # "momentum", "panic_sell", "fomo_buy", etc.
    sentiment: SentimentType
    strength: float
    participant_count: int
    trigger_agent: Optional[str] = None
    symbol: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "sentiment": self.sentiment.value,
            "strength": round(self.strength, 3),
            "participant_count": self.participant_count,
            "trigger_agent": self.trigger_agent,
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat()
        }


class SocialSentimentNetwork:
    """
    Social network for sentiment propagation and herd behavior.

    Usage:
        network = SocialSentimentNetwork()

        # Register agents
        network.register_agent("agent1", SocialRole.INFLUENCER, influence=0.9)
        network.register_agent("agent2", SocialRole.FOLLOWER, susceptibility=0.7)

        # Create connections
        network.add_follow("agent2", "agent1")

        # Propagate sentiment
        signal = network.emit_signal("agent1", SentimentType.BULLISH, 0.8, "AAPL")
        effects = network.propagate_sentiment(signal)

        # Get aggregate sentiment
        agg = network.get_aggregate_sentiment("AAPL")
    """

    # Default role configurations
    ROLE_DEFAULTS = {
        SocialRole.INFLUENCER: {
            "influence_score": 0.85,
            "susceptibility": 0.2,
            "credibility": 0.75
        },
        SocialRole.FOLLOWER: {
            "influence_score": 0.2,
            "susceptibility": 0.7,
            "credibility": 0.4
        },
        SocialRole.CONTRARIAN: {
            "influence_score": 0.4,
            "susceptibility": 0.3,
            "credibility": 0.5
        },
        SocialRole.ANALYST: {
            "influence_score": 0.6,
            "susceptibility": 0.4,
            "credibility": 0.8
        },
        SocialRole.NOISE_TRADER: {
            "influence_score": 0.1,
            "susceptibility": 0.9,
            "credibility": 0.2
        },
        SocialRole.INSTITUTIONAL: {
            "influence_score": 0.7,
            "susceptibility": 0.3,
            "credibility": 0.85
        }
    }

    def __init__(
        self,
        propagation_decay: float = 0.7,
        herd_threshold: float = 0.6,
        sentiment_decay_hours: float = 24.0,
        enable_logging: bool = True
    ):
        """
        Initialize social sentiment network.

        Args:
            propagation_decay: How much signal weakens per hop (0-1)
            herd_threshold: Sentiment alignment needed for herd event
            sentiment_decay_hours: Hours before sentiment fades
            enable_logging: Enable event logging
        """
        self.propagation_decay = propagation_decay
        self.herd_threshold = herd_threshold
        self.sentiment_decay_hours = sentiment_decay_hours
        self.enable_logging = enable_logging

        self._agents: Dict[str, SocialAgent] = {}
        self._signal_history: List[SentimentSignal] = []
        self._herd_events: List[HerdEvent] = []
        self._symbol_sentiments: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)

    def register_agent(
        self,
        agent_id: str,
        role: SocialRole,
        influence: Optional[float] = None,
        susceptibility: Optional[float] = None,
        credibility: Optional[float] = None
    ) -> SocialAgent:
        """
        Register an agent in the social network.

        Args:
            agent_id: Unique agent identifier
            role: Social role
            influence: Override default influence score
            susceptibility: Override default susceptibility
            credibility: Override default credibility

        Returns:
            Created SocialAgent
        """
        defaults = self.ROLE_DEFAULTS.get(role, self.ROLE_DEFAULTS[SocialRole.FOLLOWER])

        agent = SocialAgent(
            agent_id=agent_id,
            role=role,
            influence_score=influence if influence is not None else defaults["influence_score"],
            susceptibility=susceptibility if susceptibility is not None else defaults["susceptibility"],
            credibility=credibility if credibility is not None else defaults["credibility"]
        )

        self._agents[agent_id] = agent

        if self.enable_logging:
            logger.debug(f"Registered social agent: {agent_id} as {role.value}")

        return agent

    def add_follow(self, follower_id: str, target_id: str):
        """Create a follow relationship."""
        if follower_id not in self._agents or target_id not in self._agents:
            return

        self._agents[follower_id].following.add(target_id)
        self._agents[target_id].followers.add(follower_id)

    def remove_follow(self, follower_id: str, target_id: str):
        """Remove a follow relationship."""
        if follower_id in self._agents:
            self._agents[follower_id].following.discard(target_id)
        if target_id in self._agents:
            self._agents[target_id].followers.discard(follower_id)

    def emit_signal(
        self,
        agent_id: str,
        sentiment: SentimentType,
        strength: float,
        symbol: Optional[str] = None,
        message: Optional[str] = None
    ) -> SentimentSignal:
        """
        Emit a sentiment signal from an agent.

        Args:
            agent_id: Source agent
            sentiment: Sentiment type
            strength: Signal strength (0-1)
            symbol: Asset symbol if relevant
            message: Optional message content

        Returns:
            Created SentimentSignal
        """
        if agent_id not in self._agents:
            raise ValueError(f"Unknown agent: {agent_id}")

        agent = self._agents[agent_id]

        # Update agent's sentiment
        agent.sentiment = sentiment
        agent.sentiment_strength = strength
        agent.last_signal = datetime.utcnow()

        # Calculate reach based on followers
        reach = len(agent.followers)

        signal = SentimentSignal(
            source_id=agent_id,
            sentiment=sentiment,
            strength=strength * agent.influence_score,
            symbol=symbol,
            message=message,
            reach=reach
        )

        self._signal_history.append(signal)

        # Track symbol sentiment
        if symbol:
            sentiment_value = self._sentiment_to_value(sentiment, strength)
            self._symbol_sentiments[symbol].append((datetime.utcnow(), sentiment_value))

        if self.enable_logging:
            logger.debug(
                f"Signal emitted: {agent_id} -> {sentiment.value} "
                f"({strength:.2f}) for {symbol or 'market'}"
            )

        return signal

    def propagate_sentiment(
        self,
        signal: SentimentSignal,
        max_hops: int = 3
    ) -> Dict[str, Any]:
        """
        Propagate a sentiment signal through the network.

        Args:
            signal: Signal to propagate
            max_hops: Maximum propagation depth

        Returns:
            Propagation results
        """
        affected_agents = {}
        queue = [(signal.source_id, signal.strength, 0)]  # (agent_id, strength, hop)
        visited = {signal.source_id}

        while queue:
            current_id, current_strength, hop = queue.pop(0)

            if hop >= max_hops or current_strength < 0.1:
                continue

            current_agent = self._agents.get(current_id)
            if not current_agent:
                continue

            # Propagate to followers
            for follower_id in current_agent.followers:
                if follower_id in visited:
                    continue

                follower = self._agents.get(follower_id)
                if not follower:
                    continue

                visited.add(follower_id)

                # Calculate influence on follower
                influence = (
                    current_strength *
                    current_agent.influence_score *
                    current_agent.credibility *
                    follower.susceptibility *
                    self.propagation_decay
                )

                if influence >= 0.1:
                    # Potentially update follower's sentiment
                    update_prob = influence * (1 - abs(
                        self._sentiment_to_value(follower.sentiment, follower.sentiment_strength) -
                        self._sentiment_to_value(signal.sentiment, signal.strength)
                    ))

                    if random.random() < update_prob:
                        old_sentiment = follower.sentiment
                        follower.sentiment = signal.sentiment
                        follower.sentiment_strength = min(
                            follower.sentiment_strength + influence * 0.5,
                            1.0
                        )
                        affected_agents[follower_id] = {
                            "old_sentiment": old_sentiment.value,
                            "new_sentiment": signal.sentiment.value,
                            "influence_received": round(influence, 3)
                        }

                    # Continue propagation
                    queue.append((follower_id, influence, hop + 1))

        # Check for herd behavior
        herd_event = self._detect_herd_behavior(signal.symbol)
        if herd_event:
            self._herd_events.append(herd_event)

        return {
            "source": signal.source_id,
            "affected_count": len(affected_agents),
            "affected_agents": affected_agents,
            "herd_event": herd_event.to_dict() if herd_event else None,
            "propagation_depth": max_hops
        }

    def _detect_herd_behavior(
        self,
        symbol: Optional[str] = None
    ) -> Optional[HerdEvent]:
        """Detect if herd behavior is occurring."""
        if len(self._agents) < 3:
            return None

        # Count sentiment alignment
        sentiment_counts = defaultdict(list)
        for agent in self._agents.values():
            sentiment_counts[agent.sentiment].append(agent)

        # Find dominant sentiment
        dominant_sentiment = max(
            sentiment_counts.keys(),
            key=lambda s: sum(a.sentiment_strength for a in sentiment_counts[s])
        )

        dominant_agents = sentiment_counts[dominant_sentiment]
        alignment_ratio = len(dominant_agents) / len(self._agents)
        avg_strength = sum(a.sentiment_strength for a in dominant_agents) / len(dominant_agents)

        # Check if herd threshold met
        if alignment_ratio >= self.herd_threshold and avg_strength > 0.5:
            # Determine event type
            if dominant_sentiment == SentimentType.PANIC:
                event_type = "panic_sell"
            elif dominant_sentiment == SentimentType.FOMO:
                event_type = "fomo_buy"
            elif dominant_sentiment == SentimentType.BULLISH:
                event_type = "momentum_long"
            elif dominant_sentiment == SentimentType.BEARISH:
                event_type = "momentum_short"
            elif dominant_sentiment == SentimentType.GREED:
                event_type = "euphoria"
            elif dominant_sentiment == SentimentType.FEAR:
                event_type = "capitulation"
            else:
                event_type = "herd_neutral"

            # Find trigger (most influential aligned agent)
            trigger = max(
                dominant_agents,
                key=lambda a: a.influence_score * a.sentiment_strength
            )

            return HerdEvent(
                event_type=event_type,
                sentiment=dominant_sentiment,
                strength=avg_strength * alignment_ratio,
                participant_count=len(dominant_agents),
                trigger_agent=trigger.agent_id,
                symbol=symbol
            )

        return None

    def get_aggregate_sentiment(
        self,
        symbol: Optional[str] = None,
        time_window_hours: float = 24.0
    ) -> Dict[str, Any]:
        """
        Get aggregate sentiment for a symbol or market.

        Args:
            symbol: Asset symbol (None for overall market)
            time_window_hours: Hours to look back

        Returns:
            Aggregate sentiment data
        """
        cutoff = datetime.utcnow() - timedelta(hours=time_window_hours)

        # Filter relevant signals
        if symbol:
            relevant_signals = [
                s for s in self._signal_history
                if s.symbol == symbol and s.timestamp > cutoff
            ]
        else:
            relevant_signals = [
                s for s in self._signal_history
                if s.timestamp > cutoff
            ]

        if not relevant_signals:
            return {
                "symbol": symbol,
                "sentiment": "neutral",
                "score": 0.0,
                "signal_count": 0,
                "confidence": 0.0
            }

        # Weight signals by source influence and recency
        weighted_scores = []
        for signal in relevant_signals:
            source = self._agents.get(signal.source_id)
            if not source:
                continue

            # Time decay
            age_hours = (datetime.utcnow() - signal.timestamp).total_seconds() / 3600
            time_weight = math.exp(-age_hours / self.sentiment_decay_hours)

            # Influence weight
            influence_weight = source.influence_score * source.credibility

            # Calculate score
            sentiment_value = self._sentiment_to_value(signal.sentiment, signal.strength)
            weighted_score = sentiment_value * time_weight * influence_weight

            weighted_scores.append((weighted_score, time_weight * influence_weight))

        if not weighted_scores:
            return {
                "symbol": symbol,
                "sentiment": "neutral",
                "score": 0.0,
                "signal_count": 0,
                "confidence": 0.0
            }

        # Aggregate
        total_weight = sum(w for _, w in weighted_scores)
        if total_weight == 0:
            aggregate_score = 0.0
        else:
            aggregate_score = sum(s * w for s, w in weighted_scores) / total_weight

        # Determine sentiment label
        if aggregate_score > 0.3:
            sentiment_label = "bullish"
        elif aggregate_score > 0.1:
            sentiment_label = "slightly_bullish"
        elif aggregate_score < -0.3:
            sentiment_label = "bearish"
        elif aggregate_score < -0.1:
            sentiment_label = "slightly_bearish"
        else:
            sentiment_label = "neutral"

        # Confidence based on signal count and agreement
        confidence = min(len(relevant_signals) / 10, 1.0) * (
            1 - abs(sum(1 for s, _ in weighted_scores if s > 0) / len(weighted_scores) - 0.5) * 2
        )

        return {
            "symbol": symbol,
            "sentiment": sentiment_label,
            "score": round(aggregate_score, 3),
            "signal_count": len(relevant_signals),
            "confidence": round(abs(confidence), 3),
            "time_window_hours": time_window_hours
        }

    def get_influencer_sentiment(
        self,
        symbol: Optional[str] = None,
        min_influence: float = 0.6
    ) -> Dict[str, Any]:
        """Get sentiment from influential agents only."""
        influencers = [
            a for a in self._agents.values()
            if a.influence_score >= min_influence
        ]

        if not influencers:
            return {"influencer_count": 0, "sentiment": "neutral", "score": 0.0}

        bullish = sum(
            1 for a in influencers
            if a.sentiment in [SentimentType.BULLISH, SentimentType.GREED, SentimentType.FOMO]
        )
        bearish = sum(
            1 for a in influencers
            if a.sentiment in [SentimentType.BEARISH, SentimentType.FEAR, SentimentType.PANIC]
        )

        if bullish > bearish:
            sentiment = "bullish"
            score = bullish / len(influencers)
        elif bearish > bullish:
            sentiment = "bearish"
            score = -bearish / len(influencers)
        else:
            sentiment = "neutral"
            score = 0.0

        return {
            "influencer_count": len(influencers),
            "sentiment": sentiment,
            "score": round(score, 3),
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": len(influencers) - bullish - bearish
        }

    def _sentiment_to_value(
        self,
        sentiment: SentimentType,
        strength: float
    ) -> float:
        """Convert sentiment to numerical value (-1 to 1)."""
        mapping = {
            SentimentType.BULLISH: 0.7,
            SentimentType.GREED: 0.9,
            SentimentType.FOMO: 0.8,
            SentimentType.NEUTRAL: 0.0,
            SentimentType.BEARISH: -0.7,
            SentimentType.FEAR: -0.8,
            SentimentType.PANIC: -0.95
        }
        base = mapping.get(sentiment, 0.0)
        return base * strength

    def get_network_statistics(self) -> Dict[str, Any]:
        """Get network statistics."""
        if not self._agents:
            return {"agent_count": 0}

        role_counts = defaultdict(int)
        sentiment_counts = defaultdict(int)
        total_connections = 0

        for agent in self._agents.values():
            role_counts[agent.role.value] += 1
            sentiment_counts[agent.sentiment.value] += 1
            total_connections += len(agent.followers) + len(agent.following)

        avg_connections = total_connections / len(self._agents) / 2  # Divide by 2 for bidirectional

        return {
            "agent_count": len(self._agents),
            "role_distribution": dict(role_counts),
            "sentiment_distribution": dict(sentiment_counts),
            "average_connections": round(avg_connections, 2),
            "total_signals": len(self._signal_history),
            "herd_events": len(self._herd_events)
        }

    def get_recent_herd_events(
        self,
        hours: float = 24.0
    ) -> List[Dict[str, Any]]:
        """Get recent herd behavior events."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            e.to_dict() for e in self._herd_events
            if e.timestamp > cutoff
        ]

    def clear_history(self):
        """Clear signal and event history."""
        self._signal_history.clear()
        self._herd_events.clear()
        self._symbol_sentiments.clear()


class FearGreedIndex:
    """
    Calculate a Fear & Greed index from multiple indicators.

    Similar to CNN's Fear & Greed Index for crypto/stocks.
    """

    def __init__(
        self,
        social_weight: float = 0.3,
        volatility_weight: float = 0.25,
        momentum_weight: float = 0.25,
        volume_weight: float = 0.2
    ):
        """
        Initialize Fear & Greed index calculator.

        Args:
            social_weight: Weight for social sentiment
            volatility_weight: Weight for volatility signal
            momentum_weight: Weight for momentum signal
            volume_weight: Weight for volume signal
        """
        self.weights = {
            "social": social_weight,
            "volatility": volatility_weight,
            "momentum": momentum_weight,
            "volume": volume_weight
        }

        # Normalize weights
        total = sum(self.weights.values())
        self.weights = {k: v / total for k, v in self.weights.items()}

        self._history: List[Tuple[datetime, float, Dict]] = []

    def calculate(
        self,
        social_sentiment: float,  # -1 to 1
        volatility_percentile: float,  # 0-100
        price_momentum: float,  # -1 to 1
        volume_ratio: float  # Current vs average (e.g., 1.5 = 50% above avg)
    ) -> Dict[str, Any]:
        """
        Calculate Fear & Greed index.

        Args:
            social_sentiment: Social sentiment score (-1 to 1)
            volatility_percentile: Volatility percentile (0-100)
            price_momentum: Price momentum score (-1 to 1)
            volume_ratio: Volume relative to average

        Returns:
            Fear & Greed index data
        """
        # Convert each indicator to 0-100 scale

        # Social: -1 (fear) to 1 (greed) -> 0-100
        social_score = (social_sentiment + 1) / 2 * 100

        # Volatility: High vol = fear (inverse)
        volatility_score = 100 - volatility_percentile

        # Momentum: -1 (fear) to 1 (greed) -> 0-100
        momentum_score = (price_momentum + 1) / 2 * 100

        # Volume: High volume in uptrend = greed, in downtrend = fear
        if price_momentum > 0:
            volume_score = min(volume_ratio * 50, 100)
        else:
            volume_score = max(100 - volume_ratio * 50, 0)

        # Weighted average
        components = {
            "social": social_score,
            "volatility": volatility_score,
            "momentum": momentum_score,
            "volume": volume_score
        }

        index_value = sum(
            components[k] * self.weights[k]
            for k in components
        )

        # Determine label
        if index_value >= 80:
            label = "extreme_greed"
        elif index_value >= 60:
            label = "greed"
        elif index_value >= 40:
            label = "neutral"
        elif index_value >= 20:
            label = "fear"
        else:
            label = "extreme_fear"

        result = {
            "index": round(index_value, 1),
            "label": label,
            "components": {k: round(v, 1) for k, v in components.items()},
            "weights": self.weights,
            "timestamp": datetime.utcnow().isoformat()
        }

        self._history.append((datetime.utcnow(), index_value, components))

        return result

    def get_trend(self, periods: int = 7) -> Dict[str, Any]:
        """Get index trend over recent periods."""
        if len(self._history) < 2:
            return {"trend": "insufficient_data", "periods": 0}

        recent = self._history[-min(periods, len(self._history)):]
        values = [v for _, v, _ in recent]

        avg = sum(values) / len(values)
        current = values[-1]

        if current > avg * 1.1:
            trend = "increasing_greed"
        elif current < avg * 0.9:
            trend = "increasing_fear"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "current": round(current, 1),
            "average": round(avg, 1),
            "periods": len(recent),
            "min": round(min(values), 1),
            "max": round(max(values), 1)
        }

    def get_history(
        self,
        hours: float = 168.0  # 7 days
    ) -> List[Dict[str, Any]]:
        """Get historical index values."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            {
                "timestamp": ts.isoformat(),
                "index": round(val, 1),
                "components": {k: round(v, 1) for k, v in comp.items()}
            }
            for ts, val, comp in self._history
            if ts > cutoff
        ]
