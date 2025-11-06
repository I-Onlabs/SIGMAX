"""
Mean Reversion Strategy Example

A simple mean reversion strategy that trades on orderbook imbalance.
This demonstrates how to create custom decision logic.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pkg.schemas import FeatureFrame, OrderIntent, Side, OrderType, TimeInForce
from pkg.common import get_logger


class MeanReversionStrategy:
    """
    Mean reversion strategy based on orderbook imbalance.
    
    Logic:
    - When bid volume >> ask volume, price likely to fall → SELL
    - When ask volume >> bid volume, price likely to rise → BUY
    - Only trade when imbalance > threshold
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Strategy parameters
        self.imbalance_threshold = 0.4  # 40% imbalance
        self.min_spread_bps = 5.0  # Minimum 5 bps spread
        self.max_position_qty = 1.0  # Max 1 BTC position
        self.order_size_pct = 0.1  # 10% of max position per trade
        
        # State
        self.positions = {}  # symbol_id -> qty
    
    def generate_signal(self, features: FeatureFrame) -> OrderIntent:
        """
        Generate trading signal from features.
        
        Args:
            features: FeatureFrame with market data
            
        Returns:
            OrderIntent or None
        """
        try:
            # Check minimum spread
            if features.spread_bps < self.min_spread_bps:
                return None
            
            # Get current position
            position = self.positions.get(features.symbol_id, 0.0)
            
            # Calculate signal based on imbalance
            if features.imbalance > self.imbalance_threshold:
                # Strong bid pressure - expect price to drop - SELL
                if position > -self.max_position_qty:
                    return self._create_order(
                        features,
                        side=Side.SELL,
                        reason="high_bid_imbalance"
                    )
            
            elif features.imbalance < -self.imbalance_threshold:
                # Strong ask pressure - expect price to rise - BUY
                if position < self.max_position_qty:
                    return self._create_order(
                        features,
                        side=Side.BUY,
                        reason="high_ask_imbalance"
                    )
            
            return None
            
        except Exception as e:
            self.logger.error("signal_error", error=str(e))
            return None
    
    def _create_order(self, features: FeatureFrame, side: Side, reason: str) -> OrderIntent:
        """Create order intent"""
        qty = self.max_position_qty * self.order_size_pct
        
        # Use microprice for better execution
        price = features.micro_price
        
        # Adjust price to be more aggressive
        if side == Side.BUY:
            price *= 1.0001  # Pay slightly more
        else:
            price *= 0.9999  # Sell slightly lower
        
        order = OrderIntent.create(
            symbol_id=features.symbol_id,
            side=side,
            order_type=OrderType.LIMIT,
            qty=qty,
            price=price,
            tif=TimeInForce.GTX  # Post-only
        )
        
        # Add metadata
        order.confidence = min(abs(features.imbalance), 1.0)
        
        self.logger.info("signal_generated",
                        symbol_id=features.symbol_id,
                        side=side.name,
                        qty=qty,
                        price=price,
                        imbalance=features.imbalance,
                        reason=reason)
        
        return order
    
    def on_fill(self, symbol_id: int, side: Side, qty: float):
        """Update position on fill"""
        if symbol_id not in self.positions:
            self.positions[symbol_id] = 0.0
        
        if side == Side.BUY:
            self.positions[symbol_id] += qty
        else:
            self.positions[symbol_id] -= qty
        
        self.logger.info("position_updated",
                        symbol_id=symbol_id,
                        position=self.positions[symbol_id])


# Example configuration
STRATEGY_CONFIG = {
    "name": "mean_reversion",
    "description": "Orderbook imbalance mean reversion",
    "parameters": {
        "imbalance_threshold": 0.4,
        "min_spread_bps": 5.0,
        "max_position_qty": 1.0,
        "order_size_pct": 0.1
    },
    "symbols": ["BTC/USDT", "ETH/USDT"],
    "risk_limits": {
        "max_position_usd": 50000,
        "max_order_usd": 5000,
        "max_drawdown_pct": 10.0
    }
}


if __name__ == "__main__":
    print("Mean Reversion Strategy Example")
    print("================================")
    print(f"Configuration: {STRATEGY_CONFIG}")
