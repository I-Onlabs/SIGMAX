"""
SIGMAX Schema Definitions

This package contains all message schemas and data models for the trading system.
Messages are designed for SBE encoding but initially implemented in Python for Profile A.
"""

from .market_data import MdUpdate, TopOfBook, BookDelta
from .orders import OrderIntent, OrderAck, Fill, Reject, Cancel, Amend
from .features import FeatureFrame
from .signals import SignalEvent
from .common import Side, OrderType, TimeInForce, OrderStatus

__all__ = [
    # Market data
    "MdUpdate",
    "TopOfBook",
    "BookDelta",
    
    # Orders
    "OrderIntent",
    "OrderAck",
    "Fill",
    "Reject",
    "Cancel",
    "Amend",
    
    # Features & Signals
    "FeatureFrame",
    "SignalEvent",
    
    # Enums
    "Side",
    "OrderType",
    "TimeInForce",
    "OrderStatus",
]
