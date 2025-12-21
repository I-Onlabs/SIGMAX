# SIGMAX Performance Baseline

**Created**: December 21, 2024
**Version**: 0.2.0-alpha
**Status**: 🟡 Benchmarks Ready - Awaiting Baseline Data Collection

---

## Executive Summary

This document defines the performance baseline for SIGMAX, outlines testing methodology, and provides instructions for collecting and validating performance metrics. Created as part of Phase 1.2 of the remediation plan to verify unverified performance claims.

### Current Status

- ✅ **Benchmarks Created**: Agent latency tests, load tests, integration tests
- ⏳ **Baseline Data**: Not yet collected (requires running benchmarks)
- ⚠️ **README Claims**: Unverified (need actual measurements)

---

## Performance Claims to Verify

From README.md and documentation (currently **UNVERIFIED**):

| Claim | Source | Status | Target |
|-------|--------|--------|--------|
| Agent decision <30ms | README.md | ❌ Not verified | <30ms mean |
| SSE streaming <50ms | API docs | ❌ Not verified | <50ms latency |
| Quantum 2-5x faster | Quantum docs | ❌ Not verified | 2x speedup min |
| 60 req/min API limit | SDK docs | ⚠️ Configured but not load tested | 60 req/min sustained |
| 10 req/min analysis | SDK docs | ⚠️ Configured but not load tested | 10 req/min |
| 5 req/min trading | SDK docs | ⚠️ Configured but not load tested | 5 req/min |

---

## Benchmark Suite Overview

### 1. Agent Performance Benchmarks

**File**: `tests/performance/benchmark_agents.py`
**Created**: 2024-12-21
**Lines**: 485
**Purpose**: Measure agent decision latency and validate <30ms claim

#### Test Classes

1. **TestOrchestratorPerformance**
   - `test_orchestrator_analyze_latency` - Measures 50 iterations of analyze_symbol()
   - `test_orchestrator_multi_symbol_throughput` - Symbols/second processing rate

2. **TestQuantumModulePerformance**
   - `test_quantum_optimization_latency` - Quantum portfolio optimization (target: <100ms)

3. **TestAgentColdStart**
   - `test_orchestrator_initialization_time` - Cold start timing
   - `test_quantum_module_initialization_time` - Quantum init timing

4. **TestConcurrentAgentPerformance**
   - `test_concurrent_analysis_requests` - 10 concurrent requests handling

5. **TestMemoryAndResourceUsage**
   - `test_orchestrator_memory_growth` - Memory leak detection (100 operations)

#### Metrics Collected

- **Mean latency** (ms)
- **Median latency** (P50)
- **P95 latency** (95th percentile)
- **P99 latency** (99th percentile)
- **Min/Max latency**
- **Throughput** (operations/second)
- **Memory growth** (MB over 100 operations)

#### How to Run

```bash
# Run all performance benchmarks with output
pytest tests/performance/benchmark_agents.py -v -s -m performance

# Run specific test class
pytest tests/performance/benchmark_agents.py::TestOrchestratorPerformance -v -s

# Generate report
pytest tests/performance/benchmark_agents.py -v -s -m performance > performance_report.txt
```

#### Expected Output Format

```
=== Orchestrator Analysis Latency ===
Samples: 50
Mean: XX.XXms
Median: XX.XXms
P95: XX.XXms
P99: XX.XXms
Min: XX.XXms
Max: XX.XXms

⚠️  Mean latency XX.XXms exceeds 30ms claim  (if applicable)
```

---

### 2. API Load Testing

**File**: `tests/load/locustfile.py`
**Enhanced**: 2024-12-21
**Purpose**: Stress test API endpoints, validate rate limits, measure concurrent user handling

#### User Simulation Classes

1. **SIGMAXProposalUser** (NEW)
   - Simulates proposal workflow: create → approve → execute
   - Tests `/api/v1/chat/proposals` endpoints
   - Measures latency for create and execute operations
   - Tracks rate limit violations (10 req/min analysis, 5 req/min trading)

2. **TradingAPIUser**
   - Simulates high-frequency trading client
   - Tests market data, orderbook, orders endpoints
   - Wait time: 0.1-1 seconds (HFT simulation)

3. **MarketMakerUser**
   - Very high frequency requests (0.05-0.2s wait)
   - Orderbook streaming, quote updates

4. **StrategyBotUser**
   - Algorithmic strategy simulation
   - Signal fetching, strategy execution
   - Wait time: 1-5 seconds

#### Rate Limits Tested

- **General API**: 60 requests/min
- **Analysis endpoints** (`/api/v1/chat/proposals`): 10 requests/min
- **Trading endpoints** (approve/execute): 5 requests/min

#### How to Run

```bash
# Install Locust first
pip install locust

# Run with web UI (recommended for interactive monitoring)
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Then open browser: http://localhost:8089
# Set users: 50, spawn rate: 10, duration: 5m

# Headless mode with output
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
       --users 100 --spawn-rate 10 --run-time 5m --headless

# Test rate limits specifically
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
       --users 20 --spawn-rate 5 --run-time 2m --headless \
       --tags rate-limit

# Save results to file
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
       --users 100 --spawn-rate 10 --run-time 5m --headless \
       --csv=load_test_results
```

#### Expected Output

```
======================================================================
SIGMAX Load Test Results
======================================================================

✅ No rate limit violations detected
(or)
📊 Rate Limit Violations:
  - proposals: X violations
  - trading: X violations

⏱️  Latency Statistics:

  proposal_create:
    Mean: XX.XXms
    P50:  XX.XXms
    P95:  XX.XXms
    P99:  XX.XXms
    Min:  XX.XXms
    Max:  XX.XXms
    Samples: XXX

    ⚠️  Exceeds 5s target  (if applicable)

📈 Overall Statistics:
  Total requests: XXXX
  Total failures: XX
  Requests/sec: XX.XX
  Failure rate: X.XX%

💡 Recommendations:
  - Check Grafana dashboards for real-time metrics
  - Review rate limit violations if any
  - Compare latencies against README claims
  - Analyze P99 latencies for worst-case performance
======================================================================
```

---

### 3. Integration Test Performance

**Files**:
- `tests/integration/test_api_flow.py` (17 tests)
- `tests/integration/test_quantum_integration.py` (19 tests)
- `tests/integration/test_safety_enforcer.py` (24 tests)

**Purpose**: Measure end-to-end workflow performance

#### How to Run

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run with timing
pytest tests/integration/ -v --durations=10

# Generate coverage report
pytest tests/integration/ -v --cov=core --cov=ui --cov-report=html
```

---

## Baseline Data Collection Procedure

### Prerequisites

1. **System Requirements**
   - Python 3.10+
   - All dependencies installed: `pip install -e .`
   - API server running: `python ui/api/main.py`
   - Clean system state (no other heavy processes)

2. **Environment Setup**
   ```bash
   export TRADING_MODE=paper
   export QUANTUM_ENABLED=true
   export API_KEY=test-api-key-123
   ```

### Step 1: Collect Agent Benchmarks

```bash
# Create output directory
mkdir -p performance_results

# Run agent benchmarks
pytest tests/performance/benchmark_agents.py -v -s -m performance \
    | tee performance_results/agent_benchmarks_$(date +%Y%m%d_%H%M%S).txt

# Extract key metrics
grep -E "(Mean:|Median:|P95:|P99:)" performance_results/agent_benchmarks_*.txt
```

### Step 2: Collect Load Test Data

```bash
# Terminal 1: Start API server
PYTHONPATH=/Users/mac/Projects/SIGMAX python ui/api/main.py

# Terminal 2: Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
       --users 100 --spawn-rate 10 --run-time 5m --headless \
       --csv=performance_results/load_test_$(date +%Y%m%d_%H%M%S) \
       | tee performance_results/load_test_console_$(date +%Y%m%d_%H%M%S).txt
```

### Step 3: Run Integration Tests with Timing

```bash
pytest tests/integration/ -v --durations=20 \
    | tee performance_results/integration_timing_$(date +%Y%m%d_%H%M%S).txt
```

### Step 4: Analyze Results

```bash
# Create analysis script
cat > performance_results/analyze_results.py << 'EOF'
#!/usr/bin/env python3
"""Analyze performance test results"""

import re
from pathlib import Path

def analyze_agent_benchmarks(file_path):
    """Extract metrics from agent benchmark output"""
    with open(file_path) as f:
        content = f.read()

    metrics = {
        'orchestrator_mean': None,
        'orchestrator_p95': None,
        'quantum_mean': None
    }

    # Extract orchestrator latency
    if match := re.search(r'Orchestrator Analysis.*?Mean: ([\d.]+)ms', content, re.DOTALL):
        metrics['orchestrator_mean'] = float(match.group(1))

    if match := re.search(r'Orchestrator Analysis.*?P95: ([\d.]+)ms', content, re.DOTALL):
        metrics['orchestrator_p95'] = float(match.group(1))

    # Extract quantum latency
    if match := re.search(r'Quantum Optimization.*?Mean: ([\d.]+)ms', content, re.DOTALL):
        metrics['quantum_mean'] = float(match.group(1))

    return metrics

def analyze_load_test(csv_path):
    """Extract metrics from load test CSV"""
    import csv

    stats_file = csv_path.replace('.csv', '_stats.csv')
    if not Path(stats_file).exists():
        return {}

    with open(stats_file) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Aggregate stats
    total_requests = sum(int(row['Request Count']) for row in rows if row['Request Count'].isdigit())
    total_failures = sum(int(row['Failure Count']) for row in rows if row['Failure Count'].isdigit())

    return {
        'total_requests': total_requests,
        'total_failures': total_failures,
        'failure_rate': (total_failures / total_requests * 100) if total_requests > 0 else 0
    }

if __name__ == '__main__':
    results_dir = Path('.')

    print("="*70)
    print("PERFORMANCE BASELINE ANALYSIS")
    print("="*70)

    # Analyze latest agent benchmark
    agent_files = sorted(results_dir.glob('agent_benchmarks_*.txt'))
    if agent_files:
        metrics = analyze_agent_benchmarks(agent_files[-1])
        print(f"\n📊 Agent Performance (from {agent_files[-1].name}):")
        print(f"  Orchestrator mean: {metrics.get('orchestrator_mean', 'N/A')}ms")
        print(f"  Orchestrator P95:  {metrics.get('orchestrator_p95', 'N/A')}ms")
        print(f"  Quantum mean:      {metrics.get('quantum_mean', 'N/A')}ms")

        # Compare to claims
        if metrics['orchestrator_mean'] and metrics['orchestrator_mean'] < 30:
            print("  ✅ Orchestrator meets <30ms claim")
        elif metrics['orchestrator_mean']:
            print(f"  ❌ Orchestrator {metrics['orchestrator_mean']:.2f}ms exceeds <30ms claim")

    # Analyze latest load test
    load_files = sorted(results_dir.glob('load_test_*_stats.csv'))
    if load_files:
        # Remove timestamp suffix to get base name
        base_name = str(load_files[-1]).replace('_stats.csv', '.csv')
        metrics = analyze_load_test(base_name)
        print(f"\n📈 Load Test (from {load_files[-1].name}):")
        print(f"  Total requests: {metrics.get('total_requests', 'N/A')}")
        print(f"  Total failures: {metrics.get('total_failures', 'N/A')}")
        print(f"  Failure rate:   {metrics.get('failure_rate', 'N/A'):.2f}%")

    print("\n" + "="*70)
EOF

chmod +x performance_results/analyze_results.py
cd performance_results && python analyze_results.py
```

---

## Performance Targets and Acceptance Criteria

### Critical Metrics (Must Pass)

| Metric | Target | Rationale |
|--------|--------|-----------|
| Orchestrator mean latency | <5000ms | Reasonable analysis time |
| Orchestrator P99 latency | <10000ms | Worst-case acceptable |
| API failure rate | <1% | System reliability |
| Memory growth (100 ops) | <200MB | No memory leaks |

### Aspirational Metrics (Nice to Have)

| Metric | Target | Current Claim |
|--------|--------|---------------|
| Orchestrator mean latency | <30ms | ❌ Unverified claim |
| Quantum optimization | <100ms | ⚠️ Needs measurement |
| SSE streaming latency | <50ms | ❌ Unverified claim |

### Rate Limit Compliance

| Endpoint Type | Limit | Test Method |
|---------------|-------|-------------|
| General API | 60 req/min | Load test with 60+ req/min |
| Analysis | 10 req/min | Burst 15 proposals in 1 min |
| Trading | 5 req/min | Burst 10 executions in 1 min |

**Expected**: Rate limiter returns HTTP 429 when exceeded

---

## Interpreting Results

### Agent Benchmarks

**Good Performance**:
- Mean <5000ms
- P95 <10000ms
- P99 <15000ms
- Memory growth <100MB

**Warning Signs**:
- Mean >10000ms (10s+ average)
- P99 >30000ms (30s+ worst case)
- Memory growth >200MB (possible leak)

### Load Tests

**Good Performance**:
- Failure rate <1%
- Rate limits enforced (429 errors when exceeded)
- Requests/sec scales with user count
- No crashes under 100 concurrent users

**Warning Signs**:
- Failure rate >5%
- No 429 errors (rate limiting broken)
- RPS plateaus before reaching capacity
- Memory errors or crashes

---

## Continuous Performance Monitoring

### Recommended Schedule

1. **Pre-commit**: Run agent benchmarks (`pytest tests/performance/` - 2 min)
2. **Pre-release**: Full load test (5 min)
3. **Weekly**: Baseline comparison to detect degradation
4. **After major changes**: Full benchmark suite

### Regression Detection

Save baseline results:
```bash
# First run establishes baseline
pytest tests/performance/ -v -s > baseline_performance.txt

# Future runs compare
pytest tests/performance/ -v -s > current_performance.txt
diff baseline_performance.txt current_performance.txt
```

Flag regressions if:
- Mean latency increases >20%
- P95 latency increases >30%
- Failure rate increases >1%
- Memory growth increases >50MB

---

## Next Steps

### Phase 1 Completion (Current)

1. ✅ Create benchmark_agents.py
2. ✅ Enhance locustfile.py
3. 🔄 **Document baseline (this file)**
4. ⏳ Update README with actual numbers

### Phase 2: Data Collection

1. Run full benchmark suite
2. Collect baseline data
3. Analyze results
4. Update this document with actual metrics
5. Update README.md with verified claims
6. Remove or revise unverified performance claims

### Phase 3: Optimization (if needed)

Based on baseline results:
- Optimize slow paths identified in P95/P99
- Fix memory leaks if detected
- Tune rate limiters
- Add caching for repeated operations

---

## References

- **REMEDIATION_PLAN.md** - Phase 1.2: Performance Benchmarking
- **PHASE1_BASELINE_ASSESSMENT.md** - Initial assessment
- **tests/performance/benchmark_agents.py** - Agent benchmarks
- **tests/load/locustfile.py** - Load testing
- **README.md** - Performance claims to verify

---

**Document Status**: Ready for data collection
**Next Action**: Run benchmark suite and populate with actual metrics
**Owner**: Development Team
**Review Date**: After baseline data collected
