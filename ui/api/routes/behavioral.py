"""
Behavioral Analytics Dashboard API Routes
Provides endpoints for behavioral finance metrics and agent analytics
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from enum import Enum

router = APIRouter(prefix="/behavioral", tags=["behavioral"])


# Enums for response models
class BiasType(str, Enum):
    DISPOSITION = "disposition"
    LOSS_AVERSION = "loss_aversion"
    LOTTERY = "lottery"
    OVERCONFIDENCE = "overconfidence"
    ANCHORING = "anchoring"
    HERDING = "herding"


class PersonaType(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CONTRARIAN = "contrarian"
    MOMENTUM = "momentum"


# Response models
class BiasMetrics(BaseModel):
    bias_type: str
    applications: int
    avg_adjustment: float
    last_applied: Optional[str]


class PersonaStats(BaseModel):
    persona: str
    agent_count: int
    avg_confidence: float
    avg_risk_tolerance: float


class SentimentData(BaseModel):
    fear_greed_index: float
    market_sentiment: str
    bullish_ratio: float
    herd_events_24h: int


class BehavioralDashboard(BaseModel):
    summary: Dict[str, Any]
    personas: List[PersonaStats]
    biases: List[BiasMetrics]
    sentiment: SentimentData
    last_updated: str


# In-memory storage for demo
_behavioral_state = {
    "agents": {},
    "bias_applications": {
        "disposition": {"count": 0, "total_adjustment": 0.0, "last": None},
        "loss_aversion": {"count": 0, "total_adjustment": 0.0, "last": None},
        "lottery": {"count": 0, "total_adjustment": 0.0, "last": None},
        "overconfidence": {"count": 0, "total_adjustment": 0.0, "last": None},
        "anchoring": {"count": 0, "total_adjustment": 0.0, "last": None},
        "herding": {"count": 0, "total_adjustment": 0.0, "last": None}
    },
    "sentiment_history": [],
    "herd_events": [],
    "decisions": [],
    "last_updated": datetime.utcnow().isoformat()
}


@router.get("/status")
async def get_behavioral_status() -> Dict[str, Any]:
    """
    Get current behavioral analytics status.

    Returns overview of behavioral finance metrics.
    """
    agent_count = len(_behavioral_state["agents"])
    decision_count = len(_behavioral_state["decisions"])

    # Calculate average fear/greed if we have history
    fear_greed = 50.0  # Neutral default
    if _behavioral_state["sentiment_history"]:
        recent = _behavioral_state["sentiment_history"][-10:]
        fear_greed = sum(s["fear_greed"] for s in recent) / len(recent)

    return {
        "status": "active",
        "agents_tracked": agent_count,
        "decisions_analyzed": decision_count,
        "fear_greed_index": round(fear_greed, 2),
        "herd_events_24h": len([
            h for h in _behavioral_state["herd_events"]
            if datetime.fromisoformat(h["timestamp"]) > datetime.utcnow() - timedelta(hours=24)
        ]),
        "last_updated": _behavioral_state["last_updated"]
    }


@router.get("/personas")
async def get_persona_distribution() -> Dict[str, Any]:
    """
    Get distribution of agent personas.

    Returns breakdown of agent types and their characteristics.
    """
    personas = {
        "conservative": {"count": 0, "total_confidence": 0.0, "total_risk": 0.0},
        "moderate": {"count": 0, "total_confidence": 0.0, "total_risk": 0.0},
        "aggressive": {"count": 0, "total_confidence": 0.0, "total_risk": 0.0},
        "contrarian": {"count": 0, "total_confidence": 0.0, "total_risk": 0.0},
        "momentum": {"count": 0, "total_confidence": 0.0, "total_risk": 0.0}
    }

    for agent_id, agent_data in _behavioral_state["agents"].items():
        persona = agent_data.get("persona", "moderate")
        if persona in personas:
            personas[persona]["count"] += 1
            personas[persona]["total_confidence"] += agent_data.get("confidence", 0.5)
            personas[persona]["total_risk"] += agent_data.get("risk_tolerance", 0.5)

    result = []
    for persona, data in personas.items():
        if data["count"] > 0:
            result.append({
                "persona": persona,
                "count": data["count"],
                "avg_confidence": round(data["total_confidence"] / data["count"], 3),
                "avg_risk_tolerance": round(data["total_risk"] / data["count"], 3)
            })

    return {
        "personas": result,
        "total_agents": len(_behavioral_state["agents"]),
        "last_updated": _behavioral_state["last_updated"]
    }


@router.get("/biases")
async def get_bias_metrics() -> Dict[str, Any]:
    """
    Get cognitive bias application metrics.

    Returns statistics on how biases affect trading decisions.
    """
    biases = []

    for bias_type, data in _behavioral_state["bias_applications"].items():
        avg_adj = 0.0
        if data["count"] > 0:
            avg_adj = data["total_adjustment"] / data["count"]

        biases.append({
            "bias_type": bias_type,
            "applications": data["count"],
            "avg_adjustment": round(avg_adj, 4),
            "last_applied": data["last"]
        })

    # Sort by application count
    biases.sort(key=lambda x: x["applications"], reverse=True)

    return {
        "biases": biases,
        "total_applications": sum(b["applications"] for b in biases),
        "last_updated": _behavioral_state["last_updated"]
    }


@router.get("/sentiment")
async def get_sentiment_data(
    hours: int = Query(default=24, ge=1, le=168)
) -> Dict[str, Any]:
    """
    Get social sentiment and Fear & Greed data.

    Args:
        hours: Hours of history to return

    Returns sentiment metrics and history.
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    # Filter recent sentiment
    recent_sentiment = [
        s for s in _behavioral_state["sentiment_history"]
        if datetime.fromisoformat(s["timestamp"]) > cutoff
    ]

    # Calculate current metrics
    if recent_sentiment:
        latest = recent_sentiment[-1]
        fear_greed = latest["fear_greed"]
        bullish_ratio = sum(1 for s in recent_sentiment if s.get("bullish", False)) / len(recent_sentiment)
    else:
        fear_greed = 50.0
        bullish_ratio = 0.5

    # Determine sentiment label
    if fear_greed < 25:
        sentiment_label = "extreme_fear"
    elif fear_greed < 45:
        sentiment_label = "fear"
    elif fear_greed < 55:
        sentiment_label = "neutral"
    elif fear_greed < 75:
        sentiment_label = "greed"
    else:
        sentiment_label = "extreme_greed"

    return {
        "current": {
            "fear_greed_index": round(fear_greed, 2),
            "sentiment": sentiment_label,
            "bullish_ratio": round(bullish_ratio, 3)
        },
        "history": recent_sentiment[-50:],  # Last 50 data points
        "data_points": len(recent_sentiment),
        "last_updated": _behavioral_state["last_updated"]
    }


@router.get("/herd-events")
async def get_herd_events(
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=50, ge=1, le=200)
) -> List[Dict[str, Any]]:
    """
    Get recent herd behavior events.

    Args:
        hours: Hours to look back
        limit: Maximum events to return

    Returns list of detected herd events.
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    recent = [
        h for h in _behavioral_state["herd_events"]
        if datetime.fromisoformat(h["timestamp"]) > cutoff
    ]

    return sorted(
        recent,
        key=lambda x: x["timestamp"],
        reverse=True
    )[:limit]


@router.post("/register-agent")
async def register_agent(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Register an agent for behavioral tracking.

    Request body:
        - agent_id: Unique agent identifier
        - persona: Agent persona type
        - confidence: Base confidence level
        - risk_tolerance: Risk tolerance (0-1)

    Returns registration confirmation.
    """
    agent_id = agent_data.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required")

    _behavioral_state["agents"][agent_id] = {
        "persona": agent_data.get("persona", "moderate"),
        "confidence": agent_data.get("confidence", 0.5),
        "risk_tolerance": agent_data.get("risk_tolerance", 0.5),
        "registered_at": datetime.utcnow().isoformat(),
        "decisions": 0
    }

    _behavioral_state["last_updated"] = datetime.utcnow().isoformat()

    return {
        "status": "registered",
        "agent_id": agent_id,
        "persona": _behavioral_state["agents"][agent_id]["persona"]
    }


@router.post("/record-decision")
async def record_decision(decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    Record a behavioral trading decision.

    Request body:
        - agent_id: Agent making decision
        - original_action: Original intended action
        - final_action: Action after bias application
        - biases_applied: List of biases that affected decision
        - confidence_adjustment: Net confidence change

    Returns recording confirmation.
    """
    agent_id = decision.get("agent_id")

    # Update agent decision count
    if agent_id in _behavioral_state["agents"]:
        _behavioral_state["agents"][agent_id]["decisions"] += 1

    # Record bias applications
    for bias in decision.get("biases_applied", []):
        bias_type = bias.get("type", "").lower()
        if bias_type in _behavioral_state["bias_applications"]:
            _behavioral_state["bias_applications"][bias_type]["count"] += 1
            _behavioral_state["bias_applications"][bias_type]["total_adjustment"] += bias.get("adjustment", 0)
            _behavioral_state["bias_applications"][bias_type]["last"] = datetime.utcnow().isoformat()

    # Store decision
    _behavioral_state["decisions"].append({
        **decision,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Keep only last 1000 decisions
    if len(_behavioral_state["decisions"]) > 1000:
        _behavioral_state["decisions"] = _behavioral_state["decisions"][-1000:]

    _behavioral_state["last_updated"] = datetime.utcnow().isoformat()

    return {
        "status": "recorded",
        "decision_id": len(_behavioral_state["decisions"]),
        "biases_applied": len(decision.get("biases_applied", []))
    }


@router.post("/update-sentiment")
async def update_sentiment(sentiment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update market sentiment data.

    Request body:
        - fear_greed: Fear & Greed index (0-100)
        - bullish: Whether overall sentiment is bullish
        - source: Source of sentiment data

    Returns update confirmation.
    """
    fear_greed = sentiment.get("fear_greed", 50)

    if not 0 <= fear_greed <= 100:
        raise HTTPException(status_code=400, detail="fear_greed must be 0-100")

    _behavioral_state["sentiment_history"].append({
        "fear_greed": fear_greed,
        "bullish": sentiment.get("bullish", fear_greed > 50),
        "source": sentiment.get("source", "manual"),
        "timestamp": datetime.utcnow().isoformat()
    })

    # Keep only last 1000 sentiment points
    if len(_behavioral_state["sentiment_history"]) > 1000:
        _behavioral_state["sentiment_history"] = _behavioral_state["sentiment_history"][-1000:]

    _behavioral_state["last_updated"] = datetime.utcnow().isoformat()

    return {
        "status": "updated",
        "fear_greed": fear_greed,
        "data_points": len(_behavioral_state["sentiment_history"])
    }


@router.post("/record-herd-event")
async def record_herd_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Record a herd behavior event.

    Request body:
        - symbol: Trading symbol
        - direction: Herd direction (bullish/bearish)
        - strength: Herd strength (0-1)
        - agents_involved: Number of agents participating

    Returns event recording confirmation.
    """
    symbol = event.get("symbol")
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol required")

    herd_event = {
        "symbol": symbol,
        "direction": event.get("direction", "neutral"),
        "strength": event.get("strength", 0.5),
        "agents_involved": event.get("agents_involved", 0),
        "timestamp": datetime.utcnow().isoformat()
    }

    _behavioral_state["herd_events"].append(herd_event)

    # Keep only last 500 events
    if len(_behavioral_state["herd_events"]) > 500:
        _behavioral_state["herd_events"] = _behavioral_state["herd_events"][-500:]

    _behavioral_state["last_updated"] = datetime.utcnow().isoformat()

    return {
        "status": "recorded",
        "event": herd_event
    }


@router.get("/dashboard")
async def get_behavioral_dashboard() -> Dict[str, Any]:
    """
    Get complete behavioral analytics dashboard data.

    Returns all data needed for behavioral dashboard UI.
    """
    # Get persona stats
    personas = {}
    for agent_id, data in _behavioral_state["agents"].items():
        p = data.get("persona", "moderate")
        if p not in personas:
            personas[p] = {"count": 0, "confidence": 0, "risk": 0}
        personas[p]["count"] += 1
        personas[p]["confidence"] += data.get("confidence", 0.5)
        personas[p]["risk"] += data.get("risk_tolerance", 0.5)

    persona_stats = []
    for p, d in personas.items():
        if d["count"] > 0:
            persona_stats.append({
                "persona": p,
                "agent_count": d["count"],
                "avg_confidence": round(d["confidence"] / d["count"], 3),
                "avg_risk_tolerance": round(d["risk"] / d["count"], 3)
            })

    # Get bias metrics
    bias_metrics = []
    for bias_type, data in _behavioral_state["bias_applications"].items():
        avg = data["total_adjustment"] / data["count"] if data["count"] > 0 else 0
        bias_metrics.append({
            "bias_type": bias_type,
            "applications": data["count"],
            "avg_adjustment": round(avg, 4),
            "last_applied": data["last"]
        })

    # Get current sentiment
    fear_greed = 50.0
    bullish_ratio = 0.5
    if _behavioral_state["sentiment_history"]:
        recent = _behavioral_state["sentiment_history"][-10:]
        fear_greed = sum(s["fear_greed"] for s in recent) / len(recent)
        bullish_ratio = sum(1 for s in recent if s.get("bullish", False)) / len(recent)

    # Count recent herd events
    herd_24h = len([
        h for h in _behavioral_state["herd_events"]
        if datetime.fromisoformat(h["timestamp"]) > datetime.utcnow() - timedelta(hours=24)
    ])

    # Determine sentiment label
    if fear_greed < 25:
        sentiment = "extreme_fear"
    elif fear_greed < 45:
        sentiment = "fear"
    elif fear_greed < 55:
        sentiment = "neutral"
    elif fear_greed < 75:
        sentiment = "greed"
    else:
        sentiment = "extreme_greed"

    return {
        "summary": {
            "total_agents": len(_behavioral_state["agents"]),
            "total_decisions": len(_behavioral_state["decisions"]),
            "total_bias_applications": sum(b["applications"] for b in bias_metrics),
            "herd_events_24h": herd_24h
        },
        "personas": persona_stats,
        "biases": bias_metrics,
        "sentiment": {
            "fear_greed_index": round(fear_greed, 2),
            "market_sentiment": sentiment,
            "bullish_ratio": round(bullish_ratio, 3),
            "herd_events_24h": herd_24h
        },
        "recent_decisions": _behavioral_state["decisions"][-10:],
        "recent_herd_events": _behavioral_state["herd_events"][-5:],
        "last_updated": _behavioral_state["last_updated"]
    }


@router.get("/agent/{agent_id}")
async def get_agent_analytics(agent_id: str) -> Dict[str, Any]:
    """
    Get detailed analytics for a specific agent.

    Args:
        agent_id: Agent identifier

    Returns agent's behavioral profile and decision history.
    """
    if agent_id not in _behavioral_state["agents"]:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent = _behavioral_state["agents"][agent_id]

    # Get agent's decisions
    agent_decisions = [
        d for d in _behavioral_state["decisions"]
        if d.get("agent_id") == agent_id
    ]

    # Calculate bias breakdown for this agent
    bias_counts = {}
    for decision in agent_decisions:
        for bias in decision.get("biases_applied", []):
            bt = bias.get("type", "unknown")
            bias_counts[bt] = bias_counts.get(bt, 0) + 1

    return {
        "agent_id": agent_id,
        "profile": {
            "persona": agent["persona"],
            "confidence": agent["confidence"],
            "risk_tolerance": agent["risk_tolerance"],
            "registered_at": agent["registered_at"]
        },
        "stats": {
            "total_decisions": len(agent_decisions),
            "bias_breakdown": bias_counts
        },
        "recent_decisions": agent_decisions[-10:]
    }
