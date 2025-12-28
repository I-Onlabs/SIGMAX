"""
Ensemble Voting Mechanism
Aggregates decisions from multiple competing models for higher confidence

Supports multiple voting strategies:
- Simple majority voting
- Confidence-weighted voting
- Performance-weighted voting
- Dynamic weight adjustment
"""

from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import Counter
from loguru import logger
import numpy as np

from .multi_model_arena import (
    TradeDecision,
    ModelPerformance,
    CompetitionArena
)


class VotingStrategy(Enum):
    """Voting strategy types."""
    SIMPLE_MAJORITY = "simple_majority"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    PERFORMANCE_WEIGHTED = "performance_weighted"
    SHARPE_WEIGHTED = "sharpe_weighted"
    RECENCY_WEIGHTED = "recency_weighted"
    DYNAMIC = "dynamic"


@dataclass
class Vote:
    """A single vote from a model."""
    model_name: str
    action: str  # "buy", "sell", "hold"
    confidence: float
    weight: float = 1.0
    reasoning: str = ""


@dataclass
class EnsembleDecision:
    """Aggregated decision from ensemble voting."""
    symbol: str
    action: str
    confidence: float
    consensus_score: float  # How much models agree (0-1)
    vote_distribution: Dict[str, float]
    participating_models: int
    winning_votes: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reasoning: str = ""
    individual_votes: List[Vote] = field(default_factory=list)

    @property
    def is_unanimous(self) -> bool:
        return self.consensus_score >= 0.99

    @property
    def is_strong_consensus(self) -> bool:
        return self.consensus_score >= 0.75


class EnsembleVotingSystem:
    """
    Ensemble voting system for aggregating model decisions.

    Usage:
        ensemble = EnsembleVotingSystem()

        # Add votes from different models
        ensemble.add_vote(Vote(model_name="gpt4", action="buy", confidence=0.8))
        ensemble.add_vote(Vote(model_name="claude", action="buy", confidence=0.7))
        ensemble.add_vote(Vote(model_name="deepseek", action="hold", confidence=0.6))

        # Get ensemble decision
        decision = ensemble.get_decision("BTC/USDT")
    """

    def __init__(
        self,
        strategy: VotingStrategy = VotingStrategy.CONFIDENCE_WEIGHTED,
        min_voters: int = 2,
        min_consensus: float = 0.5
    ):
        """
        Initialize ensemble voting system.

        Args:
            strategy: Voting strategy to use
            min_voters: Minimum voters required for a decision
            min_consensus: Minimum consensus score to execute
        """
        self.strategy = strategy
        self.min_voters = min_voters
        self.min_consensus = min_consensus

        # Current round votes
        self._current_votes: Dict[str, List[Vote]] = {}

        # Historical data for weight calculation
        self._model_history: Dict[str, List[Dict]] = {}
        self._decision_history: List[EnsembleDecision] = []

        # Performance-based weights (updated dynamically)
        self._model_weights: Dict[str, float] = {}

    def add_vote(self, vote: Vote, symbol: str = "default"):
        """
        Add a vote for a symbol.

        Args:
            vote: The vote to add
            symbol: Symbol being voted on
        """
        if symbol not in self._current_votes:
            self._current_votes[symbol] = []

        # Apply weight based on strategy
        if self.strategy == VotingStrategy.PERFORMANCE_WEIGHTED:
            vote.weight = self._model_weights.get(vote.model_name, 1.0)
        elif self.strategy == VotingStrategy.CONFIDENCE_WEIGHTED:
            vote.weight = vote.confidence

        self._current_votes[symbol].append(vote)

        logger.debug(
            f"Vote added: {vote.model_name} -> {vote.action} "
            f"(conf={vote.confidence:.2f}, weight={vote.weight:.2f})"
        )

    def get_decision(
        self,
        symbol: str,
        clear_votes: bool = True
    ) -> Optional[EnsembleDecision]:
        """
        Get ensemble decision for a symbol.

        Args:
            symbol: Symbol to get decision for
            clear_votes: Whether to clear votes after decision

        Returns:
            EnsembleDecision or None if not enough votes
        """
        votes = self._current_votes.get(symbol, [])

        if len(votes) < self.min_voters:
            logger.warning(
                f"Not enough votes for {symbol}: {len(votes)}/{self.min_voters}"
            )
            return None

        # Calculate decision based on strategy
        decision = self._calculate_decision(symbol, votes)

        # Check consensus threshold
        if decision.consensus_score < self.min_consensus:
            logger.warning(
                f"Consensus too low for {symbol}: {decision.consensus_score:.2f}"
            )
            decision.action = "hold"  # Default to hold on low consensus

        # Record decision
        self._decision_history.append(decision)

        # Clear votes if requested
        if clear_votes:
            self._current_votes.pop(symbol, None)

        return decision

    def _calculate_decision(
        self,
        symbol: str,
        votes: List[Vote]
    ) -> EnsembleDecision:
        """Calculate ensemble decision from votes."""
        if self.strategy == VotingStrategy.SIMPLE_MAJORITY:
            return self._simple_majority(symbol, votes)
        elif self.strategy == VotingStrategy.CONFIDENCE_WEIGHTED:
            return self._confidence_weighted(symbol, votes)
        elif self.strategy == VotingStrategy.PERFORMANCE_WEIGHTED:
            return self._performance_weighted(symbol, votes)
        elif self.strategy == VotingStrategy.SHARPE_WEIGHTED:
            return self._sharpe_weighted(symbol, votes)
        elif self.strategy == VotingStrategy.RECENCY_WEIGHTED:
            return self._recency_weighted(symbol, votes)
        else:  # DYNAMIC
            return self._dynamic_voting(symbol, votes)

    def _simple_majority(
        self,
        symbol: str,
        votes: List[Vote]
    ) -> EnsembleDecision:
        """Simple majority voting - one model, one vote."""
        action_counts = Counter(v.action for v in votes)
        total_votes = len(votes)

        # Get winning action
        winning_action, winning_count = action_counts.most_common(1)[0]

        # Calculate vote distribution
        distribution = {
            action: count / total_votes
            for action, count in action_counts.items()
        }

        # Consensus is proportion of winning votes
        consensus = winning_count / total_votes

        # Average confidence of winning votes
        winning_votes = [v for v in votes if v.action == winning_action]
        avg_confidence = sum(v.confidence for v in winning_votes) / len(winning_votes)

        return EnsembleDecision(
            symbol=symbol,
            action=winning_action,
            confidence=avg_confidence,
            consensus_score=consensus,
            vote_distribution=distribution,
            participating_models=total_votes,
            winning_votes=winning_count,
            reasoning=self._aggregate_reasoning(winning_votes),
            individual_votes=votes
        )

    def _confidence_weighted(
        self,
        symbol: str,
        votes: List[Vote]
    ) -> EnsembleDecision:
        """Weighted voting by confidence scores."""
        weighted_scores: Dict[str, float] = {"buy": 0, "sell": 0, "hold": 0}
        total_weight = 0

        for vote in votes:
            weight = vote.confidence
            weighted_scores[vote.action] += weight
            total_weight += weight

        # Normalize
        for action in weighted_scores:
            weighted_scores[action] /= total_weight if total_weight > 0 else 1

        # Get winning action
        winning_action = max(weighted_scores.items(), key=lambda x: x[1])

        # Calculate confidence as weighted average
        winning_votes = [v for v in votes if v.action == winning_action[0]]
        if winning_votes:
            total_conf_weight = sum(v.confidence for v in winning_votes)
            avg_confidence = (
                sum(v.confidence * v.confidence for v in winning_votes) /
                total_conf_weight
            )
        else:
            avg_confidence = 0

        return EnsembleDecision(
            symbol=symbol,
            action=winning_action[0],
            confidence=avg_confidence,
            consensus_score=winning_action[1],
            vote_distribution=weighted_scores,
            participating_models=len(votes),
            winning_votes=len(winning_votes),
            reasoning=self._aggregate_reasoning(winning_votes),
            individual_votes=votes
        )

    def _performance_weighted(
        self,
        symbol: str,
        votes: List[Vote]
    ) -> EnsembleDecision:
        """Weighted voting by historical performance."""
        weighted_scores: Dict[str, float] = {"buy": 0, "sell": 0, "hold": 0}
        total_weight = 0

        for vote in votes:
            # Use pre-assigned performance weight
            weight = vote.weight * vote.confidence
            weighted_scores[vote.action] += weight
            total_weight += weight

        # Normalize
        for action in weighted_scores:
            weighted_scores[action] /= total_weight if total_weight > 0 else 1

        # Get winning action
        winning_action = max(weighted_scores.items(), key=lambda x: x[1])
        winning_votes = [v for v in votes if v.action == winning_action[0]]

        return EnsembleDecision(
            symbol=symbol,
            action=winning_action[0],
            confidence=sum(v.confidence * v.weight for v in winning_votes) / len(winning_votes) if winning_votes else 0,
            consensus_score=winning_action[1],
            vote_distribution=weighted_scores,
            participating_models=len(votes),
            winning_votes=len(winning_votes),
            reasoning=self._aggregate_reasoning(winning_votes),
            individual_votes=votes
        )

    def _sharpe_weighted(
        self,
        symbol: str,
        votes: List[Vote]
    ) -> EnsembleDecision:
        """Weight by Sharpe ratio (risk-adjusted returns)."""
        # Similar to performance weighted but uses Sharpe as weight
        return self._performance_weighted(symbol, votes)

    def _recency_weighted(
        self,
        symbol: str,
        votes: List[Vote]
    ) -> EnsembleDecision:
        """Weight recent performance more heavily."""
        # Would require timestamp on historical performance
        return self._confidence_weighted(symbol, votes)

    def _dynamic_voting(
        self,
        symbol: str,
        votes: List[Vote]
    ) -> EnsembleDecision:
        """
        Dynamic voting that adapts based on agreement level.

        If high agreement: use simple majority
        If low agreement: weight by confidence and performance
        """
        # Check initial agreement
        action_counts = Counter(v.action for v in votes)
        top_action_pct = action_counts.most_common(1)[0][1] / len(votes)

        if top_action_pct >= 0.8:
            # High agreement - simple majority
            return self._simple_majority(symbol, votes)
        elif top_action_pct >= 0.6:
            # Medium agreement - confidence weighted
            return self._confidence_weighted(symbol, votes)
        else:
            # Low agreement - full weighted analysis
            return self._performance_weighted(symbol, votes)

    def _aggregate_reasoning(self, votes: List[Vote]) -> str:
        """Aggregate reasoning from votes."""
        reasonings = [v.reasoning for v in votes if v.reasoning]
        if not reasonings:
            return ""
        return " | ".join(reasonings[:3])  # Top 3

    def update_model_weights(
        self,
        performance_data: Dict[str, ModelPerformance]
    ):
        """
        Update model weights based on performance.

        Args:
            performance_data: Dict of model name -> performance
        """
        if not performance_data:
            return

        # Calculate weights based on Sharpe ratio
        sharpes = {
            name: max(0.1, perf.sharpe_ratio + 1)  # Shift to positive
            for name, perf in performance_data.items()
        }

        total = sum(sharpes.values())

        self._model_weights = {
            name: sharpe / total
            for name, sharpe in sharpes.items()
        }

        logger.info(f"Updated model weights: {self._model_weights}")

    def integrate_with_arena(self, arena: CompetitionArena):
        """
        Integrate with competition arena to get votes automatically.

        Args:
            arena: Competition arena instance
        """
        # Update weights from arena performance
        self.update_model_weights(arena.performance)

        # Get latest decisions from arena
        for name, perf in arena.performance.items():
            for decision in perf.decisions[-10:]:  # Last 10 decisions
                vote = Vote(
                    model_name=name,
                    action=decision.action,
                    confidence=decision.confidence,
                    weight=self._model_weights.get(name, 1.0),
                    reasoning=decision.reasoning
                )
                self.add_vote(vote, decision.symbol)

    def get_ensemble_recommendation(
        self,
        arena: CompetitionArena,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Get ensemble recommendation from arena competition.

        Convenience method that:
        1. Updates weights from arena
        2. Collects votes from competitors
        3. Returns aggregated decision

        Args:
            arena: Competition arena
            symbol: Symbol to get recommendation for

        Returns:
            Ensemble recommendation dict
        """
        # Update weights
        self.update_model_weights(arena.performance)

        # Collect latest votes for symbol
        self._current_votes[symbol] = []

        for name, perf in arena.performance.items():
            symbol_decisions = [d for d in perf.decisions if d.symbol == symbol]
            if symbol_decisions:
                latest = symbol_decisions[-1]
                vote = Vote(
                    model_name=name,
                    action=latest.action,
                    confidence=latest.confidence,
                    weight=self._model_weights.get(name, 1.0),
                    reasoning=latest.reasoning
                )
                self.add_vote(vote, symbol)

        # Get decision
        decision = self.get_decision(symbol, clear_votes=True)

        if decision:
            return {
                "symbol": decision.symbol,
                "action": decision.action,
                "confidence": round(decision.confidence, 3),
                "consensus": round(decision.consensus_score, 3),
                "vote_distribution": {
                    k: round(v, 3) for k, v in decision.vote_distribution.items()
                },
                "participating_models": decision.participating_models,
                "is_unanimous": decision.is_unanimous,
                "is_strong_consensus": decision.is_strong_consensus,
                "reasoning": decision.reasoning
            }

        return {
            "symbol": symbol,
            "action": "hold",
            "confidence": 0,
            "error": "Not enough votes"
        }

    def get_voting_statistics(self) -> Dict[str, Any]:
        """Get statistics about voting patterns."""
        if not self._decision_history:
            return {"total_decisions": 0}

        total = len(self._decision_history)
        unanimous = sum(1 for d in self._decision_history if d.is_unanimous)
        strong = sum(1 for d in self._decision_history if d.is_strong_consensus)

        action_dist = Counter(d.action for d in self._decision_history)
        avg_consensus = sum(d.consensus_score for d in self._decision_history) / total
        avg_confidence = sum(d.confidence for d in self._decision_history) / total

        return {
            "total_decisions": total,
            "unanimous_decisions": unanimous,
            "strong_consensus_decisions": strong,
            "avg_consensus": round(avg_consensus, 3),
            "avg_confidence": round(avg_confidence, 3),
            "action_distribution": dict(action_dist),
            "strategy": self.strategy.value,
            "model_weights": self._model_weights
        }

    def reset(self):
        """Reset voting state."""
        self._current_votes.clear()
        self._decision_history.clear()


class ConflictResolver:
    """
    Resolves conflicts when models strongly disagree.

    Strategies:
    - Escalation to higher-tier model
    - Debate synthesis
    - Conservative default
    """

    def __init__(
        self,
        escalation_model: Optional[str] = None,
        conservative_default: str = "hold"
    ):
        """
        Initialize conflict resolver.

        Args:
            escalation_model: Model to consult on conflicts
            conservative_default: Default action when unresolved
        """
        self.escalation_model = escalation_model
        self.conservative_default = conservative_default

    def should_resolve(self, decision: EnsembleDecision) -> bool:
        """Check if conflict resolution is needed."""
        return (
            not decision.is_strong_consensus and
            decision.participating_models >= 3
        )

    async def resolve(
        self,
        decision: EnsembleDecision,
        escalation_callback: Optional[Callable] = None
    ) -> EnsembleDecision:
        """
        Resolve a conflicting decision.

        Args:
            decision: The conflicting decision
            escalation_callback: Optional callback for escalation

        Returns:
            Resolved decision
        """
        if decision.is_strong_consensus:
            return decision

        # Try escalation if available
        if self.escalation_model and escalation_callback:
            logger.info(f"Escalating conflict to {self.escalation_model}")
            escalated = await escalation_callback(
                symbol=decision.symbol,
                votes=decision.individual_votes,
                model=self.escalation_model
            )
            if escalated:
                return escalated

        # Default to conservative action
        logger.warning(
            f"Conflict unresolved for {decision.symbol}, "
            f"defaulting to {self.conservative_default}"
        )

        decision.action = self.conservative_default
        decision.reasoning = f"Conflict resolved: defaulted to {self.conservative_default}"

        return decision
