"""
Task Queue System - Manages and executes research tasks

Supports:
- Parallel execution of independent tasks
- Dependency resolution
- Priority-based scheduling
- Result tracking and aggregation
- Error handling and retry logic
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from collections import defaultdict
from loguru import logger

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from planner import ResearchTask, TaskStatus


class TaskExecutor:
    """
    Executes research tasks with support for parallel execution and dependencies
    """

    def __init__(
        self,
        max_parallel: int = 3,
        retry_failed: bool = True,
        max_retries: int = 2
    ):
        """
        Initialize TaskExecutor

        Args:
            max_parallel: Maximum number of tasks to run in parallel
            retry_failed: Whether to retry failed tasks
            max_retries: Maximum number of retries per task
        """
        if max_parallel is not None:
            if not isinstance(max_parallel, int):
                raise TypeError("max_parallel must be an integer or None")
            if max_parallel <= 0:
                raise ValueError("max_parallel must be a positive integer")

        self.max_parallel = max_parallel
        self.retry_failed = retry_failed
        self.max_retries = max_retries

        # Task registry
        self.task_handlers: Dict[str, Callable] = {}

        # Execution tracking
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, Any] = {}
        self.task_errors: Dict[str, str] = {}
        self.retry_counts: Dict[str, int] = defaultdict(int)

        logger.info(f"✓ Task executor initialized (max_parallel={max_parallel})")

    def register_handler(self, task_type: str, handler: Callable):
        """
        Register a handler for a specific task type

        Args:
            task_type: Task type identifier
            handler: Async function that executes the task
        """
        self.task_handlers[task_type] = handler
        logger.debug(f"Registered handler for task type: {task_type}")

    async def execute_plan(
        self,
        tasks: List[ResearchTask],
        execution_order: List[List[str]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a research plan with tasks organized in batches

        Args:
            tasks: List of ResearchTask objects
            execution_order: List of task ID batches to execute
            context: Execution context (symbol, market_data, etc.)

        Returns:
            Aggregated results from all tasks
        """
        logger.info(f"🚀 Executing research plan: {len(tasks)} tasks in {len(execution_order)} batches")

        task_dict = {task.task_id: task for task in tasks}
        start_time = datetime.now()

        try:
            # Execute batches in order
            for batch_idx, batch in enumerate(execution_order, 1):
                logger.info(f"📦 Batch {batch_idx}/{len(execution_order)}: {len(batch)} tasks")

                # Execute batch in parallel
                batch_results = await self._execute_batch(
                    batch_tasks=[task_dict[tid] for tid in batch],
                    context=context
                )

                # Store results
                for task_id, result in batch_results.items():
                    self.task_results[task_id] = result

                # Log batch completion
                completed = len([r for r in batch_results.values() if r.get('status') == 'completed'])
                failed = len([r for r in batch_results.values() if r.get('status') == 'failed'])
                logger.info(f"  ✓ Batch complete: {completed} succeeded, {failed} failed")

            # Calculate overall stats
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            completed_count = len([r for r in self.task_results.values() if r.get('status') == 'completed'])
            failed_count = len([r for r in self.task_results.values() if r.get('status') == 'failed'])
            skipped_count = len([r for r in self.task_results.values() if r.get('status') == 'skipped'])

            # Aggregate results
            aggregated = self._aggregate_results(tasks, self.task_results)

            execution_summary = {
                'total_tasks': len(tasks),
                'completed': completed_count,
                'failed': failed_count,
                'skipped': skipped_count,
                'success_rate': completed_count / len(tasks) if tasks else 0.0,
                'duration_seconds': duration,
                'results': aggregated,
                'task_details': self.task_results
            }

            logger.info(f"✅ Plan execution complete: {completed_count}/{len(tasks)} tasks succeeded ({duration:.1f}s)")

            return execution_summary

        except Exception as e:
            logger.error(f"Plan execution error: {e}", exc_info=True)
            return {
                'total_tasks': len(tasks),
                'completed': 0,
                'failed': len(tasks),
                'error': str(e),
                'results': {}
            }

    async def _execute_batch(
        self,
        batch_tasks: List[ResearchTask],
        context: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Execute a batch of tasks in parallel

        Args:
            batch_tasks: Tasks to execute in parallel
            context: Execution context

        Returns:
            Dict mapping task_id to result
        """
        if not batch_tasks:
            return {}

        # Create coroutines for each task
        coroutines = []
        task_ids = []

        if self.max_parallel is not None and self.max_parallel < len(batch_tasks):
            semaphore = asyncio.Semaphore(max(self.max_parallel, 1))

            async def run_with_limit(task: ResearchTask):
                """Execute task while respecting the parallel limit."""
                async with semaphore:
                    return await self._execute_task(task, context)

            for task in batch_tasks:
                task_ids.append(task.task_id)
                coroutines.append(run_with_limit(task))
        else:
            for task in batch_tasks:
                task_ids.append(task.task_id)
                coroutines.append(self._execute_task(task, context))

        # Execute in parallel with timeout
        try:
            results = await asyncio.gather(*coroutines, return_exceptions=True)

            # Map results to task IDs
            batch_results = {}
            for task_id, result in zip(task_ids, results):
                if isinstance(result, Exception):
                    batch_results[task_id] = {
                        'status': 'failed',
                        'error': str(result)
                    }
                else:
                    batch_results[task_id] = result

            return batch_results

        except Exception as e:
            logger.error(f"Batch execution error: {e}")
            # Return failure for all tasks
            return {
                task_id: {'status': 'failed', 'error': str(e)}
                for task_id in task_ids
            }

    async def _execute_task(
        self,
        task: ResearchTask,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single research task

        Args:
            task: ResearchTask to execute
            context: Execution context

        Returns:
            Task result dict
        """
        task.mark_started()
        logger.debug(f"  ⏳ Starting: {task.name}")

        try:
            # Determine handler based on task data sources
            handler = self._get_handler_for_task(task)

            if not handler:
                # No specific handler - use default research
                result = await self._default_research(task, context)
            else:
                # Execute with specific handler
                result = await asyncio.wait_for(
                    handler(task, context),
                    timeout=task.timeout_seconds
                )

            task.mark_completed(result)
            logger.debug(f"  ✓ Completed: {task.name}")

            return {
                'status': 'completed',
                'task_id': task.task_id,
                'result': result,
                'duration': (task.end_time - task.start_time).total_seconds() if task.end_time and task.start_time else 0
            }

        except asyncio.TimeoutError:
            error_msg = f"Task timeout after {task.timeout_seconds}s"
            task.mark_failed(error_msg)
            logger.warning(f"  ⏱ Timeout: {task.name}")

            # Retry if configured
            if self.retry_failed and self.retry_counts[task.task_id] < self.max_retries:
                self.retry_counts[task.task_id] += 1
                logger.info(f"  🔄 Retrying: {task.name} (attempt {self.retry_counts[task.task_id] + 1})")
                return await self._execute_task(task, context)

            return {
                'status': 'failed',
                'task_id': task.task_id,
                'error': error_msg
            }

        except Exception as e:
            error_msg = str(e)
            task.mark_failed(error_msg)
            logger.error(f"  ✗ Failed: {task.name} - {error_msg}")

            # Retry if configured
            if self.retry_failed and self.retry_counts[task.task_id] < self.max_retries:
                self.retry_counts[task.task_id] += 1
                logger.info(f"  🔄 Retrying: {task.name} (attempt {self.retry_counts[task.task_id] + 1})")
                return await self._execute_task(task, context)

            return {
                'status': 'failed',
                'task_id': task.task_id,
                'error': error_msg
            }

    def _get_handler_for_task(self, task: ResearchTask) -> Optional[Callable]:
        """
        Get appropriate handler for task based on data sources

        Args:
            task: ResearchTask

        Returns:
            Handler function or None
        """
        # Match handler based on primary data source
        primary_source = task.data_sources[0] if task.data_sources else None

        if primary_source in self.task_handlers:
            return self.task_handlers[primary_source]

        # Try to find handler by task name pattern
        task_name_lower = task.name.lower()
        for handler_key in self.task_handlers:
            if handler_key.lower() in task_name_lower:
                return self.task_handlers[handler_key]

        return None

    async def _default_research(
        self,
        task: ResearchTask,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Default research handler when no specific handler is registered

        Args:
            task: ResearchTask
            context: Execution context

        Returns:
            Research result
        """
        # Simulate research with placeholder data
        logger.debug(f"Using default research handler for: {task.name}")

        await asyncio.sleep(0.1)  # Simulate work

        return {
            'task_name': task.name,
            'data_sources': task.data_sources,
            'status': 'completed_with_defaults',
            'note': 'No specific handler registered, using placeholder data'
        }

    def _aggregate_results(
        self,
        tasks: List[ResearchTask],
        task_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate results from all tasks into unified structure

        Args:
            tasks: List of all tasks
            task_results: Results keyed by task_id

        Returns:
            Aggregated results
        """
        aggregated = {
            'news': {},
            'social': {},
            'onchain': {},
            'technical': {},
            'macro': {},
            'patterns': {},
            'keywords': [],
            'metadata': {
                'tasks_completed': 0,
                'tasks_failed': 0,
                'data_sources_used': set()
            }
        }

        for task in tasks:
            result = task_results.get(task.task_id, {})

            if result.get('status') == 'completed':
                aggregated['metadata']['tasks_completed'] += 1

                # Add data sources used
                aggregated['metadata']['data_sources_used'].update(task.data_sources)

                # Map results to appropriate category
                if 'sentiment' in task.task_id or 'news' in task.task_id:
                    aggregated['news'].update(result.get('result', {}))
                elif 'social' in task.task_id:
                    aggregated['social'].update(result.get('result', {}))
                elif 'onchain' in task.task_id:
                    aggregated['onchain'].update(result.get('result', {}))
                elif 'technical' in task.task_id:
                    aggregated['technical'].update(result.get('result', {}))
                elif 'macro' in task.task_id:
                    aggregated['macro'].update(result.get('result', {}))
                elif 'pattern' in task.task_id:
                    aggregated['patterns'].update(result.get('result', {}))
                elif 'keyword' in task.task_id:
                    keywords = result.get('result', {}).get('keywords', [])
                    aggregated['keywords'].extend(keywords)

            elif result.get('status') == 'failed':
                aggregated['metadata']['tasks_failed'] += 1

        # Convert set to list for JSON serialization
        aggregated['metadata']['data_sources_used'] = list(aggregated['metadata']['data_sources_used'])

        return aggregated

    def reset(self):
        """Reset executor state for new execution"""
        self.active_tasks.clear()
        self.task_results.clear()
        self.task_errors.clear()
        self.retry_counts.clear()
        logger.debug("Task executor reset")


class TaskQueue:
    """
    Simple task queue for managing research tasks
    """

    def __init__(self):
        self.queue: List[ResearchTask] = []
        self.completed: List[ResearchTask] = []
        self.failed: List[ResearchTask] = []

    def add_task(self, task: ResearchTask):
        """Add task to queue"""
        self.queue.append(task)

    def add_tasks(self, tasks: List[ResearchTask]):
        """Add multiple tasks to queue"""
        self.queue.extend(tasks)

    def get_pending_tasks(self) -> List[ResearchTask]:
        """Get all pending tasks"""
        return [t for t in self.queue if t.status == TaskStatus.PENDING]

    def get_ready_tasks(self, completed_ids: set) -> List[ResearchTask]:
        """
        Get tasks that are ready to execute (dependencies met)

        Args:
            completed_ids: Set of completed task IDs

        Returns:
            List of ready tasks
        """
        ready = []
        for task in self.queue:
            if task.status != TaskStatus.PENDING:
                continue

            # Check if all dependencies are completed
            if all(dep_id in completed_ids for dep_id in task.dependencies):
                ready.append(task)

        return ready

    def mark_completed(self, task: ResearchTask):
        """Mark task as completed"""
        self.completed.append(task)
        if task in self.queue:
            self.queue.remove(task)

    def mark_failed(self, task: ResearchTask):
        """Mark task as failed"""
        self.failed.append(task)
        if task in self.queue:
            self.queue.remove(task)

    def get_status(self) -> Dict[str, int]:
        """Get queue status"""
        return {
            'pending': len(self.get_pending_tasks()),
            'completed': len(self.completed),
            'failed': len(self.failed),
            'total': len(self.queue) + len(self.completed) + len(self.failed)
        }
