"""
AI-centric chat interface routes.

Provides:
- Streaming analysis with step-level progress (SSE)
- Trade proposal / approval / execution endpoints
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import AsyncIterator, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from loguru import logger

from sigmax_manager import get_sigmax_manager
from auth import verify_api_key

from interfaces.contracts import (
    Channel,
    ExecutionPermissions,
    Intent,
    StructuredRequest,
    UserPreferences,
)

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])


def _now() -> str:
    return datetime.now().isoformat()


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


class ChatRequest(BaseModel):
    message: str = Field(..., description="User chat message")
    symbol: Optional[str] = Field(None, description="Optional explicit symbol (e.g. BTC/USDT)")
    risk_profile: str = Field("conservative", description="conservative|balanced|aggressive")
    mode: str = Field("paper", description="paper|live")
    require_manual_approval_live: bool = Field(True, description="Require manual approval before live execution")


@router.post("/stream", dependencies=[Depends(verify_api_key)])
async def chat_stream(req: ChatRequest):
    """
    Stream step-level orchestrator progress and artifacts as Server-Sent Events (SSE).

    Client receives events:
    - step: {step, update}
    - final: {state, decision, proposal?}
    - error: {error}
    """
    manager = await get_sigmax_manager()
    service = manager.get_channel_service()

    # Minimal intent inference: if symbol provided -> analyze; otherwise treat as help.
    if not req.symbol:
        async def help_stream() -> AsyncIterator[str]:
            yield _sse("final", {
                "timestamp": _now(),
                "message": "Provide a symbol (e.g. BTC/USDT) to run a full multi-agent analysis stream.",
            })
        return StreamingResponse(help_stream(), media_type="text/event-stream")

    session_id = str(uuid.uuid4())
    structured = StructuredRequest(
        channel=Channel.web,
        intent=Intent.analyze,
        message=req.message,
        symbol=req.symbol,
        session_id=session_id,
        preferences=UserPreferences(
            risk_profile=req.risk_profile,  # type: ignore[arg-type]
            mode=req.mode,  # type: ignore[arg-type]
            permissions=ExecutionPermissions(
                allow_paper=True,
                allow_live=(req.mode == "live"),
                require_manual_approval_live=req.require_manual_approval_live,
            ),
        ),
    )

    async def event_stream() -> AsyncIterator[str]:
        try:
            yield _sse("meta", {"session_id": session_id, "timestamp": _now()})

            final_state = None
            async for ev in service.stream_analyze(structured):
                if ev.type == "step":
                    yield _sse("step", {"timestamp": ev.timestamp, "step": ev.step, "update": ev.data})
                elif ev.type == "final":
                    final_state = ev.data
                elif ev.type == "error":
                    yield _sse("error", {"timestamp": ev.timestamp, "error": ev.data})
                    return

            # Build artifacts + optionally propose trade
            decision = (final_state or {}).get("final_decision", {}) if isinstance(final_state, dict) else {}
            propose = StructuredRequest(**structured.model_dump(), intent=Intent.propose_trade)
            proposal = None
            try:
                proposal_resp = await service.handle(propose)
                proposal = proposal_resp.proposal.model_dump() if proposal_resp.proposal else None
            except Exception:
                proposal = None

            yield _sse("final", {
                "timestamp": _now(),
                "session_id": session_id,
                "state": final_state,
                "decision": decision,
                "proposal": proposal,
            })

        except Exception as e:
            logger.error(f"chat_stream error: {e}", exc_info=True)
            yield _sse("error", {"timestamp": _now(), "error": str(e)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


class ProposalRequest(BaseModel):
    symbol: str
    risk_profile: str = "conservative"
    mode: str = "paper"


@router.get("/proposals", dependencies=[Depends(verify_api_key)])
async def list_trade_proposals():
    manager = await get_sigmax_manager()
    service = manager.get_channel_service()
    proposals = service.list_proposals()
    return {
        "timestamp": _now(),
        "count": len(proposals),
        "proposals": {pid: p.model_dump() for pid, p in proposals.items()},
    }


@router.get("/proposals/{proposal_id}", dependencies=[Depends(verify_api_key)])
async def get_trade_proposal(proposal_id: str):
    manager = await get_sigmax_manager()
    service = manager.get_channel_service()
    proposal = service.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Unknown proposal_id")
    return proposal.model_dump()


@router.post("/proposals", dependencies=[Depends(verify_api_key)])
async def create_trade_proposal(req: ProposalRequest):
    manager = await get_sigmax_manager()
    service = manager.get_channel_service()
    resp = await service.handle(
        StructuredRequest(
            channel=Channel.api,
            intent=Intent.propose_trade,
            symbol=req.symbol,
            preferences=UserPreferences(
                risk_profile=req.risk_profile,  # type: ignore[arg-type]
                mode=req.mode,  # type: ignore[arg-type]
                permissions=ExecutionPermissions(
                    allow_paper=True,
                    allow_live=(req.mode == "live"),
                    require_manual_approval_live=True,
                ),
            ),
        )
    )
    if resp.proposal:
        manager.add_event("trade_proposal", resp.proposal.model_dump())
    return resp.model_dump()


@router.post("/proposals/{proposal_id}/approve", dependencies=[Depends(verify_api_key)])
async def approve_trade_proposal(proposal_id: str):
    manager = await get_sigmax_manager()
    service = manager.get_channel_service()
    try:
        proposal = service.approve_proposal(proposal_id)
        manager.add_event("trade_proposal_approved", proposal.model_dump())
        return proposal.model_dump()
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown proposal_id")


@router.post("/proposals/{proposal_id}/execute", dependencies=[Depends(verify_api_key)])
async def execute_trade_proposal(proposal_id: str):
    manager = await get_sigmax_manager()
    service = manager.get_channel_service()
    try:
        result = await service.execute_proposal(proposal_id)
        manager.add_event("trade_execution", {"proposal_id": proposal_id, "result": result})
        return {"success": True, "result": result, "timestamp": _now()}
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown proposal_id")
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

