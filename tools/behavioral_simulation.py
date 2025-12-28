#!/usr/bin/env python3
"""
Multi-Agent Behavioral Finance Simulation
TwinMarket-inspired market simulation with diverse agent personalities

Features:
- Multiple agent personas with distinct behavioral profiles
- Social network with sentiment propagation
- Order book matching with realistic execution
- Fear & Greed dynamics
- Market microstructure simulation

Usage:
    python tools/behavioral_simulation.py --agents 20 --rounds 100 --symbol BTC/USDT
"""

import argparse
import asyncio
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import json

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from core.behavioral import (
    InvestorBeliefSystem,
    InvestorPersona,
    MarketAttitude,
    RiskTolerance,
    InvestmentStyle,
    BehavioralBiasEngine,
    BiasProfile,
    PositionHistory,
    SocialSentimentNetwork,
    SocialRole,
    SentimentType,
    FearGreedIndex,
    MatchingEngine,
    OrderSide,
    OrderType
)


@dataclass
class SimulationAgent:
    """An agent in the simulation."""
    agent_id: str
    persona: InvestorPersona
    bias_profile: BiasProfile
    social_role: SocialRole
    cash: float = 100000.0
    positions: Dict[str, float] = field(default_factory=dict)
    entry_prices: Dict[str, float] = field(default_factory=dict)
    trades: List[Dict] = field(default_factory=list)
    pnl: float = 0.0

    def get_position_value(self, prices: Dict[str, float]) -> float:
        """Calculate total position value."""
        return sum(
            qty * prices.get(symbol, 0)
            for symbol, qty in self.positions.items()
        )

    def get_total_value(self, prices: Dict[str, float]) -> float:
        """Calculate total portfolio value."""
        return self.cash + self.get_position_value(prices)


@dataclass
class SimulationResult:
    """Result of a simulation run."""
    rounds: int
    agents: int
    symbol: str
    final_price: float
    price_history: List[float]
    volume_history: List[float]
    sentiment_history: List[float]
    fear_greed_history: List[Dict]
    agent_performance: Dict[str, Dict]
    herd_events: List[Dict]
    trade_count: int
    duration_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rounds": self.rounds,
            "agents": self.agents,
            "symbol": self.symbol,
            "final_price": self.final_price,
            "price_change_pct": (self.final_price - self.price_history[0]) / self.price_history[0] * 100,
            "volatility": self._calculate_volatility(),
            "total_trades": self.trade_count,
            "herd_events_count": len(self.herd_events),
            "duration_seconds": self.duration_seconds,
            "top_performers": self._get_top_performers(),
            "worst_performers": self._get_worst_performers()
        }

    def _calculate_volatility(self) -> float:
        if len(self.price_history) < 2:
            return 0.0
        returns = [
            (self.price_history[i] - self.price_history[i-1]) / self.price_history[i-1]
            for i in range(1, len(self.price_history))
        ]
        if not returns:
            return 0.0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        return variance ** 0.5

    def _get_top_performers(self, n: int = 3) -> List[Dict]:
        sorted_agents = sorted(
            self.agent_performance.items(),
            key=lambda x: x[1].get("final_pnl", 0),
            reverse=True
        )
        return [
            {"agent_id": aid, "pnl": data.get("final_pnl", 0)}
            for aid, data in sorted_agents[:n]
        ]

    def _get_worst_performers(self, n: int = 3) -> List[Dict]:
        sorted_agents = sorted(
            self.agent_performance.items(),
            key=lambda x: x[1].get("final_pnl", 0)
        )
        return [
            {"agent_id": aid, "pnl": data.get("final_pnl", 0)}
            for aid, data in sorted_agents[:n]
        ]


class BehavioralMarketSimulation:
    """
    Multi-agent market simulation with behavioral finance dynamics.

    Simulates a market with diverse agent personalities,
    social sentiment propagation, and realistic order matching.
    """

    # Agent type distributions
    AGENT_DISTRIBUTION = {
        "conservative_value": 0.15,
        "aggressive_momentum": 0.15,
        "balanced_growth": 0.20,
        "contrarian_deep": 0.10,
        "institutional_steady": 0.10,
        "retail_fomo": 0.20,
        "noise_trader": 0.10
    }

    def __init__(
        self,
        symbol: str = "BTC/USDT",
        initial_price: float = 50000.0,
        num_agents: int = 20,
        seed: Optional[int] = None
    ):
        """
        Initialize simulation.

        Args:
            symbol: Trading symbol
            initial_price: Starting price
            num_agents: Number of agents
            seed: Random seed for reproducibility
        """
        self.symbol = symbol
        self.initial_price = initial_price
        self.current_price = initial_price
        self.num_agents = num_agents

        if seed is not None:
            random.seed(seed)

        # Initialize components
        self.belief_system = InvestorBeliefSystem()
        self.bias_engine = BehavioralBiasEngine(randomize_biases=True)
        self.social_network = SocialSentimentNetwork()
        self.fear_greed = FearGreedIndex()
        self.matching_engine = MatchingEngine(enable_logging=False)

        # Agents
        self.agents: Dict[str, SimulationAgent] = {}

        # Market state
        self.price_history: List[float] = [initial_price]
        self.volume_history: List[float] = []
        self.sentiment_history: List[float] = []
        self.round_number = 0

        # Create agents
        self._create_agents()

        logger.info(f"Simulation initialized: {num_agents} agents, {symbol} @ ${initial_price}")

    def _create_agents(self):
        """Create diverse agent population."""
        agent_types = []
        for agent_type, proportion in self.AGENT_DISTRIBUTION.items():
            count = int(self.num_agents * proportion)
            agent_types.extend([agent_type] * count)

        # Fill remaining with random types
        while len(agent_types) < self.num_agents:
            agent_types.append(random.choice(list(self.AGENT_DISTRIBUTION.keys())))

        random.shuffle(agent_types)

        for i, agent_type in enumerate(agent_types):
            agent_id = f"agent_{i:03d}"
            self._create_agent(agent_id, agent_type)

        # Create social network connections
        self._create_social_connections()

    def _create_agent(self, agent_id: str, agent_type: str):
        """Create a single agent."""
        # Map agent type to configurations
        type_configs = {
            "conservative_value": {
                "persona": "conservative_value",
                "bias": "rational",
                "role": SocialRole.ANALYST
            },
            "aggressive_momentum": {
                "persona": "aggressive_momentum",
                "bias": "emotional",
                "role": SocialRole.INFLUENCER
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
                "role": SocialRole.NOISE_TRADER
            },
            "noise_trader": {
                "persona": "aggressive_momentum",
                "bias": "emotional",
                "role": SocialRole.NOISE_TRADER
            }
        }

        config = type_configs.get(agent_type, type_configs["balanced_growth"])

        persona = self.belief_system.create_persona(
            name=agent_id,
            template=config["persona"]
        )

        bias_profile = self.bias_engine.create_profile(template=config["bias"])

        agent = SimulationAgent(
            agent_id=agent_id,
            persona=persona,
            bias_profile=bias_profile,
            social_role=config["role"],
            cash=100000.0 + random.uniform(-20000, 20000)
        )

        self.agents[agent_id] = agent

        # Register in social network
        self.social_network.register_agent(
            agent_id=agent_id,
            role=config["role"]
        )

    def _create_social_connections(self):
        """Create social network connections."""
        agent_ids = list(self.agents.keys())

        # Find influencers
        influencers = [
            aid for aid, agent in self.agents.items()
            if agent.social_role == SocialRole.INFLUENCER
        ]

        # Followers follow influencers
        for agent_id, agent in self.agents.items():
            if agent.social_role in [SocialRole.FOLLOWER, SocialRole.NOISE_TRADER]:
                # Follow 1-3 influencers
                for inf in random.sample(influencers, min(len(influencers), random.randint(1, 3))):
                    self.social_network.add_follow(agent_id, inf)

            # Random connections
            num_connections = random.randint(1, 5)
            for other in random.sample(agent_ids, min(len(agent_ids), num_connections)):
                if other != agent_id:
                    self.social_network.add_follow(agent_id, other)

    async def run(self, rounds: int = 100) -> SimulationResult:
        """
        Run the simulation.

        Args:
            rounds: Number of trading rounds

        Returns:
            SimulationResult
        """
        start_time = datetime.utcnow()

        for round_num in range(rounds):
            self.round_number = round_num
            await self._run_round()

            if round_num % 10 == 0:
                logger.info(f"Round {round_num}/{rounds}, Price: ${self.current_price:.2f}")

        duration = (datetime.utcnow() - start_time).total_seconds()

        # Calculate final performance
        agent_performance = {}
        prices = {self.symbol: self.current_price}

        for agent_id, agent in self.agents.items():
            final_value = agent.get_total_value(prices)
            initial_value = 100000.0  # Approximate initial
            pnl = final_value - initial_value

            agent_performance[agent_id] = {
                "persona": agent.persona.name,
                "role": agent.social_role.value,
                "final_value": final_value,
                "final_pnl": pnl,
                "trade_count": len(agent.trades),
                "position": agent.positions.get(self.symbol, 0)
            }

        return SimulationResult(
            rounds=rounds,
            agents=len(self.agents),
            symbol=self.symbol,
            final_price=self.current_price,
            price_history=self.price_history,
            volume_history=self.volume_history,
            sentiment_history=self.sentiment_history,
            fear_greed_history=self.fear_greed.get_history(hours=24),
            agent_performance=agent_performance,
            herd_events=self.social_network.get_recent_herd_events(hours=24),
            trade_count=sum(len(a.trades) for a in self.agents.values()),
            duration_seconds=duration
        )

    async def _run_round(self):
        """Run a single trading round."""
        # 1. Calculate market sentiment
        sentiment = self._calculate_market_sentiment()
        self.sentiment_history.append(sentiment)

        # 2. Calculate Fear & Greed
        fg = self.fear_greed.calculate(
            social_sentiment=sentiment,
            volatility_percentile=self._get_volatility_percentile(),
            price_momentum=self._get_momentum(),
            volume_ratio=self._get_volume_ratio()
        )

        # 3. Each agent makes decisions
        orders = []
        for agent_id, agent in self.agents.items():
            order = await self._agent_decision(agent, sentiment, fg)
            if order:
                orders.append(order)

        # 4. Execute orders
        round_volume = 0.0
        for order_data in orders:
            order, trades = self.matching_engine.submit_order(**order_data)
            if trades:
                for trade in trades:
                    round_volume += trade.quantity
                    self._record_trade(trade)
                    self.current_price = trade.price

        self.volume_history.append(round_volume)

        # 5. Update price based on order flow
        self._update_price(orders)

        self.price_history.append(self.current_price)

    async def _agent_decision(
        self,
        agent: SimulationAgent,
        market_sentiment: float,
        fear_greed: Dict
    ) -> Optional[Dict]:
        """Generate agent's trading decision."""
        # Generate belief
        belief = self.belief_system.generate_belief(
            persona=agent.persona,
            market_data={"price": self.current_price, "change_pct": self._get_momentum() * 100},
            social_sentiment=market_sentiment
        )

        # Base decision from belief
        if belief.direction > 0.3:
            base_action = "BUY"
        elif belief.direction < -0.3:
            base_action = "SELL"
        else:
            base_action = "HOLD"

        if base_action == "HOLD":
            return None

        # Create position history for bias engine
        position = None
        if self.symbol in agent.positions and agent.positions[self.symbol] > 0:
            position = PositionHistory(
                symbol=self.symbol,
                entry_price=agent.entry_prices.get(self.symbol, self.current_price),
                entry_time=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
                current_price=self.current_price,
                quantity=agent.positions[self.symbol]
            )

        # Apply biases
        decision = {
            "action": base_action,
            "symbol": self.symbol,
            "confidence": belief.confidence,
            "size": min(agent.cash / self.current_price * 0.1, 1.0)
        }

        adjustment = self.bias_engine.apply_biases(
            decision=decision,
            profile=agent.bias_profile,
            position_history=position,
            market_sentiment=market_sentiment,
            asset_volatility=self._get_volatility_percentile() / 100
        )

        adjusted = adjustment.behavioral_decision

        # Check if agent can execute
        if adjusted["action"] == "BUY":
            max_qty = agent.cash / self.current_price * 0.8
            quantity = min(adjusted.get("size", 0.1), max_qty)
            if quantity < 0.001 or agent.cash < self.current_price * quantity:
                return None

            return {
                "agent_id": agent.agent_id,
                "symbol": self.symbol,
                "side": OrderSide.BUY,
                "order_type": OrderType.LIMIT,
                "quantity": quantity,
                "price": self.current_price * (1 + random.uniform(0, 0.01))
            }

        elif adjusted["action"] == "SELL":
            position_qty = agent.positions.get(self.symbol, 0)
            if position_qty < 0.001:
                return None

            quantity = min(adjusted.get("size", 0.1), position_qty)

            return {
                "agent_id": agent.agent_id,
                "symbol": self.symbol,
                "side": OrderSide.SELL,
                "order_type": OrderType.LIMIT,
                "quantity": quantity,
                "price": self.current_price * (1 - random.uniform(0, 0.01))
            }

        return None

    def _record_trade(self, trade):
        """Record a trade for the involved agents."""
        buyer = self.agents.get(trade.buyer_agent_id)
        seller = self.agents.get(trade.seller_agent_id)

        if buyer:
            cost = trade.price * trade.quantity
            buyer.cash -= cost
            buyer.positions[trade.symbol] = buyer.positions.get(trade.symbol, 0) + trade.quantity
            if trade.symbol not in buyer.entry_prices:
                buyer.entry_prices[trade.symbol] = trade.price
            buyer.trades.append({
                "side": "buy",
                "price": trade.price,
                "quantity": trade.quantity,
                "round": self.round_number
            })

        if seller:
            proceeds = trade.price * trade.quantity
            seller.cash += proceeds
            seller.positions[trade.symbol] = seller.positions.get(trade.symbol, 0) - trade.quantity
            seller.trades.append({
                "side": "sell",
                "price": trade.price,
                "quantity": trade.quantity,
                "round": self.round_number
            })

    def _update_price(self, orders: List[Dict]):
        """Update price based on order imbalance."""
        buy_volume = sum(o["quantity"] for o in orders if o["side"] == OrderSide.BUY)
        sell_volume = sum(o["quantity"] for o in orders if o["side"] == OrderSide.SELL)

        total = buy_volume + sell_volume
        if total > 0:
            imbalance = (buy_volume - sell_volume) / total
            # Price impact: max 2% per round
            price_change = imbalance * 0.02
            self.current_price *= (1 + price_change)

        # Add small random noise
        self.current_price *= (1 + random.uniform(-0.001, 0.001))

    def _calculate_market_sentiment(self) -> float:
        """Calculate overall market sentiment."""
        agg = self.social_network.get_aggregate_sentiment()
        return agg.get("score", 0.0)

    def _get_momentum(self) -> float:
        """Get price momentum."""
        if len(self.price_history) < 2:
            return 0.0
        return (self.current_price - self.price_history[-1]) / self.price_history[-1]

    def _get_volatility_percentile(self) -> float:
        """Get volatility percentile."""
        if len(self.price_history) < 10:
            return 50.0

        returns = [
            (self.price_history[i] - self.price_history[i-1]) / self.price_history[i-1]
            for i in range(-10, 0)
        ]
        volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5
        # Normalize to percentile (rough approximation)
        return min(volatility * 1000, 100)

    def _get_volume_ratio(self) -> float:
        """Get volume ratio vs average."""
        if len(self.volume_history) < 5:
            return 1.0

        recent = self.volume_history[-1] if self.volume_history else 0
        avg = sum(self.volume_history[-5:]) / min(len(self.volume_history), 5)

        if avg == 0:
            return 1.0
        return recent / avg


async def main():
    parser = argparse.ArgumentParser(description="Behavioral Finance Market Simulation")
    parser.add_argument("--agents", type=int, default=20, help="Number of agents")
    parser.add_argument("--rounds", type=int, default=100, help="Number of rounds")
    parser.add_argument("--symbol", type=str, default="BTC/USDT", help="Trading symbol")
    parser.add_argument("--price", type=float, default=50000.0, help="Initial price")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file")

    args = parser.parse_args()

    logger.info(f"Starting simulation: {args.agents} agents, {args.rounds} rounds")

    sim = BehavioralMarketSimulation(
        symbol=args.symbol,
        initial_price=args.price,
        num_agents=args.agents,
        seed=args.seed
    )

    result = await sim.run(rounds=args.rounds)

    # Print summary
    summary = result.to_dict()
    print("\n" + "=" * 60)
    print("SIMULATION RESULTS")
    print("=" * 60)
    print(f"Symbol: {summary['symbol']}")
    print(f"Rounds: {summary['rounds']}")
    print(f"Agents: {summary['agents']}")
    print(f"Final Price: ${result.final_price:,.2f}")
    print(f"Price Change: {summary['price_change_pct']:.2f}%")
    print(f"Volatility: {summary['volatility']:.4f}")
    print(f"Total Trades: {summary['total_trades']}")
    print(f"Herd Events: {summary['herd_events_count']}")
    print(f"Duration: {summary['duration_seconds']:.2f}s")
    print("\nTop Performers:")
    for p in summary['top_performers']:
        print(f"  {p['agent_id']}: ${p['pnl']:+,.2f}")
    print("\nWorst Performers:")
    for p in summary['worst_performers']:
        print(f"  {p['agent_id']}: ${p['pnl']:+,.2f}")
    print("=" * 60)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
