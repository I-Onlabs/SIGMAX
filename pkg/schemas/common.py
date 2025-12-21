"""
Common types and enums used across the trading system.
"""

from enum import IntEnum
from dataclasses import dataclass


class Side(IntEnum):
    """Order side"""
    BUY = 1
    SELL = 2


class OrderType(IntEnum):
    """Order type"""
    MARKET = 1
    LIMIT = 2
    STOP_LOSS = 3
    STOP_LOSS_LIMIT = 4
    TAKE_PROFIT = 5
    TAKE_PROFIT_LIMIT = 6


class TimeInForce(IntEnum):
    """Time in force"""
    GTC = 1  # Good Till Cancel
    IOC = 2  # Immediate or Cancel
    FOK = 3  # Fill or Kill
    GTX = 4  # Good Till Crossing (Post Only)


class OrderStatus(IntEnum):
    """Order status"""
    PENDING = 1
    SUBMITTED = 2
    PARTIAL = 3
    FILLED = 4
    CANCELLED = 5
    REJECTED = 6
    EXPIRED = 7


class SignalType(IntEnum):
    """Signal types for pluggable signals"""
    VOL = 1       # Volatility
    NEWS = 2      # News sentiment
    LISTING = 3   # New listing
    REDDIT = 4    # Social sentiment
    CUSTOM = 99   # Custom signal


class VenueCode(IntEnum):
    """Exchange venue codes"""
    BINANCE = 1
    COINBASE = 2
    KRAKEN = 3
    BYBIT = 4
    OKX = 5
    BINANCE_US = 6
    GEMINI = 7
    BITSTAMP = 8


@dataclass
class Symbol:
    """Trading symbol representation"""
    symbol_id: int
    exchange: str
    base: str
    quote: str
    
    @property
    def pair(self) -> str:
        return f"{self.base}/{self.quote}"
    
    def __str__(self) -> str:
        return f"{self.exchange}:{self.pair}"


@dataclass
class PriceSize:
    """Price and size level"""
    price: float
    size: float
    
    def __repr__(self) -> str:
        return f"PriceSize(price={self.price:.8f}, size={self.size:.8f})"
