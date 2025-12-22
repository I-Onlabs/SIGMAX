#!/usr/bin/env python3
"""
SIGMAX Performance Benchmarking Suite
Measures actual performance of core components
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from statistics import mean, median, stdev
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set environment variables
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_DB'] = 'sigmax'
os.environ['POSTGRES_USER'] = 'sigmax'
os.environ['POSTGRES_PASSWORD'] = 'sigmax_dev'


class PerformanceBenchmark:
    """Performance benchmarking framework"""

    def __init__(self):
        self.results: Dict[str, Any] = {}

    def benchmark(self, name: str, func, iterations: int = 100, warmup: int = 10):
        """
        Benchmark a function

        Args:
            name: Benchmark name
            func: Function to benchmark (callable)
            iterations: Number of iterations
            warmup: Number of warmup iterations

        Returns:
            Dict with benchmark statistics
        """
        print(f"\n{'='*70}")
        print(f"Benchmarking: {name}")
        print(f"{'='*70}")

        # Warmup
        print(f"Warmup: {warmup} iterations...")
        for _ in range(warmup):
            func()

        # Benchmark
        print(f"Running: {iterations} iterations...")
        times = []

        for i in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to milliseconds

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{iterations}")

        # Calculate statistics
        stats = {
            "name": name,
            "iterations": iterations,
            "min_ms": min(times),
            "max_ms": max(times),
            "mean_ms": mean(times),
            "median_ms": median(times),
            "stdev_ms": stdev(times) if len(times) > 1 else 0,
            "p95_ms": sorted(times)[int(len(times) * 0.95)],
            "p99_ms": sorted(times)[int(len(times) * 0.99)],
        }

        # Print results
        print(f"\nResults:")
        print(f"  Min:    {stats['min_ms']:.3f} ms")
        print(f"  Max:    {stats['max_ms']:.3f} ms")
        print(f"  Mean:   {stats['mean_ms']:.3f} ms")
        print(f"  Median: {stats['median_ms']:.3f} ms")
        print(f"  StdDev: {stats['stdev_ms']:.3f} ms")
        print(f"  P95:    {stats['p95_ms']:.3f} ms")
        print(f"  P99:    {stats['p99_ms']:.3f} ms")

        self.results[name] = stats
        return stats

    async def benchmark_async(self, name: str, func, iterations: int = 100, warmup: int = 10):
        """Benchmark an async function"""
        print(f"\n{'='*70}")
        print(f"Benchmarking (async): {name}")
        print(f"{'='*70}")

        # Warmup
        print(f"Warmup: {warmup} iterations...")
        for _ in range(warmup):
            await func()

        # Benchmark
        print(f"Running: {iterations} iterations...")
        times = []

        for i in range(iterations):
            start = time.perf_counter()
            await func()
            end = time.perf_counter()
            times.append((end - start) * 1000)

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{iterations}")

        # Calculate statistics
        stats = {
            "name": name,
            "iterations": iterations,
            "min_ms": min(times),
            "max_ms": max(times),
            "mean_ms": mean(times),
            "median_ms": median(times),
            "stdev_ms": stdev(times) if len(times) > 1 else 0,
            "p95_ms": sorted(times)[int(len(times) * 0.95)],
            "p99_ms": sorted(times)[int(len(times) * 0.99)],
        }

        # Print results
        print(f"\nResults:")
        print(f"  Min:    {stats['min_ms']:.3f} ms")
        print(f"  Max:    {stats['max_ms']:.3f} ms")
        print(f"  Mean:   {stats['mean_ms']:.3f} ms")
        print(f"  Median: {stats['median_ms']:.3f} ms")
        print(f"  StdDev: {stats['stdev_ms']:.3f} ms")
        print(f"  P95:    {stats['p95_ms']:.3f} ms")
        print(f"  P99:    {stats['p99_ms']:.3f} ms")

        self.results[name] = stats
        return stats

    def save_results(self, filename: str):
        """Save benchmark results to JSON file"""
        filepath = Path(__file__).parent / filename
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✅ Results saved to: {filepath}")

    def print_summary(self):
        """Print summary of all benchmarks"""
        print(f"\n{'='*70}")
        print("BENCHMARK SUMMARY")
        print(f"{'='*70}\n")

        print(f"{'Benchmark':<40} {'Mean':<12} {'Median':<12} {'P95':<12}")
        print(f"{'-'*40} {'-'*12} {'-'*12} {'-'*12}")

        for name, stats in self.results.items():
            print(f"{name:<40} {stats['mean_ms']:>10.2f}ms {stats['median_ms']:>10.2f}ms {stats['p95_ms']:>10.2f}ms")


def benchmark_decision_history():
    """Benchmark DecisionHistory operations"""
    from core.utils.decision_history import DecisionHistory

    bench = PerformanceBenchmark()
    history = DecisionHistory(use_redis=False, use_postgres=False)  # In-memory only for speed

    # Benchmark: Add decision
    decision = {
        "action": "buy",
        "confidence": 0.75,
        "sentiment": 0.5
    }
    agent_debate = {
        "bull_argument": "Test bull argument",
        "bear_argument": "Test bear argument",
        "research_summary": "Test summary"
    }

    bench.benchmark(
        "DecisionHistory.add_decision (in-memory)",
        lambda: history.add_decision("BTC/USDT", decision, agent_debate),
        iterations=1000
    )

    # Benchmark: Get last decision
    bench.benchmark(
        "DecisionHistory.get_last_decision",
        lambda: history.get_last_decision("BTC/USDT"),
        iterations=1000
    )

    # Benchmark: Get decisions with limit
    bench.benchmark(
        "DecisionHistory.get_decisions (limit=10)",
        lambda: history.get_decisions("BTC/USDT", limit=10),
        iterations=1000
    )

    # Benchmark: Format explanation
    last_decision = history.get_last_decision("BTC/USDT")
    bench.benchmark(
        "DecisionHistory.format_decision_explanation",
        lambda: history.format_decision_explanation(last_decision),
        iterations=1000
    )

    return bench


def benchmark_decision_history_postgres():
    """Benchmark DecisionHistory with PostgreSQL"""
    from core.utils.decision_history import DecisionHistory

    bench = PerformanceBenchmark()

    try:
        history = DecisionHistory(use_redis=False, use_postgres=True)

        if not history.pg_connection:
            print("⚠️  PostgreSQL not available, skipping PostgreSQL benchmarks")
            return bench

        decision = {
            "action": "buy",
            "confidence": 0.75,
            "sentiment": 0.5
        }
        agent_debate = {
            "bull_argument": "Test bull argument",
            "bear_argument": "Test bear argument",
            "research_summary": "Test summary"
        }

        # Benchmark: Add decision with PostgreSQL
        bench.benchmark(
            "DecisionHistory.add_decision (PostgreSQL)",
            lambda: history.add_decision("TEST/USDT", decision, agent_debate),
            iterations=100  # Fewer iterations for database operations
        )

        # Benchmark: Database query
        def query_debates():
            cursor = history.pg_connection.cursor()
            cursor.execute(
                "SELECT * FROM agent_debates WHERE symbol = %s ORDER BY created_at DESC LIMIT 10",
                ("TEST/USDT",)
            )
            return cursor.fetchall()

        bench.benchmark(
            "PostgreSQL: Query debates (LIMIT 10)",
            query_debates,
            iterations=100
        )

    except Exception as e:
        print(f"⚠️  PostgreSQL benchmark failed: {e}")

    return bench


def benchmark_quantum_module():
    """Benchmark quantum module operations"""
    from core.modules.quantum import QuantumModule

    bench = PerformanceBenchmark()

    try:
        quantum = QuantumModule()

        # Benchmark: Simple quantum operation
        assets = [
            {"symbol": "BTC/USDT", "weight": 0.4},
            {"symbol": "ETH/USDT", "weight": 0.3},
            {"symbol": "SOL/USDT", "weight": 0.3}
        ]

        # Note: This will be slow, so fewer iterations
        bench.benchmark(
            "QuantumModule initialization",
            lambda: QuantumModule(),
            iterations=10,
            warmup=2
        )

        print("\n⚠️  Note: Full quantum optimization benchmarks would be very slow")
        print("    Actual quantum operations take seconds to minutes")

    except Exception as e:
        print(f"⚠️  Quantum benchmark skipped: {e}")

    return bench


def run_all_benchmarks():
    """Run all performance benchmarks"""
    print("\n" + "="*70)
    print("SIGMAX PERFORMANCE BENCHMARK SUITE")
    print("="*70)

    all_results = {}

    # Benchmark 1: DecisionHistory (in-memory)
    print("\n" + "="*70)
    print("1. DECISION HISTORY (IN-MEMORY)")
    print("="*70)
    bench1 = benchmark_decision_history()
    all_results.update(bench1.results)

    # Benchmark 2: DecisionHistory with PostgreSQL
    print("\n" + "="*70)
    print("2. DECISION HISTORY (POSTGRESQL)")
    print("="*70)
    bench2 = benchmark_decision_history_postgres()
    all_results.update(bench2.results)

    # Benchmark 3: Quantum Module
    print("\n" + "="*70)
    print("3. QUANTUM MODULE")
    print("="*70)
    bench3 = benchmark_quantum_module()
    all_results.update(bench3.results)

    # Create combined benchmark with all results
    combined = PerformanceBenchmark()
    combined.results = all_results

    # Print summary
    combined.print_summary()

    # Save results
    combined.save_results("benchmark_results.json")

    return combined


if __name__ == "__main__":
    results = run_all_benchmarks()
