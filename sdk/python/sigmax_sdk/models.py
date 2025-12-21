"""
SIGMAX SDK Data Models.

Pydantic models for request/response validation and serialization.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class RiskProfile(str, Enum):
    """Risk profile for trading strategies."""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class TradeMode(str, Enum):
    """Trading mode."""

    PAPER = "paper"
    LIVE = "live"


class ProposalStatus(str, Enum):
    """Trade proposal status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


class ChatMessage(BaseModel):
    """Chat message for analysis requests."""

    message: str = Field(..., description="Natural language request")
    symbol: Optional[str] = Field(None, description="Trading pair symbol (e.g., BTC/USDT)")
    risk_profile: RiskProfile = Field(
        default=RiskProfile.CONSERVATIVE,
        description="Risk profile for analysis",
    )
    mode: TradeMode = Field(
        default=TradeMode.PAPER,
        description="Trading mode",
    )

    class Config:
        use_enum_values = True


class MarketData(BaseModel):
    """Market data snapshot."""

    symbol: str
    price: Decimal
    volume_24h: Optional[Decimal] = None
    change_24h: Optional[Decimal] = None
    high_24h: Optional[Decimal] = None
    low_24h: Optional[Decimal] = None
    timestamp: datetime

    @field_validator("price", "volume_24h", "change_24h", "high_24h", "low_24h", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: Any) -> Optional[Decimal]:
        """Convert numeric values to Decimal."""
        if v is None:
            return None
        return Decimal(str(v))


class AnalysisResult(BaseModel):
    """Market analysis result."""

    symbol: str
    recommendation: str = Field(..., description="Trading recommendation (buy/sell/hold)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    analysis: str = Field(..., description="Detailed analysis text")
    risk_level: str = Field(..., description="Assessed risk level")
    market_data: Optional[MarketData] = None
    indicators: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }


class TradeProposal(BaseModel):
    """Trade proposal details."""

    proposal_id: str = Field(..., description="Unique proposal identifier")
    symbol: str = Field(..., description="Trading pair")
    side: str = Field(..., description="Trade side (buy/sell)")
    size: Decimal = Field(..., description="Trade size")
    price: Optional[Decimal] = Field(None, description="Entry price")
    stop_loss: Optional[Decimal] = Field(None, description="Stop loss price")
    take_profit: Optional[Decimal] = Field(None, description="Take profit price")
    status: ProposalStatus = Field(default=ProposalStatus.PENDING)
    risk_profile: RiskProfile
    mode: TradeMode
    rationale: str = Field(..., description="Trading rationale")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("size", "price", "stop_loss", "take_profit", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: Any) -> Optional[Decimal]:
        """Convert numeric values to Decimal."""
        if v is None:
            return None
        return Decimal(str(v))

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }


class SystemStatus(BaseModel):
    """SIGMAX system status."""

    status: str = Field(..., description="System status (online/offline/degraded)")
    version: str = Field(..., description="System version")
    uptime_seconds: float = Field(..., ge=0, description="Uptime in seconds")
    active_trades: int = Field(default=0, ge=0, description="Number of active trades")
    pending_proposals: int = Field(default=0, ge=0, description="Number of pending proposals")
    mode: TradeMode = Field(..., description="Current trading mode")
    api_health: bool = Field(..., description="API health status")
    database_health: bool = Field(..., description="Database health status")
    exchange_health: bool = Field(..., description="Exchange connectivity status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ProposalCreateRequest(BaseModel):
    """Request to create a trade proposal."""

    symbol: str
    risk_profile: RiskProfile = RiskProfile.CONSERVATIVE
    mode: TradeMode = TradeMode.PAPER
    size: Optional[Decimal] = None

    @field_validator("size", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: Any) -> Optional[Decimal]:
        """Convert size to Decimal."""
        if v is None:
            return None
        return Decimal(str(v))

    class Config:
        use_enum_values = True


class ProposalResponse(BaseModel):
    """Response from proposal operations."""

    success: bool
    proposal_id: str
    message: str
    proposal: Optional[TradeProposal] = None
