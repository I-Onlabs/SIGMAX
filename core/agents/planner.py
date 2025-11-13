"""
PlanningAgent - Decomposes trading decisions into structured research tasks

Inspired by Dexter's planning approach, this agent:
1. Breaks down complex decisions into actionable tasks
2. Identifies required data sources and dependencies
3. Prioritizes tasks based on value and urgency
4. Defines success criteria for each task
5. Enables parallel execution of independent tasks
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from loguru import logger


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1   # Must complete for valid decision
    HIGH = 2       # Very important, significant impact
    MEDIUM = 3     # Important but not critical
    LOW = 4        # Nice to have, minor impact


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ResearchTask:
    """
    Represents a single research task in the plan
    """

    def __init__(
        self,
        task_id: str,
        name: str,
        description: str,
        priority: TaskPriority,
        data_sources: List[str],
        dependencies: Optional[List[str]] = None,
        estimated_cost: float = 0.0,
        timeout_seconds: int = 30
    ):
        self.task_id = task_id
        self.name = name
        self.description = description
        self.priority = priority
        self.data_sources = data_sources
        self.dependencies = dependencies or []
        self.estimated_cost = estimated_cost
        self.timeout_seconds = timeout_seconds
        self.status = TaskStatus.PENDING
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'description': self.description,
            'priority': self.priority.value,
            'data_sources': self.data_sources,
            'dependencies': self.dependencies,
            'estimated_cost': self.estimated_cost,
            'timeout_seconds': self.timeout_seconds,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }

    def mark_started(self):
        """Mark task as started"""
        self.status = TaskStatus.IN_PROGRESS
        self.start_time = datetime.now()

    def mark_completed(self, result: Dict[str, Any]):
        """Mark task as completed with result"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.end_time = datetime.now()

    def mark_failed(self, error: str):
        """Mark task as failed with error"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.end_time = datetime.now()

    def mark_skipped(self, reason: str):
        """Mark task as skipped"""
        self.status = TaskStatus.SKIPPED
        self.error = reason
        self.end_time = datetime.now()


class PlanningAgent:
    """
    PlanningAgent - Decomposes trading decisions into structured research plans

    Inspired by Dexter's approach to breaking down complex queries into
    actionable, prioritized tasks.
    """

    def __init__(self, llm=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PlanningAgent

        Args:
            llm: Optional language model for enhanced planning
            config: Configuration dict
        """
        self.llm = llm
        self.config = config or {}

        # Planning settings
        self.enable_parallel_tasks = self.config.get('enable_parallel_tasks', True)
        self.max_parallel_tasks = self.config.get('max_parallel_tasks', 3)
        self.include_optional_tasks = self.config.get('include_optional_tasks', True)

        logger.info("✓ Planning agent initialized")

    async def create_plan(
        self,
        symbol: str,
        decision_context: Dict[str, Any],
        risk_profile: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Create a structured research plan for a trading decision

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            decision_context: Context for the decision (market data, etc.)
            risk_profile: Risk profile (conservative/balanced/aggressive)

        Returns:
            Research plan with prioritized tasks
        """
        logger.info(f"📋 Creating research plan for {symbol} ({risk_profile} profile)")

        try:
            # Extract symbol components
            base_symbol = symbol.split('/')[0]
            quote_symbol = symbol.split('/')[1] if '/' in symbol else 'USDT'

            # Create base research tasks
            tasks = []

            # Task 1: Market sentiment analysis (CRITICAL)
            tasks.append(ResearchTask(
                task_id="task_sentiment",
                name="Market Sentiment Analysis",
                description=f"Gather sentiment from news, social media, and fear/greed index for {symbol}",
                priority=TaskPriority.CRITICAL,
                data_sources=['news', 'social', 'fear_greed'],
                dependencies=[],
                estimated_cost=0.05,
                timeout_seconds=30
            ))

            # Task 2: On-chain metrics (CRITICAL)
            tasks.append(ResearchTask(
                task_id="task_onchain",
                name="On-Chain Metrics",
                description=f"Fetch on-chain data: whale activity, exchange flows, active addresses for {base_symbol}",
                priority=TaskPriority.CRITICAL,
                data_sources=['onchain', 'coingecko'],
                dependencies=[],
                estimated_cost=0.03,
                timeout_seconds=20
            ))

            # Task 3: Technical indicators (CRITICAL)
            tasks.append(ResearchTask(
                task_id="task_technical",
                name="Technical Analysis",
                description=f"Calculate technical indicators: RSI, MACD, Bollinger Bands, patterns for {symbol}",
                priority=TaskPriority.CRITICAL,
                data_sources=['price_data', 'volume_data'],
                dependencies=[],
                estimated_cost=0.02,
                timeout_seconds=15
            ))

            # Task 4: Macro factors (HIGH)
            tasks.append(ResearchTask(
                task_id="task_macro",
                name="Macroeconomic Factors",
                description="Analyze macro environment: Fed policy, DXY, risk sentiment, correlation with traditional markets",
                priority=TaskPriority.HIGH,
                data_sources=['macro_data', 'fear_greed'],
                dependencies=[],
                estimated_cost=0.03,
                timeout_seconds=20
            ))

            # Risk profile adjustments
            if risk_profile == "conservative":
                # Add liquidity check for conservative profile
                tasks.append(ResearchTask(
                    task_id="task_liquidity",
                    name="Liquidity Analysis",
                    description=f"Assess market liquidity and order book depth for {symbol}",
                    priority=TaskPriority.HIGH,
                    data_sources=['orderbook', 'volume_data'],
                    dependencies=[],
                    estimated_cost=0.02,
                    timeout_seconds=15
                ))

                # Add correlation analysis
                tasks.append(ResearchTask(
                    task_id="task_correlation",
                    name="Correlation Analysis",
                    description=f"Analyze correlation with BTC and major altcoins for {symbol}",
                    priority=TaskPriority.MEDIUM,
                    data_sources=['price_data'],
                    dependencies=['task_technical'],
                    estimated_cost=0.02,
                    timeout_seconds=15
                ))

            elif risk_profile == "aggressive":
                # Add momentum signals for aggressive profile
                tasks.append(ResearchTask(
                    task_id="task_momentum",
                    name="Momentum Signals",
                    description=f"Identify short-term momentum and breakout signals for {symbol}",
                    priority=TaskPriority.HIGH,
                    data_sources=['price_data', 'volume_data'],
                    dependencies=['task_technical'],
                    estimated_cost=0.02,
                    timeout_seconds=10
                ))

            # Optional tasks (if enabled)
            if self.include_optional_tasks:
                # Task: Historical pattern matching (MEDIUM)
                tasks.append(ResearchTask(
                    task_id="task_patterns",
                    name="Historical Pattern Matching",
                    description=f"Find similar historical patterns and their outcomes for {symbol}",
                    priority=TaskPriority.MEDIUM,
                    data_sources=['historical_data'],
                    dependencies=['task_technical'],
                    estimated_cost=0.04,
                    timeout_seconds=25
                ))

                # Task: News keyword extraction (LOW)
                tasks.append(ResearchTask(
                    task_id="task_keywords",
                    name="News Keyword Extraction",
                    description=f"Extract trending keywords and themes from recent {base_symbol} news",
                    priority=TaskPriority.LOW,
                    data_sources=['news'],
                    dependencies=['task_sentiment'],
                    estimated_cost=0.02,
                    timeout_seconds=15
                ))

            # Calculate execution order
            execution_order = self._calculate_execution_order(tasks)

            # Estimate total cost and time
            total_cost = sum(task.estimated_cost for task in tasks)
            total_time_sequential = sum(task.timeout_seconds for task in tasks)
            total_time_parallel = self._estimate_parallel_time(tasks, execution_order)

            # Generate summary
            summary = self._generate_plan_summary(
                symbol=symbol,
                risk_profile=risk_profile,
                tasks=tasks,
                execution_order=execution_order,
                total_cost=total_cost,
                total_time_sequential=total_time_sequential,
                total_time_parallel=total_time_parallel
            )

            plan = {
                'symbol': symbol,
                'risk_profile': risk_profile,
                'tasks': [task.to_dict() for task in tasks],
                'execution_order': execution_order,
                'task_count': len(tasks),
                'critical_tasks': len([t for t in tasks if t.priority == TaskPriority.CRITICAL]),
                'estimated_cost': total_cost,
                'estimated_time_sequential': total_time_sequential,
                'estimated_time_parallel': total_time_parallel,
                'speedup': total_time_sequential / total_time_parallel if total_time_parallel > 0 else 1.0,
                'summary': summary,
                'created_at': datetime.now().isoformat()
            }

            logger.info(f"✓ Research plan created: {len(tasks)} tasks, ${total_cost:.2f} cost, {total_time_parallel}s est. time")

            return plan

        except Exception as e:
            logger.error(f"Planning error: {e}", exc_info=True)
            return {
                'symbol': symbol,
                'tasks': [],
                'error': str(e),
                'summary': f"Planning failed: {str(e)}"
            }

    def _calculate_execution_order(self, tasks: List[ResearchTask]) -> List[List[str]]:
        """
        Calculate optimal execution order considering dependencies and parallelization

        Returns:
            List of task batches (can execute in parallel within each batch)
        """
        # Build dependency graph
        task_dict = {task.task_id: task for task in tasks}
        execution_order = []
        completed = set()

        while len(completed) < len(tasks):
            # Find tasks ready to execute (no pending dependencies)
            ready_tasks = []

            for task in tasks:
                if task.task_id in completed:
                    continue

                dependencies_met = all(dep in completed for dep in task.dependencies)
                if dependencies_met:
                    ready_tasks.append(task.task_id)

            if not ready_tasks:
                # Circular dependency or error - add remaining tasks
                remaining = [t.task_id for t in tasks if t.task_id not in completed]
                if remaining:
                    execution_order.append(remaining)
                    completed.update(remaining)
                break

            # Sort ready tasks by priority
            ready_tasks_sorted = sorted(
                ready_tasks,
                key=lambda tid: task_dict[tid].priority.value
            )

            # Limit parallelism if configured
            if self.enable_parallel_tasks:
                batch_size = min(len(ready_tasks_sorted), self.max_parallel_tasks)
                batch = ready_tasks_sorted[:batch_size]
            else:
                batch = [ready_tasks_sorted[0]]  # Sequential execution

            execution_order.append(batch)
            completed.update(batch)

        return execution_order

    def _estimate_parallel_time(self, tasks: List[ResearchTask], execution_order: List[List[str]]) -> int:
        """
        Estimate total time with parallel execution

        Returns:
            Estimated time in seconds
        """
        task_dict = {task.task_id: task for task in tasks}
        total_time = 0

        for batch in execution_order:
            # Time for batch = max time of tasks in batch
            batch_time = max(task_dict[tid].timeout_seconds for tid in batch)
            total_time += batch_time

        return total_time

    def _generate_plan_summary(
        self,
        symbol: str,
        risk_profile: str,
        tasks: List[ResearchTask],
        execution_order: List[List[str]],
        total_cost: float,
        total_time_sequential: int,
        total_time_parallel: int
    ) -> str:
        """
        Generate human-readable plan summary
        """
        task_dict = {task.task_id: task for task in tasks}

        # Count by priority
        critical = len([t for t in tasks if t.priority == TaskPriority.CRITICAL])
        high = len([t for t in tasks if t.priority == TaskPriority.HIGH])
        medium = len([t for t in tasks if t.priority == TaskPriority.MEDIUM])
        low = len([t for t in tasks if t.priority == TaskPriority.LOW])

        # Calculate speedup
        speedup = total_time_sequential / total_time_parallel if total_time_parallel > 0 else 1.0

        summary = f"""
Research Plan for {symbol} ({risk_profile} profile)

📊 Task Breakdown:
  • Total tasks: {len(tasks)}
  • Critical: {critical}
  • High priority: {high}
  • Medium priority: {medium}
  • Low priority: {low}

⚡ Execution Strategy:
  • Parallel batches: {len(execution_order)}
  • Sequential time: {total_time_sequential}s
  • Parallel time: {total_time_parallel}s
  • Speedup: {speedup:.1f}x

💰 Resource Estimates:
  • Estimated cost: ${total_cost:.2f}
  • API calls: {len(tasks) * 2}  # Rough estimate

🔄 Execution Order:
"""

        for i, batch in enumerate(execution_order, 1):
            batch_tasks = [task_dict[tid].name for tid in batch]
            if len(batch) == 1:
                summary += f"  {i}. {batch_tasks[0]}\n"
            else:
                summary += f"  {i}. Parallel: {', '.join(batch_tasks)}\n"

        return summary.strip()

    def get_config(self) -> Dict[str, Any]:
        """Get current planning configuration"""
        return {
            'enable_parallel_tasks': self.enable_parallel_tasks,
            'max_parallel_tasks': self.max_parallel_tasks,
            'include_optional_tasks': self.include_optional_tasks
        }

    def update_config(self, config: Dict[str, Any]) -> None:
        """Update planning configuration"""
        for key, value in config.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info(f"✓ Updated planning config: {key} = {value}")
