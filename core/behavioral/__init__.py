"""
SIGMAX Behavioral Finance Module - TwinMarket-Inspired Simulation
Multi-agent behavioral finance simulation with realistic market dynamics

Features:
- Investor belief and personality systems
- Behavioral bias modeling (disposition, loss aversion, etc.)
- Social sentiment and herd behavior
- Order book matching engine
"""

from .investor_belief import (
    InvestorPersona,
    InvestorBeliefSystem,
    MarketBelief,
    MarketAttitude,
    InvestmentStyle,
    RiskTolerance,
    TimeHorizon
)

from .behavioral_biases import (
    BehavioralBiasEngine,
    BiasProfile,
    BiasAdjustment,
    BiasType,
    PositionHistory,
    calculate_prospect_theory_value,
    calculate_probability_weight
)

from .social_sentiment import (
    SocialSentimentNetwork,
    SocialAgent,
    SocialRole,
    SentimentSignal,
    SentimentType,
    HerdEvent,
    FearGreedIndex
)

from .matching_engine import (
    MatchingEngine,
    OrderBook,
    Order,
    Trade,
    OrderSide,
    OrderType,
    OrderStatus,
    OrderBookLevel
)

__all__ = [
    # Investor Belief
    "InvestorPersona",
    "InvestorBeliefSystem",
    "MarketBelief",
    "MarketAttitude",
    "InvestmentStyle",
    "RiskTolerance",
    "TimeHorizon",
    # Behavioral Biases
    "BehavioralBiasEngine",
    "BiasProfile",
    "BiasAdjustment",
    "BiasType",
    "PositionHistory",
    "calculate_prospect_theory_value",
    "calculate_probability_weight",
    # Social Sentiment
    "SocialSentimentNetwork",
    "SocialAgent",
    "SocialRole",
    "SentimentSignal",
    "SentimentType",
    "HerdEvent",
    "FearGreedIndex",
    # Matching Engine
    "MatchingEngine",
    "OrderBook",
    "Order",
    "Trade",
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "OrderBookLevel"
]
