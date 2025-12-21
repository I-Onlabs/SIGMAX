"""
Risk Engine

Performs pre-trade risk checks with reason codes for deterministic replay.
"""

from typing import Dict, Tuple
from dataclasses import dataclass
import time

from pkg.common import get_logger, get_metrics_collector, get_timestamp_ns, calculate_latency_us
from pkg.schemas import OrderIntent, Reject, RejectReason, get_trading_metrics


@dataclass
class PositionState:
    """Current position state for a symbol"""
    symbol_id: int
    qty: float = 0.0
    notional_usd: float = 0.0
    avg_price: float = 0.0


@dataclass
class RateLimitState:
    """Rate limiting state"""
    count: int = 0
    window_start_ns: int = 0


class RiskEngine:
    """
    Pre-trade risk engine with pure function checks.
    
    Performs:
    - Position limit checks
    - Notional limit checks
    - Price band checks
    - Rate limiting
    - Basic sanity checks
    """
    
    def __init__(self, config, publisher):
        self.config = config
        self.publisher = publisher
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("risk")
        self.trading_metrics = get_trading_metrics()
        
        # Get risk limits from config
        self.max_position_usd = 5000.0
        self.max_order_usd = 500.0
        self.price_band_pct = 5.0
        self.rate_limit_per_sec = 5
        
        if hasattr(config, 'risk'):
            self.max_position_usd = config.risk.max_position_usd
            self.max_order_usd = config.risk.max_order_usd
            self.price_band_pct = config.risk.price_band_pct
            self.rate_limit_per_sec = config.risk.rate_limit_per_sec
        
        # State tracking
        self.positions: Dict[int, PositionState] = {}
        self.rate_limits: Dict[int, RateLimitState] = {}
        
        # Price cache for band checks
        self.last_prices: Dict[int, float] = {}
        
        self.running = False
        
    async def start(self):
        """Start the risk engine"""
        self.logger.info("risk_engine_started",
                        max_position_usd=self.max_position_usd,
                        max_order_usd=self.max_order_usd,
                        rate_limit_per_sec=self.rate_limit_per_sec)
        self.running = True
        
    async def stop(self):
        """Stop the risk engine"""
        self.running = False
        self.logger.info("risk_engine_stopped")
    
    async def check_order(self, order: OrderIntent):
        """
        Perform all risk checks on an order intent.
        
        Args:
            order: OrderIntent to check
        
        Returns:
            Publishes approved order or rejection
        """
        try:
            start_ts = get_timestamp_ns()
            
            # Perform checks
            passed, reason_code, reason_msg = self._perform_checks(order)
            
            # Record metrics
            self.trading_metrics.record_risk_check(passed, reason_msg if not passed else None)
            
            if passed:
                # Forward to router
                await self.publisher.publish_approved(order)
                
                # Update position tracking
                self._update_position_tracking(order)
                
                self.logger.info("order_approved",
                               client_id=order.client_id,
                               symbol_id=order.symbol_id,
                               side=order.side,
                               qty=order.qty)
            else:
                # Publish rejection
                reject = Reject(
                    ts_ns=get_timestamp_ns(),
                    client_id=order.client_id,
                    reason_code=reason_code,
                    reason_msg=reason_msg,
                    source="risk"
                )
                
                await self.publisher.publish_rejection(reject)
                
                self.logger.warning("order_rejected",
                                  client_id=order.client_id,
                                  symbol_id=order.symbol_id,
                                  reason_code=reason_code,
                                  reason_msg=reason_msg)
            
            # Record latency
            end_ts = get_timestamp_ns()
            risk_latency_us = calculate_latency_us(start_ts, end_ts)
            total_latency_us = calculate_latency_us(order.ts_ns, end_ts)
            
            self.metrics.record_latency("risk_check", risk_latency_us)
            self.metrics.record_latency("order_to_risk", total_latency_us)
            
        except Exception as e:
            self.logger.error("check_order_error",
                            client_id=order.client_id,
                            error=str(e),
                            exc_info=True)
            self.metrics.record_error("check_order_failed")
    
    def _perform_checks(self, order: OrderIntent) -> Tuple[bool, int, str]:
        """
        Perform all risk checks.
        
        Returns:
            (passed, reason_code, reason_msg)
        """
        
        # 1. Sanity checks
        if order.qty <= 0:
            return False, RejectReason.INVALID_QUANTITY, "Invalid quantity"
        
        if order.price is not None and order.price <= 0:
            return False, RejectReason.INVALID_PRICE, "Invalid price"
        
        # 2. Order size check
        if order.price:
            order_notional = order.qty * order.price
            if order_notional > self.max_order_usd:
                return False, RejectReason.POSITION_LIMIT, \
                       f"Order size ${order_notional:.2f} exceeds max ${self.max_order_usd}"
        
        # 3. Position limit check
        position = self.positions.get(order.symbol_id, PositionState(order.symbol_id))
        new_position_qty = position.qty
        
        if order.side.name == "BUY":
            new_position_qty += order.qty
        else:
            new_position_qty -= order.qty
        
        if order.price:
            new_position_notional = abs(new_position_qty * order.price)
            if new_position_notional > self.max_position_usd:
                return False, RejectReason.POSITION_LIMIT, \
                       f"Position would be ${new_position_notional:.2f}, exceeds max ${self.max_position_usd}"
        
        # 4. Price band check
        if order.price and order.symbol_id in self.last_prices:
            last_price = self.last_prices[order.symbol_id]
            price_change_pct = abs((order.price - last_price) / last_price * 100)
            
            if price_change_pct > self.price_band_pct:
                return False, RejectReason.PRICE_BAND, \
                       f"Price {order.price} deviates {price_change_pct:.2f}% from last {last_price}"
        
        # 5. Rate limiting
        if not self._check_rate_limit(order.symbol_id):
            return False, RejectReason.RATE_LIMIT, "Rate limit exceeded"
        
        # All checks passed
        return True, 0, ""
    
    def _check_rate_limit(self, symbol_id: int) -> bool:
        """Check rate limit for symbol"""
        now_ns = time.time_ns()
        window_ns = 1_000_000_000  # 1 second
        
        if symbol_id not in self.rate_limits:
            self.rate_limits[symbol_id] = RateLimitState(count=1, window_start_ns=now_ns)
            return True
        
        rl = self.rate_limits[symbol_id]
        
        # Check if we're in a new window
        if now_ns - rl.window_start_ns > window_ns:
            # New window
            rl.count = 1
            rl.window_start_ns = now_ns
            return True
        
        # Same window - check count
        if rl.count >= self.rate_limit_per_sec:
            return False
        
        rl.count += 1
        return True
    
    def _update_position_tracking(self, order: OrderIntent):
        """Update position tracking after order approval"""
        if order.symbol_id not in self.positions:
            self.positions[order.symbol_id] = PositionState(order.symbol_id)
        
        position = self.positions[order.symbol_id]
        
        if order.side.name == "BUY":
            position.qty += order.qty
        else:
            position.qty -= order.qty
        
        if order.price:
            position.notional_usd = abs(position.qty * order.price)
            self.last_prices[order.symbol_id] = order.price
