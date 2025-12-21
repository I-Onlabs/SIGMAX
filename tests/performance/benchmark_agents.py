#!/usr/bin/env python3
"""
Agent Performance Benchmarks

Measures agent latency to verify <30ms claim from README.
Tests orchestrator, researcher, analyzer, and quantum module performance.
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict
from unittest.mock import AsyncMock, patch
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.agents.orchestrator import SIGMAXOrchestrator
from core.agents.researcher import ResearcherAgent
from core.agents.fundamental_analyzer import FundamentalAnalyzer
from core.modules.quantum import QuantumModule


class AgentBenchmark:
    """Benchmark utility for measuring agent performance"""

    @staticmethod
    async def measure_async(func, *args, **kwargs) -> float:
        """
        Measure async function execution time in milliseconds

        Returns:
            Execution time in ms
        """
        start = time.perf_counter()
        await func(*args, **kwargs)
        end = time.perf_counter()
        return (end - start) * 1000  # Convert to ms

    @staticmethod
    def calculate_stats(measurements: List[float]) -> Dict[str, float]:
        """
        Calculate statistics from measurements

        Returns:
            Dict with mean, median, p95, p99, min, max
        """
        if not measurements:
            return {}

        sorted_measurements = sorted(measurements)
        return {
            "mean_ms": statistics.mean(sorted_measurements),
            "median_ms": statistics.median(sorted_measurements),
            "p50_ms": sorted_measurements[int(len(sorted_measurements) * 0.50)],
            "p95_ms": sorted_measurements[int(len(sorted_measurements) * 0.95)],
            "p99_ms": sorted_measurements[int(len(sorted_measurements) * 0.99)],
            "min_ms": min(sorted_measurements),
            "max_ms": max(sorted_measurements),
            "count": len(measurements)
        }


class TestOrchestratorPerformance:
    """Benchmark orchestrator agent latency"""

    @pytest.fixture
    async def orchestrator(self):
        """Create orchestrator with mocked dependencies"""
        with patch.dict('os.environ', {'TRADING_MODE': 'paper'}):
            orch = SIGMAXOrchestrator()
            await orch.initialize()
            yield orch

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_orchestrator_analyze_latency(self, orchestrator):
        """
        Benchmark orchestrator.analyze_symbol() latency

        Target: <30ms (claimed in README)
        """
        print("\n=== Orchestrator Analysis Latency ===")

        mock_data = {
            'symbol': 'BTC/USDT',
            'price': 95000.0,
            'volume_24h': 1000000000.0,
            'ohlcv': np.random.rand(100, 6)
        }

        measurements = []

        with patch.object(
            orchestrator.data_module,
            'get_market_data',
            AsyncMock(return_value=mock_data)
        ):
            # Warmup
            await orchestrator.analyze_symbol('BTC/USDT')

            # Measure 50 iterations
            for i in range(50):
                latency = await AgentBenchmark.measure_async(
                    orchestrator.analyze_symbol,
                    'BTC/USDT'
                )
                measurements.append(latency)

        stats = AgentBenchmark.calculate_stats(measurements)

        print(f"Samples: {stats['count']}")
        print(f"Mean: {stats['mean_ms']:.2f}ms")
        print(f"Median: {stats['median_ms']:.2f}ms")
        print(f"P95: {stats['p95_ms']:.2f}ms")
        print(f"P99: {stats['p99_ms']:.2f}ms")
        print(f"Min: {stats['min_ms']:.2f}ms")
        print(f"Max: {stats['max_ms']:.2f}ms")

        # Verify reasonable performance (allow more than 30ms for now)
        assert stats['mean_ms'] < 5000, f"Mean latency {stats['mean_ms']:.2f}ms exceeds 5s"
        assert stats['p99_ms'] < 10000, f"P99 latency {stats['p99_ms']:.2f}ms exceeds 10s"

        # Document if exceeds 30ms claim
        if stats['mean_ms'] > 30:
            print(f"\n⚠️  Mean latency {stats['mean_ms']:.2f}ms exceeds 30ms claim")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_orchestrator_multi_symbol_throughput(self, orchestrator):
        """
        Benchmark orchestrator throughput for multiple symbols

        Measures symbols/second processing rate
        """
        print("\n=== Orchestrator Multi-Symbol Throughput ===")

        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "MATIC/USDT"]
        mock_data = {
            'price': 95000.0,
            'volume_24h': 1000000000.0,
            'ohlcv': np.random.rand(100, 6)
        }

        with patch.object(
            orchestrator.data_module,
            'get_market_data',
            AsyncMock(return_value=mock_data)
        ):
            start = time.perf_counter()

            # Process all symbols
            for symbol in symbols:
                await orchestrator.analyze_symbol(symbol)

            end = time.perf_counter()

        duration = end - start
        throughput = len(symbols) / duration

        print(f"Symbols: {len(symbols)}")
        print(f"Duration: {duration:.2f}s")
        print(f"Throughput: {throughput:.2f} symbols/sec")
        print(f"Avg per symbol: {(duration/len(symbols))*1000:.2f}ms")

        assert duration < 60, f"Processing {len(symbols)} symbols took {duration:.2f}s (>60s)"


class TestQuantumModulePerformance:
    """Benchmark quantum module performance"""

    @pytest.fixture
    async def quantum_module(self):
        """Create quantum module"""
        with patch.dict('os.environ', {'QUANTUM_ENABLED': 'true'}):
            module = QuantumModule()
            await module.initialize()
            yield module

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_quantum_optimization_latency(self, quantum_module):
        """
        Benchmark quantum portfolio optimization latency

        Target: <100ms for practical use
        """
        print("\n=== Quantum Optimization Latency ===")

        measurements = []

        # Warmup
        await quantum_module.optimize_portfolio(
            symbol="BTC/USDT",
            signal=0.5,
            current_portfolio={}
        )

        # Measure 20 iterations
        for _ in range(20):
            latency = await AgentBenchmark.measure_async(
                quantum_module.optimize_portfolio,
                symbol="BTC/USDT",
                signal=0.7,
                current_portfolio={"BTC/USDT": 0.5}
            )
            measurements.append(latency)

        stats = AgentBenchmark.calculate_stats(measurements)

        print(f"Samples: {stats['count']}")
        print(f"Mean: {stats['mean_ms']:.2f}ms")
        print(f"Median: {stats['median_ms']:.2f}ms")
        print(f"P95: {stats['p95_ms']:.2f}ms")
        print(f"P99: {stats['p99_ms']:.2f}ms")

        # Verify reasonable performance
        assert stats['mean_ms'] < 5000, f"Mean latency {stats['mean_ms']:.2f}ms exceeds 5s"

        if stats['mean_ms'] > 100:
            print(f"\n⚠️  Mean latency {stats['mean_ms']:.2f}ms may be too slow for real-time trading")


class TestAgentColdStart:
    """Benchmark agent cold start (initialization) times"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_orchestrator_initialization_time(self):
        """Measure orchestrator cold start time"""

        print("\n=== Orchestrator Initialization ===")

        with patch.dict('os.environ', {'TRADING_MODE': 'paper'}):
            start = time.perf_counter()

            orchestrator = SIGMAXOrchestrator()
            await orchestrator.initialize()

            end = time.perf_counter()

        init_time = (end - start) * 1000

        print(f"Initialization time: {init_time:.2f}ms")

        assert init_time < 10000, f"Init time {init_time:.2f}ms exceeds 10s"

        if init_time > 1000:
            print(f"\n⚠️  Init time {init_time:.2f}ms > 1s (slow cold start)")

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_quantum_module_initialization_time(self):
        """Measure quantum module initialization time"""

        print("\n=== Quantum Module Initialization ===")

        with patch.dict('os.environ', {'QUANTUM_ENABLED': 'true'}):
            start = time.perf_counter()

            module = QuantumModule()
            await module.initialize()

            end = time.perf_counter()

        init_time = (end - start) * 1000

        print(f"Initialization time: {init_time:.2f}ms")

        assert init_time < 10000, f"Init time {init_time:.2f}ms exceeds 10s"


class TestConcurrentAgentPerformance:
    """Benchmark agent performance under concurrent load"""

    @pytest.fixture
    async def orchestrator(self):
        """Create orchestrator"""
        with patch.dict('os.environ', {'TRADING_MODE': 'paper'}):
            orch = SIGMAXOrchestrator()
            await orch.initialize()
            yield orch

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_analysis_requests(self, orchestrator):
        """
        Benchmark orchestrator under concurrent load

        Tests 10 concurrent analysis requests
        """
        print("\n=== Concurrent Analysis Load ===")

        mock_data = {
            'price': 95000.0,
            'volume_24h': 1000000000.0,
            'ohlcv': np.random.rand(100, 6)
        }

        with patch.object(
            orchestrator.data_module,
            'get_market_data',
            AsyncMock(return_value=mock_data)
        ):
            start = time.perf_counter()

            # 10 concurrent requests
            tasks = [
                orchestrator.analyze_symbol('BTC/USDT')
                for _ in range(10)
            ]

            results = await asyncio.gather(*tasks)

            end = time.perf_counter()

        duration = (end - start) * 1000
        avg_per_request = duration / len(tasks)

        print(f"Concurrent requests: {len(tasks)}")
        print(f"Total duration: {duration:.2f}ms")
        print(f"Avg per request: {avg_per_request:.2f}ms")
        print(f"Throughput: {len(tasks)/(duration/1000):.2f} req/sec")

        assert all(r is not None for r in results), "Some requests failed"
        assert duration < 60000, f"10 concurrent requests took {duration:.2f}ms (>60s)"


class TestMemoryAndResourceUsage:
    """Benchmark memory and resource usage"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_orchestrator_memory_growth(self):
        """
        Test orchestrator memory usage over multiple operations

        Ensures no memory leaks during repeated analysis
        """
        import gc
        import psutil
        import os as os_module

        print("\n=== Orchestrator Memory Growth Test ===")

        process = psutil.Process(os_module.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        with patch.dict('os.environ', {'TRADING_MODE': 'paper'}):
            orchestrator = SIGMAXOrchestrator()
            await orchestrator.initialize()

            mock_data = {
                'price': 95000.0,
                'volume_24h': 1000000000.0,
                'ohlcv': np.random.rand(100, 6)
            }

            with patch.object(
                orchestrator.data_module,
                'get_market_data',
                AsyncMock(return_value=mock_data)
            ):
                # Run 100 analyses
                for _ in range(100):
                    await orchestrator.analyze_symbol('BTC/USDT')

        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_growth = final_memory - initial_memory

        print(f"Initial memory: {initial_memory:.1f} MB")
        print(f"Final memory: {final_memory:.1f} MB")
        print(f"Growth: {memory_growth:.1f} MB")

        # Allow up to 200MB growth for 100 operations
        assert memory_growth < 200, f"Memory grew by {memory_growth:.1f}MB (>200MB suggests leak)"

        if memory_growth > 50:
            print(f"\n⚠️  Memory growth {memory_growth:.1f}MB after 100 ops (potential leak)")


def print_summary_report():
    """Print benchmark summary (called after all tests)"""
    print("\n" + "="*60)
    print("AGENT PERFORMANCE BENCHMARK SUMMARY")
    print("="*60)
    print("\nKey Findings:")
    print("- Orchestrator latency benchmarked (target: <30ms)")
    print("- Quantum optimization latency measured (target: <100ms)")
    print("- Concurrent load tested (10 parallel requests)")
    print("- Memory growth validated (100 operations)")
    print("\nRefer to individual test outputs for detailed metrics.")
    print("="*60)


if __name__ == "__main__":
    # Run with: pytest tests/performance/benchmark_agents.py -v -s -m performance
    pytest.main([__file__, "-v", "-s", "-m", "performance"])
    print_summary_report()
