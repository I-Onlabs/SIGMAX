import pytest


class DummyOrchestrator:
    async def analyze_symbol_detailed(self, symbol: str, market_data=None):
        return {
            "symbol": symbol,
            "market_data": {"price": 100.0},
            "research_plan": {"summary": "plan"},
            "research_summary": "research",
            "validation_passed": True,
            "validation_score": 0.9,
            "risk_assessment": {"approved": True},
            "compliance_check": {"approved": True},
            "final_decision": {"action": "buy", "confidence": 0.8, "timestamp": "t"},
        }

    async def stream_symbol_analysis(self, symbol: str, market_data=None):
        yield {"type": "final", "state": await self.analyze_symbol_detailed(symbol), "timestamp": "t"}


class DummyExecution:
    async def execute_trade(self, symbol: str, action: str, size: float, price=None):
        return {"success": True, "symbol": symbol, "action": action, "size": size}


@pytest.mark.asyncio
async def test_proposal_requires_approval_for_live_by_default(monkeypatch):
    from core.interfaces.channel_service import ChannelService
    from core.interfaces.contracts import Channel, Intent, StructuredRequest, UserPreferences, ExecutionPermissions

    monkeypatch.setenv("REQUIRE_MANUAL_APPROVAL", "true")

    svc = ChannelService(orchestrator=DummyOrchestrator(), execution_module=DummyExecution(), compliance_module=None)

    resp = await svc.handle(
        StructuredRequest(
            channel=Channel.api,
            intent=Intent.propose_trade,
            symbol="BTC/USDT",
            preferences=UserPreferences(
                risk_profile="conservative",
                mode="live",
                permissions=ExecutionPermissions(allow_paper=True, allow_live=True, require_manual_approval_live=True),
            ),
        )
    )

    assert resp.proposal is not None
    assert resp.proposal.requires_manual_approval is True
    assert resp.proposal.approved is False


@pytest.mark.asyncio
async def test_execute_requires_approval_when_flagged(monkeypatch):
    from core.interfaces.channel_service import ChannelService
    from core.interfaces.contracts import Channel, Intent, StructuredRequest, UserPreferences, ExecutionPermissions

    monkeypatch.setenv("REQUIRE_MANUAL_APPROVAL", "true")

    svc = ChannelService(orchestrator=DummyOrchestrator(), execution_module=DummyExecution(), compliance_module=None)
    resp = await svc.handle(
        StructuredRequest(
            channel=Channel.api,
            intent=Intent.propose_trade,
            symbol="BTC/USDT",
            preferences=UserPreferences(
                risk_profile="conservative",
                mode="live",
                permissions=ExecutionPermissions(allow_paper=True, allow_live=True, require_manual_approval_live=True),
            ),
        )
    )
    pid = resp.proposal.proposal_id  # type: ignore[union-attr]

    with pytest.raises(PermissionError):
        await svc.execute_proposal(pid)

    svc.approve_proposal(pid)
    result = await svc.execute_proposal(pid)
    assert result["success"] is True

