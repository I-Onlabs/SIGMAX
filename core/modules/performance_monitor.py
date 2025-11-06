"""
Performance Monitoring and Metrics Collection for SIGMAX

Tracks system performance, trading metrics, and resource usage
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import time
import asyncio
from loguru import logger
import numpy as np

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available. System metrics disabled.")


@dataclass
class PerformanceMetric:
    """Single performance metric"""
    timestamp: datetime
    name: str
    value: float
    unit: str
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class TradingMetrics:
    """Trading performance metrics"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    current_streak: int = 0
    best_trade: float = 0.0
    worst_trade: float = 0.0


@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_mb: float = 0.0
    disk_usage_percent: float = 0.0
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0
    open_files: int = 0
    threads: int = 0


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system

    Features:
    - Trading metrics tracking
    - System resource monitoring
    - Latency measurement
    - Throughput analysis
    - Historical data storage
    - Real-time statistics
    """

    def __init__(
        self,
        history_size: int = 10000,
        aggregate_interval: int = 60
    ):
        self.history_size = history_size
        self.aggregate_interval = aggregate_interval

        # Metrics storage
        self.metrics_history: deque = deque(maxlen=history_size)
        self.trading_metrics = TradingMetrics()
        self.system_metrics = SystemMetrics()

        # Latency tracking
        self.latency_measurements: Dict[str, deque] = {}

        # Throughput tracking
        self.throughput_counters: Dict[str, int] = {}
        self.throughput_start_time = time.time()

        # Trade history
        self.trade_history: deque = deque(maxlen=1000)
        self.pnl_history: deque = deque(maxlen=1000)

        # Monitoring task
        self.monitoring_task: Optional[asyncio.Task] = None
        self.running = False

        logger.info("✓ Performance Monitor initialized")

    async def start(self):
        """Start monitoring"""
        if self.running:
            logger.warning("Performance monitor already running")
            return

        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("✓ Performance monitoring started")

    async def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("✓ Performance monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Collect system metrics
                if PSUTIL_AVAILABLE:
                    await self._collect_system_metrics()

                # Calculate trading metrics
                self._calculate_trading_metrics()

                # Sleep until next interval
                await asyncio.sleep(self.aggregate_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.aggregate_interval)

    async def _collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # CPU
            self.system_metrics.cpu_percent = psutil.cpu_percent(interval=1)

            # Memory
            mem = psutil.virtual_memory()
            self.system_metrics.memory_percent = mem.percent
            self.system_metrics.memory_mb = mem.used / 1024 / 1024

            # Disk
            disk = psutil.disk_usage('/')
            self.system_metrics.disk_usage_percent = disk.percent

            # Network
            net = psutil.net_io_counters()
            self.system_metrics.network_sent_mb = net.bytes_sent / 1024 / 1024
            self.system_metrics.network_recv_mb = net.bytes_recv / 1024 / 1024

            # Process info
            process = psutil.Process()
            self.system_metrics.open_files = len(process.open_files())
            self.system_metrics.threads = process.num_threads()

            # Record metrics
            self._record_metric('cpu_percent', self.system_metrics.cpu_percent, '%')
            self._record_metric('memory_mb', self.system_metrics.memory_mb, 'MB')

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    def _calculate_trading_metrics(self):
        """Calculate trading performance metrics"""
        if not self.trade_history:
            return

        trades = list(self.trade_history)

        # Basic counts
        self.trading_metrics.total_trades = len(trades)
        self.trading_metrics.winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
        self.trading_metrics.losing_trades = sum(1 for t in trades if t.get('pnl', 0) < 0)

        # Win rate
        if self.trading_metrics.total_trades > 0:
            self.trading_metrics.win_rate = self.trading_metrics.winning_trades / self.trading_metrics.total_trades

        # PnL
        pnls = [t.get('pnl', 0) for t in trades]
        self.trading_metrics.total_pnl = sum(pnls)

        # Average win/loss
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]

        self.trading_metrics.avg_win = np.mean(wins) if wins else 0.0
        self.trading_metrics.avg_loss = np.mean(losses) if losses else 0.0

        # Profit factor
        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 1
        self.trading_metrics.profit_factor = total_wins / total_losses if total_losses > 0 else 0

        # Best/worst trades
        self.trading_metrics.best_trade = max(pnls) if pnls else 0.0
        self.trading_metrics.worst_trade = min(pnls) if pnls else 0.0

        # Sharpe ratio (simplified)
        if len(pnls) > 1:
            returns = np.array(pnls)
            sharpe = np.mean(returns) / (np.std(returns) + 1e-10)
            self.trading_metrics.sharpe_ratio = sharpe * np.sqrt(252)  # Annualized

        # Max drawdown
        if self.pnl_history:
            cumulative = np.cumsum([p.get('pnl', 0) for p in self.pnl_history])
            running_max = np.maximum.accumulate(cumulative)
            drawdown = running_max - cumulative
            self.trading_metrics.max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0.0

        # Current streak
        streak = 0
        for trade in reversed(trades):
            pnl = trade.get('pnl', 0)
            if pnl > 0:
                if streak >= 0:
                    streak += 1
                else:
                    break
            elif pnl < 0:
                if streak <= 0:
                    streak -= 1
                else:
                    break
            else:
                break
        self.trading_metrics.current_streak = streak

    def _record_metric(
        self,
        name: str,
        value: float,
        unit: str,
        tags: Optional[Dict[str, str]] = None
    ):
        """Record a metric"""
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            name=name,
            value=value,
            unit=unit,
            tags=tags or {}
        )
        self.metrics_history.append(metric)

    def record_trade(
        self,
        symbol: str,
        action: str,
        size: float,
        entry_price: float,
        exit_price: Optional[float] = None,
        pnl: Optional[float] = None,
        fees: float = 0.0
    ):
        """Record a trade"""
        trade = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'action': action,
            'size': size,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl or 0.0,
            'fees': fees
        }
        self.trade_history.append(trade)

        if pnl is not None:
            self.pnl_history.append({'timestamp': datetime.now(), 'pnl': pnl})

        logger.debug(f"Trade recorded: {symbol} {action} {size} @ {entry_price}")

    def record_latency(self, operation: str, latency_ms: float):
        """Record operation latency"""
        if operation not in self.latency_measurements:
            self.latency_measurements[operation] = deque(maxlen=1000)

        self.latency_measurements[operation].append(latency_ms)
        self._record_metric(f'latency_{operation}', latency_ms, 'ms', {'operation': operation})

    def record_throughput(self, operation: str, count: int = 1):
        """Record throughput counter"""
        if operation not in self.throughput_counters:
            self.throughput_counters[operation] = 0

        self.throughput_counters[operation] += count

    def get_latency_stats(self, operation: str) -> Dict[str, float]:
        """Get latency statistics for an operation"""
        if operation not in self.latency_measurements:
            return {}

        measurements = list(self.latency_measurements[operation])
        if not measurements:
            return {}

        return {
            'min': np.min(measurements),
            'max': np.max(measurements),
            'mean': np.mean(measurements),
            'median': np.median(measurements),
            'p95': np.percentile(measurements, 95),
            'p99': np.percentile(measurements, 99),
            'count': len(measurements)
        }

    def get_throughput_stats(self) -> Dict[str, Dict[str, float]]:
        """Get throughput statistics"""
        elapsed_time = time.time() - self.throughput_start_time

        stats = {}
        for operation, count in self.throughput_counters.items():
            stats[operation] = {
                'total_count': count,
                'rate_per_second': count / elapsed_time if elapsed_time > 0 else 0,
                'rate_per_minute': (count / elapsed_time) * 60 if elapsed_time > 0 else 0
            }

        return stats

    def get_trading_metrics(self) -> Dict[str, Any]:
        """Get current trading metrics"""
        return {
            'total_trades': self.trading_metrics.total_trades,
            'winning_trades': self.trading_metrics.winning_trades,
            'losing_trades': self.trading_metrics.losing_trades,
            'win_rate': self.trading_metrics.win_rate,
            'total_pnl': self.trading_metrics.total_pnl,
            'avg_win': self.trading_metrics.avg_win,
            'avg_loss': self.trading_metrics.avg_loss,
            'profit_factor': self.trading_metrics.profit_factor,
            'sharpe_ratio': self.trading_metrics.sharpe_ratio,
            'max_drawdown': self.trading_metrics.max_drawdown,
            'current_streak': self.trading_metrics.current_streak,
            'best_trade': self.trading_metrics.best_trade,
            'worst_trade': self.trading_metrics.worst_trade
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            'cpu_percent': self.system_metrics.cpu_percent,
            'memory_percent': self.system_metrics.memory_percent,
            'memory_mb': self.system_metrics.memory_mb,
            'disk_usage_percent': self.system_metrics.disk_usage_percent,
            'network_sent_mb': self.system_metrics.network_sent_mb,
            'network_recv_mb': self.system_metrics.network_recv_mb,
            'open_files': self.system_metrics.open_files,
            'threads': self.system_metrics.threads
        }

    def get_recent_metrics(
        self,
        name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent metrics"""
        metrics = list(self.metrics_history)

        if name:
            metrics = [m for m in metrics if m.name == name]

        metrics = metrics[-limit:]

        return [
            {
                'timestamp': m.timestamp.isoformat(),
                'name': m.name,
                'value': m.value,
                'unit': m.unit,
                'tags': m.tags
            }
            for m in metrics
        ]

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            'trading': self.get_trading_metrics(),
            'system': self.get_system_metrics(),
            'latency': {
                op: self.get_latency_stats(op)
                for op in self.latency_measurements.keys()
            },
            'throughput': self.get_throughput_stats(),
            'uptime_seconds': time.time() - self.throughput_start_time
        }

    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics_history.clear()
        self.latency_measurements.clear()
        self.throughput_counters.clear()
        self.trade_history.clear()
        self.pnl_history.clear()
        self.throughput_start_time = time.time()
        self.trading_metrics = TradingMetrics()
        logger.info("✓ Performance metrics reset")


class LatencyTimer:
    """Context manager for measuring latency"""

    def __init__(self, monitor: PerformanceMonitor, operation: str):
        self.monitor = monitor
        self.operation = operation
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.time() - self.start_time) * 1000
        self.monitor.record_latency(self.operation, latency_ms)


# Global performance monitor instance
_global_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor"""
    global _global_performance_monitor
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor()
    return _global_performance_monitor


def set_performance_monitor(monitor: PerformanceMonitor):
    """Set global performance monitor"""
    global _global_performance_monitor
    _global_performance_monitor = monitor
