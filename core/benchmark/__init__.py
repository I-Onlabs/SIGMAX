"""
SIGMAX Benchmark Module - Live Benchmarking Framework

Features:
- Live benchmarking with real market data
- Real-time leaderboard with WebSocket support
- Comprehensive agent performance analytics
"""

from .live_benchmark import (
    LiveBenchmark,
    BenchmarkState,
    BenchmarkMetrics,
    BenchmarkCheckpoint,
    AgentRegistration,
    create_mock_data_feed
)

from .realtime_leaderboard import (
    RealtimeLeaderboard,
    RankingMetric,
    LeaderboardEntry,
    RankingSnapshot,
    create_leaderboard_router
)

from .agent_analytics import (
    AgentAnalytics,
    PerformanceBreakdown,
    AgentProfile,
    DecisionPattern,
    TimeWindow,
    RiskProfile,
    create_analytics_router
)

__all__ = [
    # Live Benchmark
    "LiveBenchmark",
    "BenchmarkState",
    "BenchmarkMetrics",
    "BenchmarkCheckpoint",
    "AgentRegistration",
    "create_mock_data_feed",
    # Real-time Leaderboard
    "RealtimeLeaderboard",
    "RankingMetric",
    "LeaderboardEntry",
    "RankingSnapshot",
    "create_leaderboard_router",
    # Agent Analytics
    "AgentAnalytics",
    "PerformanceBreakdown",
    "AgentProfile",
    "DecisionPattern",
    "TimeWindow",
    "RiskProfile",
    "create_analytics_router"
]
