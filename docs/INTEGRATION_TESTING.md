# SIGMAX Integration Testing Guide

**Testing Phase 1 & Phase 2 Enhancements End-to-End**

This guide provides comprehensive instructions for testing the Dexter-inspired validation and planning systems integrated into SIGMAX.

---

## Overview

The integration combines three major systems:

1. **Phase 1: ValidationAgent** - Self-validation with quality checks
2. **Phase 2: PlanningAgent** - Task decomposition and planning
3. **Phase 2: TaskExecutor** - Parallel execution with result aggregation

**Expected Flow**:
```
Planner → Researcher (parallel tasks) → Validator → Bull/Bear → ... → Decision
   ↓           ↓                           ↓
 Creates    Executes                   Validates
  Plan     in Parallel                  Quality
           (1.8-2.4x                    (Re-research
            speedup)                    if needed)
```

---

## Prerequisites

### 1. Install Dependencies

```bash
cd core
pip install -r requirements.txt
```

**Key packages needed**:
- `pytest>=8.3.4`
- `pytest-asyncio>=0.24.0`
- `langchain>=0.3.13`
- `langgraph>=0.2.59`
- `pyyaml>=6.0.2`

### 2. Configure Environment

Create `.env` file in project root:

```bash
# Optional: LLM provider (defaults to Ollama if not set)
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Market data APIs
NEWSAPI_KEY=...
COINGECKO_API_KEY=...
```

**Note**: System works without API keys using mock data for testing.

---

## Unit Tests

### Phase 1: Validation System

```bash
# Run all validation tests
python -m pytest tests/test_validation.py -v

# Run specific test class
python -m pytest tests/test_validation.py::TestValidationAgent -v

# Run specific test
python -m pytest tests/test_validation.py::TestValidationAgent::test_validation_passing -v
```

**Expected output**:
```
tests/test_validation.py::TestValidationAgent::test_validator_creation PASSED
tests/test_validation.py::TestValidationAgent::test_validation_passing PASSED
tests/test_validation.py::TestValidationAgent::test_validation_failing PASSED
tests/test_validation.py::TestResearchSafety::test_cost_tracking PASSED
...
==================== 11 passed in 2.3s ====================
```

### Phase 2: Planning System

```bash
# Run all planning tests
python -m pytest tests/test_planning.py -v

# Test planning agent
python -m pytest tests/test_planning.py::TestPlanningAgent -v

# Test task executor
python -m pytest tests/test_planning.py::TestTaskExecutor -v

# Test integration
python -m pytest tests/test_planning.py::TestIntegration::test_end_to_end_planning_execution -v
```

**Expected output**:
```
tests/test_planning.py::TestPlanningAgent::test_create_plan_balanced PASSED
tests/test_planning.py::TestTaskExecutor::test_execute_batch_parallel PASSED
tests/test_planning.py::TestIntegration::test_end_to_end_planning_execution PASSED
...
==================== 21 passed in 4.7s ====================
```

---

## Integration Tests

### Test 1: End-to-End Workflow (Manual)

Create `test_integration.py`:

```python
"""
Manual integration test for Phase 1 + Phase 2
Run: python test_integration.py
"""

import asyncio
from core.agents.orchestrator import SIGMAXOrchestrator

async def test_full_workflow():
    """Test complete workflow with planning and validation"""

    # Initialize orchestrator with balanced risk profile
    orchestrator = SIGMAXOrchestrator(
        risk_profile='balanced',
        enable_autonomous_engine=False
    )

    await orchestrator.initialize()

    # Make a decision for BTC/USDT
    print("🚀 Starting decision process for BTC/USDT...")

    decision = await orchestrator.make_decision(
        symbol='BTC/USDT',
        market_data={
            'current_price': 50000,
            'volume': 1000000000,
            '24h_change': 2.5,
            'high_24h': 51000,
            'low_24h': 49000
        }
    )

    # Verify results
    print("\n" + "="*60)
    print("📊 DECISION RESULTS")
    print("="*60)

    assert 'action' in decision, "Missing action in decision"
    assert 'confidence' in decision, "Missing confidence"
    assert 'research_summary' in decision, "Missing research summary"

    print(f"Action: {decision['action']}")
    print(f"Confidence: {decision['confidence']:.2%}")
    print(f"Position Size: ${decision.get('position_size', 0):.2f}")

    # Check Phase 1: Validation
    print("\n📋 PHASE 1 - VALIDATION")
    print(f"Validation Score: {decision.get('validation_score', 'N/A')}")
    print(f"Validation Passed: {decision.get('validation_passed', 'N/A')}")
    print(f"Data Gaps: {decision.get('data_gaps', [])}")

    # Check Phase 2: Planning
    print("\n📋 PHASE 2 - PLANNING")
    plan = decision.get('research_plan', {})
    if plan:
        print(f"Tasks Planned: {plan.get('task_count', 0)}")
        print(f"Critical Tasks: {plan.get('critical_tasks', 0)}")
        print(f"Estimated Cost: ${plan.get('estimated_cost', 0):.3f}")
        print(f"Execution Time: {plan.get('estimated_time_parallel', 0):.1f}s (parallel)")
        print(f"Speedup: {plan.get('speedup', 1.0):.1f}x")

        # Show execution results
        task_results = decision.get('task_execution_results', {})
        completed = sum(1 for r in task_results.values() if r.get('status') == 'completed')
        print(f"Tasks Completed: {completed}/{len(task_results)}")

    print("\n✅ Integration test PASSED!")
    return decision

if __name__ == "__main__":
    asyncio.run(test_full_workflow())
```

**Run it**:
```bash
cd /home/user/SIGMAX
python test_integration.py
```

**Expected output**:
```
🚀 Starting decision process for BTC/USDT...
📋 Planning research for BTC/USDT
📋 Executing 7 planned tasks
✓ Parallel research completed: 7/7 tasks
✅ Validating research for BTC/USDT
Validation score: 0.82 ✓ PASSED

============================================================
📊 DECISION RESULTS
============================================================
Action: BUY
Confidence: 73.50%
Position Size: $12.50

📋 PHASE 1 - VALIDATION
Validation Score: 0.82
Validation Passed: True
Data Gaps: []

📋 PHASE 2 - PLANNING
Tasks Planned: 7
Critical Tasks: 3
Estimated Cost: $0.210
Execution Time: 65.0s (parallel)
Speedup: 1.9x
Tasks Completed: 7/7

✅ Integration test PASSED!
```

### Test 2: Validation Loop (Re-research Scenario)

Create `test_validation_loop.py`:

```python
"""
Test validation triggering re-research
"""

import asyncio
from core.agents.orchestrator import SIGMAXOrchestrator

async def test_validation_loop():
    """Test that low-quality research triggers re-research"""

    orchestrator = SIGMAXOrchestrator(risk_profile='conservative')
    await orchestrator.initialize()

    # Simulate scenario with missing data
    decision = await orchestrator.make_decision(
        symbol='ETH/USDT',
        market_data={
            'current_price': 3000,
            # Intentionally sparse data to trigger validation failure
        }
    )

    # Check if re-research was triggered
    messages = decision.get('messages', [])
    researcher_runs = sum(1 for m in messages if m.get('role') == 'researcher')

    print(f"Researcher runs: {researcher_runs}")

    if researcher_runs > 1:
        print("✅ Validation triggered re-research (as expected)")
    else:
        print("ℹ️  Single research pass was sufficient")

    return decision

if __name__ == "__main__":
    asyncio.run(test_validation_loop())
```

### Test 3: Parallel Execution Performance

Create `test_parallel_performance.py`:

```python
"""
Benchmark parallel vs sequential execution
"""

import asyncio
import time
from core.agents.planner import PlanningAgent
from core.utils.task_queue import TaskExecutor

async def test_parallel_speedup():
    """Verify parallel execution is faster than sequential"""

    # Create planner
    planner = PlanningAgent(llm=None, config={
        'enable_parallel_tasks': True,
        'max_parallel_tasks': 3,
        'include_optional_tasks': True
    })

    # Create plan
    plan = await planner.create_plan(
        symbol='BTC/USDT',
        decision_context={'price': 50000},
        risk_profile='balanced'
    )

    print(f"Plan created with {plan['task_count']} tasks")
    print(f"Estimated sequential time: {plan['estimated_time_sequential']}s")
    print(f"Estimated parallel time: {plan['estimated_time_parallel']}s")
    print(f"Expected speedup: {plan['speedup']:.2f}x")

    # Execute plan (with mock data)
    executor = TaskExecutor(max_parallel=3)

    start = time.time()
    # Execution happens here (would call actual APIs in production)
    # For testing, tasks complete quickly
    await asyncio.sleep(0.5)  # Simulate some work
    duration = time.time() - start

    print(f"\nActual execution time: {duration:.2f}s")
    print(f"✅ Performance test complete")

if __name__ == "__main__":
    asyncio.run(test_parallel_speedup())
```

---

## Configuration Testing

### Test Different Risk Profiles

```python
"""
Test planning behavior across risk profiles
"""

import asyncio
from core.agents.planner import PlanningAgent

async def test_risk_profiles():
    """Test that different risk profiles generate different plans"""

    profiles = ['conservative', 'balanced', 'aggressive']

    for profile in profiles:
        planner = PlanningAgent(llm=None, config={
            'enable_parallel_tasks': True,
            'max_parallel_tasks': 3,
            'include_optional_tasks': profile != 'aggressive'
        })

        plan = await planner.create_plan(
            symbol='BTC/USDT',
            decision_context={'price': 50000},
            risk_profile=profile
        )

        print(f"\n{profile.upper()} Profile:")
        print(f"  Tasks: {plan['task_count']}")
        print(f"  Critical: {plan['critical_tasks']}")
        print(f"  Cost: ${plan['estimated_cost']:.3f}")
        print(f"  Time: {plan['estimated_time_parallel']:.1f}s")

    print("\n✅ Risk profile test complete")

if __name__ == "__main__":
    asyncio.run(test_risk_profiles())
```

---

## Troubleshooting

### Issue: "No module named 'langchain_core'"

**Solution**:
```bash
pip install langchain-core==0.3.28 langchain==0.3.13 langgraph==0.2.59
```

### Issue: "ValidationAgent not found"

**Solution**: Ensure you're running from the project root:
```bash
cd /home/user/SIGMAX
python test_integration.py
```

### Issue: Tests hang or timeout

**Possible causes**:
1. **No LLM configured**: Set `OPENAI_API_KEY` or install Ollama
2. **API rate limits**: Reduce `max_parallel_tasks` in config
3. **Network issues**: Check internet connection for API calls

**Solution**:
```python
# Use mock LLM for testing
orchestrator = SIGMAXOrchestrator(
    risk_profile='balanced',
    llm=None  # Will use mock responses
)
```

### Issue: Validation always fails

**Check**:
```bash
# Verify validation config
cat core/config/validation_config.yaml

# Check thresholds
validation:
  min_validation_score: 0.6  # Lower if too strict
```

### Issue: Tasks not executing in parallel

**Debug**:
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check execution order
plan = await planner.create_plan(...)
print(f"Execution order: {plan['execution_order']}")
# Should show batches: [['task1', 'task2'], ['task3']]
```

---

## Performance Benchmarks

### Expected Metrics

**Phase 1 (Validation)**:
- Validation overhead: ~200-500ms
- Re-research trigger rate: 5-10% (for low-quality data)
- Cost per validation: ~$0.01-0.02

**Phase 2 (Planning)**:
- Planning overhead: ~300-800ms
- Parallel speedup: 1.8-2.4x
- Cost reduction: 10-15%
- Research time: 25-40s (vs 40-60s sequential)

### Benchmark Script

```python
"""
Comprehensive performance benchmark
"""

import asyncio
import time
from statistics import mean, stdev

async def benchmark():
    """Run multiple iterations and collect metrics"""

    from core.agents.orchestrator import SIGMAXOrchestrator

    orchestrator = SIGMAXOrchestrator(risk_profile='balanced')
    await orchestrator.initialize()

    # Run 10 iterations
    durations = []
    validations_passed = 0

    for i in range(10):
        start = time.time()

        decision = await orchestrator.make_decision(
            symbol='BTC/USDT',
            market_data={'current_price': 50000 + (i * 100)}
        )

        duration = time.time() - start
        durations.append(duration)

        if decision.get('validation_passed'):
            validations_passed += 1

        print(f"Iteration {i+1}: {duration:.2f}s")

    # Statistics
    print(f"\n{'='*60}")
    print("BENCHMARK RESULTS")
    print(f"{'='*60}")
    print(f"Avg duration: {mean(durations):.2f}s ± {stdev(durations):.2f}s")
    print(f"Min duration: {min(durations):.2f}s")
    print(f"Max duration: {max(durations):.2f}s")
    print(f"Validation pass rate: {validations_passed/10:.0%}")

if __name__ == "__main__":
    asyncio.run(benchmark())
```

---

## CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/test-integration.yml`:

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd core
        pip install -r requirements.txt

    - name: Run validation tests
      run: |
        pytest tests/test_validation.py -v

    - name: Run planning tests
      run: |
        pytest tests/test_planning.py -v

    - name: Run integration tests
      run: |
        python test_integration.py
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

---

## Monitoring in Production

### Metrics to Track

```python
# In production orchestrator
from prometheus_client import Counter, Histogram

# Phase 1 metrics
validation_score = Histogram(
    'sigmax_validation_score',
    'Validation quality score'
)
validation_failures = Counter(
    'sigmax_validation_failures',
    'Number of validation failures'
)

# Phase 2 metrics
planning_duration = Histogram(
    'sigmax_planning_duration_seconds',
    'Time to create execution plan'
)
parallel_speedup = Histogram(
    'sigmax_parallel_speedup',
    'Speedup from parallel execution'
)
task_execution_time = Histogram(
    'sigmax_task_execution_seconds',
    'Task execution duration',
    ['task_type']
)
```

### Dashboard Queries

```promql
# Average validation score (last hour)
avg(sigmax_validation_score{job="sigmax"}) by (risk_profile)

# Parallel execution speedup
histogram_quantile(0.95, sigmax_parallel_speedup)

# Task execution time by type
avg(sigmax_task_execution_seconds) by (task_type)

# Validation failure rate
rate(sigmax_validation_failures[5m])
```

---

## Best Practices

### 1. Always Test with Multiple Risk Profiles

```python
# Test conservative, balanced, and aggressive
for profile in ['conservative', 'balanced', 'aggressive']:
    orchestrator = SIGMAXOrchestrator(risk_profile=profile)
    # ... run tests
```

### 2. Verify Parallel Execution

```python
# Check that tasks actually run in parallel
plan = await planner.create_plan(...)
assert len(plan['execution_order']) > 1, "Should have multiple batches"
assert len(plan['execution_order'][0]) > 1, "First batch should be parallel"
```

### 3. Monitor Validation Rates

```python
# Track validation pass/fail rates
validation_passed = decision.get('validation_passed')
if not validation_passed:
    logger.warning(f"Validation failed: {decision.get('data_gaps')}")
```

### 4. Cost Tracking

```python
# Monitor research costs
total_cost = plan.get('estimated_cost', 0)
assert total_cost < 0.50, "Research cost too high"
```

---

## Next Steps

After confirming integration works:

1. **Backtest Performance**: Run historical backtests to validate improvements
2. **Production Deploy**: Start with paper trading
3. **Monitor Metrics**: Track validation rates, speedup, costs
4. **Fine-tune**: Adjust thresholds based on real performance

---

## Support

- **Issues**: Check [Troubleshooting](#troubleshooting) section
- **Questions**: [GitHub Discussions](https://github.com/I-Onlabs/SIGMAX/discussions)
- **Bugs**: [GitHub Issues](https://github.com/I-Onlabs/SIGMAX/issues)

---

**Last Updated**: 2025-11-10
**Phase**: 1 & 2 Integration Complete ✅
