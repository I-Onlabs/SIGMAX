"""
Security Dashboard API Routes
Provides endpoints for security metrics and threat monitoring
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter(prefix="/security", tags=["security"])


# Response models
class ThreatSummary(BaseModel):
    level: str
    attack_types: List[str]
    confidence: float
    timestamp: str


class SecurityMetrics(BaseModel):
    prompts_scanned: int
    threats_blocked: int
    tools_validated: int
    anomalies_detected: int
    state_checks: int
    tampering_detected: int
    news_validated: int
    fake_news_blocked: int


class SecurityStatus(BaseModel):
    status: str
    threat_level: str
    recent_threats: int
    metrics: SecurityMetrics
    last_updated: str


# In-memory storage for demo (replace with actual security module integration)
_security_state = {
    "metrics": {
        "prompts_scanned": 0,
        "threats_blocked": 0,
        "tools_validated": 0,
        "anomalies_detected": 0,
        "state_checks": 0,
        "tampering_detected": 0,
        "news_validated": 0,
        "fake_news_blocked": 0
    },
    "recent_threats": [],
    "last_updated": datetime.utcnow().isoformat()
}


@router.get("/status", response_model=SecurityStatus)
async def get_security_status():
    """
    Get current security status and metrics.

    Returns overall security health and recent threat summary.
    """
    recent_count = len([
        t for t in _security_state["recent_threats"]
        if datetime.fromisoformat(t["timestamp"]) > datetime.utcnow() - timedelta(hours=1)
    ])

    # Determine threat level
    if _security_state["metrics"]["threats_blocked"] > 10:
        threat_level = "elevated"
    elif _security_state["metrics"]["threats_blocked"] > 0:
        threat_level = "guarded"
    else:
        threat_level = "normal"

    return SecurityStatus(
        status="active",
        threat_level=threat_level,
        recent_threats=recent_count,
        metrics=SecurityMetrics(**_security_state["metrics"]),
        last_updated=_security_state["last_updated"]
    )


@router.get("/metrics")
async def get_security_metrics() -> Dict[str, Any]:
    """
    Get detailed security metrics.

    Returns comprehensive security statistics.
    """
    return {
        "metrics": _security_state["metrics"],
        "rates": {
            "threat_rate": _security_state["metrics"]["threats_blocked"] /
                          max(_security_state["metrics"]["prompts_scanned"], 1),
            "anomaly_rate": _security_state["metrics"]["anomalies_detected"] /
                           max(_security_state["metrics"]["tools_validated"], 1),
            "fake_news_rate": _security_state["metrics"]["fake_news_blocked"] /
                             max(_security_state["metrics"]["news_validated"], 1)
        },
        "last_updated": _security_state["last_updated"]
    }


@router.get("/threats")
async def get_recent_threats(
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=50, ge=1, le=200)
) -> List[Dict[str, Any]]:
    """
    Get recent security threats.

    Args:
        hours: Hours to look back (default 24)
        limit: Maximum threats to return

    Returns list of recent threat events.
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    recent = [
        t for t in _security_state["recent_threats"]
        if datetime.fromisoformat(t["timestamp"]) > cutoff
    ]

    return sorted(
        recent,
        key=lambda x: x["timestamp"],
        reverse=True
    )[:limit]


@router.post("/scan")
async def scan_content(content: Dict[str, str]) -> Dict[str, Any]:
    """
    Scan content for security threats.

    Request body:
        - text: Content to scan

    Returns scan results with any detected threats.
    """
    text = content.get("text", "")

    if not text:
        raise HTTPException(status_code=400, detail="No content provided")

    # Import and use PromptGuard
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

        from core.security import PromptGuard

        guard = PromptGuard()
        result = guard.analyze(text)

        # Update metrics
        _security_state["metrics"]["prompts_scanned"] += 1
        if result.level.value != "none":
            _security_state["metrics"]["threats_blocked"] += 1
            _security_state["recent_threats"].append({
                "type": "prompt_threat",
                "level": result.level.value,
                "attack_types": [a.value for a in result.attack_types],
                "confidence": result.confidence,
                "timestamp": datetime.utcnow().isoformat()
            })

        _security_state["last_updated"] = datetime.utcnow().isoformat()

        return {
            "safe": result.level.value == "none",
            "threat_level": result.level.value,
            "attack_types": [a.value for a in result.attack_types],
            "confidence": result.confidence,
            "sanitized": guard.sanitize(text) if result.level.value != "none" else None
        }

    except ImportError:
        # Fallback if security module not available
        return {
            "safe": True,
            "threat_level": "unknown",
            "attack_types": [],
            "confidence": 0.0,
            "note": "Security module not available"
        }


@router.post("/validate-data")
async def validate_market_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate market data for anomalies.

    Request body should contain market data to validate.

    Returns validation results with any detected anomalies.
    """
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

        from core.security import ToolResponseValidator

        validator = ToolResponseValidator()
        tool_name = data.pop("_tool_name", "get_price")
        result = validator.validate(tool_name, data)

        # Update metrics
        _security_state["metrics"]["tools_validated"] += 1
        if result.anomalies:
            _security_state["metrics"]["anomalies_detected"] += len(result.anomalies)

        _security_state["last_updated"] = datetime.utcnow().isoformat()

        return {
            "valid": result.status.value == "valid",
            "status": result.status.value,
            "anomalies": [a.value for a in result.anomalies],
            "confidence": result.confidence,
            "details": result.details
        }

    except ImportError:
        return {
            "valid": True,
            "status": "unknown",
            "anomalies": [],
            "confidence": 0.0,
            "note": "Validation module not available"
        }


@router.post("/validate-news")
async def validate_news(news: Dict[str, str]) -> Dict[str, Any]:
    """
    Validate news content for authenticity.

    Request body:
        - headline: News headline
        - source: News source (optional)
        - content: Full content (optional)

    Returns credibility assessment.
    """
    headline = news.get("headline", "")
    source = news.get("source")
    content = news.get("content")

    if not headline:
        raise HTTPException(status_code=400, detail="Headline required")

    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

        from core.security import NewsValidator

        validator = NewsValidator()
        result = validator.validate(
            headline=headline,
            source=source,
            content=content
        )

        # Update metrics
        _security_state["metrics"]["news_validated"] += 1
        if result.credibility.value in ["low", "very_low"]:
            _security_state["metrics"]["fake_news_blocked"] += 1

        _security_state["last_updated"] = datetime.utcnow().isoformat()

        return {
            "credible": result.credibility.value not in ["low", "very_low"],
            "credibility": result.credibility.value,
            "credibility_score": result.credibility_score,
            "manipulation_indicators": [i.value for i in result.manipulation_indicators],
            "source_info": result.source_profile.to_dict() if result.source_profile else None
        }

    except ImportError:
        return {
            "credible": True,
            "credibility": "unknown",
            "credibility_score": 0.5,
            "manipulation_indicators": [],
            "note": "News validator not available"
        }


@router.get("/dashboard")
async def get_security_dashboard() -> Dict[str, Any]:
    """
    Get complete security dashboard data.

    Returns all data needed for security dashboard UI.
    """
    metrics = _security_state["metrics"]

    # Calculate rates
    scan_rate = metrics["threats_blocked"] / max(metrics["prompts_scanned"], 1) * 100
    anomaly_rate = metrics["anomalies_detected"] / max(metrics["tools_validated"], 1) * 100
    fake_rate = metrics["fake_news_blocked"] / max(metrics["news_validated"], 1) * 100

    # Get recent threats by type
    threat_types = {}
    for threat in _security_state["recent_threats"][-100:]:
        for attack_type in threat.get("attack_types", []):
            threat_types[attack_type] = threat_types.get(attack_type, 0) + 1

    return {
        "summary": {
            "status": "active",
            "threat_level": "normal" if scan_rate < 5 else "elevated" if scan_rate < 20 else "high",
            "health_score": max(0, 100 - scan_rate - anomaly_rate - fake_rate)
        },
        "metrics": metrics,
        "rates": {
            "threat_rate_pct": round(scan_rate, 2),
            "anomaly_rate_pct": round(anomaly_rate, 2),
            "fake_news_rate_pct": round(fake_rate, 2)
        },
        "threat_distribution": threat_types,
        "recent_threats": _security_state["recent_threats"][-10:],
        "last_updated": _security_state["last_updated"]
    }
