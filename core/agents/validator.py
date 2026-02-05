"""
ValidationAgent - Validates research quality and completeness

Inspired by Dexter's validation approach, this agent checks:
- Research completeness (all required data gathered)
- Data quality and freshness
- Confidence thresholds
- Data gap identification
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger


class ValidationAgent:
    """
    ValidationAgent - Ensures research quality before proceeding to decision

    Responsibilities:
    1. Validate research completeness
    2. Check data quality and freshness
    3. Identify data gaps
    4. Calculate validation score
    5. Recommend re-research if needed
    """

    def __init__(self, llm=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ValidationAgent

        Args:
            llm: Optional language model for enhanced validation
            config: Configuration dict with thresholds
        """
        self.llm = llm

        # Default configuration
        self.config = config or {}
        self.validation_threshold = self.config.get('validation_threshold', 0.7)
        self.data_freshness_seconds = self.config.get('data_freshness_seconds', 300)  # 5 min
        self.required_data_sources = self.config.get('required_data_sources', [
            'news', 'social', 'onchain', 'technical'
        ])
        self.min_summary_length = self.config.get('min_summary_length', 20)
        self.min_technical_length = self.config.get('min_technical_length', 20)

        logger.info("✓ Validation agent initialized")

    async def validate(
        self,
        research_summary: Optional[str],
        technical_analysis: Optional[str] = None,
        planned_tasks: Optional[List[Dict[str, Any]]] = None,
        completed_tasks: Optional[List[str]] = None,
        market_data: Optional[Dict[str, Any]] = None,
        research_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate research quality and completeness

        Args:
            research_summary: Research summary text
            technical_analysis: Technical analysis summary
            planned_tasks: List of planned research tasks
            completed_tasks: List of completed task IDs
            market_data: Market data dictionary
            research_data: Full research data including sources

        Returns:
            Validation result with score, gaps, and pass/fail
        """
        logger.info("🔍 Validating research quality...")

        try:
            # Initialize validation metrics
            validation_checks = {
                'completeness': 0.0,
                'data_quality': 0.0,
                'freshness': 0.0,
                'coverage': 0.0
            }

            data_gaps = []

            # 1. Check completeness
            completeness_result = await self._check_completeness(
                research_summary=research_summary,
                technical_analysis=technical_analysis,
                planned_tasks=planned_tasks,
                completed_tasks=completed_tasks
            )
            validation_checks['completeness'] = completeness_result['score']
            data_gaps.extend(completeness_result['gaps'])

            # 2. Check data quality
            quality_result = await self._check_data_quality(
                research_summary=research_summary,
                research_data=research_data
            )
            validation_checks['data_quality'] = quality_result['score']
            if quality_result['issues']:
                data_gaps.extend(quality_result['issues'])

            # 3. Check data freshness
            freshness_result = await self._check_freshness(
                market_data=market_data,
                research_data=research_data
            )
            validation_checks['freshness'] = freshness_result['score']
            if freshness_result['stale_sources']:
                data_gaps.extend([f"Stale data from {src}" for src in freshness_result['stale_sources']])

            # 4. Check coverage (are all required sources present?)
            coverage_result = await self._check_coverage(
                research_data=research_data
            )
            validation_checks['coverage'] = coverage_result['score']
            data_gaps.extend(coverage_result['missing_sources'])

            # Calculate overall validation score (weighted average)
            weights = {
                'completeness': 0.35,
                'data_quality': 0.25,
                'freshness': 0.20,
                'coverage': 0.20
            }

            validation_score = sum(
                validation_checks[key] * weights[key]
                for key in validation_checks
            )

            # Determine pass/fail
            passed = validation_score >= self.validation_threshold and len(data_gaps) == 0

            # Generate summary
            summary = await self._generate_validation_summary(
                validation_checks=validation_checks,
                validation_score=validation_score,
                data_gaps=data_gaps,
                passed=passed
            )

            result = {
                'passed': passed,
                'score': validation_score,
                'checks': validation_checks,
                'gaps': data_gaps,
                'summary': summary,
                'threshold': self.validation_threshold,
                'timestamp': datetime.now().isoformat()
            }

            if passed:
                logger.info(f"✅ Validation PASSED: {validation_score:.2%}")
            else:
                logger.warning(f"⚠️ Validation FAILED: {validation_score:.2%} (threshold: {self.validation_threshold:.2%})")
                logger.warning(f"   Data gaps: {len(data_gaps)}")

            return result

        except Exception as e:
            logger.error(f"Validation error: {e}", exc_info=True)
            return {
                'passed': False,
                'score': 0.0,
                'checks': {},
                'gaps': [f"Validation error: {str(e)}"],
                'summary': f"Validation failed due to error: {str(e)}",
                'error': str(e)
            }

    async def _check_completeness(
        self,
        research_summary: Optional[str],
        technical_analysis: Optional[str],
        planned_tasks: Optional[List[Dict[str, Any]]],
        completed_tasks: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Check if research is complete

        Returns:
            Score (0.0-1.0) and list of gaps
        """
        gaps = []
        score = 1.0

        # Check if research summary exists
        if not research_summary or len(research_summary.strip()) < self.min_summary_length:
            gaps.append("Research summary missing or too short")
            score -= 0.4

        # Check if technical analysis exists
        if not technical_analysis or len(technical_analysis.strip()) < self.min_technical_length:
            gaps.append("Technical analysis missing or incomplete")
            score -= 0.3

        # Check task completion (if tasks were planned)
        if planned_tasks and completed_tasks:
            planned_count = len(planned_tasks)
            completed_count = len(completed_tasks)

            completion_ratio = completed_count / planned_count if planned_count > 0 else 1.0

            if completion_ratio < 1.0:
                gaps.append(f"Only {completed_count}/{planned_count} tasks completed")
                score -= (1.0 - completion_ratio) * 0.3

        return {
            'score': max(0.0, min(1.0, score)),
            'gaps': gaps
        }

    async def _check_data_quality(
        self,
        research_summary: Optional[str],
        research_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check quality of gathered data

        Returns:
            Score (0.0-1.0) and list of quality issues
        """
        issues = []
        score = 1.0

        if not research_data:
            return {'score': 0.5, 'issues': ["No research data provided"]}

        # Check for error indicators in research
        if research_summary:
            error_indicators = [
                'error', 'failed', 'unable', 'unavailable',
                'timeout', 'exception', 'could not'
            ]

            summary_lower = research_summary.lower()
            for indicator in error_indicators:
                if indicator in summary_lower:
                    issues.append(f"Potential error detected: '{indicator}' in research")
                    score -= 0.15

        # Check sentiment score validity
        sentiment = research_data.get('sentiment', 0.0)
        if not isinstance(sentiment, (int, float)) or not (-1.0 <= sentiment <= 1.0):
            issues.append("Invalid sentiment score")
            score -= 0.2

        # Check for placeholder/mock data
        if research_data.get('source') == 'fallback' or research_data.get('source') == 'mock':
            issues.append("Using fallback/mock data instead of real sources")
            score -= 0.3

        return {
            'score': max(0.0, min(1.0, score)),
            'issues': issues
        }

    async def _check_freshness(
        self,
        market_data: Optional[Dict[str, Any]],
        research_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check if data is fresh enough for trading decisions

        Returns:
            Score (0.0-1.0) and list of stale sources
        """
        stale_sources = []
        score = 1.0

        if not research_data:
            return {'score': 0.5, 'stale_sources': ["No research data to check"]}

        current_time = datetime.now()
        max_age = timedelta(seconds=self.data_freshness_seconds)

        # Check research timestamp
        if 'timestamp' in research_data:
            try:
                data_time = datetime.fromisoformat(research_data['timestamp'])
                age = current_time - data_time

                if age > max_age:
                    stale_sources.append(f"Research data ({age.seconds}s old)")
                    score -= 0.4
            except Exception:
                pass

        # Check individual source timestamps
        for source_name in ['news', 'social', 'onchain', 'macro']:
            source_data = research_data.get(source_name, {})

            if isinstance(source_data, dict) and 'timestamp' in source_data:
                try:
                    source_time = datetime.fromisoformat(source_data['timestamp'])
                    age = current_time - source_time

                    if age > max_age:
                        stale_sources.append(f"{source_name} ({age.seconds}s old)")
                        score -= 0.15
                except Exception:
                    pass

        # Check on-chain RPC snapshot freshness if provided
        onchain = research_data.get('onchain', {})
        rpc_snapshot = onchain.get('rpc_snapshot', {}) if isinstance(onchain, dict) else {}
        if isinstance(rpc_snapshot, dict):
            for chain_name, chain_data in rpc_snapshot.items():
                if not isinstance(chain_data, dict):
                    continue
                block_age_sec = chain_data.get("block_age_sec")
                if isinstance(block_age_sec, (int, float)) and block_age_sec > max_age.total_seconds():
                    stale_sources.append(f"{chain_name} rpc (block_age {int(block_age_sec)}s)")
                    score -= 0.1

        return {
            'score': max(0.0, min(1.0, score)),
            'stale_sources': stale_sources
        }

    async def _check_coverage(
        self,
        research_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check if all required data sources are present

        Returns:
            Score (0.0-1.0) and list of missing sources
        """
        missing_sources = []
        score = 1.0

        if not research_data:
            return {
                'score': 0.0,
                'missing_sources': self.required_data_sources.copy()
            }

        # Check each required source
        for source in self.required_data_sources:
            if source not in research_data:
                missing_sources.append(f"Missing {source} data")
                score -= (1.0 / len(self.required_data_sources))
            else:
                # Check if source has actual data (not empty dict)
                source_data = research_data[source]
                if isinstance(source_data, dict) and len(source_data) == 0:
                    missing_sources.append(f"{source} data is empty")
                    score -= (0.5 / len(self.required_data_sources))

        return {
            'score': max(0.0, min(1.0, score)),
            'missing_sources': missing_sources
        }

    async def _generate_validation_summary(
        self,
        validation_checks: Dict[str, float],
        validation_score: float,
        data_gaps: List[str],
        passed: bool
    ) -> str:
        """
        Generate human-readable validation summary
        """
        status = "✅ PASSED" if passed else "❌ FAILED"

        summary = f"""
Validation Report: {status}

Overall Score: {validation_score:.1%} (threshold: {self.validation_threshold:.1%})

Detailed Checks:
  • Completeness: {validation_checks.get('completeness', 0):.1%}
  • Data Quality: {validation_checks.get('data_quality', 0):.1%}
  • Freshness:    {validation_checks.get('freshness', 0):.1%}
  • Coverage:     {validation_checks.get('coverage', 0):.1%}

Data Gaps: {len(data_gaps)}
"""

        if data_gaps:
            summary += "\nIdentified Issues:\n"
            for i, gap in enumerate(data_gaps[:5], 1):  # Show max 5 gaps
                summary += f"  {i}. {gap}\n"

            if len(data_gaps) > 5:
                summary += f"  ... and {len(data_gaps) - 5} more\n"

        if passed:
            summary += "\n✓ Research quality is sufficient. Proceeding to decision."
        else:
            summary += "\n⚠ Research quality is insufficient. Consider re-research."

        return summary.strip()

    def get_config(self) -> Dict[str, Any]:
        """Get current validation configuration"""
        return {
            'validation_threshold': self.validation_threshold,
            'data_freshness_seconds': self.data_freshness_seconds,
            'required_data_sources': self.required_data_sources,
            'min_summary_length': self.min_summary_length,
            'min_technical_length': self.min_technical_length
        }

    def update_config(self, config: Dict[str, Any]) -> None:
        """Update validation configuration"""
        if 'validation_threshold' in config:
            self.validation_threshold = config['validation_threshold']

        if 'data_freshness_seconds' in config:
            self.data_freshness_seconds = config['data_freshness_seconds']

        if 'required_data_sources' in config:
            self.required_data_sources = config['required_data_sources']

        if 'min_summary_length' in config:
            self.min_summary_length = config['min_summary_length']

        if 'min_technical_length' in config:
            self.min_technical_length = config['min_technical_length']

        logger.info(f"✓ Validation config updated: {config}")
