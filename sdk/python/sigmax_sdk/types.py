"""
SIGMAX SDK Type Definitions.

Type aliases and protocols for the SDK.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict


class StreamEvent(TypedDict, total=False):
    """Server-sent event structure."""

    type: str
    status: str
    message: str
    data: dict[str, Any]
    error: str
    final: bool


# Type aliases
RiskProfileType = Literal["conservative", "moderate", "aggressive"]
TradeModeType = Literal["paper", "live"]
ProposalStatusType = Literal["pending", "approved", "rejected", "executed", "cancelled"]
EventType = Literal["analysis", "proposal", "execution", "status", "error"]
