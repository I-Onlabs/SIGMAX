"""
ChannelService

Single, shared "front door" into the orchestrator for all interfaces.

Responsibilities:
- Normalize/validate inputs (symbol formatting, intent routing)
- Run orchestrator analysis (detailed or streaming)
- Produce step artifacts for UIs (plan, research, validation, debate, risk)
- Create trade proposals (never executes live trades without explicit approval gates)
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Optional, Tuple

from loguru import logger

from .contracts import (
    Artifact,
    ChannelResponse,
    Intent,
    StructuredRequest,
    StreamEvent,
    TradeProposal,
)


def _now() -> str:
    return datetime.now().isoformat()


def _normalize_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if "/" not in s:
        raise ValueError("Symbol must be in format BASE/QUOTE (e.g., BTC/USDT)")
    return s


class ChannelService:
    def __init__(self, orchestrator, execution_module=None, compliance_module=None):
        self.orchestrator = orchestrator
        self.execution_module = execution_module
        self.compliance_module = compliance_module

        # In-memory proposal store (sufficient for single-process; swap for DB/Redis later)
        self._proposals: Dict[str, TradeProposal] = {}

    def get_proposal(self, proposal_id: str) -> Optional[TradeProposal]:
        return self._proposals.get(proposal_id)

    def list_proposals(self) -> Dict[str, TradeProposal]:
        return dict(self._proposals)

    def approve_proposal(self, proposal_id: str) -> TradeProposal:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise KeyError("Unknown proposal_id")
        proposal.approved = True
        self._proposals[proposal_id] = proposal
        return proposal

    async def execute_proposal(self, proposal_id: str) -> Dict[str, Any]:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise KeyError("Unknown proposal_id")

        if proposal.requires_manual_approval and not proposal.approved:
            raise PermissionError("Proposal requires manual approval before execution")

        if not self.execution_module:
            raise RuntimeError("Execution module not available")

        # Final compliance gate (best-effort)
        if self.compliance_module:
            compliance = await self.compliance_module.check_compliance(
                trade={
                    "symbol": proposal.symbol,
                    "size": proposal.size,
                    "action": proposal.action,
                    "timestamp": _now(),
                },
                risk_profile=os.getenv("RISK_PROFILE", "conservative"),
            )
            if not compliance.get("compliant", False):
                raise PermissionError(f"Compliance rejected: {compliance.get('reason', 'unknown')}")

        return await self.execution_module.execute_trade(
            symbol=proposal.symbol,
            action=proposal.action,
            size=proposal.size,
        )

    def _proposal_requires_approval(self, mode: str, req: StructuredRequest) -> bool:
        if mode == "paper":
            return False
        return bool(req.preferences.permissions.require_manual_approval_live) or (
            os.getenv("REQUIRE_MANUAL_APPROVAL", "true").lower() == "true"
        )

    def _infer_trade_size(self, symbol: str, price: float, req: StructuredRequest) -> Tuple[float, float]:
        """
        Infer a safe default size for a proposal.

        - Uses TOTAL_CAPITAL and profile max_position_pct from ComplianceModule embedded policies when available.
        - Produces a small notional by default to keep paper-mode safe.
        """
        total_capital = float(os.getenv("TOTAL_CAPITAL", "50"))
        default_pct = {"conservative": 0.10, "balanced": 0.15, "aggressive": 0.25}.get(
            req.preferences.risk_profile, 0.10
        )
        notional = total_capital * default_pct

        # If compliance module has risk limits, respect them.
        if self.compliance_module and hasattr(self.compliance_module, "get_policies"):
            try:
                policies = self.compliance_module.get_policies()
                limits = (policies.get("risk_limits") or {}).get(req.preferences.risk_profile) or {}
                pct = float(limits.get("max_position_pct", default_pct * 100)) / 100.0
                notional = min(notional, total_capital * pct)
            except Exception:
                pass

        if price <= 0:
            # Fall back to a conservative unit size.
            return 0.001, notional

        size = notional / price
        # Hard clamp if MAX_POSITION_SIZE is set (best-effort; note units vary by exchange/symbol).
        try:
            max_size = float(os.getenv("MAX_POSITION_SIZE", "15"))
            size = min(size, max_size)
        except Exception:
            pass

        return max(size, 0.000001), notional

    def _build_artifacts_from_state(self, state: Dict[str, Any]) -> list[Artifact]:
        artifacts: list[Artifact] = []
        if state.get("research_plan"):
            artifacts.append(Artifact(type="plan", title="Research plan", content=state["research_plan"]))
        if state.get("task_execution_results"):
            artifacts.append(
                Artifact(type="research.tasks", title="Task execution results", content=state["task_execution_results"])
            )
        if state.get("research_summary"):
            artifacts.append(Artifact(type="research.summary", title="Research summary", content=state["research_summary"]))
        if state.get("validation_checks") or state.get("validation_score") is not None:
            artifacts.append(
                Artifact(
                    type="validation",
                    title="Validation",
                    content={
                        "passed": state.get("validation_passed"),
                        "score": state.get("validation_score"),
                        "gaps": state.get("data_gaps", []),
                        "checks": state.get("validation_checks", {}),
                    },
                )
            )
        if state.get("fundamental_analysis"):
            artifacts.append(
                Artifact(type="fundamentals", title="Fundamental analysis", content=state.get("fundamental_analysis"))
            )
        if state.get("financial_ratios"):
            artifacts.append(Artifact(type="ratios", title="Financial ratios", content=state.get("financial_ratios")))
        if state.get("bull_argument"):
            artifacts.append(Artifact(type="debate.bull", title="Bull case", content=state.get("bull_argument")))
        if state.get("bear_argument"):
            artifacts.append(Artifact(type="debate.bear", title="Bear case", content=state.get("bear_argument")))
        if state.get("technical_analysis"):
            artifacts.append(
                Artifact(type="analysis.technical", title="Technical analysis", content=state.get("technical_analysis"))
            )
        if state.get("risk_assessment"):
            artifacts.append(Artifact(type="risk", title="Risk assessment", content=state.get("risk_assessment")))
        if state.get("compliance_check"):
            artifacts.append(Artifact(type="privacy", title="Privacy/compliance check", content=state.get("compliance_check")))
        return artifacts

    async def handle(self, req: StructuredRequest) -> ChannelResponse:
        if req.intent in {Intent.analyze, Intent.propose_trade}:
            if not req.symbol:
                raise ValueError("symbol is required for analyze/propose_trade")

            symbol = _normalize_symbol(req.symbol)
            mode = req.preferences.mode

            state = await self.orchestrator.analyze_symbol_detailed(symbol)
            decision = (state.get("final_decision") or {}) if isinstance(state, dict) else {}
            artifacts = self._build_artifacts_from_state(state)

            message = f"Decision: {decision.get('action', 'hold')} {symbol} (confidence {decision.get('confidence', 0):.2f})"
            response = ChannelResponse(ok=True, message=message, intent=req.intent, symbol=symbol, artifacts=artifacts, decision=decision)

            if req.intent == Intent.propose_trade:
                action = decision.get("action")
                if action not in ("buy", "sell"):
                    response.message = "No trade proposed (decision is hold or not actionable)."
                    return response

                price = float((state.get("market_data") or {}).get("price", 0.0))
                size, notional = self._infer_trade_size(symbol, price, req)

                proposal_id = str(uuid.uuid4())
                proposal = TradeProposal(
                    proposal_id=proposal_id,
                    symbol=symbol,
                    action=action,
                    size=size,
                    notional_usd=notional,
                    mode=mode,
                    requires_manual_approval=self._proposal_requires_approval(mode, req),
                    approved=False,
                    created_at=_now(),
                    rationale=decision.get("reason") or (decision.get("reasoning") or {}).get("technical"),
                )
                self._proposals[proposal_id] = proposal
                response.proposal = proposal
                response.message = f"Proposed {action} {size:.6f} {symbol} (≈${notional:.2f})."

            return response

        if req.intent == Intent.approve_trade:
            if not req.proposal_id:
                raise ValueError("proposal_id is required for approve_trade")
            proposal = self.approve_proposal(req.proposal_id)
            return ChannelResponse(
                ok=True,
                message=f"Approved proposal {proposal.proposal_id}.",
                intent=req.intent,
                symbol=proposal.symbol,
                proposal=proposal,
            )

        if req.intent == Intent.execute_trade:
            if not req.proposal_id:
                raise ValueError("proposal_id is required for execute_trade")
            result = await self.execute_proposal(req.proposal_id)
            return ChannelResponse(ok=True, message="Trade executed.", intent=req.intent, decision=result)

        raise ValueError(f"Unsupported intent: {req.intent}")

    async def stream_analyze(self, req: StructuredRequest) -> AsyncIterator[StreamEvent]:
        if not req.symbol:
            raise ValueError("symbol is required for streaming analysis")
        symbol = _normalize_symbol(req.symbol)

        try:
            async for event in self.orchestrator.stream_symbol_analysis(symbol):
                yield StreamEvent(type=event["type"], timestamp=event.get("timestamp", _now()), step=event.get("step"), data=event.get("update") or event.get("state"))
        except Exception as e:
            logger.error(f"Streaming analysis error: {e}", exc_info=True)
            yield StreamEvent(type="error", timestamp=_now(), data={"error": str(e)})

