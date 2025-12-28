"""
Real-Time Leaderboard System
Live-updating rankings across all benchmarks and competitions

Features:
- WebSocket-based real-time updates
- Multi-source aggregation (benchmarks, arenas, backtests)
- Customizable ranking criteria
- Historical ranking snapshots
"""

from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import asyncio
import json
from loguru import logger

from .live_benchmark import LiveBenchmark, BenchmarkMetrics


class RankingMetric(Enum):
    """Metrics for ranking agents."""
    TOTAL_RETURN = "total_return_pct"
    SHARPE_RATIO = "sharpe_ratio"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    MAX_DRAWDOWN = "max_drawdown"
    RISK_ADJUSTED = "risk_adjusted"
    CONSISTENCY = "consistency"


@dataclass
class LeaderboardEntry:
    """A single entry in the leaderboard."""
    agent_id: str
    agent_name: str
    model: str
    strategy: str
    rank: int
    score: float
    metrics: Dict[str, float]
    trend: str  # "up", "down", "stable", "new"
    previous_rank: Optional[int] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "model": self.model,
            "strategy": self.strategy,
            "rank": self.rank,
            "score": round(self.score, 4),
            "metrics": {k: round(v, 4) for k, v in self.metrics.items()},
            "trend": self.trend,
            "previous_rank": self.previous_rank,
            "last_updated": self.last_updated.isoformat()
        }


@dataclass
class RankingSnapshot:
    """Historical snapshot of rankings."""
    timestamp: datetime
    rankings: List[LeaderboardEntry]
    metric_used: RankingMetric

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "rankings": [e.to_dict() for e in self.rankings],
            "metric_used": self.metric_used.value
        }


class RealtimeLeaderboard:
    """
    Real-time leaderboard with WebSocket support.

    Usage:
        leaderboard = RealtimeLeaderboard()

        # Connect data sources
        leaderboard.connect_benchmark(benchmark)
        leaderboard.connect_arena(arena)

        # Get current rankings
        rankings = leaderboard.get_rankings()

        # Subscribe to updates
        async for update in leaderboard.subscribe():
            print(f"New ranking: {update}")
    """

    def __init__(
        self,
        primary_metric: RankingMetric = RankingMetric.RISK_ADJUSTED,
        update_interval: float = 1.0,
        snapshot_interval: float = 60.0
    ):
        """
        Initialize real-time leaderboard.

        Args:
            primary_metric: Primary ranking metric
            update_interval: Seconds between updates
            snapshot_interval: Seconds between snapshots
        """
        self.primary_metric = primary_metric
        self.update_interval = update_interval
        self.snapshot_interval = snapshot_interval

        # Agent data
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._metrics: Dict[str, Dict[str, float]] = {}
        self._previous_ranks: Dict[str, int] = {}

        # Data sources
        self._benchmarks: List[LiveBenchmark] = []
        self._arenas: List[Any] = []  # CompetitionArena

        # History
        self._snapshots: List[RankingSnapshot] = []
        self._max_snapshots = 1440  # 24 hours at 1-min intervals

        # Subscribers
        self._subscribers: Set[asyncio.Queue] = set()

        # State
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        self._last_snapshot: datetime = datetime.utcnow()

    def register_agent(
        self,
        agent_id: str,
        name: str,
        model: str,
        strategy: str
    ):
        """Register an agent for tracking."""
        self._agents[agent_id] = {
            "name": name,
            "model": model,
            "strategy": strategy,
            "registered_at": datetime.utcnow()
        }
        self._metrics[agent_id] = {}
        logger.debug(f"Registered agent: {name} ({agent_id})")

    def update_metrics(
        self,
        agent_id: str,
        metrics: Dict[str, float]
    ):
        """Update metrics for an agent."""
        if agent_id not in self._agents:
            logger.warning(f"Unknown agent: {agent_id}")
            return

        self._metrics[agent_id].update(metrics)

    def connect_benchmark(self, benchmark: LiveBenchmark):
        """Connect a live benchmark as data source."""
        self._benchmarks.append(benchmark)

        # Import existing agents
        for agent_id, reg in benchmark._agents.items():
            self.register_agent(
                agent_id=agent_id,
                name=reg.name,
                model=reg.model,
                strategy=reg.strategy
            )

        logger.info(f"Connected benchmark: {benchmark.name}")

    def connect_arena(self, arena):
        """Connect a competition arena as data source."""
        self._arenas.append(arena)

        # Import competitors
        for name, perf in arena.performance.items():
            agent_id = f"arena_{name}"
            self.register_agent(
                agent_id=agent_id,
                name=name,
                model=arena.competitors[name].config.model_id if name in arena.competitors else "unknown",
                strategy=arena.competitors[name].config.strategy.value if name in arena.competitors else "unknown"
            )

        logger.info(f"Connected arena: {arena.name}")

    def _collect_metrics(self):
        """Collect metrics from all sources."""
        # From benchmarks
        for benchmark in self._benchmarks:
            for agent_id, metrics in benchmark._metrics.items():
                if agent_id in self._agents:
                    self._metrics[agent_id] = {
                        "total_return_pct": metrics.total_return_pct,
                        "sharpe_ratio": metrics.sharpe_ratio,
                        "win_rate": metrics.win_rate,
                        "total_trades": metrics.total_trades,
                        "max_drawdown": metrics.max_drawdown_pct,
                        "profit_factor": metrics.profit_factor
                    }

        # From arenas
        for arena in self._arenas:
            for name, perf in arena.performance.items():
                agent_id = f"arena_{name}"
                if agent_id in self._agents:
                    self._metrics[agent_id] = {
                        "total_return_pct": perf.total_return_pct,
                        "sharpe_ratio": perf.sharpe_ratio,
                        "win_rate": perf.win_rate,
                        "total_trades": perf.total_trades,
                        "max_drawdown": perf.max_drawdown_pct,
                        "profit_factor": perf.profit_factor if hasattr(perf, 'profit_factor') else 0
                    }

    def _calculate_score(self, metrics: Dict[str, float]) -> float:
        """Calculate ranking score based on primary metric."""
        if self.primary_metric == RankingMetric.TOTAL_RETURN:
            return metrics.get("total_return_pct", 0)

        elif self.primary_metric == RankingMetric.SHARPE_RATIO:
            return metrics.get("sharpe_ratio", 0)

        elif self.primary_metric == RankingMetric.WIN_RATE:
            return metrics.get("win_rate", 0)

        elif self.primary_metric == RankingMetric.PROFIT_FACTOR:
            return metrics.get("profit_factor", 0)

        elif self.primary_metric == RankingMetric.MAX_DRAWDOWN:
            # Lower is better, so negate
            return -metrics.get("max_drawdown", 0)

        elif self.primary_metric == RankingMetric.RISK_ADJUSTED:
            # Composite score
            sharpe = metrics.get("sharpe_ratio", 0)
            returns = metrics.get("total_return_pct", 0)
            drawdown = metrics.get("max_drawdown", 0)

            # Risk-adjusted = (Sharpe * 0.4) + (Return * 0.4) - (Drawdown * 0.2)
            return (sharpe * 0.4) + (returns * 0.4) - (drawdown * 0.2)

        elif self.primary_metric == RankingMetric.CONSISTENCY:
            win_rate = metrics.get("win_rate", 0)
            profit_factor = metrics.get("profit_factor", 0)
            return (win_rate * 0.5) + (min(profit_factor, 3) / 3 * 0.5)

        return 0

    def _determine_trend(
        self,
        agent_id: str,
        new_rank: int
    ) -> str:
        """Determine rank trend for agent."""
        if agent_id not in self._previous_ranks:
            return "new"

        prev_rank = self._previous_ranks[agent_id]

        if new_rank < prev_rank:
            return "up"
        elif new_rank > prev_rank:
            return "down"
        else:
            return "stable"

    def get_rankings(
        self,
        limit: int = 50,
        metric: Optional[RankingMetric] = None
    ) -> List[LeaderboardEntry]:
        """
        Get current rankings.

        Args:
            limit: Maximum entries to return
            metric: Override primary metric for sorting

        Returns:
            List of LeaderboardEntry sorted by rank
        """
        self._collect_metrics()

        use_metric = metric or self.primary_metric
        entries = []

        for agent_id, agent_info in self._agents.items():
            metrics = self._metrics.get(agent_id, {})

            if not metrics:
                continue

            score = self._calculate_score(metrics)

            entries.append({
                "agent_id": agent_id,
                "agent_info": agent_info,
                "metrics": metrics,
                "score": score
            })

        # Sort by score descending
        entries.sort(key=lambda x: x["score"], reverse=True)

        # Build leaderboard entries with ranks
        leaderboard = []
        for rank, entry in enumerate(entries[:limit], 1):
            agent_id = entry["agent_id"]
            trend = self._determine_trend(agent_id, rank)

            lb_entry = LeaderboardEntry(
                agent_id=agent_id,
                agent_name=entry["agent_info"]["name"],
                model=entry["agent_info"]["model"],
                strategy=entry["agent_info"]["strategy"],
                rank=rank,
                score=entry["score"],
                metrics=entry["metrics"],
                trend=trend,
                previous_rank=self._previous_ranks.get(agent_id)
            )

            leaderboard.append(lb_entry)
            self._previous_ranks[agent_id] = rank

        return leaderboard

    def get_rankings_dict(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get rankings as list of dicts."""
        return [e.to_dict() for e in self.get_rankings(limit)]

    def get_agent_rank(self, agent_id: str) -> Optional[LeaderboardEntry]:
        """Get specific agent's ranking."""
        rankings = self.get_rankings(limit=1000)
        for entry in rankings:
            if entry.agent_id == agent_id:
                return entry
        return None

    def get_top_performers(
        self,
        n: int = 3,
        by_metric: Optional[RankingMetric] = None
    ) -> List[LeaderboardEntry]:
        """Get top N performers."""
        return self.get_rankings(limit=n, metric=by_metric)

    def get_ranking_history(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical rankings for an agent."""
        history = []

        for snapshot in self._snapshots[-limit:]:
            for entry in snapshot.rankings:
                if entry.agent_id == agent_id:
                    history.append({
                        "timestamp": snapshot.timestamp.isoformat(),
                        "rank": entry.rank,
                        "score": entry.score
                    })
                    break

        return history

    def _take_snapshot(self):
        """Take a ranking snapshot."""
        rankings = self.get_rankings()

        snapshot = RankingSnapshot(
            timestamp=datetime.utcnow(),
            rankings=rankings,
            metric_used=self.primary_metric
        )

        self._snapshots.append(snapshot)

        # Prune old snapshots
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots = self._snapshots[-self._max_snapshots:]

        self._last_snapshot = datetime.utcnow()

    async def subscribe(self) -> asyncio.Queue:
        """
        Subscribe to real-time updates.

        Returns:
            Queue that receives update events
        """
        queue = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from updates."""
        self._subscribers.discard(queue)

    async def _broadcast(self, event: Dict[str, Any]):
        """Broadcast event to all subscribers."""
        for queue in self._subscribers:
            try:
                await queue.put(event)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")

    async def _update_loop(self):
        """Main update loop."""
        while self._running:
            try:
                # Collect and rank
                rankings = self.get_rankings()

                # Check for snapshot
                if (datetime.utcnow() - self._last_snapshot).seconds >= self.snapshot_interval:
                    self._take_snapshot()

                # Broadcast update
                await self._broadcast({
                    "type": "ranking_update",
                    "timestamp": datetime.utcnow().isoformat(),
                    "rankings": [e.to_dict() for e in rankings[:10]],  # Top 10
                    "total_agents": len(rankings)
                })

                await asyncio.sleep(self.update_interval)

            except Exception as e:
                logger.error(f"Update loop error: {e}")
                await asyncio.sleep(1)

    async def start(self):
        """Start real-time updates."""
        if self._running:
            return

        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("Leaderboard started")

    async def stop(self):
        """Stop real-time updates."""
        self._running = False

        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        logger.info("Leaderboard stopped")

    def get_statistics(self) -> Dict[str, Any]:
        """Get leaderboard statistics."""
        rankings = self.get_rankings()

        if not rankings:
            return {"total_agents": 0}

        scores = [e.score for e in rankings]

        return {
            "total_agents": len(rankings),
            "total_snapshots": len(self._snapshots),
            "connected_benchmarks": len(self._benchmarks),
            "connected_arenas": len(self._arenas),
            "primary_metric": self.primary_metric.value,
            "score_stats": {
                "max": round(max(scores), 4),
                "min": round(min(scores), 4),
                "mean": round(sum(scores) / len(scores), 4)
            },
            "trend_distribution": {
                "up": sum(1 for e in rankings if e.trend == "up"),
                "down": sum(1 for e in rankings if e.trend == "down"),
                "stable": sum(1 for e in rankings if e.trend == "stable"),
                "new": sum(1 for e in rankings if e.trend == "new")
            }
        }


# FastAPI WebSocket integration
def create_leaderboard_router(leaderboard: RealtimeLeaderboard):
    """Create FastAPI router for leaderboard."""
    try:
        from fastapi import APIRouter, WebSocket, WebSocketDisconnect
        from fastapi.responses import JSONResponse
    except ImportError:
        logger.warning("FastAPI not installed")
        return None

    router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

    @router.get("/rankings")
    async def get_rankings(limit: int = 50, metric: str = None):
        """Get current rankings."""
        m = RankingMetric(metric) if metric else None
        return leaderboard.get_rankings_dict(limit=limit)

    @router.get("/agent/{agent_id}")
    async def get_agent(agent_id: str):
        """Get specific agent ranking."""
        entry = leaderboard.get_agent_rank(agent_id)
        if entry:
            return entry.to_dict()
        return JSONResponse(status_code=404, content={"error": "Agent not found"})

    @router.get("/agent/{agent_id}/history")
    async def get_agent_history(agent_id: str, limit: int = 100):
        """Get agent ranking history."""
        return leaderboard.get_ranking_history(agent_id, limit)

    @router.get("/top/{n}")
    async def get_top(n: int = 3):
        """Get top N performers."""
        return [e.to_dict() for e in leaderboard.get_top_performers(n)]

    @router.get("/statistics")
    async def get_statistics():
        """Get leaderboard statistics."""
        return leaderboard.get_statistics()

    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket for real-time updates."""
        await websocket.accept()

        queue = await leaderboard.subscribe()

        try:
            while True:
                update = await queue.get()
                await websocket.send_json(update)
        except WebSocketDisconnect:
            leaderboard.unsubscribe(queue)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            leaderboard.unsubscribe(queue)

    return router
