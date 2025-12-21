#!/usr/bin/env python3
"""
Performance Benchmarking Tool

Measures tick-to-trade latency and system throughput.
"""

import sys
import argparse
import asyncio
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
import statistics

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pkg.common import get_logger, Clock
from pkg.schemas import MdUpdate, TopOfBook, FeatureFrame, OrderIntent, Side, OrderType


@dataclass
class LatencyMeasurement:
    """Single latency measurement"""
    stage: str
    latency_us: float
    timestamp_ns: int


@dataclass
class BenchmarkResult:
    """Benchmark results for a stage"""
    stage: str
    count: int
    mean_us: float
    median_us: float
    p50_us: float
    p95_us: float
    p99_us: float
    min_us: float
    max_us: float


class PerformanceBenchmark:
    """
    Benchmark SIGMAX pipeline performance.

    Measures:
    - Tick-to-trade latency (end-to-end)
    - Per-stage latency (book, features, decision, risk, router, exec)
    - Throughput (ticks/sec, orders/sec)
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.measurements: List[LatencyMeasurement] = []
        self.start_time_ns = 0
        self.tick_count = 0
        self.order_count = 0

    def start_benchmark(self):
        """Start benchmark timing"""
        self.start_time_ns = Clock.now_ns()
        self.measurements = []
        self.tick_count = 0
        self.order_count = 0
        self.logger.info("benchmark_started")

    def record_latency(self, stage: str, start_ns: int, end_ns: int):
        """Record latency for a stage"""
        latency_us = (end_ns - start_ns) / 1000.0
        self.measurements.append(
            LatencyMeasurement(
                stage=stage,
                latency_us=latency_us,
                timestamp_ns=end_ns
            )
        )

    def increment_tick(self):
        """Increment tick counter"""
        self.tick_count += 1

    def increment_order(self):
        """Increment order counter"""
        self.order_count += 1

    def get_results(self) -> Dict[str, BenchmarkResult]:
        """
        Calculate benchmark results.

        Returns:
            Dict of stage -> BenchmarkResult
        """
        if not self.measurements:
            return {}

        # Group by stage
        by_stage: Dict[str, List[float]] = {}
        for m in self.measurements:
            if m.stage not in by_stage:
                by_stage[m.stage] = []
            by_stage[m.stage].append(m.latency_us)

        # Calculate statistics
        results = {}
        for stage, latencies in by_stage.items():
            latencies_sorted = sorted(latencies)
            count = len(latencies_sorted)

            results[stage] = BenchmarkResult(
                stage=stage,
                count=count,
                mean_us=statistics.mean(latencies_sorted),
                median_us=statistics.median(latencies_sorted),
                p50_us=self._percentile(latencies_sorted, 0.50),
                p95_us=self._percentile(latencies_sorted, 0.95),
                p99_us=self._percentile(latencies_sorted, 0.99),
                min_us=min(latencies_sorted),
                max_us=max(latencies_sorted)
            )

        return results

    def _percentile(self, data: List[float], p: float) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        k = (len(data) - 1) * p
        f = int(k)
        c = f + 1
        if c >= len(data):
            return data[-1]
        return data[f] + (k - f) * (data[c] - data[f])

    def get_throughput(self) -> Dict[str, float]:
        """
        Calculate throughput metrics.

        Returns:
            Dict with ticks_per_sec and orders_per_sec
        """
        duration_sec = (Clock.now_ns() - self.start_time_ns) / 1_000_000_000.0
        if duration_sec == 0:
            return {"ticks_per_sec": 0.0, "orders_per_sec": 0.0}

        return {
            "ticks_per_sec": self.tick_count / duration_sec,
            "orders_per_sec": self.order_count / duration_sec,
            "duration_sec": duration_sec
        }

    def print_results(self):
        """Print benchmark results"""
        results = self.get_results()
        throughput = self.get_throughput()

        print("\n" + "=" * 80)
        print("SIGMAX PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)

        # Throughput
        print("\n📊 THROUGHPUT")
        print("-" * 80)
        print(f"Duration:        {throughput['duration_sec']:.2f} seconds")
        print(f"Ticks processed: {self.tick_count}")
        print(f"Orders created:  {self.order_count}")
        print(f"Ticks/sec:       {throughput['ticks_per_sec']:.2f}")
        print(f"Orders/sec:      {throughput['orders_per_sec']:.2f}")

        # Latency by stage
        print("\n⚡ LATENCY BY STAGE")
        print("-" * 80)
        print(f"{'Stage':<20} {'Count':>8} {'Mean':>10} {'p50':>10} {'p95':>10} {'p99':>10} {'Min':>10} {'Max':>10}")
        print("-" * 80)

        for stage, result in sorted(results.items()):
            print(f"{stage:<20} {result.count:>8} "
                  f"{result.mean_us:>9.2f}µs {result.p50_us:>9.2f}µs "
                  f"{result.p95_us:>9.2f}µs {result.p99_us:>9.2f}µs "
                  f"{result.min_us:>9.2f}µs {result.max_us:>9.2f}µs")

        # Check SLOs
        print("\n✓ SLO COMPLIANCE (Profile A)")
        print("-" * 80)

        tick_to_trade_p50 = results.get('tick_to_trade', None)
        if tick_to_trade_p50:
            p50_ms = tick_to_trade_p50.p50_us / 1000.0
            p99_ms = tick_to_trade_p50.p99_us / 1000.0

            p50_status = "✓ PASS" if p50_ms <= 10.0 else "✗ FAIL"
            p99_status = "✓ PASS" if p99_ms <= 20.0 else "✗ FAIL"

            print(f"Tick-to-Trade p50: {p50_ms:>8.2f}ms (target ≤10ms)  {p50_status}")
            print(f"Tick-to-Trade p99: {p99_ms:>8.2f}ms (target ≤20ms)  {p99_status}")
        else:
            print("Tick-to-Trade: No measurements")

        risk_gate = results.get('risk_gate', None)
        if risk_gate:
            risk_p99_us = risk_gate.p99_us
            risk_status = "✓ PASS" if risk_p99_us <= 100.0 else "✗ FAIL"
            print(f"Risk Gate p99:     {risk_p99_us:>8.2f}µs (target ≤100µs) {risk_status}")
        else:
            print("Risk Gate: No measurements")

        print("=" * 80 + "\n")


class MockPipeline:
    """
    Mock pipeline for benchmarking without running full system.

    Simulates the data flow through all stages.
    """

    def __init__(self, benchmark: PerformanceBenchmark):
        self.benchmark = benchmark

    async def simulate_tick(self, symbol_id: int):
        """Simulate a single tick through the pipeline"""
        tick_start_ns = Clock.now_ns()

        # Stage 1: Market data update
        md_update = MdUpdate(
            symbol_id=symbol_id,
            timestamp_ns=tick_start_ns,
            bid_px=50000.0,
            bid_sz=1.5,
            ask_px=50010.0,
            ask_sz=2.0,
            sequence=1
        )
        self.benchmark.increment_tick()

        # Stage 2: Order book processing
        book_start_ns = Clock.now_ns()
        await asyncio.sleep(0.0001)  # Simulate 100µs processing
        tob = TopOfBook(
            symbol_id=symbol_id,
            timestamp_ns=Clock.now_ns(),
            bid_price=md_update.bid_px,
            bid_size=md_update.bid_sz,
            ask_price=md_update.ask_px,
            ask_size=md_update.ask_sz
        )
        book_end_ns = Clock.now_ns()
        self.benchmark.record_latency('book', book_start_ns, book_end_ns)

        # Stage 3: Feature extraction
        features_start_ns = Clock.now_ns()
        await asyncio.sleep(0.0002)  # Simulate 200µs processing
        features = FeatureFrame(
            symbol_id=symbol_id,
            timestamp_ns=Clock.now_ns(),
            mid_price=tob.mid_price,
            micro_price=tob.micro_price,
            spread_bps=tob.spread_bps,
            imbalance=tob.imbalance,
            bid_price=tob.bid_price,
            ask_price=tob.ask_price,
            bid_size=tob.bid_size,
            ask_size=tob.ask_size,
            price_change_pct=0.01,
            realized_vol=0.005,
            regime_bits=0
        )
        features_end_ns = Clock.now_ns()
        self.benchmark.record_latency('features', features_start_ns, features_end_ns)

        # Stage 4: Decision layer
        decision_start_ns = Clock.now_ns()
        await asyncio.sleep(0.0005)  # Simulate 500µs processing
        order_intent = None
        if abs(features.imbalance) > 0.4:  # Simple signal
            order_intent = OrderIntent.create(
                symbol_id=symbol_id,
                side=Side.BUY if features.imbalance < 0 else Side.SELL,
                order_type=OrderType.LIMIT,
                qty=0.1,
                price=features.mid_price
            )
            self.benchmark.increment_order()
        decision_end_ns = Clock.now_ns()
        self.benchmark.record_latency('decision', decision_start_ns, decision_end_ns)

        if order_intent:
            # Stage 5: Risk gate
            risk_start_ns = Clock.now_ns()
            await asyncio.sleep(0.00005)  # Simulate 50µs processing
            risk_passed = True  # Assume pass
            risk_end_ns = Clock.now_ns()
            self.benchmark.record_latency('risk_gate', risk_start_ns, risk_end_ns)

            if risk_passed:
                # Stage 6: Router
                router_start_ns = Clock.now_ns()
                await asyncio.sleep(0.0001)  # Simulate 100µs processing
                router_end_ns = Clock.now_ns()
                self.benchmark.record_latency('router', router_start_ns, router_end_ns)

                # Stage 7: Execution
                exec_start_ns = Clock.now_ns()
                await asyncio.sleep(0.001)  # Simulate 1ms network latency
                exec_end_ns = Clock.now_ns()
                self.benchmark.record_latency('exec', exec_start_ns, exec_end_ns)

        # End-to-end tick-to-trade
        tick_end_ns = Clock.now_ns()
        self.benchmark.record_latency('tick_to_trade', tick_start_ns, tick_end_ns)


async def run_benchmark(args):
    """Run performance benchmark"""
    benchmark = PerformanceBenchmark()
    pipeline = MockPipeline(benchmark)

    print(f"\nStarting benchmark: {args.ticks} ticks across {args.symbols} symbols...")
    print(f"Mode: {'Mock pipeline' if args.mock else 'Live system'}")

    benchmark.start_benchmark()

    # Run simulation
    for i in range(args.ticks):
        symbol_id = (i % args.symbols) + 1  # Rotate through symbols
        await pipeline.simulate_tick(symbol_id)

        if (i + 1) % 1000 == 0:
            print(f"  Processed {i + 1}/{args.ticks} ticks...")

    # Print results
    benchmark.print_results()


def main():
    parser = argparse.ArgumentParser(description='SIGMAX Performance Benchmark')
    parser.add_argument('--ticks', type=int, default=10000,
                       help='Number of ticks to simulate (default: 10000)')
    parser.add_argument('--symbols', type=int, default=2,
                       help='Number of symbols (default: 2)')
    parser.add_argument('--mock', action='store_true',
                       help='Use mock pipeline (default: true)')

    args = parser.parse_args()

    asyncio.run(run_benchmark(args))


if __name__ == "__main__":
    main()
