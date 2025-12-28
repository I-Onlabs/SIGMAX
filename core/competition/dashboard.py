"""
Strategy Comparison Dashboard
Real-time visualization and comparison of competing models

Provides API endpoints for:
- Live leaderboard
- Strategy performance comparison
- Cost efficiency analysis
- Decision history visualization
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
from loguru import logger
import json

from .multi_model_arena import (
    CompetitionArena,
    ModelPerformance,
    StrategyType,
    TradeDecision
)


@dataclass
class DashboardMetrics:
    """Aggregated metrics for dashboard display."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    total_competitors: int = 0
    total_trades: int = 0
    total_volume: float = 0
    best_performer: str = ""
    best_return: float = 0
    avg_win_rate: float = 0
    total_cost: float = 0


@dataclass
class StrategyComparison:
    """Comparison of strategy types."""
    strategy: str
    competitor_count: int
    avg_return: float
    avg_sharpe: float
    avg_win_rate: float
    avg_cost: float
    best_performer: str
    worst_performer: str


class CompetitionDashboard:
    """
    Dashboard for monitoring and comparing trading strategies.

    Features:
    - Real-time leaderboard updates
    - Strategy performance comparison
    - Cost efficiency tracking
    - Decision history browsing
    - Chart data generation
    """

    def __init__(self, arena: CompetitionArena):
        """
        Initialize dashboard with competition arena.

        Args:
            arena: The competition arena to monitor
        """
        self.arena = arena
        self._snapshot_history: List[DashboardMetrics] = []
        self._last_update = datetime.utcnow()

    def get_overview(self) -> Dict[str, Any]:
        """Get dashboard overview metrics."""
        leaderboard = self.arena.get_leaderboard()

        if not leaderboard:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "no_data",
                "competitors": 0
            }

        total_trades = sum(p.total_trades for p in self.arena.performance.values())
        total_cost = sum(p.total_cost_usd for p in self.arena.performance.values())
        win_rates = [p.win_rate for p in self.arena.performance.values()]

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "competition_id": self.arena.competition_id,
            "is_running": self.arena.is_running,
            "start_time": self.arena.start_time.isoformat() if self.arena.start_time else None,
            "competitors": len(self.arena.competitors),
            "total_trades": total_trades,
            "total_cost_usd": round(total_cost, 2),
            "avg_win_rate": round(sum(win_rates) / len(win_rates), 3) if win_rates else 0,
            "leader": {
                "name": leaderboard[0]["name"],
                "return_pct": leaderboard[0]["total_return_pct"],
                "strategy": leaderboard[0]["strategy"]
            } if leaderboard else None
        }

    def get_leaderboard(
        self,
        sort_by: str = "total_return_pct",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get formatted leaderboard for display.

        Args:
            sort_by: Metric to sort by
            limit: Max entries to return
        """
        leaderboard = self.arena.get_leaderboard(sort_by=sort_by)[:limit]

        # Add formatted fields
        for entry in leaderboard:
            entry["return_display"] = f"{entry['total_return_pct']:+.2f}%"
            entry["win_rate_display"] = f"{entry['win_rate']:.1%}"
            entry["cost_display"] = f"${entry['total_cost_usd']:.2f}"

        return leaderboard

    def get_strategy_comparison(self) -> List[Dict[str, Any]]:
        """Compare performance across strategy types."""
        strategy_data: Dict[str, List[Dict]] = defaultdict(list)

        for entry in self.arena.get_leaderboard():
            strategy_data[entry["strategy"]].append(entry)

        comparisons = []
        for strategy, entries in strategy_data.items():
            if not entries:
                continue

            returns = [e["total_return_pct"] for e in entries]
            sharpes = [e["sharpe_ratio"] for e in entries]
            win_rates = [e["win_rate"] for e in entries]
            costs = [e["total_cost_usd"] for e in entries]

            best = max(entries, key=lambda x: x["total_return_pct"])
            worst = min(entries, key=lambda x: x["total_return_pct"])

            comparisons.append({
                "strategy": strategy,
                "competitor_count": len(entries),
                "avg_return": round(sum(returns) / len(returns), 2),
                "avg_sharpe": round(sum(sharpes) / len(sharpes), 2),
                "avg_win_rate": round(sum(win_rates) / len(win_rates), 3),
                "avg_cost": round(sum(costs) / len(costs), 2),
                "best_performer": best["name"],
                "worst_performer": worst["name"],
                "return_range": {
                    "min": round(min(returns), 2),
                    "max": round(max(returns), 2)
                }
            })

        # Sort by average return
        comparisons.sort(key=lambda x: x["avg_return"], reverse=True)

        return comparisons

    def get_cost_efficiency(self) -> List[Dict[str, Any]]:
        """Get cost efficiency analysis for each competitor."""
        efficiency = []

        for name, perf in self.arena.performance.items():
            config = self.arena.competitors[name].config

            efficiency.append({
                "name": name,
                "provider": config.provider.value,
                "model": config.model_id,
                "strategy": config.strategy.value,
                "total_cost": round(perf.total_cost_usd, 4),
                "total_trades": perf.total_trades,
                "cost_per_trade": round(perf.cost_per_trade, 4),
                "total_pnl": round(perf.total_pnl, 2),
                "profit_per_dollar": round(perf.profit_per_dollar_spent, 2),
                "return_pct": round(perf.total_return_pct, 2)
            })

        # Sort by profit per dollar spent
        efficiency.sort(key=lambda x: x["profit_per_dollar"], reverse=True)

        return efficiency

    def get_decision_history(
        self,
        competitor: Optional[str] = None,
        symbol: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get trading decision history.

        Args:
            competitor: Filter by competitor name
            symbol: Filter by symbol
            action: Filter by action (buy/sell/hold)
            limit: Max decisions to return
        """
        decisions = []

        for name, perf in self.arena.performance.items():
            if competitor and name != competitor:
                continue

            for decision in perf.decisions:
                if symbol and decision.symbol != symbol:
                    continue
                if action and decision.action != action:
                    continue

                decisions.append({
                    "timestamp": decision.timestamp.isoformat(),
                    "competitor": decision.model_name,
                    "symbol": decision.symbol,
                    "action": decision.action,
                    "amount": round(decision.amount, 4),
                    "confidence": round(decision.confidence, 3),
                    "reasoning": decision.reasoning[:200]  # Truncate
                })

        # Sort by timestamp descending
        decisions.sort(key=lambda x: x["timestamp"], reverse=True)

        return decisions[:limit]

    def get_chart_data(
        self,
        chart_type: str,
        competitors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get data formatted for chart visualization.

        Args:
            chart_type: Type of chart (equity_curve, returns_bar, win_rate_pie, etc.)
            competitors: Optional list of competitors to include

        Returns:
            Chart.js compatible data structure
        """
        if chart_type == "returns_bar":
            return self._get_returns_bar_data(competitors)
        elif chart_type == "strategy_comparison":
            return self._get_strategy_bar_data()
        elif chart_type == "cost_scatter":
            return self._get_cost_scatter_data(competitors)
        elif chart_type == "confidence_distribution":
            return self._get_confidence_histogram(competitors)
        else:
            return {"error": f"Unknown chart type: {chart_type}"}

    def _get_returns_bar_data(
        self,
        competitors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get bar chart data for returns comparison."""
        leaderboard = self.arena.get_leaderboard()

        if competitors:
            leaderboard = [e for e in leaderboard if e["name"] in competitors]

        return {
            "type": "bar",
            "data": {
                "labels": [e["name"] for e in leaderboard],
                "datasets": [{
                    "label": "Total Return %",
                    "data": [e["total_return_pct"] for e in leaderboard],
                    "backgroundColor": [
                        "rgba(75, 192, 192, 0.6)" if e["total_return_pct"] >= 0
                        else "rgba(255, 99, 132, 0.6)"
                        for e in leaderboard
                    ]
                }]
            },
            "options": {
                "indexAxis": "y",
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "Competitor Returns"}
                }
            }
        }

    def _get_strategy_bar_data(self) -> Dict[str, Any]:
        """Get grouped bar chart for strategy comparison."""
        comparisons = self.get_strategy_comparison()

        return {
            "type": "bar",
            "data": {
                "labels": [c["strategy"] for c in comparisons],
                "datasets": [
                    {
                        "label": "Avg Return %",
                        "data": [c["avg_return"] for c in comparisons],
                        "backgroundColor": "rgba(54, 162, 235, 0.6)"
                    },
                    {
                        "label": "Avg Sharpe",
                        "data": [c["avg_sharpe"] for c in comparisons],
                        "backgroundColor": "rgba(75, 192, 192, 0.6)"
                    }
                ]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "Strategy Performance Comparison"}
                }
            }
        }

    def _get_cost_scatter_data(
        self,
        competitors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get scatter plot data for cost vs return analysis."""
        efficiency = self.get_cost_efficiency()

        if competitors:
            efficiency = [e for e in efficiency if e["name"] in competitors]

        return {
            "type": "scatter",
            "data": {
                "datasets": [{
                    "label": "Cost vs Return",
                    "data": [
                        {"x": e["total_cost"], "y": e["return_pct"], "label": e["name"]}
                        for e in efficiency
                    ],
                    "backgroundColor": "rgba(255, 99, 132, 0.6)"
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "Cost Efficiency Analysis"}
                },
                "scales": {
                    "x": {"title": {"display": True, "text": "Total Cost ($)"}},
                    "y": {"title": {"display": True, "text": "Return (%)"}}
                }
            }
        }

    def _get_confidence_histogram(
        self,
        competitors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get histogram of decision confidence levels."""
        confidences = []

        for name, perf in self.arena.performance.items():
            if competitors and name not in competitors:
                continue

            for decision in perf.decisions:
                confidences.append(decision.confidence)

        # Create histogram bins
        bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
        counts = [0] * (len(bins) - 1)

        for conf in confidences:
            for i in range(len(bins) - 1):
                if bins[i] <= conf < bins[i + 1]:
                    counts[i] += 1
                    break

        return {
            "type": "bar",
            "data": {
                "labels": ["0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"],
                "datasets": [{
                    "label": "Decision Count",
                    "data": counts,
                    "backgroundColor": "rgba(153, 102, 255, 0.6)"
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "Confidence Distribution"}
                }
            }
        }

    def export_data(self, format: str = "json") -> str:
        """
        Export dashboard data.

        Args:
            format: Export format (json, csv)

        Returns:
            Serialized data string
        """
        data = {
            "overview": self.get_overview(),
            "leaderboard": self.get_leaderboard(limit=100),
            "strategy_comparison": self.get_strategy_comparison(),
            "cost_efficiency": self.get_cost_efficiency()
        }

        if format == "json":
            return json.dumps(data, indent=2, default=str)
        else:
            # CSV export for leaderboard
            rows = ["rank,name,model,strategy,return_pct,win_rate,sharpe,cost"]
            for entry in data["leaderboard"]:
                rows.append(
                    f"{entry['rank']},{entry['name']},{entry['model']},"
                    f"{entry['strategy']},{entry['total_return_pct']:.2f},"
                    f"{entry['win_rate']:.3f},{entry['sharpe_ratio']:.2f},"
                    f"{entry['total_cost_usd']:.4f}"
                )
            return "\n".join(rows)

    def take_snapshot(self):
        """Take a snapshot of current metrics for history tracking."""
        leaderboard = self.arena.get_leaderboard()

        if leaderboard:
            best = leaderboard[0]
            metrics = DashboardMetrics(
                total_competitors=len(self.arena.competitors),
                total_trades=sum(p.total_trades for p in self.arena.performance.values()),
                best_performer=best["name"],
                best_return=best["total_return_pct"],
                avg_win_rate=sum(p.win_rate for p in self.arena.performance.values()) / len(self.arena.performance),
                total_cost=sum(p.total_cost_usd for p in self.arena.performance.values())
            )
        else:
            metrics = DashboardMetrics()

        self._snapshot_history.append(metrics)
        self._last_update = datetime.utcnow()

        # Keep only last 1000 snapshots
        if len(self._snapshot_history) > 1000:
            self._snapshot_history = self._snapshot_history[-1000:]


# FastAPI Router for dashboard endpoints (for integration with existing API)
def create_dashboard_router(dashboard: CompetitionDashboard):
    """
    Create FastAPI router for dashboard endpoints.

    Usage:
        from fastapi import FastAPI
        from core.competition.dashboard import create_dashboard_router, CompetitionDashboard

        app = FastAPI()
        dashboard = CompetitionDashboard(arena)
        app.include_router(create_dashboard_router(dashboard), prefix="/competition")
    """
    try:
        from fastapi import APIRouter, Query
    except ImportError:
        logger.warning("FastAPI not installed, router creation skipped")
        return None

    router = APIRouter()

    @router.get("/overview")
    async def get_overview():
        """Get competition overview."""
        return dashboard.get_overview()

    @router.get("/leaderboard")
    async def get_leaderboard(
        sort_by: str = Query("total_return_pct"),
        limit: int = Query(20, ge=1, le=100)
    ):
        """Get competition leaderboard."""
        return dashboard.get_leaderboard(sort_by=sort_by, limit=limit)

    @router.get("/strategies")
    async def get_strategy_comparison():
        """Get strategy comparison."""
        return dashboard.get_strategy_comparison()

    @router.get("/efficiency")
    async def get_cost_efficiency():
        """Get cost efficiency analysis."""
        return dashboard.get_cost_efficiency()

    @router.get("/decisions")
    async def get_decisions(
        competitor: Optional[str] = None,
        symbol: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = Query(100, ge=1, le=1000)
    ):
        """Get decision history."""
        return dashboard.get_decision_history(
            competitor=competitor,
            symbol=symbol,
            action=action,
            limit=limit
        )

    @router.get("/chart/{chart_type}")
    async def get_chart_data(
        chart_type: str,
        competitors: Optional[str] = None
    ):
        """Get chart data for visualization."""
        competitor_list = competitors.split(",") if competitors else None
        return dashboard.get_chart_data(chart_type, competitor_list)

    @router.get("/export")
    async def export_data(format: str = Query("json")):
        """Export dashboard data."""
        return {"data": dashboard.export_data(format=format)}

    return router
