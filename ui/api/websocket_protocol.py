"""
WebSocket Message Protocol for SIGMAX
Defines message types and validation for bidirectional communication.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class WSMessageType(str, Enum):
    """WebSocket message types from client"""
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"
    PONG = "pong"
    COMMAND = "command"
    GET_STATUS = "get_status"
    GET_SUBSCRIPTIONS = "get_subscriptions"


class WSEventType(str, Enum):
    """WebSocket event types from server"""
    CONNECTED = "connected"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"

    # Data events
    ANALYSIS_UPDATE = "analysis_update"
    PROPOSAL_CREATED = "proposal_created"
    PROPOSAL_APPROVED = "proposal_approved"
    TRADE_EXECUTED = "trade_executed"
    STATUS_CHANGE = "status_change"
    MARKET_UPDATE = "market_update"
    PORTFOLIO_UPDATE = "portfolio_update"
    HEALTH_UPDATE = "health_update"
    SYSTEM_STATUS = "system_status"

    # Alert events
    ALERT = "alert"
    WARNING = "warning"


class SubscriptionTopic(str, Enum):
    """Available subscription topics"""
    ALL = "all"
    PROPOSALS = "proposals"
    EXECUTIONS = "executions"
    ANALYSIS = "analysis"
    STATUS = "status"
    MARKET = "market"
    PORTFOLIO = "portfolio"
    HEALTH = "health"
    ALERTS = "alerts"


# Client -> Server Messages

class WSMessage(BaseModel):
    """Base WebSocket message from client"""
    type: WSMessageType
    data: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class SubscribeMessage(BaseModel):
    """Subscribe to topics/symbols"""
    type: Literal[WSMessageType.SUBSCRIBE] = WSMessageType.SUBSCRIBE
    data: Dict[str, Any] = Field(
        ...,
        description="Subscription data",
        example={
            "topics": ["proposals", "executions"],
            "symbols": ["BTC/USDT", "ETH/USDT"]
        }
    )


class UnsubscribeMessage(BaseModel):
    """Unsubscribe from topics/symbols"""
    type: Literal[WSMessageType.UNSUBSCRIBE] = WSMessageType.UNSUBSCRIBE
    data: Dict[str, Any] = Field(
        ...,
        description="Unsubscription data",
        example={
            "topics": ["proposals"],
            "symbols": ["BTC/USDT"]
        }
    )


class CommandMessage(BaseModel):
    """Execute a command"""
    type: Literal[WSMessageType.COMMAND] = WSMessageType.COMMAND
    data: Dict[str, Any] = Field(
        ...,
        description="Command data",
        example={
            "command": "analyze",
            "symbol": "BTC/USDT"
        }
    )


# Server -> Client Events

class WSEvent(BaseModel):
    """Base WebSocket event from server"""
    type: WSEventType
    data: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    connection_id: Optional[str] = None


class ConnectedEvent(BaseModel):
    """Connection established event"""
    type: Literal[WSEventType.CONNECTED] = WSEventType.CONNECTED
    data: Dict[str, Any] = Field(
        default_factory=lambda: {
            "message": "Connected to SIGMAX WebSocket",
            "server_version": "2.0.0"
        }
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    connection_id: str


class SubscribedEvent(BaseModel):
    """Subscription confirmed event"""
    type: Literal[WSEventType.SUBSCRIBED] = WSEventType.SUBSCRIBED
    data: Dict[str, List[str]] = Field(
        ...,
        description="Confirmed subscriptions",
        example={
            "topics": ["proposals", "executions"],
            "symbols": ["BTC/USDT"]
        }
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class AnalysisUpdateEvent(BaseModel):
    """Market analysis update event"""
    type: Literal[WSEventType.ANALYSIS_UPDATE] = WSEventType.ANALYSIS_UPDATE
    data: Dict[str, Any] = Field(
        ...,
        description="Analysis data",
        example={
            "symbol": "BTC/USDT",
            "decision": "buy",
            "confidence": 0.75,
            "bull_score": 0.8,
            "bear_score": 0.4,
            "reasoning": "Strong upward momentum"
        }
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ProposalCreatedEvent(BaseModel):
    """Trade proposal created event"""
    type: Literal[WSEventType.PROPOSAL_CREATED] = WSEventType.PROPOSAL_CREATED
    data: Dict[str, Any] = Field(
        ...,
        description="Proposal data",
        example={
            "proposal_id": "prop_123",
            "symbol": "BTC/USDT",
            "action": "buy",
            "size": 0.001,
            "reason": "Agent consensus"
        }
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ProposalApprovedEvent(BaseModel):
    """Trade proposal approved event"""
    type: Literal[WSEventType.PROPOSAL_APPROVED] = WSEventType.PROPOSAL_APPROVED
    data: Dict[str, Any] = Field(
        ...,
        description="Approval data",
        example={
            "proposal_id": "prop_123",
            "approved_by": "user_1",
            "approved_at": "2025-12-21T10:30:00Z"
        }
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class TradeExecutedEvent(BaseModel):
    """Trade execution completed event"""
    type: Literal[WSEventType.TRADE_EXECUTED] = WSEventType.TRADE_EXECUTED
    data: Dict[str, Any] = Field(
        ...,
        description="Execution result",
        example={
            "proposal_id": "prop_123",
            "symbol": "BTC/USDT",
            "action": "buy",
            "size": 0.001,
            "filled_price": 95000.0,
            "order_id": "order_456",
            "status": "filled"
        }
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class StatusChangeEvent(BaseModel):
    """System status change event"""
    type: Literal[WSEventType.STATUS_CHANGE] = WSEventType.STATUS_CHANGE
    data: Dict[str, Any] = Field(
        ...,
        description="Status data",
        example={
            "previous_status": "running",
            "current_status": "paused",
            "reason": "User initiated"
        }
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class MarketUpdateEvent(BaseModel):
    """Market data update event"""
    type: Literal[WSEventType.MARKET_UPDATE] = WSEventType.MARKET_UPDATE
    data: List[Dict[str, Any]] = Field(
        ...,
        description="Market data for subscribed symbols",
        example=[
            {
                "symbol": "BTC/USDT",
                "price": 95000.0,
                "volume_24h": 1000000,
                "change_24h": 2.5
            }
        ]
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class PortfolioUpdateEvent(BaseModel):
    """Portfolio update event"""
    type: Literal[WSEventType.PORTFOLIO_UPDATE] = WSEventType.PORTFOLIO_UPDATE
    data: Dict[str, Any] = Field(
        ...,
        description="Portfolio data",
        example={
            "total_value": 100000.0,
            "available_cash": 50000.0,
            "positions": [
                {"symbol": "BTC/USDT", "size": 0.5, "value": 47500.0}
            ],
            "total_pnl": 5000.0,
            "total_pnl_percent": 5.0
        }
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class HealthUpdateEvent(BaseModel):
    """System health metrics event"""
    type: Literal[WSEventType.HEALTH_UPDATE] = WSEventType.HEALTH_UPDATE
    data: Dict[str, Any] = Field(
        ...,
        description="System health metrics",
        example={
            "cpu_percent": 45.2,
            "memory_percent": 62.1,
            "disk_percent": 35.0,
            "process_count": 150
        }
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ErrorEvent(BaseModel):
    """Error event"""
    type: Literal[WSEventType.ERROR] = WSEventType.ERROR
    data: Dict[str, Any] = Field(
        ...,
        description="Error details",
        example={
            "error": "Invalid subscription topic",
            "code": "INVALID_TOPIC",
            "details": "Topic 'invalid' does not exist"
        }
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class AlertEvent(BaseModel):
    """Alert/warning event"""
    type: Union[Literal[WSEventType.ALERT], Literal[WSEventType.WARNING]]
    data: Dict[str, Any] = Field(
        ...,
        description="Alert details",
        example={
            "severity": "high",
            "message": "Position size exceeds 50% of portfolio",
            "action_required": "Review position sizing"
        }
    )
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# Helper functions

def create_event(event_type: WSEventType, data: Dict[str, Any], **kwargs) -> WSEvent:
    """
    Create a WebSocket event with proper timestamp.

    Args:
        event_type: Type of event
        data: Event data
        **kwargs: Additional event fields (connection_id, etc.)

    Returns:
        WSEvent instance
    """
    return WSEvent(
        type=event_type,
        data=data,
        timestamp=datetime.now().isoformat(),
        **kwargs
    )


def parse_client_message(message: Dict[str, Any]) -> Union[WSMessage, SubscribeMessage, UnsubscribeMessage, CommandMessage]:
    """
    Parse client message into appropriate type.

    Args:
        message: Raw message dict

    Returns:
        Parsed message object

    Raises:
        ValueError: If message type is invalid
    """
    msg_type = message.get("type")

    if msg_type == WSMessageType.SUBSCRIBE:
        return SubscribeMessage(**message)
    elif msg_type == WSMessageType.UNSUBSCRIBE:
        return UnsubscribeMessage(**message)
    elif msg_type == WSMessageType.COMMAND:
        return CommandMessage(**message)
    else:
        return WSMessage(**message)


# Message validation helpers

def validate_subscription_topics(topics: List[str]) -> List[str]:
    """
    Validate and normalize subscription topics.

    Args:
        topics: List of topics to validate

    Returns:
        List of valid topics

    Raises:
        ValueError: If any topic is invalid
    """
    valid_topics = [t.value for t in SubscriptionTopic]
    normalized = []

    for topic in topics:
        topic_lower = topic.lower()
        if topic_lower not in valid_topics:
            raise ValueError(f"Invalid topic: {topic}. Valid topics: {valid_topics}")
        normalized.append(topic_lower)

    return normalized


def validate_symbols(symbols: List[str]) -> List[str]:
    """
    Validate and normalize trading symbols.

    Args:
        symbols: List of symbols to validate

    Returns:
        List of normalized symbols (uppercase, with /)

    Raises:
        ValueError: If any symbol is invalid
    """
    normalized = []

    for symbol in symbols:
        symbol_upper = symbol.upper()
        if "/" not in symbol_upper:
            raise ValueError(f"Invalid symbol format: {symbol}. Expected format: BASE/QUOTE")
        normalized.append(symbol_upper)

    return normalized
