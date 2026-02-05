import pytest

from core.modules.chain_data import ChainDataModule


@pytest.mark.asyncio
async def test_chain_data_snapshot_empty():
    module = ChainDataModule(chains=[])
    await module.initialize()
    snapshot = await module.get_onchain_snapshot()
    assert snapshot == {}


@pytest.mark.asyncio
async def test_chain_data_snapshot(monkeypatch):
    monkeypatch.setenv("CHAIN_RPC_EVM", "http://example-evm")
    monkeypatch.setenv("CHAIN_RPC_SOLANA", "http://example-solana")

    module = ChainDataModule(chains=["evm", "solana"])

    def fake_post_json(url, payload):
        if payload.get("method") == "eth_getBlockByNumber":
            return {
                "result": {
                    "number": "0x10",
                    "baseFeePerGas": "0x1",
                    "timestamp": "0x0"
                }
            }
        if payload.get("method") == "getSlot":
            return {"result": 123}
        return {}

    module._post_json = fake_post_json

    await module.initialize()
    snapshot = await module.get_onchain_snapshot()

    assert snapshot["evm"]["latest_block"] == 16
    assert snapshot["evm"]["base_fee_wei"] == 1
    assert snapshot["solana"]["latest_slot"] == 123
