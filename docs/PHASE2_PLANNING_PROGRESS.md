# Phase 2: Planning System - Progress Update

**Status**: 🔄 In Progress (70% Complete)
**Inspired by**: [Dexter](https://github.com/virattt/dexter) autonomous research agent
**Start Date**: 2025-11-10

---

## ✅ Completed Components

### 1. Planning Agent (`core/agents/planner.py`)

**Purpose**: Decomposes trading decisions into structured, prioritized research tasks

**Key Features**:
- ✅ Task decomposition based on symbol and risk profile
- ✅ Priority-based task organization (Critical, High, Medium, Low)
- ✅ Dependency tracking between tasks
- ✅ Cost and time estimation for each task
- ✅ Parallel execution planning
- ✅ Risk profile-specific task generation

**Task Types Generated**:
1. **Market Sentiment Analysis** (CRITICAL)
   - News, social media, fear/greed index
   - Est. cost: $0.05, Time: 30s

2. **On-Chain Metrics** (CRITICAL)
   - Whale activity, exchange flows, active addresses
   - Est. cost: $0.03, Time: 20s

3. **Technical Analysis** (CRITICAL)
   - RSI, MACD, Bollinger Bands, patterns
   - Est. cost: $0.02, Time: 15s

4. **Macroeconomic Factors** (HIGH)
   - Fed policy, DXY, risk sentiment
   - Est. cost: $0.03, Time: 20s

5. **Risk Profile-Specific Tasks**:
   - Conservative: Liquidity analysis, correlation analysis
   - Aggressive: Momentum signals, breakout detection
   - Balanced: Historical pattern matching

**Execution Planning**:
```python
# Example plan output:
{
    'symbol': 'BTC/USDT',
    'risk_profile': 'balanced',
    'tasks': [<ResearchTask>, ...],
    'execution_order': [
        ['task_sentiment', 'task_onchain', 'task_technical'],  # Batch 1: Parallel
        ['task_macro'],                                         # Batch 2: Sequential
        ['task_patterns']                                       # Batch 3: Depends on technical
    ],
    'estimated_cost': 0.15,
    'estimated_time_sequential': 120s,
    'estimated_time_parallel': 50s,
    'speedup': 2.4x
}
```

---

### 2. Task Queue System (`core/utils/task_queue.py`)

**Purpose**: Manages and executes research tasks with parallel execution and error handling

**Components**:

#### ResearchTask Class
```python
class ResearchTask:
    - task_id: Unique identifier
    - name: Human-readable name
    - description: Detailed description
    - priority: TaskPriority enum
    - data_sources: List of required sources
    - dependencies: List of task IDs that must complete first
    - estimated_cost: USD cost estimate
    - timeout_seconds: Max execution time
    - status: TaskStatus (pending/in_progress/completed/failed)
```

#### TaskExecutor Class
**Features**:
- ✅ Parallel execution (configurable max_parallel)
- ✅ Dependency resolution
- ✅ Automatic retry on failure (configurable retries)
- ✅ Timeout handling per task
- ✅ Result aggregation
- ✅ Error tracking

**Execution Flow**:
1. Organize tasks into batches based on dependencies
2. Execute each batch in parallel
3. Wait for batch completion before next batch
4. Aggregate results from all tasks
5. Return unified research output

**Example Usage**:
```python
executor = TaskExecutor(max_parallel=3, retry_failed=True, max_retries=2)

# Execute research plan
results = await executor.execute_plan(
    tasks=research_tasks,
    execution_order=[[tid1, tid2], [tid3]],
    context={'symbol': 'BTC/USDT', 'market_data': {...}}
)

# Results:
{
    'total_tasks': 5,
    'completed': 4,
    'failed': 1,
    'success_rate': 0.8,
    'duration_seconds': 42,
    'results': {
        'news': {...},
        'social': {...},
        'onchain': {...},
        'technical': {...}
    }
}
```

---

### 3. Orchestrator Integration (Partial)

**Updates Made**:
- ✅ Imported PlanningAgent
- ✅ Extended AgentState with planning fields:
  - `research_plan`: Full research plan
  - `planned_tasks`: List of tasks
  - `completed_task_ids`: Tracking completion
  - `task_execution_results`: Results from task execution
- ✅ Initialized PlanningAgent with risk-profile config
- ✅ Dynamic configuration based on risk profile

**Configuration**:
```python
planning_config = {
    'enable_parallel_tasks': True,
    'max_parallel_tasks': 3,
    'include_optional_tasks': risk_profile != 'aggressive'
}
```

---

## 🔄 In Progress

### Workflow Integration
Need to add:
- [ ] `_planner_node()` - Planning workflow node
- [ ] Update workflow graph to include planner as entry point
- [ ] Add edges: planner → researcher → validator → ...
- [ ] Pass planning context to researcher for targeted research

**Planned Workflow**:
```
Planner → Researcher (executes plan) → Validator →
[Quality Check] → Bull/Bear → Analyzer → Risk →
Privacy → Optimizer → Decision
```

---

## 📋 Remaining Work

### 1. Complete Workflow Integration (1-2 hours)
- [ ] Add `_planner_node()` method
- [ ] Update `workflow.set_entry_point("planner")`
- [ ] Add conditional edge from planner
- [ ] Pass plan to researcher for execution

### 2. Researcher Enhancement (2-3 hours)
- [ ] Update researcher to accept and execute task plan
- [ ] Integrate TaskExecutor into researcher
- [ ] Register task handlers for different data sources
- [ ] Map task results back to research_data structure

### 3. Configuration System (1 hour)
- [ ] Create `core/config/planning_config.yaml`
- [ ] Add risk profile-specific presets
- [ ] Add feature flags for planning

### 4. Testing (2-3 hours)
- [ ] Unit tests for PlanningAgent
- [ ] Unit tests for TaskExecutor
- [ ] Integration tests for full planning workflow
- [ ] Performance benchmarks (parallel vs sequential)

### 5. Documentation (1-2 hours)
- [ ] Complete Phase 2 implementation guide
- [ ] Usage examples
- [ ] Migration guide
- [ ] Performance comparison

---

## 🎯 Expected Benefits

### Performance Improvements
- **Research Speed**: 30-50% faster through parallelization
- **Cost Efficiency**: 10-15% cost reduction through smart task prioritization
- **Resource Utilization**: Better API quota management

### Quality Improvements
- **Structured Research**: Clear task breakdown ensures completeness
- **Priority-Based**: Critical tasks always executed
- **Dependency Tracking**: Ensures logical research flow
- **Failure Handling**: Automatic retries prevent partial research

### Developer Experience
- **Visibility**: Clear view of what research is being done
- **Debuggability**: Track each task independently
- **Extensibility**: Easy to add new research task types
- **Configurability**: Fine-tune based on needs

---

## 🔬 Performance Estimates

### Before Planning (Phase 1)
```
Research Time:  40-60s (sequential)
API Calls:      15-20
Cost:           $0.15-0.25
Parallelization: None
```

### After Planning (Phase 2)
```
Research Time:  25-40s (parallel, 30-40% faster)
API Calls:      15-20 (same, but better organized)
Cost:           $0.13-0.22 (10-15% reduction through optimization)
Parallelization: 2-3x speedup on independent tasks
```

### Example: BTC/USDT Analysis
```
Without Planning:
- Sentiment: 30s
- On-chain: 20s  } Sequential = 120s total
- Technical: 15s
- Macro: 20s
- Patterns: 25s
- Keywords: 10s

With Planning:
- Batch 1 (parallel): Sentiment, On-chain, Technical = 30s (max of 30,20,15)
- Batch 2 (parallel): Macro, Patterns = 25s (max of 20,25)
- Batch 3: Keywords = 10s (depends on sentiment)
Total: 65s (1.8x speedup)
```

---

## 💡 Design Decisions

### Why Dexter-Style Planning?

1. **Structured Approach**: Breaking down complex decisions into discrete tasks
2. **Parallel Execution**: Run independent research tasks concurrently
3. **Explicit Dependencies**: Clear understanding of research flow
4. **Priority-Based**: Ensure critical research always completes
5. **Cost-Aware**: Estimate and optimize research costs

### Why Task-Based Architecture?

1. **Modularity**: Each task is independent and testable
2. **Reusability**: Tasks can be reused across different decisions
3. **Extensibility**: Easy to add new task types
4. **Observability**: Track progress at task level
5. **Error Handling**: Fail gracefully and retry specific tasks

---

## 🚀 Next Steps

1. **Complete workflow integration** (highest priority)
2. **Test end-to-end** with real trading scenarios
3. **Benchmark performance** vs Phase 1
4. **Tune parameters** based on results
5. **Document** comprehensive usage guide

---

## 📊 Code Stats

**New Files**:
- `core/agents/planner.py` (645 lines)
- `core/utils/task_queue.py` (486 lines)

**Modified Files**:
- `core/agents/orchestrator.py` (+35 lines)

**Total**: ~1,150 lines of new code

---

## 🔗 Related

- [Phase 1: Validation](./PHASE1_VALIDATION.md) - Prerequisite
- [Dexter Analysis](./DEXTER_ANALYSIS.md) - Original inspiration
- [Dexter Comparison](./DEXTER_COMPARISON.md) - Feature comparison

---

**Last Updated**: 2025-11-10
**Status**: 70% complete, workflow integration pending
