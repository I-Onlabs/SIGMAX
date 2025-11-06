"""
Signal event schema for pluggable signal modules.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import time

from .common import SignalType


@dataclass
class SignalEvent:
    """
    Signal event from pluggable signal modules.
    Stream 13 in the IPC topology.
    
    Signals can be:
    - VOL: Volatility scanner (RV, turnover)
    - NEWS: News sentiment
    - LISTING: New listing alerts
    - REDDIT: Social sentiment
    - CUSTOM: User-defined signals
    """
    ts_ns: int
    symbol_id: int
    sig_type: SignalType
    value: float  # Signal value (interpretation depends on type)
    meta_code: int = 0  # Additional metadata
    confidence: float = 0.0  # Confidence score 0-1
    
    # Optional metadata (not in SBE, for logging)
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(cls, symbol_id: int, sig_type: SignalType, 
               value: float, confidence: float = 0.0,
               meta_code: int = 0, metadata: Optional[Dict[str, Any]] = None) -> 'SignalEvent':
        """Create new signal event"""
        return cls(
            ts_ns=time.time_ns(),
            symbol_id=symbol_id,
            sig_type=sig_type,
            value=value,
            meta_code=meta_code,
            confidence=confidence,
            metadata=metadata or {}
        )
    
    def __repr__(self) -> str:
        return (f"SignalEvent(symbol_id={self.symbol_id}, "
                f"type={SignalType(self.sig_type).name}, "
                f"value={self.value:.4f}, confidence={self.confidence:.2f})")


# Signal metadata codes for different signal types
class VolatilityMetaCode:
    """Metadata codes for volatility signals"""
    RV_SPIKE = 1
    TURNOVER_SPIKE = 2
    CORRELATION_BREAK = 3


class NewsMetaCode:
    """Metadata codes for news signals"""
    POSITIVE = 1
    NEGATIVE = 2
    NEUTRAL = 3
    EXCHANGE_ANNOUNCEMENT = 4
    REGULATORY = 5


class ListingMetaCode:
    """Metadata codes for listing signals"""
    NEW_LISTING = 1
    DELISTING = 2
    TRADING_HALT = 3


class SocialMetaCode:
    """Metadata codes for social signals"""
    REDDIT_HYPE = 1
    TWITTER_TREND = 2
    DISCORD_ACTIVITY = 3
