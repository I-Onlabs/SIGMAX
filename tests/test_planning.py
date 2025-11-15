"""
Test suite for PlanningAgent and TaskQueue System (Phase 2)

Tests Dexter-inspired task decomposition and parallel execution
"""

import pytest
import asyncio
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from agents.planner import PlanningAgent, ResearchTask, TaskPriority, TaskStatus
from utils.task_queue import TaskExecutor, TaskQueue


class TestPlanningAgent:
    """Test PlanningAgent functionality"""

    @pytest.fixture
    def planner(self):
        """Create a PlanningAgent for testing"""
        config = {
            'enable_parallel_tasks': True,
            'max_parallel_tasks': 3,
            'include_optional_tasks': True
        }
        return PlanningAgent(llm=None, config=config)

    @pytest.mark.asyncio
    async def test_create_plan_balanced(self, planner):
        """Test plan creation for balanced risk profile"""
        plan = await planner.create_plan(
            symbol='BTC/USDT',
            decision_context={'price': 50000},
            risk_profile='balanced'
        )

        assert plan['symbol'] == 'BTC/USDT'
        assert plan['risk_profile'] == 'balanced'
        assert len(plan['tasks']) > 0
        assert 'execution_order' in plan
        assert plan['estimated_cost'] > 0
        assert plan['estimated_time_parallel'] < plan['estimated_time_sequential']

    @pytest.mark.asyncio
    async def test_create_plan_conservative(self, planner):
        """Test that conservative profile includes additional tasks"""
        plan = await planner.create_plan(
            symbol='ETH/USDT',
            decision_context={'price': 3000},
            risk_profile='conservative'
        )

        task_names = [t['name'] for t in plan['tasks']]

        # Conservative should include liquidity and correlation
        assert any('liquidity' in name.lower() for name in task_names)
        assert any('correlation' in name.lower() for name in task_names)

    @pytest.mark.asyncio
    async def test_create_plan_aggressive(self, planner):
        """Test that aggressive profile focuses on speed"""
        planner.include_optional_tasks = False  # Aggressive skips optional

        plan = await planner.create_plan(
            symbol='SOL/USDT',
            decision_context={'price': 100},
            risk_profile='aggressive'
        )

        # Aggressive should have fewer tasks (no optional)
        assert plan['task_count'] <= 6  # Roughly critical + high priority only

    @pytest.mark.asyncio
    async def test_task_priority_levels(self, planner):
        """Test that tasks have correct priority levels"""
        plan = await planner.create_plan(
            symbol='BTC/USDT',
            decision_context={'price': 50000},
            risk_profile='balanced'
        )

        # Should have critical tasks
        assert plan['critical_tasks'] >= 3

        # Check priorities in task list
        priorities = [t['priority'] for t in plan['tasks']]
        assert TaskPriority.CRITICAL.value in priorities

    @pytest.mark.asyncio
    async def test_execution_order_respects_dependencies(self, planner):
        """Test that execution order respects task dependencies"""
        plan = await planner.create_plan(
            symbol='BTC/USDT',
            decision_context={'price': 50000},
            risk_profile='balanced'
        )

        execution_order = plan['execution_order']
        task_dict = {t['task_id']: t for t in plan['tasks']}
        executed = set()

        # Verify each batch's dependencies are met
        for batch in execution_order:
            for task_id in batch:
                task = task_dict[task_id]
                deps = task['dependencies']

                # All dependencies should be in previously executed tasks
                for dep in deps:
                    assert dep in executed, f"Dependency {dep} not executed before {task_id}"

            executed.update(batch)

    @pytest.mark.asyncio
    async def test_parallel_speedup_calculation(self, planner):
        """Test that parallel execution provides speedup"""
        plan = await planner.create_plan(
            symbol='BTC/USDT',
            decision_context={'price': 50000},
            risk_profile='balanced'
        )

        # Speedup should be > 1.0 (faster with parallelism)
        assert plan['speedup'] > 1.0

        # Parallel time should be less than sequential
        assert plan['estimated_time_parallel'] < plan['estimated_time_sequential']

    def test_config_management(self, planner):
        """Test configuration get/update"""
        # Get config
        config = planner.get_config()
        assert 'enable_parallel_tasks' in config
        assert config['max_parallel_tasks'] == 3

        # Update config
        planner.update_config({'max_parallel_tasks': 5})
        assert planner.max_parallel_tasks == 5


class TestResearchTask:
    """Test ResearchTask class"""

    def test_task_creation(self):
        """Test task instantiation"""
        task = ResearchTask(
            task_id='task_1',
            name='Test Task',
            description='Test description',
            priority=TaskPriority.HIGH,
            data_sources=['source1', 'source2'],
            dependencies=['task_0'],
            estimated_cost=0.05,
            timeout_seconds=30
        )

        assert task.task_id == 'task_1'
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert len(task.data_sources) == 2

    def test_task_lifecycle(self):
        """Test task status transitions"""
        task = ResearchTask(
            task_id='task_1',
            name='Test Task',
            description='Test',
            priority=TaskPriority.MEDIUM,
            data_sources=['source1']
        )

        # Initial state
        assert task.status == TaskStatus.PENDING

        # Mark started
        task.mark_started()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.start_time is not None

        # Mark completed
        result = {'data': 'test_data'}
        task.mark_completed(result)
        assert task.status == TaskStatus.COMPLETED
        assert task.result == result
        assert task.end_time is not None

    def test_task_failure(self):
        """Test task failure handling"""
        task = ResearchTask(
            task_id='task_1',
            name='Test Task',
            description='Test',
            priority=TaskPriority.LOW,
            data_sources=['source1']
        )

        task.mark_started()
        task.mark_failed("Test error")

        assert task.status == TaskStatus.FAILED
        assert task.error == "Test error"

    def test_task_to_dict(self):
        """Test task serialization"""
        task = ResearchTask(
            task_id='task_1',
            name='Test Task',
            description='Test',
            priority=TaskPriority.CRITICAL,
            data_sources=['source1']
        )

        task_dict = task.to_dict()

        assert task_dict['task_id'] == 'task_1'
        assert task_dict['name'] == 'Test Task'
        assert task_dict['priority'] == TaskPriority.CRITICAL.value
        assert task_dict['status'] == TaskStatus.PENDING.value


class TestTaskExecutor:
    """Test TaskExecutor functionality"""

    def test_invalid_parallel_configuration(self):
        """Invalid parallel limits should raise informative errors."""
        with pytest.raises(ValueError):
            TaskExecutor(max_parallel=0)

        with pytest.raises(TypeError):
            TaskExecutor(max_parallel="2")

    @pytest.fixture
    def executor(self):
        """Create a TaskExecutor for testing"""
        return TaskExecutor(max_parallel=3, retry_failed=True, max_retries=2)

    @pytest.mark.asyncio
    async def test_execute_single_task(self, executor):
        """Test single task execution"""
        task = ResearchTask(
            task_id='task_1',
            name='Test Task',
            description='Test',
            priority=TaskPriority.HIGH,
            data_sources=['test_source'],
            timeout_seconds=5
        )

        result = await executor._execute_task(task, {})

        assert result['status'] in ['completed', 'failed']
        assert result['task_id'] == 'task_1'

    @pytest.mark.asyncio
    async def test_execute_batch_parallel(self, executor):
        """Test parallel batch execution"""
        tasks = [
            ResearchTask(
                task_id=f'task_{i}',
                name=f'Task {i}',
                description='Test',
                priority=TaskPriority.MEDIUM,
                data_sources=['test'],
                timeout_seconds=1
            )
            for i in range(3)
        ]

        start_time = datetime.now()
        results = await executor._execute_batch(tasks, {})
        duration = (datetime.now() - start_time).total_seconds()

        # All tasks should complete
        assert len(results) == 3

        # Parallel execution should be faster than 3 seconds (3 tasks * 1s each)
        assert duration < 2.5  # Some overhead allowed

    @pytest.mark.asyncio
    async def test_execute_batch_respects_max_parallel(self):
        """Ensure batches honor the configured parallel limit."""
        executor = TaskExecutor(max_parallel=2)
        concurrency_state = {
            'current': 0,
            'peak': 0
        }
        lock = asyncio.Lock()

        async def tracked_handler(task, context):
            async with lock:
                concurrency_state['current'] += 1
                concurrency_state['peak'] = max(
                    concurrency_state['peak'],
                    concurrency_state['current']
                )
            try:
                await asyncio.sleep(0.1)
                return {'result': 'ok'}
            finally:
                async with lock:
                    concurrency_state['current'] -= 1

        executor.register_handler('concurrency_test', tracked_handler)

        tasks = [
            ResearchTask(
                task_id=f'parallel_{i}',
                name=f'Parallel Task {i}',
                description='Ensure concurrency control',
                priority=TaskPriority.MEDIUM,
                data_sources=['concurrency_test'],
                timeout_seconds=1
            )
            for i in range(4)
        ]

        results = await executor._execute_batch(tasks, {})

        assert len(results) == 4
        assert concurrency_state['peak'] <= executor.max_parallel

    @pytest.mark.asyncio
    async def test_execute_plan(self, executor):
        """Test full plan execution"""
        # Create a simple plan with dependencies
        task1 = ResearchTask(
            task_id='task_1',
            name='Task 1',
            description='Independent task',
            priority=TaskPriority.CRITICAL,
            data_sources=['source1'],
            timeout_seconds=1
        )

        task2 = ResearchTask(
            task_id='task_2',
            name='Task 2',
            description='Depends on task 1',
            priority=TaskPriority.HIGH,
            data_sources=['source2'],
            dependencies=['task_1'],
            timeout_seconds=1
        )

        tasks = [task1, task2]
        execution_order = [['task_1'], ['task_2']]  # Sequential due to dependency

        summary = await executor.execute_plan(tasks, execution_order, {})

        assert summary['total_tasks'] == 2
        assert 'completed' in summary
        assert summary['duration_seconds'] > 0

    def test_handler_registration(self, executor):
        """Test task handler registration"""
        async def test_handler(task, context):
            return {'result': 'test'}

        executor.register_handler('test_source', test_handler)

        assert 'test_source' in executor.task_handlers

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, executor):
        """Test automatic retry on task failure"""
        call_count = 0

        async def failing_handler(task, context):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Simulated failure")
            return {'result': 'success'}

        executor.register_handler('retry_test', failing_handler)

        task = ResearchTask(
            task_id='task_retry',
            name='Retry Test',
            description='Test retry logic',
            priority=TaskPriority.MEDIUM,
            data_sources=['retry_test'],
            timeout_seconds=5
        )

        result = await executor._execute_task(task, {})

        # Should succeed after retry
        assert result['status'] == 'completed'
        assert call_count == 2  # Failed once, succeeded on retry


class TestTaskQueue:
    """Test TaskQueue functionality"""

    @pytest.fixture
    def queue(self):
        """Create a TaskQueue for testing"""
        return TaskQueue()

    def test_add_tasks(self, queue):
        """Test adding tasks to queue"""
        task = ResearchTask(
            task_id='task_1',
            name='Test',
            description='Test',
            priority=TaskPriority.MEDIUM,
            data_sources=['source1']
        )

        queue.add_task(task)
        assert len(queue.queue) == 1

    def test_get_pending_tasks(self, queue):
        """Test getting pending tasks"""
        task1 = ResearchTask(
            task_id='task_1',
            name='Test 1',
            description='Test',
            priority=TaskPriority.HIGH,
            data_sources=['source1']
        )

        task2 = ResearchTask(
            task_id='task_2',
            name='Test 2',
            description='Test',
            priority=TaskPriority.MEDIUM,
            data_sources=['source1']
        )
        task2.mark_completed({'data': 'test'})

        queue.add_tasks([task1, task2])

        pending = queue.get_pending_tasks()
        assert len(pending) == 1
        assert pending[0].task_id == 'task_1'

    def test_get_ready_tasks_with_dependencies(self, queue):
        """Test getting ready tasks based on dependencies"""
        task1 = ResearchTask(
            task_id='task_1',
            name='Test 1',
            description='Independent',
            priority=TaskPriority.HIGH,
            data_sources=['source1']
        )

        task2 = ResearchTask(
            task_id='task_2',
            name='Test 2',
            description='Depends on task_1',
            priority=TaskPriority.MEDIUM,
            data_sources=['source1'],
            dependencies=['task_1']
        )

        queue.add_tasks([task1, task2])

        # Initially, only task1 is ready
        ready = queue.get_ready_tasks(set())
        assert len(ready) == 1
        assert ready[0].task_id == 'task_1'

        # After task1 completes, task2 is ready
        ready = queue.get_ready_tasks({'task_1'})
        assert len(ready) == 2  # Both are ready now
        assert any(t.task_id == 'task_2' for t in ready)

    def test_queue_status(self, queue):
        """Test queue status reporting"""
        task1 = ResearchTask(
            task_id='task_1',
            name='Test 1',
            description='Test',
            priority=TaskPriority.HIGH,
            data_sources=['source1']
        )

        task2 = ResearchTask(
            task_id='task_2',
            name='Test 2',
            description='Test',
            priority=TaskPriority.MEDIUM,
            data_sources=['source1']
        )

        queue.add_tasks([task1, task2])
        queue.mark_completed(task1)

        status = queue.get_status()
        assert status['pending'] == 1
        assert status['completed'] == 1
        assert status['total'] == 2


class TestIntegration:
    """Integration tests for complete planning workflow"""

    @pytest.mark.asyncio
    async def test_end_to_end_planning_execution(self):
        """Test complete plan creation and execution"""
        # Create planner
        planner = PlanningAgent(llm=None, config={
            'enable_parallel_tasks': True,
            'max_parallel_tasks': 3,
            'include_optional_tasks': False  # Keep it simple
        })

        # Create plan
        plan = await planner.create_plan(
            symbol='BTC/USDT',
            decision_context={'price': 50000},
            risk_profile='balanced'
        )

        assert len(plan['tasks']) > 0
        assert len(plan['execution_order']) > 0

        # Execute plan
        executor = TaskExecutor(max_parallel=3)
        tasks = [ResearchTask(**{
            k: v for k, v in task.items()
            if k in ['task_id', 'name', 'description', 'priority', 'data_sources', 'dependencies', 'estimated_cost', 'timeout_seconds']
        }) for task in plan['tasks']]

        # Convert priority back to enum
        for i, task in enumerate(tasks):
            priority_value = plan['tasks'][i]['priority']
            task.priority = TaskPriority(priority_value)

        summary = await executor.execute_plan(
            tasks=tasks,
            execution_order=plan['execution_order'],
            context={'symbol': 'BTC/USDT'}
        )

        assert summary['total_tasks'] == len(tasks)
        assert summary['completed'] + summary['failed'] + summary['skipped'] == len(tasks)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
