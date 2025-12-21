"""
SIGMAX Python SDK - Official Python client for SIGMAX API.

A production-ready async-first SDK for interacting with the SIGMAX
autonomous AI crypto trading system.
"""

from __future__ import annotations

from .client import SigmaxClient
from .exceptions import (
    SigmaxAPIError,
    SigmaxAuthenticationError,
    SigmaxConnectionError,
    SigmaxError,
    SigmaxRateLimitError,
    SigmaxTimeoutError,
    SigmaxValidationError,
)
from .models import (
    AnalysisResult,
    ChatMessage,
    ProposalStatus,
    RiskProfile,
    SystemStatus,
    TradeMode,
    TradeProposal,
)
from .types import StreamEvent

__version__ = "1.0.0"
__author__ = "SIGMAX Contributors"
__license__ = "MIT"

__all__ = [
    # Client
    "SigmaxClient",
    # Models
    "AnalysisResult",
    "ChatMessage",
    "ProposalStatus",
    "RiskProfile",
    "SystemStatus",
    "TradeMode",
    "TradeProposal",
    # Types
    "StreamEvent",
    # Exceptions
    "SigmaxAPIError",
    "SigmaxAuthenticationError",
    "SigmaxConnectionError",
    "SigmaxError",
    "SigmaxRateLimitError",
    "SigmaxTimeoutError",
    "SigmaxValidationError",
]
