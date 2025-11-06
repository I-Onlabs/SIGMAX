"""
Feature frame schema for the features extraction engine.
"""

from dataclasses import dataclass
import time


@dataclass
class FeatureFrame:
    """
    Feature vector computed from market data.
    Stream 12 in the IPC topology.
    
    Features are computed over micro-windows (200-500ms) and include:
    - Microprice, spread, imbalance
    - Realized volatility
    - Regime flags from signal fusion
    """
    ts_ns: int
    symbol_id: int
    
    # Price features
    mid_price: float
    micro_price: float
    spread: float
    spread_bps: float  # Spread in basis points
    
    # Volume features
    bid_volume: float
    ask_volume: float
    imbalance: float  # -1 to 1
    
    # Volatility features
    realized_vol: float  # Short-term RV
    price_range: float  # High - Low over window
    
    # Momentum features
    price_change: float
    price_change_pct: float
    
    # Regime flags (set by signal fusion)
    regime_bits: int = 0  # Bitfield for regime flags
    
    # Regime flag masks
    HIGH_VOL = 1 << 0
    LISTING_WINDOW = 1 << 1
    NEWS_POSITIVE = 1 << 2
    NEWS_NEGATIVE = 1 << 3
    SOCIAL_HYPE = 1 << 4
    
    def has_regime(self, flag: int) -> bool:
        """Check if regime flag is set"""
        return bool(self.regime_bits & flag)
    
    def set_regime(self, flag: int):
        """Set regime flag"""
        self.regime_bits |= flag
    
    def clear_regime(self, flag: int):
        """Clear regime flag"""
        self.regime_bits &= ~flag
    
    @classmethod
    def create_empty(cls, symbol_id: int) -> 'FeatureFrame':
        """Create empty feature frame"""
        return cls(
            ts_ns=time.time_ns(),
            symbol_id=symbol_id,
            mid_price=0.0,
            micro_price=0.0,
            spread=0.0,
            spread_bps=0.0,
            bid_volume=0.0,
            ask_volume=0.0,
            imbalance=0.0,
            realized_vol=0.0,
            price_range=0.0,
            price_change=0.0,
            price_change_pct=0.0,
            regime_bits=0
        )
