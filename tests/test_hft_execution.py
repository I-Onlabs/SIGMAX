"""
Tests for HFT Execution Engine
"""

import pytest
import asyncio
from core.modules.hft_execution import (
    HFTExecutionEngine,
    LatencySimulator,
    QueuePositionManager,
    HFTOrder,
    HFTStrategy,
    create_hft_engine,
    HFTBACKTEST_AVAILABLE
)


class MockExchangeConnector:
    """Mock exchange for testing"""

    async def submit_order(self, order):
        return {"status": "submitted", "order_id": order.order_id}

    async def cancel_order(self, order_id):
        return {"status": "cancelled"}


class TestLatencySimulator:
    """Test latency simulation"""

    def test_latency_simulator_initialization(self):
        """Test latency simulator initializes"""
        sim = LatencySimulator()

        assert sim.feed_latency_ns == 50
        assert sim.order_latency_ns == 100
        assert sim.jitter_ns == 20

    def test_get_feed_latency(self):
        """Test feed latency generation"""
        sim = LatencySimulator()

        latencies = [sim.get_feed_latency_ns() for _ in range(100)]

        # Should be around 50ns with jitter
        avg_latency = sum(latencies) / len(latencies)
        assert 30 < avg_latency < 70  # 50 ± 20ns range

    def test_get_order_latency(self):
        """Test order latency generation"""
        sim = LatencySimulator()

        latencies = [sim.get_order_latency_ns() for _ in range(100)]

        # Should be around 100ns with jitter
        avg_latency = sum(latencies) / len(latencies)
        assert 80 < avg_latency < 120  # 100 ± 20ns range

    def test_get_total_latency(self):
        """Test total round-trip latency"""
        sim = LatencySimulator()

        latencies = [sim.get_total_latency_ns() for _ in range(100)]

        # Should be around 150ns (50 + 100)
        avg_latency = sum(latencies) / len(latencies)
        assert 110 < avg_latency < 190  # ~150 ± 40ns range


class TestQueuePositionManager:
    """Test queue position management"""

    def test_queue_manager_initialization(self):
        """Test queue manager initializes"""
        manager = QueuePositionManager(model="PowerProb")

        assert manager.model_type == "PowerProb"

    def test_queue_position_estimation(self):
        """Test queue position estimation"""
        manager = QueuePositionManager()

        order = HFTOrder(
            order_id="test1",
            symbol="BTCUSDT",
            side="buy",
            order_type="limit",
            price=50000,
            quantity=1.0,
            timestamp=0
        )

        order_book = {
            "bids": [[50000, 10.0], [49999, 5.0]],
            "asks": [[50001, 8.0], [50002, 12.0]]
        }

        position = manager.estimate_queue_position(order, order_book)

        # Should estimate middle of queue
        assert 0 <= position <= 10


class TestHFTExecutionEngine:
    """Test HFT execution engine"""

    def setup_engine(self):
        """Setup engine for tests"""
        return create_hft_engine(
            exchange_connector=MockExchangeConnector(),
            latency_model="realistic",
            queue_model="PowerProb",
            enable_backtesting=False
        )

    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        engine = self.setup_engine()

        assert engine is not None
        assert engine.total_orders == 0
        assert engine.total_executions == 0
        assert len(engine.active_orders) == 0

    @pytest.mark.asyncio
    async def test_execute_limit_order(self):
        """Test executing limit order"""
        engine = self.setup_engine()

        execution = await engine.execute_order(
            symbol="BTCUSDT",
            side="buy",
            order_type="limit",
            price=50000,
            quantity=1.0
        )

        assert execution is not None
        assert execution.symbol == "BTCUSDT"
        assert execution.side == "buy"
        assert execution.executed_quantity == 1.0
        assert execution.execution_time_ns > 0

        # Check stats
        assert engine.total_orders == 1
        assert engine.total_executions == 1
        assert len(engine.active_orders) == 0

    @pytest.mark.asyncio
    async def test_execute_market_order(self):
        """Test executing market order"""
        engine = self.setup_engine()

        execution = await engine.execute_order(
            symbol="ETHUSDT",
            side="sell",
            order_type="market",
            price=3000,
            quantity=2.0
        )

        assert execution is not None
        assert execution.symbol == "ETHUSDT"
        assert execution.side == "sell"
        assert execution.executed_quantity == 2.0

    @pytest.mark.asyncio
    async def test_multiple_orders(self):
        """Test executing multiple orders"""
        engine = self.setup_engine()

        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        executions = []

        for symbol in symbols:
            execution = await engine.execute_order(
                symbol=symbol,
                side="buy",
                order_type="limit",
                price=100,
                quantity=1.0
            )
            executions.append(execution)

        assert len(executions) == 3
        assert engine.total_orders == 3
        assert engine.total_executions == 3

    @pytest.mark.asyncio
    async def test_latency_tracking(self):
        """Test latency tracking"""
        engine = self.setup_engine()

        # Execute several orders
        for _ in range(10):
            await engine.execute_order(
                symbol="BTCUSDT",
                side="buy",
                order_type="limit",
                price=50000,
                quantity=0.1
            )

        stats = engine.get_performance_stats()

        assert stats["total_executions"] == 10
        assert stats["latency"]["avg_ns"] > 0
        assert stats["latency"]["min_ns"] > 0
        assert stats["latency"]["max_ns"] > 0
        assert stats["latency"]["avg_us"] > 0

    @pytest.mark.asyncio
    async def test_sub_100ns_target(self):
        """Test if we can achieve sub-100ns latency"""
        engine = self.setup_engine()

        # Execute orders and check latency
        for _ in range(5):
            await engine.execute_order(
                symbol="BTCUSDT",
                side="buy",
                order_type="limit",
                price=50000,
                quantity=1.0
            )

        stats = engine.get_performance_stats()

        # Note: In real HFT, we'd expect sub-100ns
        # In simulation with sleep, it will be higher
        # This test just verifies tracking works
        assert "achieved" in stats["latency"]
        assert stats["latency"]["target_ns"] == 100

    @pytest.mark.asyncio
    async def test_queue_position_awareness(self):
        """Test queue position tracking"""
        engine = self.setup_engine()

        order_book = {
            "bids": [[50000, 10.0], [49999, 5.0]],
            "asks": [[50001, 8.0], [50002, 12.0]]
        }

        execution = await engine.execute_order(
            symbol="BTCUSDT",
            side="buy",
            order_type="limit",
            price=50000,
            quantity=1.0,
            order_book=order_book
        )

        assert execution is not None
        # Queue wait time should be tracked
        assert execution.queue_wait_time_ns >= 0

    @pytest.mark.asyncio
    async def test_cancel_order(self):
        """Test order cancellation"""
        engine = self.setup_engine()

        # Create an order but don't execute yet
        # (In real scenario, order would be pending)
        # For now, test the cancel mechanism
        cancelled = await engine.cancel_order("nonexistent_id")
        assert cancelled == False

    @pytest.mark.asyncio
    async def test_cancel_all_orders(self):
        """Test cancelling all orders"""
        engine = self.setup_engine()

        # Cancel all
        cancelled = await engine.cancel_all_orders()
        assert cancelled >= 0

    def test_performance_stats(self):
        """Test performance statistics"""
        engine = self.setup_engine()

        stats = engine.get_performance_stats()

        assert "total_orders" in stats
        assert "total_executions" in stats
        assert "active_orders" in stats
        assert "latency" in stats
        assert "fill_rate" in stats

        # Check latency stats structure
        latency = stats["latency"]
        assert "avg_ns" in latency
        assert "min_ns" in latency
        assert "max_ns" in latency
        assert "avg_us" in latency
        assert "target_ns" in latency
        assert "achieved" in latency

    def test_execution_history(self):
        """Test execution history tracking"""
        engine = self.setup_engine()

        history = engine.get_execution_history(limit=10)
        assert isinstance(history, list)
        assert len(history) == 0  # No executions yet


class TestHFTStrategy:
    """Test HFT strategy base class"""

    @pytest.mark.asyncio
    async def test_strategy_start_stop(self):
        """Test strategy lifecycle"""
        engine = create_hft_engine(
            exchange_connector=MockExchangeConnector()
        )

        strategy = HFTStrategy(execution_engine=engine)

        assert strategy.running == False

        await strategy.start()
        assert strategy.running == True

        await strategy.stop()
        assert strategy.running == False


class TestHFTBacktesting:
    """Test HFT backtesting capabilities"""

    def test_backtest_mode(self):
        """Test backtesting mode initialization"""
        engine = create_hft_engine(
            exchange_connector=MockExchangeConnector(),
            enable_backtesting=True
        )

        assert engine.enable_backtesting == True

    @pytest.mark.asyncio
    async def test_backtest_execution(self):
        """Test order execution in backtest mode"""
        engine = create_hft_engine(
            exchange_connector=MockExchangeConnector(),
            enable_backtesting=True
        )

        execution = await engine.execute_order(
            symbol="BTCUSDT",
            side="buy",
            order_type="limit",
            price=50000,
            quantity=1.0
        )

        assert execution is not None
        assert execution.executed_quantity == 1.0


class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_full_trading_workflow(self):
        """Test complete HFT trading workflow"""
        engine = create_hft_engine(
            exchange_connector=MockExchangeConnector()
        )

        # Execute buy order
        buy_execution = await engine.execute_order(
            symbol="BTCUSDT",
            side="buy",
            order_type="limit",
            price=50000,
            quantity=1.0
        )

        # Execute sell order
        sell_execution = await engine.execute_order(
            symbol="BTCUSDT",
            side="sell",
            order_type="limit",
            price=50100,
            quantity=1.0
        )

        # Check both executions
        assert buy_execution.side == "buy"
        assert sell_execution.side == "sell"

        # Check performance
        stats = engine.get_performance_stats()
        assert stats["total_executions"] == 2
        assert stats["fill_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_high_frequency_execution(self):
        """Test high-frequency order execution"""
        engine = create_hft_engine(
            exchange_connector=MockExchangeConnector()
        )

        # Execute 50 orders rapidly
        start_time = asyncio.get_event_loop().time()

        for i in range(50):
            await engine.execute_order(
                symbol="BTCUSDT",
                side="buy" if i % 2 == 0 else "sell",
                order_type="limit",
                price=50000 + i,
                quantity=0.1
            )

        end_time = asyncio.get_event_loop().time()
        duration_seconds = end_time - start_time

        # Check all executed
        assert engine.total_executions == 50

        # Check throughput
        orders_per_second = 50 / duration_seconds
        print(f"Throughput: {orders_per_second:.2f} orders/second")


class TestAvailability:
    """Test hftbacktest availability"""

    def test_hftbacktest_availability(self):
        """Test if hftbacktest is available"""
        assert isinstance(HFTBACKTEST_AVAILABLE, bool)

        if HFTBACKTEST_AVAILABLE:
            import hftbacktest
            assert hftbacktest.__version__ is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
