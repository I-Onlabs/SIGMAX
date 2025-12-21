"""
Market Making Strategy Example

A dual-sided market making strategy with inventory management.
"""

import sys
from pathlib import Path
from typing import List

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pkg.schemas import FeatureFrame, OrderIntent, Side, OrderType, TimeInForce
from pkg.common import get_logger


class MarketMakingStrategy:
    """
    Market making strategy with dual-sided quoting.

    Logic:
    - Quote both bid and ask sides simultaneously
    - Adjust spread based on volatility and inventory
    - Widen spread when inventory skewed
    - Cancel and requote on market moves
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)

        # Strategy parameters
        self.base_spread_bps = 10.0  # Base spread: 10 bps
        self.min_spread_bps = 5.0    # Minimum spread
        self.max_spread_bps = 50.0   # Maximum spread
        self.quote_size = 0.1        # Quote size per side
        self.max_inventory = 2.0     # Max inventory deviation from neutral
        self.inventory_skew_factor = 2.0  # Spread adjustment per unit inventory

        # State tracking
        self.inventory = {}  # symbol_id -> net position
        self.active_quotes = {}  # symbol_id -> {'bid': OrderIntent, 'ask': OrderIntent}
        self.last_mid_price = {}  # symbol_id -> last mid price

    def generate_signals(self, features: FeatureFrame) -> List[OrderIntent]:
        """
        Generate dual-sided market making quotes.

        Returns:
            List of OrderIntent (both bid and ask)
        """
        symbol_id = features.symbol_id

        # Initialize tracking
        if symbol_id not in self.inventory:
            self.inventory[symbol_id] = 0.0
            self.last_mid_price[symbol_id] = features.mid_price

        # Check if we should requote
        if not self._should_requote(features):
            return []

        # Calculate inventory skew
        current_inventory = self.inventory[symbol_id]
        inventory_pct = current_inventory / self.max_inventory if self.max_inventory > 0 else 0.0

        # Adjust spread based on volatility
        vol_multiplier = 1.0 + (features.realized_vol / 0.01)  # Scale by 1% vol
        target_spread_bps = self.base_spread_bps * vol_multiplier
        target_spread_bps = max(self.min_spread_bps, min(self.max_spread_bps, target_spread_bps))

        # Inventory skew: widen spread on heavy side, tighten on light side
        bid_spread_bps = target_spread_bps * (1.0 + inventory_pct * self.inventory_skew_factor)
        ask_spread_bps = target_spread_bps * (1.0 - inventory_pct * self.inventory_skew_factor)

        # Ensure minimum spreads
        bid_spread_bps = max(self.min_spread_bps, bid_spread_bps)
        ask_spread_bps = max(self.min_spread_bps, ask_spread_bps)

        # Calculate quote prices
        mid_price = features.mid_price
        bid_price = mid_price * (1.0 - bid_spread_bps / 20000.0)  # Divide by 2 for half-spread
        ask_price = mid_price * (1.0 + ask_spread_bps / 20000.0)

        orders = []

        # Create bid quote (only if inventory not too long)
        if current_inventory < self.max_inventory:
            bid_order = self._create_quote(
                features,
                side=Side.BUY,
                price=bid_price,
                spread_bps=bid_spread_bps
            )
            orders.append(bid_order)

        # Create ask quote (only if inventory not too short)
        if current_inventory > -self.max_inventory:
            ask_order = self._create_quote(
                features,
                side=Side.SELL,
                price=ask_price,
                spread_bps=ask_spread_bps
            )
            orders.append(ask_order)

        # Update state
        self.last_mid_price[symbol_id] = mid_price
        self.active_quotes[symbol_id] = {
            'bid': orders[0] if orders and orders[0].side == Side.BUY else None,
            'ask': orders[-1] if orders and orders[-1].side == Side.SELL else None
        }

        self.logger.info("market_making_quotes",
                        symbol_id=symbol_id,
                        bid_price=bid_price if current_inventory < self.max_inventory else None,
                        ask_price=ask_price if current_inventory > -self.max_inventory else None,
                        bid_spread_bps=bid_spread_bps,
                        ask_spread_bps=ask_spread_bps,
                        inventory=current_inventory,
                        vol_multiplier=vol_multiplier)

        return orders

    def _should_requote(self, features: FeatureFrame) -> bool:
        """Determine if we should cancel and requote"""
        symbol_id = features.symbol_id

        # Always quote if no active quotes
        if symbol_id not in self.active_quotes:
            return True

        # Check if market has moved significantly
        last_mid = self.last_mid_price.get(symbol_id)
        if last_mid is None:
            return True

        price_move_pct = abs(features.mid_price - last_mid) / last_mid

        # Requote if price moved more than 5 bps
        if price_move_pct > 0.0005:
            self.logger.debug("requote_on_price_move",
                            symbol_id=symbol_id,
                            price_move_pct=price_move_pct * 100)
            return True

        # Requote if volatility changed significantly
        # (In production, would track last vol and compare)

        return False

    def _create_quote(self, features: FeatureFrame, side: Side, price: float, spread_bps: float) -> OrderIntent:
        """Create a market making quote"""
        order = OrderIntent.create(
            symbol_id=features.symbol_id,
            side=side,
            order_type=OrderType.LIMIT,
            qty=self.quote_size,
            price=price,
            tif=TimeInForce.GTX  # Post-only to ensure maker rebates
        )

        # High confidence - we're providing liquidity
        order.confidence = 0.95

        return order

    def on_fill(self, symbol_id: int, side: Side, qty: float):
        """Update inventory on fill"""
        if symbol_id not in self.inventory:
            self.inventory[symbol_id] = 0.0

        if side == Side.BUY:
            self.inventory[symbol_id] += qty
        else:
            self.inventory[symbol_id] -= qty

        self.logger.info("inventory_updated",
                        symbol_id=symbol_id,
                        side=side.name,
                        qty=qty,
                        new_inventory=self.inventory[symbol_id])

    def on_cancel(self, symbol_id: int, side: Side):
        """Handle quote cancellation"""
        if symbol_id in self.active_quotes:
            side_key = 'bid' if side == Side.BUY else 'ask'
            self.active_quotes[symbol_id][side_key] = None


# Example configuration
STRATEGY_CONFIG = {
    "name": "market_making",
    "description": "Dual-sided market making with inventory management",
    "parameters": {
        "base_spread_bps": 10.0,
        "min_spread_bps": 5.0,
        "max_spread_bps": 50.0,
        "quote_size": 0.1,
        "max_inventory": 2.0,
        "inventory_skew_factor": 2.0
    },
    "symbols": ["BTC/USDT", "ETH/USDT"],
    "timeframe": "1s",  # High frequency requoting
    "risk_limits": {
        "max_position_usd": 100000,  # Higher for market making
        "max_order_usd": 5000,
        "max_inventory_deviation": 2.0
    }
}


if __name__ == "__main__":
    print("Market Making Strategy Example")
    print("==============================")
    print(f"Configuration: {STRATEGY_CONFIG}")
    print("\nStrategy Features:")
    print("- Dual-sided quoting (bid and ask)")
    print("- Inventory-based spread skewing")
    print("- Volatility-adjusted spreads")
    print("- Post-only orders for maker rebates")
    print("- Automatic requoting on market moves")
