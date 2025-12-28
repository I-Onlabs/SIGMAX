"""
Multi-Model Competition Arena
Inspired by AI-Trader's multi-model benchmarking approach

This module enables head-to-head competition between different LLMs
with different trading strategies, providing:
- Fair comparison under identical conditions
- Strategy evolution through competition
- Model cost/performance tradeoffs
- Ensemble recommendations
"""

from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
from loguru import logger
import asyncio
import uuid


class ModelProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    OLLAMA = "ollama"
    GROQ = "groq"


class StrategyType(Enum):
    """Trading strategy types."""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    SENTIMENT = "sentiment"
    QUANTITATIVE = "quantitative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"


@dataclass
class ModelConfig:
    """Configuration for a competing model."""
    name: str
    provider: ModelProvider
    model_id: str
    strategy: StrategyType
    temperature: float = 0.7
    max_tokens: int = 1000
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0

    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.strategy.value})"


@dataclass
class TradeDecision:
    """A trade decision from a competing model."""
    model_name: str
    symbol: str
    action: str  # "buy", "sell", "hold"
    amount: float
    confidence: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelPerformance:
    """Performance metrics for a competing model."""
    model_name: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    total_return_pct: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate: float = 0.0
    avg_confidence: float = 0.0
    total_cost_usd: float = 0.0
    decisions: List[TradeDecision] = field(default_factory=list)

    @property
    def cost_per_trade(self) -> float:
        if self.total_trades == 0:
            return 0
        return self.total_cost_usd / self.total_trades

    @property
    def profit_per_dollar_spent(self) -> float:
        if self.total_cost_usd == 0:
            return 0
        return self.total_pnl / self.total_cost_usd


class BaseCompetitor(ABC):
    """Base class for competing trading agents."""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.current_capital = 0.0
        self.positions: Dict[str, float] = {}
        self._total_cost = 0.0
        self._token_usage = {"input": 0, "output": 0}

    @abstractmethod
    async def make_decision(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        current_positions: Dict[str, float]
    ) -> TradeDecision:
        """Make a trading decision for a symbol."""
        pass

    def register_with_capital(self, capital: float):
        """Register competitor with starting capital."""
        self.current_capital = capital
        self.positions = {"USD": capital}

    def track_tokens(self, input_tokens: int, output_tokens: int):
        """Track token usage for cost calculation."""
        self._token_usage["input"] += input_tokens
        self._token_usage["output"] += output_tokens

        cost = (
            (input_tokens / 1000) * self.config.cost_per_1k_input +
            (output_tokens / 1000) * self.config.cost_per_1k_output
        )
        self._total_cost += cost

    @property
    def total_cost(self) -> float:
        return self._total_cost


class LLMCompetitor(BaseCompetitor):
    """A competing LLM-based trading agent."""

    def __init__(
        self,
        config: ModelConfig,
        llm_client=None,
        system_prompt: Optional[str] = None
    ):
        super().__init__(config)
        self.llm_client = llm_client
        self.system_prompt = system_prompt or self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        """Generate default system prompt based on strategy."""
        strategy_prompts = {
            StrategyType.MOMENTUM: """You are a momentum-focused trading agent.
You look for assets with strong price momentum and trend continuation patterns.
Key indicators: RSI, MACD, price breakouts, volume confirmation.""",

            StrategyType.MEAN_REVERSION: """You are a mean-reversion trading agent.
You look for overbought/oversold conditions and expect prices to revert to mean.
Key indicators: Bollinger Bands, RSI extremes, price deviations.""",

            StrategyType.SENTIMENT: """You are a sentiment-driven trading agent.
You focus on market sentiment, news impact, and social media trends.
Key factors: News sentiment, social mentions, fear/greed index.""",

            StrategyType.QUANTITATIVE: """You are a quantitative trading agent.
You use statistical analysis and mathematical models for decisions.
Key factors: Historical patterns, correlations, statistical arbitrage.""",

            StrategyType.BALANCED: """You are a balanced trading agent.
You consider multiple factors: technicals, sentiment, fundamentals.
Aim for consistent returns with moderate risk.""",

            StrategyType.AGGRESSIVE: """You are an aggressive trading agent.
You take higher risks for potentially higher returns.
Willing to make larger position sizes on high-conviction trades.""",

            StrategyType.CONSERVATIVE: """You are a conservative trading agent.
You prioritize capital preservation over aggressive returns.
Focus on high-probability, lower-risk setups."""
        }

        base = strategy_prompts.get(self.config.strategy, strategy_prompts[StrategyType.BALANCED])

        return f"""{base}

When analyzing, respond with a JSON decision:
{{
    "action": "buy" | "sell" | "hold",
    "amount": float (0.0 to 1.0 as fraction of available capital),
    "confidence": float (0.0 to 1.0),
    "reasoning": "Brief explanation"
}}"""

    async def make_decision(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        current_positions: Dict[str, float]
    ) -> TradeDecision:
        """Make a trading decision using the LLM."""
        # Build prompt
        prompt = self._build_decision_prompt(symbol, market_data, current_positions)

        # Call LLM (mock if no client)
        if self.llm_client:
            response = await self._call_llm(prompt)
        else:
            response = self._mock_decision(symbol, market_data)

        # Parse response
        decision = self._parse_response(symbol, response)

        return decision

    def _build_decision_prompt(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        current_positions: Dict[str, float]
    ) -> str:
        """Build the decision prompt."""
        return f"""
Symbol: {symbol}
Current Position: {current_positions.get(symbol, 0)}
Available Capital: ${current_positions.get('USD', 0):.2f}

Market Data:
- Price: ${market_data.get('price', 0):.2f}
- 24h Change: {market_data.get('change_24h', 0):.2f}%
- RSI: {market_data.get('rsi', 50):.1f}
- Sentiment: {market_data.get('sentiment', 0):.2f}

Analyze and provide your trading decision.
"""

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM with the prompt."""
        # This would integrate with actual LLM clients
        # For now, return mock response
        return self._mock_decision("", {})

    def _mock_decision(self, symbol: str, market_data: Dict[str, Any]) -> str:
        """Generate mock decision for testing."""
        import random
        import json

        actions = ["buy", "sell", "hold"]
        weights = [0.3, 0.3, 0.4]  # Slightly favor hold

        if self.config.strategy == StrategyType.AGGRESSIVE:
            weights = [0.4, 0.4, 0.2]
        elif self.config.strategy == StrategyType.CONSERVATIVE:
            weights = [0.2, 0.2, 0.6]

        action = random.choices(actions, weights=weights)[0]

        return json.dumps({
            "action": action,
            "amount": random.uniform(0.1, 0.3) if action != "hold" else 0,
            "confidence": random.uniform(0.5, 0.9),
            "reasoning": f"Mock {self.config.strategy.value} decision"
        })

    def _parse_response(self, symbol: str, response: str) -> TradeDecision:
        """Parse LLM response into TradeDecision."""
        import json

        try:
            data = json.loads(response)
            return TradeDecision(
                model_name=self.config.name,
                symbol=symbol,
                action=data.get("action", "hold"),
                amount=data.get("amount", 0),
                confidence=data.get("confidence", 0.5),
                reasoning=data.get("reasoning", "")
            )
        except json.JSONDecodeError:
            return TradeDecision(
                model_name=self.config.name,
                symbol=symbol,
                action="hold",
                amount=0,
                confidence=0.5,
                reasoning="Failed to parse response"
            )


class CompetitionArena:
    """
    Arena for multi-model trading competition.

    Usage:
        arena = CompetitionArena(initial_capital=50000)

        # Register competitors
        arena.add_competitor(ModelConfig(
            name="gpt4-momentum",
            provider=ModelProvider.OPENAI,
            model_id="gpt-4o",
            strategy=StrategyType.MOMENTUM
        ))

        arena.add_competitor(ModelConfig(
            name="claude-sentiment",
            provider=ModelProvider.ANTHROPIC,
            model_id="claude-3.5-sonnet",
            strategy=StrategyType.SENTIMENT
        ))

        # Run competition
        results = await arena.run_competition(
            symbols=["BTC/USDT", "ETH/USDT"],
            duration_hours=24
        )

        # Get leaderboard
        print(arena.get_leaderboard())
    """

    def __init__(
        self,
        initial_capital: float = 50000,
        max_position_pct: float = 0.2,
        commission: float = 0.001
    ):
        """
        Initialize competition arena.

        Args:
            initial_capital: Starting capital for each competitor
            max_position_pct: Max position size as fraction of capital
            commission: Trading commission rate
        """
        self.initial_capital = initial_capital
        self.max_position_pct = max_position_pct
        self.commission = commission

        self.competitors: Dict[str, BaseCompetitor] = {}
        self.performance: Dict[str, ModelPerformance] = {}
        self.competition_id = str(uuid.uuid4())[:8]
        self.start_time: Optional[datetime] = None
        self.is_running = False

        logger.info(f"Competition Arena initialized: {self.competition_id}")

    def add_competitor(
        self,
        config: ModelConfig,
        llm_client=None
    ) -> str:
        """
        Add a competitor to the arena.

        Args:
            config: Model configuration
            llm_client: Optional LLM client

        Returns:
            Competitor name
        """
        competitor = LLMCompetitor(config, llm_client)
        competitor.register_with_capital(self.initial_capital)

        self.competitors[config.name] = competitor
        self.performance[config.name] = ModelPerformance(model_name=config.name)

        logger.info(f"Added competitor: {config.display_name}")
        return config.name

    def remove_competitor(self, name: str):
        """Remove a competitor from the arena."""
        if name in self.competitors:
            del self.competitors[name]
            del self.performance[name]
            logger.info(f"Removed competitor: {name}")

    async def run_round(
        self,
        symbols: List[str],
        market_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[TradeDecision]]:
        """
        Run a single round of competition.

        All competitors make decisions for the same market state.

        Args:
            symbols: Symbols to trade
            market_data: Market data for each symbol

        Returns:
            Dict of competitor name -> decisions
        """
        round_decisions: Dict[str, List[TradeDecision]] = {}

        # Run all competitors in parallel
        async def get_competitor_decisions(name: str, competitor: BaseCompetitor):
            decisions = []
            for symbol in symbols:
                if symbol not in market_data:
                    continue

                decision = await competitor.make_decision(
                    symbol,
                    market_data[symbol],
                    competitor.positions
                )
                decisions.append(decision)

                # Record decision
                self.performance[name].decisions.append(decision)
                self.performance[name].avg_confidence = (
                    self.performance[name].avg_confidence * 0.9 +
                    decision.confidence * 0.1
                )

            return name, decisions

        tasks = [
            get_competitor_decisions(name, comp)
            for name, comp in self.competitors.items()
        ]

        results = await asyncio.gather(*tasks)

        for name, decisions in results:
            round_decisions[name] = decisions

        return round_decisions

    async def run_competition(
        self,
        symbols: List[str],
        data_generator: Callable,
        num_rounds: int = 100
    ) -> Dict[str, ModelPerformance]:
        """
        Run full competition.

        Args:
            symbols: Symbols to trade
            data_generator: Async generator yielding market data
            num_rounds: Number of trading rounds

        Returns:
            Final performance for each competitor
        """
        self.is_running = True
        self.start_time = datetime.utcnow()

        logger.info(f"Starting competition: {num_rounds} rounds, {len(symbols)} symbols")

        round_num = 0
        async for market_data in data_generator:
            if not self.is_running or round_num >= num_rounds:
                break

            await self.run_round(symbols, market_data)
            round_num += 1

            if round_num % 10 == 0:
                logger.info(f"Competition round {round_num}/{num_rounds}")

        self.is_running = False
        self._calculate_final_metrics()

        logger.info(f"Competition complete: {round_num} rounds executed")

        return self.performance

    def _calculate_final_metrics(self):
        """Calculate final metrics for all competitors."""
        for name, perf in self.performance.items():
            competitor = self.competitors[name]

            # Calculate from decisions
            trades = [d for d in perf.decisions if d.action != "hold"]
            perf.total_trades = len(trades)

            # Track cost
            perf.total_cost_usd = competitor.total_cost

            # Win rate would require actual P&L tracking
            if perf.total_trades > 0:
                perf.win_rate = perf.winning_trades / perf.total_trades

    def get_leaderboard(
        self,
        sort_by: str = "total_return_pct"
    ) -> List[Dict[str, Any]]:
        """
        Get competition leaderboard.

        Args:
            sort_by: Metric to sort by

        Returns:
            Sorted list of competitor performances
        """
        leaderboard = []

        for name, perf in self.performance.items():
            config = self.competitors[name].config

            leaderboard.append({
                "rank": 0,
                "name": name,
                "model": config.model_id,
                "strategy": config.strategy.value,
                "total_trades": perf.total_trades,
                "win_rate": perf.win_rate,
                "total_return_pct": perf.total_return_pct,
                "sharpe_ratio": perf.sharpe_ratio,
                "max_drawdown_pct": perf.max_drawdown_pct,
                "total_cost_usd": perf.total_cost_usd,
                "profit_per_dollar": perf.profit_per_dollar_spent,
                "avg_confidence": perf.avg_confidence
            })

        # Sort by metric (descending)
        leaderboard.sort(key=lambda x: x.get(sort_by, 0), reverse=True)

        # Assign ranks
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1

        return leaderboard

    def get_ensemble_recommendation(
        self,
        symbol: str,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Get ensemble recommendation by aggregating competitor decisions.

        Args:
            symbol: Symbol to get recommendation for
            weights: Optional weights for each competitor

        Returns:
            Aggregated recommendation
        """
        if weights is None:
            # Weight by historical performance
            weights = {
                name: max(0.1, perf.sharpe_ratio + 1)  # Ensure positive
                for name, perf in self.performance.items()
            }

        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}

        # Get latest decisions for symbol
        votes = {"buy": 0, "sell": 0, "hold": 0}
        total_confidence = 0
        reasonings = []

        for name, perf in self.performance.items():
            # Find latest decision for this symbol
            symbol_decisions = [
                d for d in perf.decisions
                if d.symbol == symbol
            ]

            if symbol_decisions:
                latest = symbol_decisions[-1]
                weight = weights.get(name, 0)

                votes[latest.action] += weight * latest.confidence
                total_confidence += latest.confidence * weight
                reasonings.append(f"{name}: {latest.reasoning}")

        # Determine consensus
        best_action = max(votes.items(), key=lambda x: x[1])

        return {
            "symbol": symbol,
            "action": best_action[0],
            "confidence": total_confidence,
            "vote_distribution": votes,
            "reasoning": "; ".join(reasonings[:3])  # Top 3 reasonings
        }

    def generate_report(self) -> str:
        """Generate competition report."""
        leaderboard = self.get_leaderboard()

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║           MULTI-MODEL COMPETITION REPORT                     ║
║           Competition ID: {self.competition_id}                        ║
╚══════════════════════════════════════════════════════════════╝

Start Time: {self.start_time.isoformat() if self.start_time else 'N/A'}
Competitors: {len(self.competitors)}
Initial Capital: ${self.initial_capital:,.2f}

═══════════════════════════════════════════════════════════════
LEADERBOARD
═══════════════════════════════════════════════════════════════
"""

        for entry in leaderboard:
            report += f"""
#{entry['rank']} {entry['name']}
    Model: {entry['model']} | Strategy: {entry['strategy']}
    Trades: {entry['total_trades']} | Win Rate: {entry['win_rate']:.1%}
    Return: {entry['total_return_pct']:+.2f}% | Sharpe: {entry['sharpe_ratio']:.2f}
    Max DD: {entry['max_drawdown_pct']:.2f}% | Cost: ${entry['total_cost_usd']:.2f}
    Profit/$ Spent: ${entry['profit_per_dollar']:.2f}
"""

        report += """
═══════════════════════════════════════════════════════════════

KEY INSIGHTS:
"""

        if leaderboard:
            best = leaderboard[0]
            report += f"• Top performer: {best['name']} ({best['strategy']})\n"

            # Find best cost efficiency
            by_efficiency = sorted(
                leaderboard,
                key=lambda x: x['profit_per_dollar'],
                reverse=True
            )
            if by_efficiency:
                report += f"• Most cost-efficient: {by_efficiency[0]['name']}\n"

            # Strategy comparison
            strategy_returns = {}
            for entry in leaderboard:
                s = entry['strategy']
                if s not in strategy_returns:
                    strategy_returns[s] = []
                strategy_returns[s].append(entry['total_return_pct'])

            report += "\n• Strategy Average Returns:\n"
            for strategy, returns in sorted(strategy_returns.items()):
                avg = sum(returns) / len(returns) if returns else 0
                report += f"    {strategy}: {avg:+.2f}%\n"

        report += "\n═══════════════════════════════════════════════════════════════\n"

        return report


# Predefined model configurations for common setups
PRESET_CONFIGS = {
    "gpt4-momentum": ModelConfig(
        name="gpt4-momentum",
        provider=ModelProvider.OPENAI,
        model_id="gpt-4o",
        strategy=StrategyType.MOMENTUM,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015
    ),
    "claude-sentiment": ModelConfig(
        name="claude-sentiment",
        provider=ModelProvider.ANTHROPIC,
        model_id="claude-3-5-sonnet-20241022",
        strategy=StrategyType.SENTIMENT,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015
    ),
    "deepseek-quant": ModelConfig(
        name="deepseek-quant",
        provider=ModelProvider.DEEPSEEK,
        model_id="deepseek-chat",
        strategy=StrategyType.QUANTITATIVE,
        cost_per_1k_input=0.00014,
        cost_per_1k_output=0.00028
    ),
    "qwen-balanced": ModelConfig(
        name="qwen-balanced",
        provider=ModelProvider.QWEN,
        model_id="qwen-max",
        strategy=StrategyType.BALANCED,
        cost_per_1k_input=0.0016,
        cost_per_1k_output=0.0016
    ),
    "local-llama": ModelConfig(
        name="local-llama",
        provider=ModelProvider.OLLAMA,
        model_id="llama3.2:8b",
        strategy=StrategyType.CONSERVATIVE,
        cost_per_1k_input=0,  # Free
        cost_per_1k_output=0
    ),
    "groq-fast": ModelConfig(
        name="groq-fast",
        provider=ModelProvider.GROQ,
        model_id="llama-3.3-70b-versatile",
        strategy=StrategyType.AGGRESSIVE,
        cost_per_1k_input=0.00059,
        cost_per_1k_output=0.00079
    )
}


def create_default_arena() -> CompetitionArena:
    """Create arena with default configuration."""
    arena = CompetitionArena(initial_capital=50000)

    # Add common competitors
    for name, config in PRESET_CONFIGS.items():
        arena.add_competitor(config)

    return arena
