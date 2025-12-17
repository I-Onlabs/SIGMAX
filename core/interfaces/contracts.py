"""
Structured request/response contracts for multi-channel SIGMAX.

Goal: every interface (Telegram, web chat, CLI, etc.) feeds the same structured
request into the orchestrator and receives a response with step artifacts.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Channel(str, Enum):
    telegram = "telegram"
    web = "web"
    api = "api"
    cli = "cli"


class Intent(str, Enum):
    analyze = "analyze"
    propose_trade = "propose_trade"
    approve_trade = "approve_trade"
    execute_trade = "execute_trade"
    status = "status"
    explain = "explain"


class ExecutionPermissions(BaseModel):
    allow_paper: bool = True
    allow_live: bool = False
    require_manual_approval_live: bool = True


class UserPreferences(BaseModel):
    risk_profile: Literal["conservative", "balanced", "aggressive"] = "conservative"
    mode: Literal["paper", "live"] = "paper"
    permissions: ExecutionPermissions = Field(default_factory=ExecutionPermissions)


class StructuredRequest(BaseModel):
    channel: Channel = Channel.api
    intent: Intent = Intent.analyze
    message: Optional[str] = None
    symbol: Optional[str] = None
    proposal_id: Optional[str] = None
    size: Optional[float] = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class Artifact(BaseModel):
    type: str
    title: str
    content: Any
    meta: Dict[str, Any] = Field(default_factory=dict)


class TradeProposal(BaseModel):
    proposal_id: str
    symbol: str
    action: Literal["buy", "sell"]
    size: float
    notional_usd: float
    mode: Literal["paper", "live"]
    requires_manual_approval: bool = True
    approved: bool = False
    created_at: str
    rationale: Optional[str] = None


class ChannelResponse(BaseModel):
    ok: bool = True
    message: str = ""
    intent: Intent
    symbol: Optional[str] = None
    artifacts: List[Artifact] = Field(default_factory=list)
    decision: Optional[Dict[str, Any]] = None
    proposal: Optional[TradeProposal] = None


class StreamEvent(BaseModel):
    type: Literal["step", "artifact", "final", "error"]
    timestamp: str
    step: Optional[str] = None
    data: Any = None

