"""
Data Boundary Validator - Anti-Look-Ahead Validation for Backtesting
Inspired by AI-Trader's strict temporal controls

This module provides validation to ensure backtesting doesn't accidentally
use future information, which would invalidate results.

Key Features:
- Validates data access patterns
- Detects look-ahead bias
- Integrates with TemporalGateway
- Provides validation reports
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import numpy as np

from core.utils.temporal_gateway import TemporalGateway, DataType


class ViolationType(Enum):
    """Types of look-ahead violations."""
    FUTURE_PRICE = "future_price"
    FUTURE_NEWS = "future_news"
    FUTURE_FINANCIALS = "future_financials"
    LOOKAHEAD_INDICATOR = "lookahead_indicator"
    DATA_SNOOPING = "data_snooping"
    SURVIVORSHIP_BIAS = "survivorship_bias"


@dataclass
class Violation:
    """A detected look-ahead violation."""
    violation_type: ViolationType
    timestamp: datetime
    simulation_time: datetime
    description: str
    severity: str  # "critical", "warning", "info"
    data_accessed: Optional[str] = None
    stack_trace: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of data boundary validation."""
    passed: bool
    total_checks: int
    violations: List[Violation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    @property
    def critical_violations(self) -> int:
        return len([v for v in self.violations if v.severity == "critical"])

    @property
    def warning_count(self) -> int:
        return len([v for v in self.violations if v.severity == "warning"])


class DataBoundaryValidator:
    """
    Validates that backtesting doesn't use future information.

    Usage:
        validator = DataBoundaryValidator()

        # Wrap your data access
        with validator.track(simulation_time):
            price = get_price(symbol)
            news = get_news(symbol)

        # Check for violations
        result = validator.validate()
        if not result.passed:
            print(result.violations)
    """

    def __init__(
        self,
        strict_mode: bool = True,
        track_indicators: bool = True
    ):
        """
        Initialize validator.

        Args:
            strict_mode: Fail on any violation
            track_indicators: Also track indicator calculations
        """
        self.strict_mode = strict_mode
        self.track_indicators = track_indicators

        # Access tracking
        self._current_simulation_time: Optional[datetime] = None
        self._access_log: List[Dict[str, Any]] = []
        self._violations: List[Violation] = []
        self._warnings: List[str] = []

        # Known problematic patterns
        self._detected_patterns: Set[str] = set()

    def set_simulation_time(self, simulation_time: datetime):
        """Set the current simulation time for validation."""
        self._current_simulation_time = simulation_time

    def track_data_access(
        self,
        data_type: str,
        symbol: str,
        data_timestamp: datetime,
        source: str = "unknown"
    ):
        """
        Track a data access for validation.

        Args:
            data_type: Type of data accessed
            symbol: Symbol accessed
            data_timestamp: Timestamp of the data
            source: Source of the access (for debugging)
        """
        if self._current_simulation_time is None:
            self._warnings.append("Data access without simulation time set")
            return

        access = {
            "data_type": data_type,
            "symbol": symbol,
            "data_timestamp": data_timestamp,
            "simulation_time": self._current_simulation_time,
            "source": source,
            "recorded_at": datetime.utcnow()
        }
        self._access_log.append(access)

        # Immediate validation
        if data_timestamp > self._current_simulation_time:
            violation = Violation(
                violation_type=ViolationType.FUTURE_PRICE if data_type == "price" else ViolationType.FUTURE_NEWS,
                timestamp=data_timestamp,
                simulation_time=self._current_simulation_time,
                description=f"Accessed {data_type} data from {data_timestamp} while simulating {self._current_simulation_time}",
                severity="critical",
                data_accessed=f"{symbol}:{data_type}"
            )
            self._violations.append(violation)

            if self.strict_mode:
                raise LookAheadBiasError(
                    f"Look-ahead bias detected: accessed {data_type} from future "
                    f"({data_timestamp} > {self._current_simulation_time})"
                )

    def validate_ohlcv_data(
        self,
        data: np.ndarray,
        symbol: str,
        simulation_time: datetime,
        timestamp_column: int = 0
    ) -> bool:
        """
        Validate OHLCV data doesn't contain future information.

        Args:
            data: OHLCV array (timestamp in column 0 by default)
            symbol: Symbol being validated
            simulation_time: Current simulation time
            timestamp_column: Index of timestamp column

        Returns:
            True if data is valid (no future data)
        """
        if len(data) == 0:
            return True

        # Convert simulation time to milliseconds
        sim_time_ms = simulation_time.timestamp() * 1000

        # Check for future data
        max_timestamp = data[:, timestamp_column].max()

        if max_timestamp > sim_time_ms:
            future_time = datetime.fromtimestamp(max_timestamp / 1000)
            violation = Violation(
                violation_type=ViolationType.FUTURE_PRICE,
                timestamp=future_time,
                simulation_time=simulation_time,
                description=f"OHLCV data contains future candles up to {future_time}",
                severity="critical",
                data_accessed=symbol
            )
            self._violations.append(violation)
            return False

        return True

    def validate_indicator(
        self,
        indicator_name: str,
        lookback_period: int,
        data_length: int,
        current_index: int
    ) -> bool:
        """
        Validate that an indicator doesn't use future data.

        Some indicators (like centered moving averages) naturally look ahead.
        This validates the indicator is using only past data.

        Args:
            indicator_name: Name of the indicator
            lookback_period: How many periods back it looks
            data_length: Total data length
            current_index: Current position in data

        Returns:
            True if indicator access pattern is valid
        """
        if not self.track_indicators:
            return True

        # Check if indicator could be looking ahead
        if current_index + lookback_period > data_length:
            # Indicator might be using future data
            # (e.g., centered moving average)

            pattern_key = f"{indicator_name}:{lookback_period}"

            if pattern_key not in self._detected_patterns:
                self._detected_patterns.add(pattern_key)

                violation = Violation(
                    violation_type=ViolationType.LOOKAHEAD_INDICATOR,
                    timestamp=datetime.utcnow(),
                    simulation_time=self._current_simulation_time or datetime.utcnow(),
                    description=f"Indicator {indicator_name} may use future data (lookback={lookback_period})",
                    severity="warning"
                )
                self._violations.append(violation)

        return True

    def check_survivorship_bias(
        self,
        symbols: List[str],
        simulation_time: datetime,
        delisted_symbols: Optional[Dict[str, datetime]] = None
    ) -> List[str]:
        """
        Check for survivorship bias - using only symbols that survived to present.

        Args:
            symbols: List of symbols to check
            simulation_time: Current simulation time
            delisted_symbols: Dict of symbol -> delisting date

        Returns:
            List of symbols that may cause survivorship bias
        """
        if not delisted_symbols:
            return []

        biased_symbols = []

        for symbol in symbols:
            if symbol in delisted_symbols:
                delist_date = delisted_symbols[symbol]
                if delist_date < datetime.utcnow() and simulation_time < delist_date:
                    # Symbol was delisted AFTER simulation time but BEFORE now
                    # Using it in simulation is fine, but we should track it
                    pass
                elif simulation_time > delist_date:
                    # Trying to use a symbol that should be delisted
                    biased_symbols.append(symbol)

                    violation = Violation(
                        violation_type=ViolationType.SURVIVORSHIP_BIAS,
                        timestamp=delist_date,
                        simulation_time=simulation_time,
                        description=f"Symbol {symbol} was delisted on {delist_date}",
                        severity="warning",
                        data_accessed=symbol
                    )
                    self._violations.append(violation)

        return biased_symbols

    def get_validation_result(self) -> ValidationResult:
        """Get comprehensive validation result."""
        total_checks = len(self._access_log)
        critical_violations = [v for v in self._violations if v.severity == "critical"]

        # Generate recommendations
        recommendations = []

        if any(v.violation_type == ViolationType.FUTURE_PRICE for v in self._violations):
            recommendations.append(
                "Use TemporalGateway to enforce data boundaries"
            )

        if any(v.violation_type == ViolationType.LOOKAHEAD_INDICATOR for v in self._violations):
            recommendations.append(
                "Replace centered indicators with trailing versions"
            )

        if any(v.violation_type == ViolationType.SURVIVORSHIP_BIAS for v in self._violations):
            recommendations.append(
                "Include delisted symbols in historical analysis"
            )

        passed = len(critical_violations) == 0

        return ValidationResult(
            passed=passed,
            total_checks=total_checks,
            violations=self._violations,
            warnings=self._warnings,
            recommendations=recommendations
        )

    def reset(self):
        """Reset validation state."""
        self._current_simulation_time = None
        self._access_log.clear()
        self._violations.clear()
        self._warnings.clear()
        self._detected_patterns.clear()

    def generate_report(self) -> str:
        """Generate human-readable validation report."""
        result = self.get_validation_result()

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║           DATA BOUNDARY VALIDATION REPORT                    ║
╚══════════════════════════════════════════════════════════════╝

Status: {"✅ PASSED" if result.passed else "❌ FAILED"}
Total Data Accesses: {result.total_checks}
Critical Violations: {result.critical_violations}
Warnings: {result.warning_count}

═══════════════════════════════════════════════════════════════
"""

        if result.violations:
            report += "\nVIOLATIONS DETECTED:\n"
            report += "═══════════════════════════════════════════════════════════════\n"

            for i, v in enumerate(result.violations, 1):
                report += f"""
{i}. [{v.severity.upper()}] {v.violation_type.value}
   Simulation Time: {v.simulation_time}
   Violation Time:  {v.timestamp}
   Description:     {v.description}
"""
                if v.data_accessed:
                    report += f"   Data:           {v.data_accessed}\n"

        if result.recommendations:
            report += "\nRECOMMENDATIONS:\n"
            report += "═══════════════════════════════════════════════════════════════\n"
            for rec in result.recommendations:
                report += f"• {rec}\n"

        report += "\n═══════════════════════════════════════════════════════════════\n"

        return report


class LookAheadBiasError(Exception):
    """Raised when look-ahead bias is detected in strict mode."""
    pass


class ValidatedBacktester:
    """
    Wrapper that adds temporal validation to any backtester.

    Usage:
        from core.modules.backtest import Backtester

        base_backtester = Backtester(initial_capital=10000)
        validated = ValidatedBacktester(base_backtester)

        result = await validated.run(strategy, data, start, end)
        print(validated.validation_report)
    """

    def __init__(
        self,
        backtester,
        strict_mode: bool = True
    ):
        """
        Initialize validated backtester.

        Args:
            backtester: Base backtester instance
            strict_mode: Fail on any look-ahead violation
        """
        self.backtester = backtester
        self.validator = DataBoundaryValidator(strict_mode=strict_mode)
        self.temporal_gateway: Optional[TemporalGateway] = None

        self._validation_result: Optional[ValidationResult] = None

    async def run(
        self,
        strategy_func: Callable,
        data: Dict[str, np.ndarray],
        start_date: datetime,
        end_date: datetime
    ):
        """
        Run validated backtest.

        This wraps the base backtester with temporal validation.
        """
        # Pre-validate data
        logger.info("🔍 Validating data boundaries before backtest...")

        for symbol, ohlcv in data.items():
            self.validator.validate_ohlcv_data(
                ohlcv, symbol, end_date
            )

        # Create temporal gateway for the backtest
        self.temporal_gateway = TemporalGateway(
            simulation_time=start_date,
            strict_mode=True
        )

        # Wrap strategy function to enforce temporal boundaries
        async def validated_strategy(market_data, timestamp):
            # Update temporal gateway
            self.temporal_gateway.set_simulation_time(timestamp)
            self.validator.set_simulation_time(timestamp)

            # Validate market data access
            for symbol, data_point in market_data.items():
                if len(data_point) > 0:
                    # Assuming timestamp is in column 0 (milliseconds)
                    data_timestamp = datetime.fromtimestamp(data_point[0] / 1000)
                    self.validator.track_data_access(
                        "price",
                        symbol,
                        data_timestamp,
                        "backtest_market_data"
                    )

            # Call original strategy
            return await strategy_func(market_data, timestamp)

        # Run backtest with validation
        try:
            result = await self.backtester.run(
                validated_strategy,
                data,
                start_date,
                end_date
            )

            # Generate validation result
            self._validation_result = self.validator.get_validation_result()

            if not self._validation_result.passed:
                logger.warning(
                    f"⚠️ Backtest completed but {self._validation_result.critical_violations} "
                    f"look-ahead violations detected!"
                )
            else:
                logger.info("✅ Backtest passed data boundary validation")

            return result

        except LookAheadBiasError as e:
            logger.error(f"❌ Backtest aborted due to look-ahead bias: {e}")
            self._validation_result = self.validator.get_validation_result()
            raise

    @property
    def validation_result(self) -> Optional[ValidationResult]:
        """Get validation result after backtest."""
        return self._validation_result

    @property
    def validation_report(self) -> str:
        """Get human-readable validation report."""
        return self.validator.generate_report()


def validate_backtest_data(
    data: Dict[str, np.ndarray],
    start_date: datetime,
    end_date: datetime,
    timestamp_column: int = 0
) -> ValidationResult:
    """
    Quick validation of backtest data without running a full backtest.

    Args:
        data: Dict of symbol -> OHLCV arrays
        start_date: Intended backtest start
        end_date: Intended backtest end
        timestamp_column: Index of timestamp column

    Returns:
        ValidationResult with any issues found
    """
    validator = DataBoundaryValidator(strict_mode=False)

    for symbol, ohlcv in data.items():
        if len(ohlcv) == 0:
            validator._warnings.append(f"No data for {symbol}")
            continue

        # Check data range
        min_ts = datetime.fromtimestamp(ohlcv[:, timestamp_column].min() / 1000)
        max_ts = datetime.fromtimestamp(ohlcv[:, timestamp_column].max() / 1000)

        if min_ts > start_date:
            validator._warnings.append(
                f"{symbol}: Data starts at {min_ts}, but backtest starts at {start_date}"
            )

        if max_ts < end_date:
            validator._warnings.append(
                f"{symbol}: Data ends at {max_ts}, but backtest ends at {end_date}"
            )

        # Validate no gaps
        timestamps = ohlcv[:, timestamp_column]
        if len(timestamps) > 1:
            diffs = np.diff(timestamps)
            median_diff = np.median(diffs)
            gaps = diffs > median_diff * 5  # 5x median is a gap

            if np.any(gaps):
                gap_count = np.sum(gaps)
                validator._warnings.append(
                    f"{symbol}: {gap_count} data gaps detected"
                )

    return validator.get_validation_result()
