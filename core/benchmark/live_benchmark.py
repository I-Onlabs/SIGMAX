"""
Live Benchmarking Framework
Inspired by AI-Trader's uncontaminated real-market evaluation

Unlike historical backtesting, live benchmarking:
- Uses real-time market data (no look-ahead possible)
- Tests agents under actual market conditions
- Provides uncontaminated performance metrics
- Enables fair head-to-head comparison

Key Features:
- Identical conditions for all agents
- No human intervention during evaluation
- Standardized metrics (Sharpe, drawdown, win rate)
- Real-time performance tracking
"""

from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
from loguru import logger
import asyncio
import uuid
import json


class BenchmarkState(Enum):
    """Benchmark run states."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentRegistration:
    """Registered agent for benchmarking."""
    agent_id: str
    name: str
    model: str
    strategy: str
    initial_capital: float
    current_capital: float = 0.0
    positions: Dict[str, float] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if self.current_capital == 0:
            self.current_capital = self.initial_capital


@dataclass
class BenchmarkMetrics:
    """Real-time benchmark metrics for an agent."""
    agent_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Returns
    total_return: float = 0.0
    total_return_pct: float = 0.0
    daily_return: float = 0.0

    # Risk metrics
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    current_drawdown: float = 0.0

    # Trading metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_trade_pnl: float = 0.0

    # Timing
    avg_hold_time: timedelta = field(default_factory=lambda: timedelta(0))

    # Current state
    current_capital: float = 0.0
    open_positions: int = 0
    unrealized_pnl: float = 0.0


@dataclass
class BenchmarkCheckpoint:
    """Checkpoint of benchmark state."""
    checkpoint_id: str
    timestamp: datetime
    round_number: int
    agent_metrics: Dict[str, BenchmarkMetrics]
    market_state: Dict[str, Any]


class LiveBenchmark:
    """
    Live benchmarking framework for uncontaminated AI evaluation.

    Usage:
        benchmark = LiveBenchmark(
            initial_capital=50000,
            symbols=["BTC/USDT", "ETH/USDT"],
            duration_hours=24
        )

        # Register agents
        benchmark.register_agent(agent1, "gpt4-momentum")
        benchmark.register_agent(agent2, "claude-sentiment")

        # Run benchmark
        results = await benchmark.run()

        # Get leaderboard
        print(benchmark.get_leaderboard())
    """

    def __init__(
        self,
        initial_capital: float = 50000,
        symbols: List[str] = None,
        duration_hours: Optional[float] = None,
        checkpoint_interval_minutes: int = 60,
        max_position_pct: float = 0.2,
        commission: float = 0.001
    ):
        """
        Initialize live benchmark.

        Args:
            initial_capital: Starting capital for each agent
            symbols: Symbols to trade
            duration_hours: Benchmark duration (None = indefinite)
            checkpoint_interval_minutes: How often to checkpoint
            max_position_pct: Max position size as fraction of capital
            commission: Trading commission rate
        """
        self.benchmark_id = str(uuid.uuid4())[:8]
        self.initial_capital = initial_capital
        self.symbols = symbols or ["BTC/USDT"]
        self.duration = timedelta(hours=duration_hours) if duration_hours else None
        self.checkpoint_interval = timedelta(minutes=checkpoint_interval_minutes)
        self.max_position_pct = max_position_pct
        self.commission = commission

        # State
        self.state = BenchmarkState.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.round_number = 0

        # Agents
        self.agents: Dict[str, AgentRegistration] = {}
        self.agent_callbacks: Dict[str, Callable] = {}

        # Metrics
        self.metrics: Dict[str, BenchmarkMetrics] = {}
        self.metrics_history: Dict[str, List[BenchmarkMetrics]] = {}

        # Checkpoints
        self.checkpoints: List[BenchmarkCheckpoint] = []

        # Trade history
        self.trades: Dict[str, List[Dict]] = {}

        logger.info(f"Live Benchmark initialized: {self.benchmark_id}")

    def register_agent(
        self,
        decision_callback: Callable,
        name: str,
        model: str = "unknown",
        strategy: str = "unknown"
    ) -> str:
        """
        Register an agent for the benchmark.

        Args:
            decision_callback: Async function that returns trading decision
            name: Agent name
            model: Model identifier
            strategy: Strategy type

        Returns:
            Agent ID
        """
        agent_id = f"{name}_{str(uuid.uuid4())[:4]}"

        registration = AgentRegistration(
            agent_id=agent_id,
            name=name,
            model=model,
            strategy=strategy,
            initial_capital=self.initial_capital
        )

        self.agents[agent_id] = registration
        self.agent_callbacks[agent_id] = decision_callback
        self.metrics[agent_id] = BenchmarkMetrics(agent_id=agent_id)
        self.metrics_history[agent_id] = []
        self.trades[agent_id] = []

        logger.info(f"Registered agent: {name} ({model}, {strategy})")
        return agent_id

    def unregister_agent(self, agent_id: str):
        """Unregister an agent from the benchmark."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            del self.agent_callbacks[agent_id]
            del self.metrics[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")

    async def run(
        self,
        data_feed: AsyncGenerator,
        max_rounds: Optional[int] = None
    ) -> Dict[str, BenchmarkMetrics]:
        """
        Run the live benchmark.

        Args:
            data_feed: Async generator yielding market data
            max_rounds: Optional max trading rounds

        Returns:
            Final metrics for each agent
        """
        if len(self.agents) < 1:
            raise ValueError("At least one agent must be registered")

        self.state = BenchmarkState.RUNNING
        self.start_time = datetime.utcnow()

        logger.info(f"Starting live benchmark: {len(self.agents)} agents")

        try:
            last_checkpoint = datetime.utcnow()

            async for market_data in data_feed:
                if not self._should_continue(max_rounds):
                    break

                # Run trading round
                await self._run_round(market_data)
                self.round_number += 1

                # Checkpoint if needed
                if datetime.utcnow() - last_checkpoint >= self.checkpoint_interval:
                    self._create_checkpoint(market_data)
                    last_checkpoint = datetime.utcnow()

                # Log progress
                if self.round_number % 10 == 0:
                    logger.info(f"Benchmark round {self.round_number}")

        except Exception as e:
            logger.error(f"Benchmark error: {e}")
            self.state = BenchmarkState.FAILED
            raise

        self.state = BenchmarkState.COMPLETED
        self.end_time = datetime.utcnow()

        # Final metrics calculation
        self._calculate_final_metrics()

        logger.info(
            f"Benchmark complete: {self.round_number} rounds, "
            f"duration {self.end_time - self.start_time}"
        )

        return self.metrics

    def _should_continue(self, max_rounds: Optional[int]) -> bool:
        """Check if benchmark should continue."""
        if self.state != BenchmarkState.RUNNING:
            return False

        if max_rounds and self.round_number >= max_rounds:
            return False

        if self.duration:
            elapsed = datetime.utcnow() - self.start_time
            if elapsed >= self.duration:
                return False

        return True

    async def _run_round(self, market_data: Dict[str, Any]):
        """Run a single trading round for all agents."""
        # Get decisions from all agents in parallel
        tasks = []
        for agent_id, callback in self.agent_callbacks.items():
            agent = self.agents[agent_id]
            task = self._get_agent_decision(
                agent_id, callback, market_data, agent.positions
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process decisions
        for i, (agent_id, decision) in enumerate(zip(self.agent_callbacks.keys(), results)):
            if isinstance(decision, Exception):
                logger.error(f"Agent {agent_id} error: {decision}")
                continue

            await self._process_decision(agent_id, decision, market_data)

        # Update metrics
        self._update_metrics(market_data)

    async def _get_agent_decision(
        self,
        agent_id: str,
        callback: Callable,
        market_data: Dict[str, Any],
        positions: Dict[str, float]
    ) -> Dict[str, Any]:
        """Get decision from an agent."""
        try:
            decision = await callback(market_data, positions)
            return decision
        except Exception as e:
            return {"error": str(e), "action": "hold"}

    async def _process_decision(
        self,
        agent_id: str,
        decision: Dict[str, Any],
        market_data: Dict[str, Any]
    ):
        """Process an agent's trading decision."""
        if decision.get("error") or decision.get("action") == "hold":
            return

        agent = self.agents[agent_id]
        action = decision.get("action")
        symbol = decision.get("symbol")
        amount = decision.get("amount", 0)

        if not symbol or symbol not in self.symbols:
            return

        price = market_data.get(symbol, {}).get("price", 0)
        if price <= 0:
            return

        # Execute trade
        if action == "buy":
            self._execute_buy(agent_id, symbol, amount, price)
        elif action == "sell":
            self._execute_sell(agent_id, symbol, amount, price)

    def _execute_buy(
        self,
        agent_id: str,
        symbol: str,
        amount: float,
        price: float
    ):
        """Execute a buy order."""
        agent = self.agents[agent_id]

        # Check capital constraints
        max_amount = agent.current_capital * self.max_position_pct / price
        actual_amount = min(amount, max_amount)

        if actual_amount <= 0:
            return

        cost = actual_amount * price
        commission = cost * self.commission

        if agent.current_capital < cost + commission:
            return

        # Update state
        agent.current_capital -= cost + commission
        agent.positions[symbol] = agent.positions.get(symbol, 0) + actual_amount

        # Record trade
        trade = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "buy",
            "symbol": symbol,
            "amount": actual_amount,
            "price": price,
            "cost": cost,
            "commission": commission
        }
        self.trades[agent_id].append(trade)
        self.metrics[agent_id].total_trades += 1

    def _execute_sell(
        self,
        agent_id: str,
        symbol: str,
        amount: float,
        price: float
    ):
        """Execute a sell order."""
        agent = self.agents[agent_id]

        current_position = agent.positions.get(symbol, 0)
        if current_position <= 0:
            return

        actual_amount = min(amount, current_position)
        proceeds = actual_amount * price
        commission = proceeds * self.commission

        # Update state
        agent.current_capital += proceeds - commission
        agent.positions[symbol] = current_position - actual_amount

        if agent.positions[symbol] <= 0:
            del agent.positions[symbol]

        # Record trade
        trade = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "sell",
            "symbol": symbol,
            "amount": actual_amount,
            "price": price,
            "proceeds": proceeds,
            "commission": commission
        }
        self.trades[agent_id].append(trade)
        self.metrics[agent_id].total_trades += 1

    def _update_metrics(self, market_data: Dict[str, Any]):
        """Update metrics for all agents."""
        for agent_id, agent in self.agents.items():
            metrics = self.metrics[agent_id]

            # Calculate unrealized PnL
            unrealized = 0
            for symbol, amount in agent.positions.items():
                price = market_data.get(symbol, {}).get("price", 0)
                unrealized += amount * price

            metrics.unrealized_pnl = unrealized
            metrics.current_capital = agent.current_capital + unrealized
            metrics.open_positions = len(agent.positions)

            # Calculate returns
            total_value = metrics.current_capital
            metrics.total_return = total_value - agent.initial_capital
            metrics.total_return_pct = (
                (total_value / agent.initial_capital - 1) * 100
            )

            # Track drawdown
            if metrics.total_return_pct < metrics.max_drawdown_pct:
                metrics.max_drawdown_pct = metrics.total_return_pct
                metrics.max_drawdown = metrics.total_return

            metrics.current_drawdown = metrics.total_return_pct - metrics.max_drawdown_pct

            # Store in history
            metrics.timestamp = datetime.utcnow()
            self.metrics_history[agent_id].append(
                BenchmarkMetrics(
                    agent_id=agent_id,
                    total_return=metrics.total_return,
                    total_return_pct=metrics.total_return_pct,
                    current_capital=metrics.current_capital,
                    total_trades=metrics.total_trades
                )
            )

    def _create_checkpoint(self, market_data: Dict[str, Any]):
        """Create a checkpoint of current state."""
        checkpoint = BenchmarkCheckpoint(
            checkpoint_id=str(uuid.uuid4())[:8],
            timestamp=datetime.utcnow(),
            round_number=self.round_number,
            agent_metrics={
                agent_id: BenchmarkMetrics(
                    agent_id=agent_id,
                    **{k: v for k, v in self.metrics[agent_id].__dict__.items()
                       if k != "agent_id"}
                )
                for agent_id in self.agents
            },
            market_state=market_data
        )

        self.checkpoints.append(checkpoint)
        logger.debug(f"Checkpoint created: {checkpoint.checkpoint_id}")

    def _calculate_final_metrics(self):
        """Calculate final benchmark metrics."""
        for agent_id in self.agents:
            metrics = self.metrics[agent_id]
            trades = self.trades[agent_id]

            if not trades:
                continue

            # Win rate
            # Would need to pair buys/sells to calculate actual P&L per trade
            # For now, use simplified calculation

            # Sharpe ratio (simplified - daily returns)
            history = self.metrics_history[agent_id]
            if len(history) >= 2:
                returns = [
                    (history[i].total_return_pct - history[i-1].total_return_pct)
                    for i in range(1, len(history))
                ]
                if returns:
                    import numpy as np
                    mean_return = np.mean(returns)
                    std_return = np.std(returns)
                    if std_return > 0:
                        metrics.sharpe_ratio = (mean_return * np.sqrt(252)) / std_return

    def get_leaderboard(self, sort_by: str = "total_return_pct") -> List[Dict[str, Any]]:
        """Get benchmark leaderboard."""
        leaderboard = []

        for agent_id, agent in self.agents.items():
            metrics = self.metrics[agent_id]

            leaderboard.append({
                "rank": 0,
                "agent_id": agent_id,
                "name": agent.name,
                "model": agent.model,
                "strategy": agent.strategy,
                "total_return": round(metrics.total_return, 2),
                "total_return_pct": round(metrics.total_return_pct, 2),
                "sharpe_ratio": round(metrics.sharpe_ratio, 2),
                "max_drawdown_pct": round(metrics.max_drawdown_pct, 2),
                "total_trades": metrics.total_trades,
                "win_rate": round(metrics.win_rate, 3),
                "current_capital": round(metrics.current_capital, 2)
            })

        # Sort
        leaderboard.sort(key=lambda x: x.get(sort_by, 0), reverse=True)

        # Assign ranks
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1

        return leaderboard

    def pause(self):
        """Pause the benchmark."""
        if self.state == BenchmarkState.RUNNING:
            self.state = BenchmarkState.PAUSED
            logger.info("Benchmark paused")

    def resume(self):
        """Resume the benchmark."""
        if self.state == BenchmarkState.PAUSED:
            self.state = BenchmarkState.RUNNING
            logger.info("Benchmark resumed")

    def stop(self):
        """Stop the benchmark."""
        self.state = BenchmarkState.COMPLETED
        self.end_time = datetime.utcnow()
        logger.info("Benchmark stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get benchmark status."""
        return {
            "benchmark_id": self.benchmark_id,
            "state": self.state.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "round_number": self.round_number,
            "agents": len(self.agents),
            "symbols": self.symbols,
            "initial_capital": self.initial_capital,
            "checkpoints": len(self.checkpoints),
            "duration": str(self.duration) if self.duration else "indefinite"
        }

    def export_results(self, format: str = "json") -> str:
        """Export benchmark results."""
        results = {
            "benchmark_id": self.benchmark_id,
            "status": self.get_status(),
            "leaderboard": self.get_leaderboard(),
            "checkpoints": [
                {
                    "checkpoint_id": c.checkpoint_id,
                    "timestamp": c.timestamp.isoformat(),
                    "round": c.round_number
                }
                for c in self.checkpoints
            ],
            "trades": {
                agent_id: trades[-100:]  # Last 100 trades per agent
                for agent_id, trades in self.trades.items()
            }
        }

        if format == "json":
            return json.dumps(results, indent=2, default=str)
        else:
            # CSV format for leaderboard
            rows = ["rank,name,model,strategy,return_pct,sharpe,drawdown,trades"]
            for entry in results["leaderboard"]:
                rows.append(
                    f"{entry['rank']},{entry['name']},{entry['model']},"
                    f"{entry['strategy']},{entry['total_return_pct']:.2f},"
                    f"{entry['sharpe_ratio']:.2f},{entry['max_drawdown_pct']:.2f},"
                    f"{entry['total_trades']}"
                )
            return "\n".join(rows)


async def create_mock_data_feed(
    symbols: List[str],
    duration_seconds: int = 60,
    interval_seconds: float = 1.0
) -> AsyncGenerator:
    """Create a mock data feed for testing."""
    import random

    prices = {symbol: 100 + random.random() * 1000 for symbol in symbols}
    start_time = datetime.utcnow()

    while (datetime.utcnow() - start_time).total_seconds() < duration_seconds:
        # Random walk prices
        for symbol in symbols:
            change = (random.random() - 0.5) * 0.02  # ±1% change
            prices[symbol] *= (1 + change)

        yield {
            symbol: {
                "price": prices[symbol],
                "timestamp": datetime.utcnow().isoformat()
            }
            for symbol in symbols
        }

        await asyncio.sleep(interval_seconds)
