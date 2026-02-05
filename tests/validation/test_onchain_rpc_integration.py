import pytest

from core.agents.sentiment import SentimentAgent


@pytest.mark.asyncio
async def test_onchain_rpc_adjustment(monkeypatch):
    agent = SentimentAgent(llm=None)

    rpc_snapshot = {
        "evm": {"rpc_latency_ms": 1500},
        "solana": {"rpc_latency_ms": 1200}
    }

    result = await agent._analyze_onchain("BTC/USDT", rpc_snapshot=rpc_snapshot)

    assert result["rpc_snapshot"] == rpc_snapshot
    assert result["rpc_adjustment"] <= 0
    assert -1.0 <= result["score"] <= 1.0


@pytest.mark.asyncio
async def test_onchain_rpc_adjustment_positive(monkeypatch):
    agent = SentimentAgent(llm=None)

    rpc_snapshot = {
        "evm": {"rpc_latency_ms": 100},
        "solana": {"rpc_latency_ms": 120}
    }

    result = await agent._analyze_onchain("BTC/USDT", rpc_snapshot=rpc_snapshot)

    assert result["rpc_snapshot"] == rpc_snapshot
    assert result["rpc_adjustment"] >= 0
