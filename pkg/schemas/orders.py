"""
Order message schemas.

These messages flow through the decision → risk → router → execution pipeline.
Designed for SBE encoding in Profile B, but using dataclasses for Profile A.
"""

from dataclasses import dataclass
from typing import Optional
import time
import uuid

from .common import Side, OrderType, TimeInForce, OrderStatus


@dataclass
class OrderIntent:
    """
    Order intent from decision layer.
    Stream 20 in the IPC topology.
    """
    ts_ns: int
    client_id: str  # UUID for idempotency
    symbol_id: int
    side: Side
    order_type: OrderType
    qty: float
    price: Optional[float]  # None for market orders
    tif: TimeInForce
    route: str  # Venue routing hint
    
    # Metadata for decision tracking
    decision_layer: int = 0  # Which L0-L5 layer generated this
    confidence: float = 0.0  # Confidence score
    
    @classmethod
    def create(cls, symbol_id: int, side: Side, order_type: OrderType,
               qty: float, price: Optional[float] = None,
               tif: TimeInForce = TimeInForce.GTC,
               route: str = "auto") -> 'OrderIntent':
        """Create new order intent with UUID"""
        return cls(
            ts_ns=time.time_ns(),
            client_id=str(uuid.uuid4()),
            symbol_id=symbol_id,
            side=side,
            order_type=order_type,
            qty=qty,
            price=price,
            tif=tif,
            route=route
        )


@dataclass
class Cancel:
    """
    Cancel order request.
    Stream 20 in the IPC topology.
    """
    ts_ns: int
    client_id: str  # Original order's client_id
    symbol_id: int
    reason: str = ""


@dataclass
class Amend:
    """
    Amend order request.
    Stream 20 in the IPC topology.
    """
    ts_ns: int
    client_id: str  # Original order's client_id
    symbol_id: int
    new_qty: Optional[float] = None
    new_price: Optional[float] = None


@dataclass
class OrderAck:
    """
    Order acknowledgment from exchange.
    Stream 21 in the IPC topology.
    """
    ts_ns: int
    client_id: str
    exchange_order_id: str
    status: OrderStatus
    venue_code: int
    
    # Latency tracking
    submit_ts_ns: Optional[int] = None  # When we submitted
    
    @property
    def latency_us(self) -> Optional[float]:
        """Calculate round-trip latency in microseconds"""
        if self.submit_ts_ns:
            return (self.ts_ns - self.submit_ts_ns) / 1000.0
        return None


@dataclass
class Fill:
    """
    Order fill from exchange.
    Stream 21 in the IPC topology.
    """
    ts_ns: int
    client_id: str
    exchange_order_id: str
    price: float
    qty: float
    fee: float
    fee_currency: str
    venue_code: int
    is_maker: bool = False
    trade_id: str = ""


@dataclass
class Reject:
    """
    Order rejection from exchange or risk engine.
    Stream 21 in the IPC topology.
    """
    ts_ns: int
    client_id: str
    reason_code: int
    reason_msg: str
    source: str  # "risk", "router", "exchange"
    venue_code: int = 0


# Reason codes for rejections
class RejectReason(object):
    """Rejection reason codes"""
    # Risk engine rejections (1xx)
    POSITION_LIMIT = 101
    NOTIONAL_LIMIT = 102
    PRICE_BAND = 103
    RATE_LIMIT = 104
    INVENTORY_LIMIT = 105
    CONCENTRATION_LIMIT = 106
    
    # Router rejections (2xx)
    NO_ROUTE = 201
    VENUE_UNAVAILABLE = 202
    INSUFFICIENT_BALANCE = 203
    
    # Exchange rejections (3xx)
    INVALID_PRICE = 301
    INVALID_QUANTITY = 302
    INSUFFICIENT_FUNDS = 303
    MARKET_CLOSED = 304
    RATE_LIMITED = 305
    
    # System rejections (4xx)
    INTERNAL_ERROR = 401
    TIMEOUT = 402
    INVALID_SYMBOL = 403
