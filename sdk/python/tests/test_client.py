"""
Unit tests for SIGMAX SDK client.

Tests all client methods with mocked HTTP responses.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import httpx
import pytest
from pytest_httpx import HTTPXMock

from sigmax_sdk import (
    ProposalStatus,
    RiskProfile,
    SigmaxAPIError,
    SigmaxAuthenticationError,
    SigmaxClient,
    SigmaxRateLimitError,
    SigmaxValidationError,
    SystemStatus,
    TradeMode,
    TradeProposal,
)


@pytest.fixture
def api_url() -> str:
    """Test API URL."""
    return "http://test-api.sigmax.local"


@pytest.fixture
def client(api_url: str) -> SigmaxClient:
    """Create test client."""
    return SigmaxClient(api_url=api_url, api_key="test-key")


@pytest.mark.asyncio
async def test_client_initialization(api_url: str) -> None:
    """Test client initialization."""
    client = SigmaxClient(
        api_url=api_url,
        api_key="test-key",
        timeout=30.0,
    )

    assert client.api_url == api_url
    assert client.api_key == "test-key"
    assert client.timeout == 30.0
    assert "Authorization" in client.headers
    assert client.headers["Authorization"] == "Bearer test-key"


@pytest.mark.asyncio
async def test_client_context_manager(api_url: str) -> None:
    """Test client as async context manager."""
    async with SigmaxClient(api_url=api_url) as client:
        assert client._client is not None

    assert client._client is None or client._client.is_closed


@pytest.mark.asyncio
async def test_get_status_success(
    client: SigmaxClient,
    httpx_mock: HTTPXMock,
) -> None:
    """Test successful status retrieval."""
    httpx_mock.add_response(
        url="http://test-api.sigmax.local/api/status",
        json={
            "status": "online",
            "version": "1.0.0",
            "uptime_seconds": 3600.0,
            "active_trades": 5,
            "pending_proposals": 2,
            "mode": "paper",
            "api_health": True,
            "database_health": True,
            "exchange_health": True,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    status = await client.get_status()

    assert isinstance(status, SystemStatus)
    assert status.status == "online"
    assert status.version == "1.0.0"
    assert status.uptime_seconds == 3600.0
    assert status.active_trades == 5
    assert status.pending_proposals == 2
    assert status.mode == TradeMode.PAPER
    assert status.api_health is True


@pytest.mark.asyncio
async def test_get_status_authentication_error(
    client: SigmaxClient,
    httpx_mock: HTTPXMock,
) -> None:
    """Test status retrieval with authentication error."""
    httpx_mock.add_response(
        url="http://test-api.sigmax.local/api/status",
        status_code=401,
        text="Unauthorized",
    )

    with pytest.raises(SigmaxAuthenticationError) as exc_info:
        await client.get_status()

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_status_rate_limit(
    client: SigmaxClient,
    httpx_mock: HTTPXMock,
) -> None:
    """Test status retrieval with rate limit."""
    httpx_mock.add_response(
        url="http://test-api.sigmax.local/api/status",
        status_code=429,
        headers={"Retry-After": "60"},
        text="Rate limit exceeded",
    )

    with pytest.raises(SigmaxRateLimitError) as exc_info:
        await client.get_status()

    assert exc_info.value.status_code == 429
    assert exc_info.value.retry_after == 60


@pytest.mark.asyncio
async def test_propose_trade_success(
    client: SigmaxClient,
    httpx_mock: HTTPXMock,
) -> None:
    """Test successful trade proposal creation."""
    httpx_mock.add_response(
        url="http://test-api.sigmax.local/api/chat/proposals",
        json={
            "proposal": {
                "proposal_id": "prop_123",
                "symbol": "BTC/USDT",
                "side": "buy",
                "size": "0.1",
                "price": "50000.00",
                "stop_loss": "48000.00",
                "take_profit": "55000.00",
                "status": "pending",
                "risk_profile": "moderate",
                "mode": "paper",
                "rationale": "Strong bullish signal",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        },
    )

    proposal = await client.propose_trade(
        symbol="BTC/USDT",
        risk_profile=RiskProfile.MODERATE,
        mode=TradeMode.PAPER,
        size=0.1,
    )

    assert isinstance(proposal, TradeProposal)
    assert proposal.proposal_id == "prop_123"
    assert proposal.symbol == "BTC/USDT"
    assert proposal.side == "buy"
    assert proposal.size == Decimal("0.1")
    assert proposal.status == ProposalStatus.PENDING


@pytest.mark.asyncio
async def test_propose_trade_validation_error(
    client: SigmaxClient,
    httpx_mock: HTTPXMock,
) -> None:
    """Test trade proposal with validation error."""
    httpx_mock.add_response(
        url="http://test-api.sigmax.local/api/chat/proposals",
        status_code=422,
        json={
            "detail": [
                {
                    "loc": ["body", "symbol"],
                    "msg": "Invalid symbol format",
                    "type": "value_error",
                }
            ]
        },
    )

    with pytest.raises(SigmaxValidationError):
        await client.propose_trade(symbol="INVALID")


@pytest.mark.asyncio
async def test_list_proposals_success(
    client: SigmaxClient,
    httpx_mock: HTTPXMock,
) -> None:
    """Test successful proposal listing."""
    httpx_mock.add_response(
        url="http://test-api.sigmax.local/api/chat/proposals",
        json={
            "proposals": {
                "prop_1": {
                    "proposal_id": "prop_1",
                    "symbol": "BTC/USDT",
                    "side": "buy",
                    "size": "0.1",
                    "status": "pending",
                    "risk_profile": "conservative",
                    "mode": "paper",
                    "rationale": "Test",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                },
                "prop_2": {
                    "proposal_id": "prop_2",
                    "symbol": "ETH/USDT",
                    "side": "sell",
                    "size": "1.0",
                    "status": "approved",
                    "risk_profile": "moderate",
                    "mode": "paper",
                    "rationale": "Test 2",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                },
            }
        },
    )

    proposals = await client.list_proposals()

    assert len(proposals) == 2
    assert "prop_1" in proposals
    assert "prop_2" in proposals
    assert proposals["prop_1"].symbol == "BTC/USDT"
    assert proposals["prop_2"].symbol == "ETH/USDT"


@pytest.mark.asyncio
async def test_get_proposal_success(
    client: SigmaxClient,
    httpx_mock: HTTPXMock,
) -> None:
    """Test successful proposal retrieval."""
    httpx_mock.add_response(
        url="http://test-api.sigmax.local/api/chat/proposals/prop_123",
        json={
            "proposal_id": "prop_123",
            "symbol": "BTC/USDT",
            "side": "buy",
            "size": "0.1",
            "status": "approved",
            "risk_profile": "moderate",
            "mode": "paper",
            "rationale": "Test proposal",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        },
    )

    proposal = await client.get_proposal("prop_123")

    assert proposal.proposal_id == "prop_123"
    assert proposal.status == ProposalStatus.APPROVED


@pytest.mark.asyncio
async def test_approve_proposal_success(
    client: SigmaxClient,
    httpx_mock: HTTPXMock,
) -> None:
    """Test successful proposal approval."""
    httpx_mock.add_response(
        url="http://test-api.sigmax.local/api/chat/proposals/prop_123/approve",
        json={"success": True, "message": "Proposal approved"},
    )

    result = await client.approve_proposal("prop_123")

    assert result["success"] is True
    assert "message" in result


@pytest.mark.asyncio
async def test_execute_proposal_success(
    client: SigmaxClient,
    httpx_mock: HTTPXMock,
) -> None:
    """Test successful proposal execution."""
    httpx_mock.add_response(
        url="http://test-api.sigmax.local/api/chat/proposals/prop_123/execute",
        json={
            "success": True,
            "trade_id": "trade_456",
            "message": "Trade executed",
        },
    )

    result = await client.execute_proposal("prop_123")

    assert result["success"] is True
    assert result["trade_id"] == "trade_456"


@pytest.mark.asyncio
async def test_execute_proposal_api_error(
    client: SigmaxClient,
    httpx_mock: HTTPXMock,
) -> None:
    """Test proposal execution with API error."""
    httpx_mock.add_response(
        url="http://test-api.sigmax.local/api/chat/proposals/prop_123/execute",
        status_code=400,
        json={"error": "Proposal not approved"},
    )

    with pytest.raises(SigmaxValidationError):
        await client.execute_proposal("prop_123")


@pytest.mark.asyncio
async def test_close_client(client: SigmaxClient) -> None:
    """Test client cleanup."""
    async with client:
        assert client._client is not None

    # Client should be closed after context exit
    # Note: httpx doesn't expose is_closed, so we just verify _client is None
    await client.close()
    assert client._client is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
