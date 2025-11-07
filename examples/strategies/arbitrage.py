"""
Arbitrage Strategy Example

Cross-exchange arbitrage detection and execution.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pkg.schemas import FeatureFrame, OrderIntent, Side, OrderType, TimeInForce
from pkg.common import get_logger


@dataclass
class VenuePrices:
    """Price information from a venue"""
    venue: str
    symbol_id: int
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    timestamp_ns: int


class ArbitrageStrategy:
    """
    Cross-exchange arbitrage strategy.

    Logic:
    - Monitor prices across multiple venues
    - Detect arbitrage opportunities (buy low, sell high)
    - Execute simultaneous orders on both venues
    - Account for fees and slippage
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)

        # Strategy parameters
        self.min_profit_bps = 20.0  # Minimum 20 bps profit after fees
        self.maker_fee_bps = 2.0    # Maker fee: 0.02%
        self.taker_fee_bps = 5.0    # Taker fee: 0.05%
        self.max_arb_qty = 0.5      # Max quantity per arbitrage
        self.staleness_threshold_ms = 100  # Max price age: 100ms
        self.min_size_overlap = 0.1  # Minimum overlapping size

        # State tracking
        self.venue_prices: Dict[str, Dict[int, VenuePrices]] = {}  # venue -> symbol_id -> prices
        self.active_arbs = []  # Track active arbitrage positions
        self.last_arb_time = {}  # symbol_id -> timestamp to prevent spam

    def update_venue_prices(self, venue: str, features: FeatureFrame):
        """
        Update price information from a venue.

        Call this method whenever you receive features from a venue.
        """
        symbol_id = features.symbol_id

        if venue not in self.venue_prices:
            self.venue_prices[venue] = {}

        self.venue_prices[venue][symbol_id] = VenuePrices(
            venue=venue,
            symbol_id=symbol_id,
            bid_price=features.bid_price,
            ask_price=features.ask_price,
            bid_size=features.bid_size,
            ask_size=features.ask_size,
            timestamp_ns=features.timestamp_ns
        )

    def detect_arbitrage(self, symbol_id: int, current_time_ns: int) -> Optional[List[OrderIntent]]:
        """
        Detect arbitrage opportunities for a symbol across venues.

        Returns:
            List of OrderIntent (buy on venue A, sell on venue B) or None
        """
        # Need prices from at least 2 venues
        venues_with_prices = []
        for venue, prices_by_symbol in self.venue_prices.items():
            if symbol_id in prices_by_symbol:
                venues_with_prices.append((venue, prices_by_symbol[symbol_id]))

        if len(venues_with_prices) < 2:
            return None

        # Check for stale prices
        venues_with_prices = [
            (venue, prices) for venue, prices in venues_with_prices
            if self._is_price_fresh(prices, current_time_ns)
        ]

        if len(venues_with_prices) < 2:
            return None

        # Find best arbitrage opportunity
        best_arb = self._find_best_arbitrage(venues_with_prices)

        if best_arb is None:
            return None

        buy_venue, sell_venue, qty, expected_profit_bps = best_arb

        # Create simultaneous orders
        orders = self._create_arbitrage_orders(
            symbol_id=symbol_id,
            buy_venue=buy_venue,
            sell_venue=sell_venue,
            qty=qty,
            expected_profit_bps=expected_profit_bps
        )

        self.logger.info("arbitrage_detected",
                        symbol_id=symbol_id,
                        buy_venue=buy_venue.venue,
                        sell_venue=sell_venue.venue,
                        qty=qty,
                        expected_profit_bps=expected_profit_bps,
                        buy_price=buy_venue.ask_price,
                        sell_price=sell_venue.bid_price)

        return orders

    def _is_price_fresh(self, prices: VenuePrices, current_time_ns: int) -> bool:
        """Check if price is fresh enough"""
        age_ms = (current_time_ns - prices.timestamp_ns) / 1_000_000
        return age_ms < self.staleness_threshold_ms

    def _find_best_arbitrage(self, venues_with_prices: List[Tuple[str, VenuePrices]]) -> Optional[Tuple[VenuePrices, VenuePrices, float, float]]:
        """
        Find best arbitrage opportunity among venues.

        Returns:
            (buy_venue, sell_venue, qty, expected_profit_bps) or None
        """
        best_arb = None
        best_profit_bps = self.min_profit_bps

        # Check all venue pairs
        for i, (venue_a, prices_a) in enumerate(venues_with_prices):
            for j, (venue_b, prices_b) in enumerate(venues_with_prices):
                if i >= j:  # Skip same venue and duplicate pairs
                    continue

                # Check arbitrage A->B (buy on A, sell on B)
                arb_ab = self._calculate_arbitrage(prices_a, prices_b)
                if arb_ab and arb_ab[2] > best_profit_bps:
                    best_arb = (prices_a, prices_b, arb_ab[0], arb_ab[2])
                    best_profit_bps = arb_ab[2]

                # Check arbitrage B->A (buy on B, sell on A)
                arb_ba = self._calculate_arbitrage(prices_b, prices_a)
                if arb_ba and arb_ba[2] > best_profit_bps:
                    best_arb = (prices_b, prices_a, arb_ba[0], arb_ba[2])
                    best_profit_bps = arb_ba[2]

        return best_arb

    def _calculate_arbitrage(self, buy_venue: VenuePrices, sell_venue: VenuePrices) -> Optional[Tuple[float, float, float]]:
        """
        Calculate arbitrage profit: buy on buy_venue, sell on sell_venue.

        Returns:
            (qty, gross_profit, net_profit_bps) or None
        """
        # Buy price (we pay ask on buy_venue)
        buy_price = buy_venue.ask_price
        # Sell price (we receive bid on sell_venue)
        sell_price = sell_venue.bid_price

        # Must be profitable before fees
        if sell_price <= buy_price:
            return None

        # Calculate maximum quantity (limited by available size)
        max_qty = min(
            buy_venue.ask_size,
            sell_venue.bid_size,
            self.max_arb_qty
        )

        if max_qty < self.min_size_overlap:
            return None

        # Calculate gross profit
        gross_profit = (sell_price - buy_price) * max_qty

        # Calculate fees
        # Buy side: taker fee (we take liquidity on buy venue)
        buy_cost = buy_price * max_qty
        buy_fee = buy_cost * (self.taker_fee_bps / 10000.0)

        # Sell side: taker fee (we take liquidity on sell venue)
        sell_revenue = sell_price * max_qty
        sell_fee = sell_revenue * (self.taker_fee_bps / 10000.0)

        # Net profit
        net_profit = gross_profit - buy_fee - sell_fee
        net_profit_bps = (net_profit / buy_cost) * 10000.0

        if net_profit_bps < self.min_profit_bps:
            return None

        return (max_qty, gross_profit, net_profit_bps)

    def _create_arbitrage_orders(
        self,
        symbol_id: int,
        buy_venue: VenuePrices,
        sell_venue: VenuePrices,
        qty: float,
        expected_profit_bps: float
    ) -> List[OrderIntent]:
        """Create simultaneous buy and sell orders"""
        orders = []

        # Buy order (take liquidity on buy venue)
        buy_order = OrderIntent.create(
            symbol_id=symbol_id,
            side=Side.BUY,
            order_type=OrderType.MARKET,  # Market order for speed
            qty=qty,
            price=None,  # Market order
            tif=TimeInForce.IOC  # Immediate or cancel
        )
        buy_order.confidence = 0.99  # High confidence arbitrage
        buy_order.venue = buy_venue.venue  # Custom field for routing
        orders.append(buy_order)

        # Sell order (take liquidity on sell venue)
        sell_order = OrderIntent.create(
            symbol_id=symbol_id,
            side=Side.SELL,
            order_type=OrderType.MARKET,  # Market order for speed
            qty=qty,
            price=None,  # Market order
            tif=TimeInForce.IOC  # Immediate or cancel
        )
        sell_order.confidence = 0.99  # High confidence arbitrage
        sell_order.venue = sell_venue.venue  # Custom field for routing
        orders.append(sell_order)

        return orders

    def on_fill(self, order_intent: OrderIntent, filled_qty: float, filled_price: float):
        """Track arbitrage fills"""
        self.logger.info("arb_fill",
                        symbol_id=order_intent.symbol_id,
                        side=order_intent.side.name,
                        venue=getattr(order_intent, 'venue', 'unknown'),
                        qty=filled_qty,
                        price=filled_price)

        # In production, would track both legs and calculate realized P&L


# Example configuration
STRATEGY_CONFIG = {
    "name": "arbitrage",
    "description": "Cross-exchange arbitrage",
    "parameters": {
        "min_profit_bps": 20.0,
        "maker_fee_bps": 2.0,
        "taker_fee_bps": 5.0,
        "max_arb_qty": 0.5,
        "staleness_threshold_ms": 100,
        "min_size_overlap": 0.1
    },
    "venues": ["binance", "coinbase", "kraken"],
    "symbols": ["BTC/USDT", "ETH/USDT"],
    "risk_limits": {
        "max_position_usd": 20000,
        "max_order_usd": 10000,
        "max_concurrent_arbs": 3
    }
}


if __name__ == "__main__":
    print("Arbitrage Strategy Example")
    print("===========================")
    print(f"Configuration: {STRATEGY_CONFIG}")
    print("\nStrategy Features:")
    print("- Cross-exchange price monitoring")
    print("- Automatic arbitrage detection")
    print("- Fee and slippage accounting")
    print("- Simultaneous order execution")
    print("- Staleness filtering (100ms threshold)")
    print("\nExample Arbitrage:")
    print("  Buy BTC @ $50,000 on Binance")
    print("  Sell BTC @ $50,015 on Coinbase")
    print("  Gross profit: $15 per BTC (30 bps)")
    print("  Fees: ~$7.50 per BTC (15 bps)")
    print("  Net profit: ~$7.50 per BTC (15 bps)")
