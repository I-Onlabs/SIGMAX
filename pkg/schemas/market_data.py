"""
Market data message schemas.

These messages flow through the ingestion → book → features pipeline.
Designed for SBE encoding in Profile B, but using dataclasses for Profile A.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import time


@dataclass
class MdUpdate:
    """
    Market data update from exchange feed.
    Stream 10 in the IPC topology.
    """
    ts_ns: int  # Nanosecond timestamp
    symbol_id: int
    bid_px: float
    bid_sz: float
    ask_px: float
    ask_sz: float
    seq: int  # Sequence number for gap detection
    
    @classmethod
    def now(cls, symbol_id: int, bid_px: float, bid_sz: float, 
            ask_px: float, ask_sz: float, seq: int = 0) -> 'MdUpdate':
        """Create MdUpdate with current timestamp"""
        return cls(
            ts_ns=time.time_ns(),
            symbol_id=symbol_id,
            bid_px=bid_px,
            bid_sz=bid_sz,
            ask_px=ask_px,
            ask_sz=ask_sz,
            seq=seq
        )


@dataclass
class TopOfBook:
    """
    Top of book snapshot.
    Stream 11 in the IPC topology.
    """
    ts_ns: int
    symbol_id: int
    bid_px: float
    bid_sz: float
    ask_px: float
    ask_sz: float
    
    @property
    def spread(self) -> float:
        """Calculate spread"""
        return self.ask_px - self.bid_px
    
    @property
    def mid_price(self) -> float:
        """Calculate mid price"""
        return (self.bid_px + self.ask_px) / 2.0
    
    @property
    def micro_price(self) -> float:
        """Calculate volume-weighted microprice"""
        total_sz = self.bid_sz + self.ask_sz
        if total_sz == 0:
            return self.mid_price
        return (self.bid_px * self.ask_sz + self.ask_px * self.bid_sz) / total_sz


@dataclass
class BookLevel:
    """Single order book level"""
    price: float
    size: float
    num_orders: int = 0


@dataclass
class BookDelta:
    """
    Order book delta update.
    Stream 11 in the IPC topology.
    """
    ts_ns: int
    symbol_id: int
    is_bid: bool
    price: float
    size: float  # 0 = delete level
    
    
@dataclass
class L2Book:
    """
    Full L2 order book representation.
    Maintained in-memory by book_shard service.
    """
    symbol_id: int
    bids: List[BookLevel] = field(default_factory=list)
    asks: List[BookLevel] = field(default_factory=list)
    last_update_ns: int = 0
    sequence: int = 0
    
    def get_top_of_book(self) -> Optional[TopOfBook]:
        """Extract top of book"""
        if not self.bids or not self.asks:
            return None
        
        return TopOfBook(
            ts_ns=self.last_update_ns,
            symbol_id=self.symbol_id,
            bid_px=self.bids[0].price,
            bid_sz=self.bids[0].size,
            ask_px=self.asks[0].price,
            ask_sz=self.asks[0].size
        )
    
    def get_mid_price(self) -> Optional[float]:
        """Get mid price"""
        if not self.bids or not self.asks:
            return None
        return (self.bids[0].price + self.asks[0].price) / 2.0
    
    def get_spread(self) -> Optional[float]:
        """Get spread"""
        if not self.bids or not self.asks:
            return None
        return self.asks[0].price - self.bids[0].price
    
    def get_imbalance(self, depth: int = 5) -> float:
        """
        Calculate order book imbalance.
        Returns value between -1 (all asks) and 1 (all bids).
        """
        bid_volume = sum(level.size for level in self.bids[:depth])
        ask_volume = sum(level.size for level in self.asks[:depth])
        total_volume = bid_volume + ask_volume
        
        if total_volume == 0:
            return 0.0
        
        return (bid_volume - ask_volume) / total_volume
