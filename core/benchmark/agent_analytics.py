"""
Agent Performance Analytics
Comprehensive analytics for trading agent performance

Features:
- Detailed per-agent metrics
- Historical trend analysis
- Comparative analytics
- Statistical analysis (Sharpe, Sortino, Calmar)
- Decision pattern analysis
- Risk profiling
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import math
from loguru import logger

from .live_benchmark import BenchmarkMetrics


class TimeWindow(Enum):
    """Time windows for analysis."""
    HOUR = "1h"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1m"
    ALL = "all"


class RiskProfile(Enum):
    """Agent risk profile classification."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"


@dataclass
class DecisionPattern:
    """Pattern in agent decision-making."""
    pattern_type: str  # "momentum_following", "contrarian", "sentiment_driven", etc.
    frequency: float  # How often this pattern occurs
    success_rate: float  # Win rate when this pattern is used
    avg_return: float  # Average return when this pattern is used
    sample_size: int


@dataclass
class PerformanceBreakdown:
    """Detailed performance breakdown."""
    # Core metrics
    total_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

    # Trade stats
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float

    # Risk metrics
    max_drawdown_pct: float
    avg_drawdown_pct: float
    volatility: float
    downside_volatility: float
    var_95: float  # Value at Risk 95%
    cvar_95: float  # Conditional VaR 95%

    # Time analysis
    avg_trade_duration: float  # seconds
    best_hour: int  # 0-23
    best_day: int  # 0-6 (Mon-Sun)

    # Streaks
    max_win_streak: int
    max_loss_streak: int
    current_streak: int
    current_streak_type: str  # "win" or "loss"

    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "returns": {
                "total_return_pct": round(self.total_return_pct, 4),
                "sharpe_ratio": round(self.sharpe_ratio, 4),
                "sortino_ratio": round(self.sortino_ratio, 4),
                "calmar_ratio": round(self.calmar_ratio, 4)
            },
            "trades": {
                "total": self.total_trades,
                "winning": self.winning_trades,
                "losing": self.losing_trades,
                "win_rate": round(self.win_rate, 4),
                "avg_win": round(self.avg_win, 4),
                "avg_loss": round(self.avg_loss, 4),
                "profit_factor": round(self.profit_factor, 4)
            },
            "risk": {
                "max_drawdown_pct": round(self.max_drawdown_pct, 4),
                "avg_drawdown_pct": round(self.avg_drawdown_pct, 4),
                "volatility": round(self.volatility, 4),
                "downside_volatility": round(self.downside_volatility, 4),
                "var_95": round(self.var_95, 4),
                "cvar_95": round(self.cvar_95, 4)
            },
            "timing": {
                "avg_trade_duration_sec": round(self.avg_trade_duration, 2),
                "best_hour": self.best_hour,
                "best_day": self.best_day
            },
            "streaks": {
                "max_win_streak": self.max_win_streak,
                "max_loss_streak": self.max_loss_streak,
                "current_streak": self.current_streak,
                "current_streak_type": self.current_streak_type
            },
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class AgentProfile:
    """Complete agent profile with analytics."""
    agent_id: str
    agent_name: str
    model: str
    strategy: str
    risk_profile: RiskProfile
    performance: PerformanceBreakdown
    decision_patterns: List[DecisionPattern]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


class AgentAnalytics:
    """
    Comprehensive agent performance analytics.

    Usage:
        analytics = AgentAnalytics()

        # Register agents
        analytics.register_agent("agent1", "GPT-4 Momentum", "gpt-4", "momentum")

        # Record trades
        analytics.record_trade("agent1", {...})

        # Get analytics
        breakdown = analytics.get_performance_breakdown("agent1")
        patterns = analytics.analyze_decision_patterns("agent1")
        comparison = analytics.compare_agents(["agent1", "agent2"])
    """

    def __init__(self, risk_free_rate: float = 0.04):
        """
        Initialize analytics.

        Args:
            risk_free_rate: Annual risk-free rate for Sharpe calculation
        """
        self.risk_free_rate = risk_free_rate

        # Agent data
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._trades: Dict[str, List[Dict]] = defaultdict(list)
        self._returns: Dict[str, List[float]] = defaultdict(list)
        self._equity_curve: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        self._decisions: Dict[str, List[Dict]] = defaultdict(list)

    def register_agent(
        self,
        agent_id: str,
        name: str,
        model: str,
        strategy: str
    ):
        """Register an agent for analytics."""
        self._agents[agent_id] = {
            "name": name,
            "model": model,
            "strategy": strategy,
            "registered_at": datetime.utcnow()
        }
        self._equity_curve[agent_id].append((datetime.utcnow(), 10000.0))  # Starting capital

    def record_trade(
        self,
        agent_id: str,
        trade: Dict[str, Any]
    ):
        """
        Record a completed trade.

        Trade dict should include:
        - symbol: str
        - action: "buy" or "sell"
        - entry_price: float
        - exit_price: float
        - quantity: float
        - entry_time: datetime
        - exit_time: datetime
        - pnl: float
        - pnl_pct: float
        """
        if agent_id not in self._agents:
            logger.warning(f"Unknown agent: {agent_id}")
            return

        self._trades[agent_id].append(trade)
        self._returns[agent_id].append(trade.get("pnl_pct", 0))

        # Update equity curve
        last_equity = self._equity_curve[agent_id][-1][1]
        pnl = trade.get("pnl", 0)
        new_equity = last_equity + pnl
        self._equity_curve[agent_id].append((datetime.utcnow(), new_equity))

    def record_decision(
        self,
        agent_id: str,
        decision: Dict[str, Any]
    ):
        """
        Record a decision (regardless of execution).

        Decision dict should include:
        - symbol: str
        - action: str
        - confidence: float
        - reasoning: str
        - timestamp: datetime
        - indicators_used: List[str]
        - market_conditions: Dict
        """
        if agent_id not in self._agents:
            return

        self._decisions[agent_id].append(decision)

    def get_performance_breakdown(
        self,
        agent_id: str,
        window: TimeWindow = TimeWindow.ALL
    ) -> Optional[PerformanceBreakdown]:
        """Get detailed performance breakdown."""
        if agent_id not in self._agents:
            return None

        trades = self._filter_by_window(self._trades[agent_id], window)
        returns = self._filter_returns_by_window(agent_id, window)

        if not trades:
            return PerformanceBreakdown(
                total_return_pct=0, sharpe_ratio=0, sortino_ratio=0, calmar_ratio=0,
                total_trades=0, winning_trades=0, losing_trades=0, win_rate=0,
                avg_win=0, avg_loss=0, profit_factor=0,
                max_drawdown_pct=0, avg_drawdown_pct=0, volatility=0,
                downside_volatility=0, var_95=0, cvar_95=0,
                avg_trade_duration=0, best_hour=0, best_day=0,
                max_win_streak=0, max_loss_streak=0, current_streak=0,
                current_streak_type="none"
            )

        # Core metrics
        total_return = sum(t.get("pnl_pct", 0) for t in trades)
        winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in trades if t.get("pnl", 0) < 0]

        win_rate = len(winning_trades) / len(trades) if trades else 0
        avg_win = sum(t.get("pnl_pct", 0) for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.get("pnl_pct", 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0

        gross_profit = sum(t.get("pnl", 0) for t in winning_trades)
        gross_loss = abs(sum(t.get("pnl", 0) for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Risk metrics
        volatility = self._calculate_volatility(returns)
        downside_vol = self._calculate_downside_volatility(returns)
        sharpe = self._calculate_sharpe(returns)
        sortino = self._calculate_sortino(returns)

        # Drawdown
        max_dd, avg_dd = self._calculate_drawdowns(agent_id, window)
        calmar = total_return / max_dd if max_dd > 0 else 0

        # VaR
        var_95, cvar_95 = self._calculate_var(returns)

        # Timing analysis
        avg_duration = self._calculate_avg_duration(trades)
        best_hour, best_day = self._analyze_timing(trades)

        # Streaks
        max_win, max_loss, current, current_type = self._calculate_streaks(trades)

        return PerformanceBreakdown(
            total_return_pct=total_return,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=min(profit_factor, 999),  # Cap for display
            max_drawdown_pct=max_dd,
            avg_drawdown_pct=avg_dd,
            volatility=volatility,
            downside_volatility=downside_vol,
            var_95=var_95,
            cvar_95=cvar_95,
            avg_trade_duration=avg_duration,
            best_hour=best_hour,
            best_day=best_day,
            max_win_streak=max_win,
            max_loss_streak=max_loss,
            current_streak=current,
            current_streak_type=current_type
        )

    def _filter_by_window(
        self,
        items: List[Dict],
        window: TimeWindow
    ) -> List[Dict]:
        """Filter items by time window."""
        if window == TimeWindow.ALL:
            return items

        cutoff = self._get_window_cutoff(window)
        return [
            item for item in items
            if item.get("exit_time", item.get("timestamp", datetime.utcnow())) >= cutoff
        ]

    def _filter_returns_by_window(
        self,
        agent_id: str,
        window: TimeWindow
    ) -> List[float]:
        """Filter returns by window."""
        trades = self._filter_by_window(self._trades[agent_id], window)
        return [t.get("pnl_pct", 0) for t in trades]

    def _get_window_cutoff(self, window: TimeWindow) -> datetime:
        """Get cutoff datetime for window."""
        now = datetime.utcnow()
        if window == TimeWindow.HOUR:
            return now - timedelta(hours=1)
        elif window == TimeWindow.DAY:
            return now - timedelta(days=1)
        elif window == TimeWindow.WEEK:
            return now - timedelta(weeks=1)
        elif window == TimeWindow.MONTH:
            return now - timedelta(days=30)
        return datetime.min

    def _calculate_volatility(self, returns: List[float]) -> float:
        """Calculate return volatility (std dev)."""
        if len(returns) < 2:
            return 0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
        return math.sqrt(variance)

    def _calculate_downside_volatility(self, returns: List[float]) -> float:
        """Calculate downside volatility (negative returns only)."""
        negative_returns = [r for r in returns if r < 0]
        if len(negative_returns) < 2:
            return 0
        return self._calculate_volatility(negative_returns)

    def _calculate_sharpe(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) < 2:
            return 0

        mean_return = sum(returns) / len(returns)
        vol = self._calculate_volatility(returns)

        if vol == 0:
            return 0

        # Annualize assuming hourly returns
        annual_return = mean_return * 8760  # hours per year
        annual_vol = vol * math.sqrt(8760)

        return (annual_return - self.risk_free_rate) / annual_vol

    def _calculate_sortino(self, returns: List[float]) -> float:
        """Calculate Sortino ratio (uses downside volatility)."""
        if len(returns) < 2:
            return 0

        mean_return = sum(returns) / len(returns)
        downside_vol = self._calculate_downside_volatility(returns)

        if downside_vol == 0:
            return 0

        annual_return = mean_return * 8760
        annual_downside_vol = downside_vol * math.sqrt(8760)

        return (annual_return - self.risk_free_rate) / annual_downside_vol

    def _calculate_drawdowns(
        self,
        agent_id: str,
        window: TimeWindow
    ) -> Tuple[float, float]:
        """Calculate max and average drawdown."""
        equity = self._equity_curve.get(agent_id, [])

        if len(equity) < 2:
            return 0, 0

        # Filter by window
        if window != TimeWindow.ALL:
            cutoff = self._get_window_cutoff(window)
            equity = [(t, v) for t, v in equity if t >= cutoff]

        if len(equity) < 2:
            return 0, 0

        values = [v for _, v in equity]
        peak = values[0]
        drawdowns = []

        for value in values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100 if peak > 0 else 0
            drawdowns.append(dd)

        return max(drawdowns), sum(drawdowns) / len(drawdowns)

    def _calculate_var(
        self,
        returns: List[float],
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate Value at Risk and Conditional VaR."""
        if len(returns) < 10:
            return 0, 0

        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))

        var = -sorted_returns[index] if index < len(sorted_returns) else 0
        cvar = -sum(sorted_returns[:index + 1]) / (index + 1) if index > 0 else var

        return var, cvar

    def _calculate_avg_duration(self, trades: List[Dict]) -> float:
        """Calculate average trade duration in seconds."""
        durations = []
        for trade in trades:
            entry = trade.get("entry_time")
            exit = trade.get("exit_time")
            if entry and exit:
                durations.append((exit - entry).total_seconds())

        return sum(durations) / len(durations) if durations else 0

    def _analyze_timing(self, trades: List[Dict]) -> Tuple[int, int]:
        """Analyze best performing hour and day."""
        hour_returns = defaultdict(list)
        day_returns = defaultdict(list)

        for trade in trades:
            entry_time = trade.get("entry_time")
            pnl_pct = trade.get("pnl_pct", 0)

            if entry_time:
                hour_returns[entry_time.hour].append(pnl_pct)
                day_returns[entry_time.weekday()].append(pnl_pct)

        best_hour = max(hour_returns.items(), key=lambda x: sum(x[1]), default=(12, []))[0]
        best_day = max(day_returns.items(), key=lambda x: sum(x[1]), default=(0, []))[0]

        return best_hour, best_day

    def _calculate_streaks(
        self,
        trades: List[Dict]
    ) -> Tuple[int, int, int, str]:
        """Calculate win/loss streaks."""
        if not trades:
            return 0, 0, 0, "none"

        max_win = max_loss = 0
        current_win = current_loss = 0

        for trade in trades:
            if trade.get("pnl", 0) > 0:
                current_win += 1
                current_loss = 0
                max_win = max(max_win, current_win)
            else:
                current_loss += 1
                current_win = 0
                max_loss = max(max_loss, current_loss)

        current = current_win if current_win > 0 else current_loss
        current_type = "win" if current_win > 0 else "loss"

        return max_win, max_loss, current, current_type

    def analyze_decision_patterns(
        self,
        agent_id: str
    ) -> List[DecisionPattern]:
        """Analyze patterns in agent decisions."""
        decisions = self._decisions.get(agent_id, [])
        trades = self._trades.get(agent_id, [])

        if len(decisions) < 10:
            return []

        patterns = []

        # Analyze confidence patterns
        high_conf_decisions = [d for d in decisions if d.get("confidence", 0) > 0.8]
        if high_conf_decisions:
            high_conf_trades = [t for t in trades if t.get("confidence", 0) > 0.8]
            win_rate = len([t for t in high_conf_trades if t.get("pnl", 0) > 0]) / len(high_conf_trades) if high_conf_trades else 0

            patterns.append(DecisionPattern(
                pattern_type="high_confidence",
                frequency=len(high_conf_decisions) / len(decisions),
                success_rate=win_rate,
                avg_return=sum(t.get("pnl_pct", 0) for t in high_conf_trades) / len(high_conf_trades) if high_conf_trades else 0,
                sample_size=len(high_conf_trades)
            ))

        # Analyze action patterns
        buy_decisions = [d for d in decisions if d.get("action") == "buy"]
        sell_decisions = [d for d in decisions if d.get("action") == "sell"]

        if buy_decisions:
            buy_trades = [t for t in trades if t.get("action") == "buy"]
            buy_wins = len([t for t in buy_trades if t.get("pnl", 0) > 0])

            patterns.append(DecisionPattern(
                pattern_type="buy_tendency",
                frequency=len(buy_decisions) / len(decisions),
                success_rate=buy_wins / len(buy_trades) if buy_trades else 0,
                avg_return=sum(t.get("pnl_pct", 0) for t in buy_trades) / len(buy_trades) if buy_trades else 0,
                sample_size=len(buy_trades)
            ))

        if sell_decisions:
            sell_trades = [t for t in trades if t.get("action") == "sell"]
            sell_wins = len([t for t in sell_trades if t.get("pnl", 0) > 0])

            patterns.append(DecisionPattern(
                pattern_type="sell_tendency",
                frequency=len(sell_decisions) / len(decisions),
                success_rate=sell_wins / len(sell_trades) if sell_trades else 0,
                avg_return=sum(t.get("pnl_pct", 0) for t in sell_trades) / len(sell_trades) if sell_trades else 0,
                sample_size=len(sell_trades)
            ))

        return patterns

    def classify_risk_profile(self, agent_id: str) -> RiskProfile:
        """Classify agent's risk profile."""
        breakdown = self.get_performance_breakdown(agent_id)

        if not breakdown or breakdown.total_trades < 10:
            return RiskProfile.MODERATE

        # Score based on volatility, drawdown, and trade frequency
        vol_score = min(breakdown.volatility * 100, 10)  # 0-10
        dd_score = min(breakdown.max_drawdown_pct / 5, 10)  # 0-10
        freq_score = min(breakdown.total_trades / 100, 10)  # 0-10

        risk_score = (vol_score + dd_score + freq_score) / 3

        if risk_score < 2:
            return RiskProfile.CONSERVATIVE
        elif risk_score < 5:
            return RiskProfile.MODERATE
        elif risk_score < 8:
            return RiskProfile.AGGRESSIVE
        else:
            return RiskProfile.VERY_AGGRESSIVE

    def get_agent_profile(self, agent_id: str) -> Optional[AgentProfile]:
        """Get complete agent profile with analytics."""
        if agent_id not in self._agents:
            return None

        agent = self._agents[agent_id]
        breakdown = self.get_performance_breakdown(agent_id)
        patterns = self.analyze_decision_patterns(agent_id)
        risk_profile = self.classify_risk_profile(agent_id)

        # Generate strengths
        strengths = []
        if breakdown and breakdown.win_rate > 0.6:
            strengths.append("High win rate")
        if breakdown and breakdown.sharpe_ratio > 1.5:
            strengths.append("Strong risk-adjusted returns")
        if breakdown and breakdown.max_drawdown_pct < 10:
            strengths.append("Low drawdown risk")
        if breakdown and breakdown.profit_factor > 2:
            strengths.append("Excellent profit factor")

        # Generate weaknesses
        weaknesses = []
        if breakdown and breakdown.win_rate < 0.4:
            weaknesses.append("Low win rate")
        if breakdown and breakdown.max_drawdown_pct > 20:
            weaknesses.append("High drawdown risk")
        if breakdown and breakdown.volatility > 0.05:
            weaknesses.append("High volatility")
        if breakdown and breakdown.max_loss_streak > 5:
            weaknesses.append("Prone to loss streaks")

        # Generate recommendations
        recommendations = []
        if breakdown and breakdown.max_drawdown_pct > 15:
            recommendations.append("Consider reducing position sizes")
        if breakdown and breakdown.win_rate < 0.5 and breakdown.avg_win < abs(breakdown.avg_loss):
            recommendations.append("Improve risk/reward ratio")
        if breakdown and breakdown.total_trades < 30:
            recommendations.append("More data needed for reliable analysis")

        return AgentProfile(
            agent_id=agent_id,
            agent_name=agent["name"],
            model=agent["model"],
            strategy=agent["strategy"],
            risk_profile=risk_profile,
            performance=breakdown,
            decision_patterns=patterns,
            strengths=strengths if strengths else ["Insufficient data"],
            weaknesses=weaknesses if weaknesses else ["Insufficient data"],
            recommendations=recommendations if recommendations else ["Continue monitoring"]
        )

    def compare_agents(
        self,
        agent_ids: List[str],
        window: TimeWindow = TimeWindow.ALL
    ) -> Dict[str, Any]:
        """Compare multiple agents."""
        comparisons = {}

        for agent_id in agent_ids:
            if agent_id not in self._agents:
                continue

            breakdown = self.get_performance_breakdown(agent_id, window)
            if breakdown:
                comparisons[agent_id] = {
                    "name": self._agents[agent_id]["name"],
                    "total_return": breakdown.total_return_pct,
                    "sharpe_ratio": breakdown.sharpe_ratio,
                    "win_rate": breakdown.win_rate,
                    "max_drawdown": breakdown.max_drawdown_pct,
                    "profit_factor": breakdown.profit_factor,
                    "total_trades": breakdown.total_trades
                }

        # Rank by each metric
        if comparisons:
            for metric in ["total_return", "sharpe_ratio", "win_rate", "profit_factor"]:
                sorted_agents = sorted(
                    comparisons.items(),
                    key=lambda x: x[1][metric],
                    reverse=True
                )
                for rank, (agent_id, _) in enumerate(sorted_agents, 1):
                    comparisons[agent_id][f"{metric}_rank"] = rank

        return {
            "agents": comparisons,
            "window": window.value,
            "generated_at": datetime.utcnow().isoformat()
        }

    def get_equity_curve(
        self,
        agent_id: str,
        window: TimeWindow = TimeWindow.ALL
    ) -> List[Dict[str, Any]]:
        """Get equity curve data for charting."""
        equity = self._equity_curve.get(agent_id, [])

        if window != TimeWindow.ALL:
            cutoff = self._get_window_cutoff(window)
            equity = [(t, v) for t, v in equity if t >= cutoff]

        return [
            {"timestamp": t.isoformat(), "equity": round(v, 2)}
            for t, v in equity
        ]

    def get_trade_distribution(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """Get trade PnL distribution for histogram."""
        trades = self._trades.get(agent_id, [])
        pnl_pcts = [t.get("pnl_pct", 0) for t in trades]

        if not pnl_pcts:
            return {"buckets": [], "counts": []}

        # Create buckets
        min_pnl = min(pnl_pcts)
        max_pnl = max(pnl_pcts)
        bucket_size = (max_pnl - min_pnl) / 20 if max_pnl != min_pnl else 1

        buckets = []
        counts = []

        for i in range(20):
            lower = min_pnl + i * bucket_size
            upper = lower + bucket_size
            count = sum(1 for p in pnl_pcts if lower <= p < upper)
            buckets.append(round((lower + upper) / 2, 4))
            counts.append(count)

        return {
            "buckets": buckets,
            "counts": counts,
            "mean": round(sum(pnl_pcts) / len(pnl_pcts), 4),
            "median": round(sorted(pnl_pcts)[len(pnl_pcts) // 2], 4)
        }


# FastAPI integration
def create_analytics_router(analytics: AgentAnalytics):
    """Create FastAPI router for analytics."""
    try:
        from fastapi import APIRouter
        from fastapi.responses import JSONResponse
    except ImportError:
        logger.warning("FastAPI not installed")
        return None

    router = APIRouter(prefix="/analytics", tags=["analytics"])

    @router.get("/agent/{agent_id}")
    async def get_agent_analytics(agent_id: str, window: str = "all"):
        """Get agent performance breakdown."""
        w = TimeWindow(window)
        breakdown = analytics.get_performance_breakdown(agent_id, w)
        if breakdown:
            return breakdown.to_dict()
        return JSONResponse(status_code=404, content={"error": "Agent not found"})

    @router.get("/agent/{agent_id}/profile")
    async def get_agent_profile(agent_id: str):
        """Get complete agent profile."""
        profile = analytics.get_agent_profile(agent_id)
        if profile:
            return {
                "agent_id": profile.agent_id,
                "agent_name": profile.agent_name,
                "model": profile.model,
                "strategy": profile.strategy,
                "risk_profile": profile.risk_profile.value,
                "performance": profile.performance.to_dict(),
                "decision_patterns": [
                    {
                        "type": p.pattern_type,
                        "frequency": round(p.frequency, 4),
                        "success_rate": round(p.success_rate, 4),
                        "avg_return": round(p.avg_return, 4),
                        "sample_size": p.sample_size
                    }
                    for p in profile.decision_patterns
                ],
                "strengths": profile.strengths,
                "weaknesses": profile.weaknesses,
                "recommendations": profile.recommendations
            }
        return JSONResponse(status_code=404, content={"error": "Agent not found"})

    @router.get("/agent/{agent_id}/equity")
    async def get_equity_curve(agent_id: str, window: str = "all"):
        """Get equity curve data."""
        w = TimeWindow(window)
        return analytics.get_equity_curve(agent_id, w)

    @router.get("/agent/{agent_id}/distribution")
    async def get_trade_distribution(agent_id: str):
        """Get trade PnL distribution."""
        return analytics.get_trade_distribution(agent_id)

    @router.get("/agent/{agent_id}/patterns")
    async def get_decision_patterns(agent_id: str):
        """Get decision patterns."""
        patterns = analytics.analyze_decision_patterns(agent_id)
        return [
            {
                "type": p.pattern_type,
                "frequency": round(p.frequency, 4),
                "success_rate": round(p.success_rate, 4),
                "avg_return": round(p.avg_return, 4),
                "sample_size": p.sample_size
            }
            for p in patterns
        ]

    @router.post("/compare")
    async def compare_agents(agent_ids: List[str], window: str = "all"):
        """Compare multiple agents."""
        w = TimeWindow(window)
        return analytics.compare_agents(agent_ids, w)

    return router
