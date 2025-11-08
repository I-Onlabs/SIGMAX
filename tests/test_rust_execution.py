"""Tests for Rust Execution Engine"""
import pytest
from core.modules.rust_execution import (
    RustExecutionEngine, RustExecution, execute_batch, benchmark_latency, RUST_MODULE_AVAILABLE
)

class TestRustExecutionEngine:
    def test_engine_initialization(self):
        engine = RustExecutionEngine(queue_capacity=1000)
        assert engine is not None

    def test_execute_single_order(self):
        engine = RustExecutionEngine()
        execution = engine.execute_order(1, 0, 0, 50000.0, 1.0)
        assert isinstance(execution, RustExecution)
        assert execution.order_id >= 0
        assert execution.executed_price == 50000.0
        assert execution.latency_ns > 0

    def test_get_stats(self):
        engine = RustExecutionEngine()
        for _ in range(5):
            engine.execute_order(1, 0, 0, 50000.0, 1.0)
        stats = engine.get_stats()
        assert stats["total_executions"] == 5

    def test_benchmark(self):
        results = benchmark_latency(iterations=100)
        assert results["iterations"] == 100
        assert results["avg_ns"] > 0

    def test_batch_execution(self):
        engine = RustExecutionEngine()
        orders = [(1, 0, 0, 50000.0, 1.0) for _ in range(10)]
        executions = execute_batch(engine, orders)
        assert len(executions) == 10

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
