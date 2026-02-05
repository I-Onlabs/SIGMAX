import pytest

from core.modules.lean_execution import LeanExecutionModule


@pytest.mark.asyncio
async def test_lean_execution_unconfigured():
    module = LeanExecutionModule(mode="paper")
    await module.initialize()

    status = await module.get_status()
    assert status["available"] is False
    assert status["backend"] == "lean"

    result = await module.execute_trade("BTC/USDT", "buy", 1.0, 100.0)
    assert result["success"] is False
    assert "LEAN bridge not configured" in result["error"]

    close_result = await module.close_all_positions()
    assert close_result["success"] is False
    assert "LEAN bridge not configured" in close_result["error"]
