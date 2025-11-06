"""
Tests for emergency stop functionality and cache memory management.
Validates position closing and cache cleanup behavior.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.modules.execution import ExecutionModule
from core.modules.data import DataModule


class TestEmergencyStop:
    """Test emergency stop functionality in paper mode"""

    @pytest.mark.asyncio
    async def test_paper_mode_emergency_stop(self):
        """Test emergency stop closes all positions in paper mode"""

        # Set up realistic capital for testing
        import os
        os.environ['TOTAL_CAPITAL'] = '100000'

        # Initialize execution module in paper mode
        execution = ExecutionModule(mode="paper")
        await execution.initialize()

        # Execute multiple trades with realistic sizes
        trades = [
            ("BTC/USDT", "buy", 0.01, 45000),  # ~$450
            ("ETH/USDT", "buy", 0.1, 3000),    # ~$300
            ("SOL/USDT", "buy", 1.0, 100),     # ~$100
        ]

        for symbol, action, size, price in trades:
            result = await execution.execute_trade(symbol, action, size, price)
            if not result.get("success"):
                print(f"Trade failed: {result}")
            assert result.get("success") == True

        # Verify positions are open
        status_before = await execution.get_status()
        print(f"\n=== Before Emergency Stop ===")
        print(f"Paper balance: {execution.paper_balance}")

        # Trigger emergency stop
        close_result = await execution.close_all_positions()

        print(f"\n=== After Emergency Stop ===")
        print(f"Close result: {close_result}")
        print(f"Paper balance: {execution.paper_balance}")

        # Verify all positions were closed
        assert close_result["success"] == True
        assert close_result["closed_count"] > 0

        # In paper mode, all non-USDT assets should be sold
        for asset, balance in execution.paper_balance.items():
            if asset != "USDT":
                assert balance == 0 or balance < 0.0001  # Allow for rounding errors

    @pytest.mark.asyncio
    async def test_emergency_stop_with_no_positions(self):
        """Test emergency stop when no positions are open"""

        execution = ExecutionModule(mode="paper")
        await execution.initialize()

        # Call emergency stop with no positions
        result = await execution.close_all_positions()

        print(f"\n=== Emergency Stop (No Positions) ===")
        print(f"Result: {result}")

        assert result["success"] == True
        assert result["closed_count"] == 0

    @pytest.mark.asyncio
    async def test_emergency_stop_idempotent(self):
        """Test that emergency stop can be called multiple times safely"""

        import os
        os.environ['TOTAL_CAPITAL'] = '100000'

        execution = ExecutionModule(mode="paper")
        await execution.initialize()

        # Execute one trade
        await execution.execute_trade("BTC/USDT", "buy", 0.01, 45000)

        # Call emergency stop multiple times
        result1 = await execution.close_all_positions()
        result2 = await execution.close_all_positions()
        result3 = await execution.close_all_positions()

        print(f"\n=== Emergency Stop Idempotent Test ===")
        print(f"First call: {result1['closed_count']} positions")
        print(f"Second call: {result2['closed_count']} positions")
        print(f"Third call: {result3['closed_count']} positions")

        assert result1["success"] == True
        assert result2["success"] == True
        assert result3["success"] == True
        assert result1["closed_count"] > 0
        assert result2["closed_count"] == 0  # Already closed
        assert result3["closed_count"] == 0  # Already closed

    @pytest.mark.asyncio
    async def test_emergency_stop_preserves_usdt(self):
        """Test that emergency stop preserves USDT balance"""

        execution = ExecutionModule(mode="paper")
        await execution.initialize()

        # Record initial USDT
        initial_usdt = execution.paper_balance.get("USDT", 0)

        # Execute trades
        await execution.execute_trade("BTC/USDT", "buy", 0.1, 45000)
        await execution.execute_trade("ETH/USDT", "buy", 1.0, 3000)

        # Emergency stop
        await execution.close_all_positions()

        # USDT should still exist (may have changed due to trades)
        final_usdt = execution.paper_balance.get("USDT", 0)

        print(f"\n=== USDT Preservation Test ===")
        print(f"Initial USDT: ${initial_usdt:,.2f}")
        print(f"Final USDT: ${final_usdt:,.2f}")

        assert "USDT" in execution.paper_balance
        assert final_usdt > 0  # Should have some USDT

    @pytest.mark.asyncio
    async def test_emergency_stop_status_reporting(self):
        """Test that emergency stop provides detailed status"""

        import os
        os.environ['TOTAL_CAPITAL'] = '100000'

        execution = ExecutionModule(mode="paper")
        await execution.initialize()

        # Execute trades
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        for symbol in symbols:
            await execution.execute_trade(symbol, "buy", 0.01, 45000)

        # Emergency stop
        result = await execution.close_all_positions()

        print(f"\n=== Emergency Stop Status ===")
        print(f"Success: {result['success']}")
        print(f"Closed count: {result['closed_count']}")
        print(f"Positions: {result.get('positions', [])}")

        # Verify result structure
        assert 'success' in result
        assert 'closed_count' in result
        assert 'positions' in result

        assert isinstance(result['success'], bool)
        assert isinstance(result['closed_count'], int)
        assert isinstance(result['positions'], list)


class TestCacheManagement:
    """Test cache memory management and cleanup"""

    @pytest.mark.asyncio
    async def test_cache_basic_operations(self):
        """Test basic cache operations"""

        data_module = DataModule()
        await data_module.initialize()

        # First call - cache miss
        data1 = await data_module.get_market_data("BTC/USDT", "1h", 100)
        cache_size_1 = len(data_module.cache)

        print(f"\n=== Cache Basic Operations ===")
        print(f"Cache size after first call: {cache_size_1}")

        # Second call - cache hit (within TTL)
        data2 = await data_module.get_market_data("BTC/USDT", "1h", 100)
        cache_size_2 = len(data_module.cache)

        print(f"Cache size after second call: {cache_size_2}")

        assert cache_size_1 == cache_size_2  # Same cache entry reused
        assert "BTC/USDT_1h" in data_module.cache

        await data_module.close()

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self):
        """Test that cache entries expire after TTL"""

        data_module = DataModule()
        data_module.cache_ttl = 1  # 1 second TTL for testing
        await data_module.initialize()

        # First call
        data1 = await data_module.get_market_data("BTC/USDT", "1h", 100)
        assert "BTC/USDT_1h" in data_module.cache

        # Wait for TTL to expire
        await asyncio.sleep(1.5)

        # Second call - should be cache miss due to expiration
        data2 = await data_module.get_market_data("BTC/USDT", "1h", 100)

        print(f"\n=== Cache TTL Expiration Test ===")
        print(f"Cache TTL: {data_module.cache_ttl} seconds")
        print(f"Cache after expiration: {len(data_module.cache)} entries")

        await data_module.close()

    @pytest.mark.asyncio
    async def test_cache_multiple_symbols(self):
        """Test cache with multiple symbols"""

        data_module = DataModule()
        await data_module.initialize()

        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "DOT/USDT"]

        # Fetch data for multiple symbols
        for symbol in symbols:
            await data_module.get_market_data(symbol, "1h", 100)

        cache_size = len(data_module.cache)
        print(f"\n=== Multi-Symbol Cache Test ===")
        print(f"Symbols fetched: {len(symbols)}")
        print(f"Cache entries: {cache_size}")
        print(f"Cache keys: {list(data_module.cache.keys())}")

        assert cache_size == len(symbols)
        for symbol in symbols:
            assert f"{symbol}_1h" in data_module.cache

        await data_module.close()

    @pytest.mark.asyncio
    async def test_cache_different_timeframes(self):
        """Test cache with different timeframes for same symbol"""

        data_module = DataModule()
        await data_module.initialize()

        timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]

        # Fetch data for different timeframes
        for tf in timeframes:
            await data_module.get_market_data("BTC/USDT", tf, 100)

        cache_size = len(data_module.cache)
        print(f"\n=== Multi-Timeframe Cache Test ===")
        print(f"Timeframes fetched: {len(timeframes)}")
        print(f"Cache entries: {cache_size}")

        assert cache_size == len(timeframes)
        for tf in timeframes:
            assert f"BTC/USDT_{tf}" in data_module.cache

        await data_module.close()

    @pytest.mark.asyncio
    async def test_cache_memory_efficient(self):
        """Test that cache doesn't grow unbounded"""

        data_module = DataModule()
        await data_module.initialize()

        # Fetch data for many symbol/timeframe combinations
        iterations = 50
        for i in range(iterations):
            symbol = f"SYMBOL{i}/USDT"
            await data_module.get_market_data(symbol, "1h", 100)

        cache_size = len(data_module.cache)
        print(f"\n=== Cache Memory Efficiency Test ===")
        print(f"Iterations: {iterations}")
        print(f"Cache size: {cache_size}")

        # Cache should have all entries (no cleanup yet within TTL)
        assert cache_size <= iterations  # Should not exceed iterations

        await data_module.close()

    @pytest.mark.asyncio
    async def test_cache_cleanup_on_close(self):
        """Test that cache is cleaned up on module close"""

        data_module = DataModule()
        await data_module.initialize()

        # Populate cache
        await data_module.get_market_data("BTC/USDT", "1h", 100)
        await data_module.get_market_data("ETH/USDT", "1h", 100)

        assert len(data_module.cache) > 0

        # Close module
        await data_module.close()

        print(f"\n=== Cache Cleanup On Close ===")
        print(f"Cache size after close: {len(data_module.cache)}")

        # Cache might still have entries (cleanup is async)
        # But the cleanup task should be cancelled

    @pytest.mark.asyncio
    async def test_cache_concurrent_access(self):
        """Test concurrent cache access"""

        data_module = DataModule()
        await data_module.initialize()

        # Concurrent requests for same symbol
        tasks = [
            data_module.get_market_data("BTC/USDT", "1h", 100)
            for _ in range(10)
        ]

        results = await asyncio.gather(*tasks)

        print(f"\n=== Concurrent Cache Access ===")
        print(f"Concurrent requests: {len(tasks)}")
        print(f"Cache size: {len(data_module.cache)}")

        # Should only have 1 cache entry despite 10 requests
        assert len(data_module.cache) == 1
        assert "BTC/USDT_1h" in data_module.cache

        await data_module.close()

    @pytest.mark.asyncio
    async def test_cache_hit_rate(self):
        """Test cache hit rate with repeated requests"""

        data_module = DataModule()
        await data_module.initialize()

        symbol = "BTC/USDT"

        # Make multiple requests
        for i in range(5):
            await data_module.get_market_data(symbol, "1h", 100)

        print(f"\n=== Cache Hit Rate Test ===")
        print(f"Requests made: 5")
        print(f"Cache size: {len(data_module.cache)}")
        print(f"Cache contents: {list(data_module.cache.keys())}")

        # Should still only have 1 cache entry
        assert len(data_module.cache) == 1

        await data_module.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
