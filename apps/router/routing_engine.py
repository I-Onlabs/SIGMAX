"""
Routing Engine

Smart order routing with venue selection and rate limiting.
"""

from typing import Dict
import time

from pkg.common import get_logger, get_metrics_collector, get_timestamp_ns, calculate_latency_us
from pkg.schemas import OrderIntent


class RoutingEngine:
    """
    Smart order routing engine.
    
    Routes orders to best execution venue based on:
    - Symbol availability
    - Venue liquidity
    - Fee structure
    - Rate limiting
    """
    
    def __init__(self, config, publisher):
        self.config = config
        self.publisher = publisher
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("router")
        
        # Venue routing table (simplified)
        self.venue_map = {
            1: "binance",  # BTC/USDT
            2: "binance",  # ETH/USDT
            3: "binance",  # SOL/USDT
            4: "binance",  # BNB/USDT
            5: "binance",  # XRP/USDT
        }
        
        # Rate limiting per venue
        self.venue_rate_limits: Dict[str, int] = {}
        self.venue_last_order_ns: Dict[str, int] = {}
        
        # Min delay between orders (ms)
        self.min_delay_ms = 100
        if hasattr(config, 'risk'):
            self.min_delay_ms = getattr(config.risk, 'cooldown_ms', 100)
        
        self.running = False
        
    async def start(self):
        """Start the routing engine"""
        self.logger.info("routing_engine_started", min_delay_ms=self.min_delay_ms)
        self.running = True
        
    async def stop(self):
        """Stop the routing engine"""
        self.running = False
        self.logger.info("routing_engine_stopped")
    
    async def route_order(self, order: OrderIntent):
        """
        Route order to appropriate venue.
        
        Args:
            order: OrderIntent to route
        """
        try:
            start_ts = get_timestamp_ns()
            
            # Select venue
            venue = self._select_venue(order)
            
            if not venue:
                self.logger.warning("no_venue_available",
                                  client_id=order.client_id,
                                  symbol_id=order.symbol_id)
                self.metrics.record_error("no_venue")
                return
            
            # Check rate limiting
            if not self._check_venue_rate_limit(venue):
                self.logger.warning("venue_rate_limited",
                                  client_id=order.client_id,
                                  venue=venue)
                self.metrics.record_error("venue_rate_limited")
                return
            
            # Update order route
            order.route = venue
            
            # Publish to execution gateway
            await self.publisher.publish(order, venue)
            
            # Update rate limit tracking
            self.venue_last_order_ns[venue] = get_timestamp_ns()
            
            self.logger.info("order_routed",
                           client_id=order.client_id,
                           symbol_id=order.symbol_id,
                           venue=venue)
            
            # Record latency
            end_ts = get_timestamp_ns()
            route_latency_us = calculate_latency_us(start_ts, end_ts)
            total_latency_us = calculate_latency_us(order.ts_ns, end_ts)
            
            self.metrics.record_latency("route", route_latency_us)
            self.metrics.record_latency("order_to_route", total_latency_us)
            
        except Exception as e:
            self.logger.error("route_order_error",
                            client_id=order.client_id,
                            error=str(e),
                            exc_info=True)
            self.metrics.record_error("route_order_failed")
    
    def _select_venue(self, order: OrderIntent) -> str:
        """
        Select best venue for order.
        
        Args:
            order: OrderIntent to route
        
        Returns:
            Venue name or None
        """
        # Use order route hint if provided
        if order.route and order.route != "auto":
            return order.route
        
        # Use venue map
        venue = self.venue_map.get(order.symbol_id)
        
        if not venue:
            # Default to first configured exchange
            if self.config.exchanges:
                venue = list(self.config.exchanges.keys())[0]
        
        return venue
    
    def _check_venue_rate_limit(self, venue: str) -> bool:
        """
        Check if venue rate limit allows this order.
        
        Args:
            venue: Venue name
        
        Returns:
            True if allowed, False if rate limited
        """
        now_ns = time.time_ns()
        min_delay_ns = self.min_delay_ms * 1_000_000
        
        if venue not in self.venue_last_order_ns:
            return True
        
        last_order_ns = self.venue_last_order_ns[venue]
        elapsed_ns = now_ns - last_order_ns
        
        return elapsed_ns >= min_delay_ns
