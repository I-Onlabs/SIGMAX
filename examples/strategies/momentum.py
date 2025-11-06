"""
Momentum Strategy Example

A momentum-following strategy that trades on price trends.
"""

import sys
from pathlib import Path
from collections import deque

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pkg.schemas import FeatureFrame, OrderIntent, Side, OrderType, TimeInForce
from pkg.common import get_logger


class MomentumStrategy:
    """
    Momentum strategy following price trends.
    
    Logic:
    - Track price changes over multiple windows
    - When consistent upward momentum → BUY
    - When consistent downward momentum → SELL
    - Exit on momentum reversal
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Strategy parameters
        self.momentum_threshold = 0.3  # 0.3% price change
        self.confirmation_periods = 3  # Need 3 consecutive signals
        self.volatility_threshold = 0.02  # Max 2% volatility
        self.max_position_qty = 1.0
        self.order_size_pct = 0.15
        
        # State tracking
        self.price_history = {}  # symbol_id -> deque of price changes
        self.positions = {}
        self.signals = {}  # symbol_id -> deque of signals
    
    def generate_signal(self, features: FeatureFrame) -> OrderIntent:
        """Generate momentum signal"""
        symbol_id = features.symbol_id
        
        # Initialize tracking
        if symbol_id not in self.price_history:
            self.price_history[symbol_id] = deque(maxlen=self.confirmation_periods)
            self.signals[symbol_id] = deque(maxlen=self.confirmation_periods)
            self.positions[symbol_id] = 0.0
        
        # Check volatility filter
        if features.realized_vol > self.volatility_threshold:
            self.logger.debug("volatility_too_high", vol=features.realized_vol)
            return None
        
        # Record price change
        self.price_history[symbol_id].append(features.price_change_pct)
        
        # Need enough history
        if len(self.price_history[symbol_id]) < self.confirmation_periods:
            return None
        
        # Check for consistent momentum
        recent_changes = list(self.price_history[symbol_id])
        
        # Bullish momentum: all positive and above threshold
        if all(pc > self.momentum_threshold for pc in recent_changes):
            if self.positions[symbol_id] < self.max_position_qty:
                return self._create_order(
                    features,
                    side=Side.BUY,
                    reason="bullish_momentum"
                )
        
        # Bearish momentum: all negative and below threshold
        elif all(pc < -self.momentum_threshold for pc in recent_changes):
            if self.positions[symbol_id] > -self.max_position_qty:
                return self._create_order(
                    features,
                    side=Side.SELL,
                    reason="bearish_momentum"
                )
        
        return None
    
    def _create_order(self, features: FeatureFrame, side: Side, reason: str) -> OrderIntent:
        """Create momentum order"""
        qty = self.max_position_qty * self.order_size_pct
        
        # Momentum strategy - use market price
        price = features.mid_price
        
        # Calculate confidence from momentum strength
        avg_momentum = abs(sum(self.price_history[features.symbol_id]) / self.confirmation_periods)
        confidence = min(avg_momentum / 1.0, 1.0)  # Normalize to 0-1
        
        order = OrderIntent.create(
            symbol_id=features.symbol_id,
            side=side,
            order_type=OrderType.LIMIT,
            qty=qty,
            price=price,
            tif=TimeInForce.GTC
        )
        
        order.confidence = confidence
        
        self.logger.info("momentum_signal",
                        symbol_id=features.symbol_id,
                        side=side.name,
                        qty=qty,
                        avg_momentum=avg_momentum,
                        confidence=confidence,
                        reason=reason)
        
        return order
    
    def on_fill(self, symbol_id: int, side: Side, qty: float):
        """Update position"""
        if side == Side.BUY:
            self.positions[symbol_id] += qty
        else:
            self.positions[symbol_id] -= qty


# Example configuration
STRATEGY_CONFIG = {
    "name": "momentum",
    "description": "Trend-following momentum strategy",
    "parameters": {
        "momentum_threshold": 0.3,
        "confirmation_periods": 3,
        "volatility_threshold": 0.02,
        "max_position_qty": 1.0,
        "order_size_pct": 0.15
    },
    "symbols": ["BTC/USDT", "ETH/USDT"],
    "timeframe": "5m",
    "risk_limits": {
        "max_position_usd": 50000,
        "max_order_usd": 7500,
        "stop_loss_pct": 2.0
    }
}
