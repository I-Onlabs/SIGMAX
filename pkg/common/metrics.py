"""
Metrics collection for observability.

Uses Prometheus client for metrics export.
Tracks latencies, throughput, and system health.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from typing import Dict, Optional


class MetricsCollector:
    """
    Centralized metrics collector for the trading system.
    
    Tracks:
    - Latencies at each pipeline stage
    - Message counts and throughput
    - System health (queue depths, memory, etc.)
    - Trading metrics (fills, rejections, P&L)
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        
        # Latency histograms (microseconds)
        self.latency_histogram = Histogram(
            f'{service_name}_latency_microseconds',
            'Processing latency in microseconds',
            ['stage'],
            buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
        )
        
        # Message counters
        self.messages_received = Counter(
            f'{service_name}_messages_received_total',
            'Total messages received',
            ['message_type']
        )
        
        self.messages_sent = Counter(
            f'{service_name}_messages_sent_total',
            'Total messages sent',
            ['message_type']
        )
        
        # Error counter
        self.errors = Counter(
            f'{service_name}_errors_total',
            'Total errors',
            ['error_type']
        )
        
        # Queue depth gauge
        self.queue_depth = Gauge(
            f'{service_name}_queue_depth',
            'Current queue depth',
            ['queue_name']
        )
        
        # Service info
        self.info = Info(
            f'{service_name}_info',
            'Service information'
        )
    
    def record_latency(self, stage: str, latency_us: float):
        """Record latency for a pipeline stage"""
        self.latency_histogram.labels(stage=stage).observe(latency_us)
    
    def increment_received(self, message_type: str):
        """Increment received message counter"""
        self.messages_received.labels(message_type=message_type).inc()
    
    def increment_sent(self, message_type: str):
        """Increment sent message counter"""
        self.messages_sent.labels(message_type=message_type).inc()
    
    def record_error(self, error_type: str):
        """Record an error"""
        self.errors.labels(error_type=error_type).inc()
    
    def set_queue_depth(self, queue_name: str, depth: int):
        """Set queue depth gauge"""
        self.queue_depth.labels(queue_name=queue_name).set(depth)
    
    def set_info(self, **kwargs):
        """Set service info"""
        self.info.info(kwargs)


class TradingMetrics:
    """
    Trading-specific metrics.
    
    Tracks:
    - Order flow (intents, fills, rejections)
    - P&L
    - Risk metrics
    """
    
    def __init__(self):
        # Order flow
        self.orders_submitted = Counter(
            'sigmax_orders_submitted_total',
            'Total orders submitted',
            ['symbol', 'side', 'order_type']
        )
        
        self.orders_filled = Counter(
            'sigmax_orders_filled_total',
            'Total orders filled',
            ['symbol', 'side']
        )
        
        self.orders_rejected = Counter(
            'sigmax_orders_rejected_total',
            'Total orders rejected',
            ['symbol', 'reason']
        )
        
        # Fill metrics
        self.fill_size = Histogram(
            'sigmax_fill_size_usd',
            'Fill size in USD',
            ['symbol'],
            buckets=[10, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
        )
        
        self.fill_price_slippage = Histogram(
            'sigmax_fill_slippage_bps',
            'Fill price slippage in basis points',
            ['symbol'],
            buckets=[0.1, 0.5, 1, 2, 5, 10, 25, 50, 100]
        )
        
        # P&L
        self.realized_pnl = Counter(
            'sigmax_realized_pnl_usd',
            'Realized P&L in USD',
            ['symbol']
        )
        
        self.unrealized_pnl = Gauge(
            'sigmax_unrealized_pnl_usd',
            'Unrealized P&L in USD',
            ['symbol']
        )
        
        # Positions
        self.position_size = Gauge(
            'sigmax_position_size',
            'Current position size',
            ['symbol']
        )
        
        # Risk metrics
        self.risk_checks_total = Counter(
            'sigmax_risk_checks_total',
            'Total risk checks',
            ['result']
        )
        
        self.risk_blocks = Counter(
            'sigmax_risk_blocks_total',
            'Total risk blocks',
            ['reason']
        )
        
        # Fees
        self.fees_paid = Counter(
            'sigmax_fees_paid_usd',
            'Total fees paid in USD',
            ['symbol', 'fee_type']
        )
    
    def record_order_submitted(self, symbol: str, side: str, order_type: str):
        """Record order submission"""
        self.orders_submitted.labels(
            symbol=symbol,
            side=side,
            order_type=order_type
        ).inc()
    
    def record_order_filled(self, symbol: str, side: str, size_usd: float):
        """Record order fill"""
        self.orders_filled.labels(symbol=symbol, side=side).inc()
        self.fill_size.labels(symbol=symbol).observe(size_usd)
    
    def record_order_rejected(self, symbol: str, reason: str):
        """Record order rejection"""
        self.orders_rejected.labels(symbol=symbol, reason=reason).inc()
    
    def record_risk_check(self, passed: bool, reason: Optional[str] = None):
        """Record risk check"""
        result = "pass" if passed else "block"
        self.risk_checks_total.labels(result=result).inc()
        
        if not passed and reason:
            self.risk_blocks.labels(reason=reason).inc()
    
    def update_position(self, symbol: str, size: float):
        """Update position size"""
        self.position_size.labels(symbol=symbol).set(size)
    
    def update_unrealized_pnl(self, symbol: str, pnl: float):
        """Update unrealized P&L"""
        self.unrealized_pnl.labels(symbol=symbol).set(pnl)
    
    def record_realized_pnl(self, symbol: str, pnl: float):
        """Record realized P&L"""
        self.realized_pnl.labels(symbol=symbol).inc(pnl)
    
    def record_fee(self, symbol: str, fee_usd: float, fee_type: str):
        """Record fee paid"""
        self.fees_paid.labels(symbol=symbol, fee_type=fee_type).inc(fee_usd)


# Global instances
_metrics_collectors: Dict[str, MetricsCollector] = {}
_trading_metrics: Optional[TradingMetrics] = None


def get_metrics_collector(service_name: str) -> MetricsCollector:
    """Get or create metrics collector for a service"""
    if service_name not in _metrics_collectors:
        _metrics_collectors[service_name] = MetricsCollector(service_name)
    return _metrics_collectors[service_name]


def get_trading_metrics() -> TradingMetrics:
    """Get global trading metrics instance"""
    global _trading_metrics
    if _trading_metrics is None:
        _trading_metrics = TradingMetrics()
    return _trading_metrics
