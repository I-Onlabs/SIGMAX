"""
Tool Response Validator - MCP Tool Hijacking Defense
Inspired by TradeTrap's MCP hijacking attack patterns

Validates tool responses for:
- Data integrity and consistency
- Anomaly detection in market data
- Schema conformance
- Injection attempts in responses
"""

from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import statistics
from loguru import logger


class ValidationStatus(Enum):
    """Validation result status."""
    VALID = "valid"
    SUSPICIOUS = "suspicious"
    INVALID = "invalid"
    BLOCKED = "blocked"


class AnomalyType(Enum):
    """Types of anomalies in tool responses."""
    PRICE_SPIKE = "price_spike"
    VOLUME_ANOMALY = "volume_anomaly"
    TIMESTAMP_MISMATCH = "timestamp_mismatch"
    SCHEMA_VIOLATION = "schema_violation"
    INJECTION_DETECTED = "injection_detected"
    DATA_MISSING = "data_missing"
    STALE_DATA = "stale_data"
    IMPOSSIBLE_VALUE = "impossible_value"


@dataclass
class ValidationResult:
    """Result of tool response validation."""
    status: ValidationStatus
    anomalies: List[AnomalyType]
    confidence: float
    details: Dict[str, Any]
    original_response: Any
    sanitized_response: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "anomalies": [a.value for a in self.anomalies],
            "confidence": round(self.confidence, 3),
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ToolSchema:
    """Schema definition for tool responses."""
    name: str
    required_fields: List[str]
    field_types: Dict[str, type]
    value_constraints: Dict[str, Callable[[Any], bool]] = field(default_factory=dict)
    custom_validator: Optional[Callable[[Dict], bool]] = None


class ToolResponseValidator:
    """
    Validates MCP tool responses for security and integrity.

    Usage:
        validator = ToolResponseValidator()

        # Register tool schemas
        validator.register_schema(price_schema)

        # Validate response
        result = validator.validate("get_price", response)
        if result.status == ValidationStatus.INVALID:
            print(f"Invalid response: {result.anomalies}")
    """

    # Default schemas for common trading tools
    DEFAULT_SCHEMAS = {
        "get_price": ToolSchema(
            name="get_price",
            required_fields=["symbol", "price", "timestamp"],
            field_types={
                "symbol": str,
                "price": (int, float),
                "timestamp": str
            },
            value_constraints={
                "price": lambda x: x > 0 and x < 1000000,
                "symbol": lambda x: len(x) <= 20
            }
        ),
        "get_orderbook": ToolSchema(
            name="get_orderbook",
            required_fields=["symbol", "bids", "asks"],
            field_types={
                "symbol": str,
                "bids": list,
                "asks": list
            }
        ),
        "search_news": ToolSchema(
            name="search_news",
            required_fields=["query", "articles"],
            field_types={
                "query": str,
                "articles": list
            }
        ),
        "run_trade": ToolSchema(
            name="run_trade",
            required_fields=["status", "order_id"],
            field_types={
                "status": str,
                "order_id": str
            }
        )
    }

    def __init__(
        self,
        enable_anomaly_detection: bool = True,
        max_price_change_pct: float = 50.0,
        stale_data_threshold_sec: int = 300
    ):
        """
        Initialize tool response validator.

        Args:
            enable_anomaly_detection: Enable statistical anomaly detection
            max_price_change_pct: Maximum allowed price change percentage
            stale_data_threshold_sec: Seconds before data is considered stale
        """
        self.enable_anomaly_detection = enable_anomaly_detection
        self.max_price_change_pct = max_price_change_pct
        self.stale_data_threshold_sec = stale_data_threshold_sec

        self._schemas: Dict[str, ToolSchema] = dict(self.DEFAULT_SCHEMAS)
        self._price_history: Dict[str, List[Tuple[datetime, float]]] = {}
        self._validation_history: List[ValidationResult] = []

    def register_schema(self, schema: ToolSchema):
        """Register a tool schema."""
        self._schemas[schema.name] = schema
        logger.debug(f"Registered schema: {schema.name}")

    def validate(
        self,
        tool_name: str,
        response: Any
    ) -> ValidationResult:
        """
        Validate a tool response.

        Args:
            tool_name: Name of the tool
            response: Tool response to validate

        Returns:
            ValidationResult
        """
        anomalies = []
        details = {}

        # Handle error responses
        if isinstance(response, dict) and response.get("error"):
            return ValidationResult(
                status=ValidationStatus.VALID,
                anomalies=[],
                confidence=1.0,
                details={"is_error_response": True},
                original_response=response
            )

        # Get schema
        schema = self._schemas.get(tool_name)

        # Schema validation
        if schema:
            schema_result = self._validate_schema(response, schema)
            anomalies.extend(schema_result["anomalies"])
            details["schema_validation"] = schema_result

        # Anomaly detection
        if self.enable_anomaly_detection:
            anomaly_result = self._detect_anomalies(tool_name, response)
            anomalies.extend(anomaly_result["anomalies"])
            details["anomaly_detection"] = anomaly_result

        # Injection detection
        injection_result = self._detect_injection(response)
        if injection_result["detected"]:
            anomalies.append(AnomalyType.INJECTION_DETECTED)
            details["injection_detection"] = injection_result

        # Calculate status and confidence
        status, confidence = self._calculate_status(anomalies)

        # Create sanitized response if needed
        sanitized = None
        if status in [ValidationStatus.SUSPICIOUS, ValidationStatus.INVALID]:
            sanitized = self._sanitize_response(response, anomalies)

        result = ValidationResult(
            status=status,
            anomalies=anomalies,
            confidence=confidence,
            details=details,
            original_response=response,
            sanitized_response=sanitized
        )

        self._validation_history.append(result)

        if anomalies:
            logger.warning(f"Validation issues for {tool_name}: {[a.value for a in anomalies]}")

        return result

    def _validate_schema(
        self,
        response: Any,
        schema: ToolSchema
    ) -> Dict[str, Any]:
        """Validate response against schema."""
        anomalies = []
        missing_fields = []
        type_errors = []
        constraint_violations = []

        if not isinstance(response, dict):
            return {
                "valid": False,
                "anomalies": [AnomalyType.SCHEMA_VIOLATION],
                "error": "Response is not a dictionary"
            }

        # Check required fields
        for field_name in schema.required_fields:
            if field_name not in response:
                missing_fields.append(field_name)
                anomalies.append(AnomalyType.DATA_MISSING)

        # Check field types
        for field_name, expected_type in schema.field_types.items():
            if field_name in response:
                value = response[field_name]
                if not isinstance(value, expected_type):
                    type_errors.append({
                        "field": field_name,
                        "expected": str(expected_type),
                        "got": type(value).__name__
                    })
                    anomalies.append(AnomalyType.SCHEMA_VIOLATION)

        # Check value constraints
        for field_name, constraint in schema.value_constraints.items():
            if field_name in response:
                try:
                    if not constraint(response[field_name]):
                        constraint_violations.append(field_name)
                        anomalies.append(AnomalyType.IMPOSSIBLE_VALUE)
                except Exception:
                    constraint_violations.append(field_name)

        # Custom validation
        if schema.custom_validator:
            try:
                if not schema.custom_validator(response):
                    anomalies.append(AnomalyType.SCHEMA_VIOLATION)
            except Exception as e:
                logger.error(f"Custom validator error: {e}")

        return {
            "valid": len(anomalies) == 0,
            "anomalies": list(set(anomalies)),
            "missing_fields": missing_fields,
            "type_errors": type_errors,
            "constraint_violations": constraint_violations
        }

    def _detect_anomalies(
        self,
        tool_name: str,
        response: Any
    ) -> Dict[str, Any]:
        """Detect statistical anomalies in response."""
        anomalies = []
        details = {}

        if not isinstance(response, dict):
            return {"anomalies": [], "details": {}}

        # Price anomaly detection
        if "price" in response and "symbol" in response:
            price_result = self._check_price_anomaly(
                response["symbol"],
                response["price"]
            )
            if price_result["is_anomaly"]:
                anomalies.append(AnomalyType.PRICE_SPIKE)
                details["price_anomaly"] = price_result

        # Volume anomaly detection
        if "volume" in response:
            volume = response["volume"]
            if volume < 0:
                anomalies.append(AnomalyType.IMPOSSIBLE_VALUE)
                details["volume_invalid"] = True

        # Timestamp validation
        if "timestamp" in response:
            ts_result = self._check_timestamp(response["timestamp"])
            if ts_result["is_stale"]:
                anomalies.append(AnomalyType.STALE_DATA)
                details["timestamp_issue"] = ts_result
            if ts_result["is_future"]:
                anomalies.append(AnomalyType.TIMESTAMP_MISMATCH)
                details["timestamp_issue"] = ts_result

        return {"anomalies": anomalies, "details": details}

    def _check_price_anomaly(
        self,
        symbol: str,
        price: float
    ) -> Dict[str, Any]:
        """Check for price anomalies."""
        if symbol not in self._price_history:
            self._price_history[symbol] = []

        history = self._price_history[symbol]

        # Add current price
        now = datetime.utcnow()
        history.append((now, price))

        # Keep only recent history (last hour)
        cutoff = now - timedelta(hours=1)
        self._price_history[symbol] = [
            (t, p) for t, p in history if t > cutoff
        ]

        # Need at least 3 data points for anomaly detection
        if len(history) < 3:
            return {"is_anomaly": False, "reason": "insufficient_history"}

        prices = [p for _, p in history[:-1]]  # Exclude current
        avg_price = statistics.mean(prices)
        std_price = statistics.stdev(prices) if len(prices) > 1 else avg_price * 0.1

        # Check for spike
        change_pct = abs(price - avg_price) / avg_price * 100 if avg_price > 0 else 0

        is_anomaly = change_pct > self.max_price_change_pct

        # Also check z-score
        z_score = (price - avg_price) / std_price if std_price > 0 else 0
        is_statistical_anomaly = abs(z_score) > 3

        return {
            "is_anomaly": is_anomaly or is_statistical_anomaly,
            "change_pct": round(change_pct, 2),
            "z_score": round(z_score, 2),
            "avg_price": round(avg_price, 4),
            "current_price": price
        }

    def _check_timestamp(self, timestamp: str) -> Dict[str, Any]:
        """Check timestamp validity."""
        try:
            # Try parsing ISO format
            if isinstance(timestamp, str):
                ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                ts = timestamp

            now = datetime.utcnow()

            # Check for stale data
            age_seconds = (now - ts.replace(tzinfo=None)).total_seconds()
            is_stale = age_seconds > self.stale_data_threshold_sec

            # Check for future timestamps
            is_future = ts.replace(tzinfo=None) > now + timedelta(minutes=5)

            return {
                "is_stale": is_stale,
                "is_future": is_future,
                "age_seconds": round(age_seconds, 1)
            }
        except Exception as e:
            return {
                "is_stale": False,
                "is_future": False,
                "parse_error": str(e)
            }

    def _detect_injection(self, response: Any) -> Dict[str, Any]:
        """Detect injection attempts in response."""
        response_str = json.dumps(response) if isinstance(response, dict) else str(response)

        # Suspicious patterns in tool responses
        injection_patterns = [
            "ignore previous",
            "new instructions",
            "system prompt",
            "override",
            "run command",
            "<script>",
            "javascript:",
        ]

        detected = []
        for pattern in injection_patterns:
            if pattern.lower() in response_str.lower():
                detected.append(pattern)

        return {
            "detected": len(detected) > 0,
            "patterns": detected
        }

    def _calculate_status(
        self,
        anomalies: List[AnomalyType]
    ) -> Tuple[ValidationStatus, float]:
        """Calculate validation status and confidence."""
        if not anomalies:
            return ValidationStatus.VALID, 1.0

        # Critical anomalies
        critical = {
            AnomalyType.INJECTION_DETECTED,
            AnomalyType.IMPOSSIBLE_VALUE
        }

        # High severity anomalies
        high = {
            AnomalyType.PRICE_SPIKE,
            AnomalyType.SCHEMA_VIOLATION
        }

        if any(a in critical for a in anomalies):
            return ValidationStatus.BLOCKED, 0.9

        if any(a in high for a in anomalies):
            return ValidationStatus.INVALID, 0.8

        if len(anomalies) >= 3:
            return ValidationStatus.INVALID, 0.7

        return ValidationStatus.SUSPICIOUS, 0.6

    def _sanitize_response(
        self,
        response: Any,
        anomalies: List[AnomalyType]
    ) -> Any:
        """Sanitize response by removing/fixing issues."""
        if not isinstance(response, dict):
            return {"error": "sanitized_invalid_response", "original_type": type(response).__name__}

        sanitized = dict(response)

        # Remove suspicious text fields
        if AnomalyType.INJECTION_DETECTED in anomalies:
            for key, value in list(sanitized.items()):
                if isinstance(value, str):
                    # Remove any content after suspicious patterns
                    for pattern in ["ignore", "instruction", "override"]:
                        if pattern in value.lower():
                            sanitized[key] = "[SANITIZED]"

        # Mark anomalous prices
        if AnomalyType.PRICE_SPIKE in anomalies:
            sanitized["_price_anomaly_warning"] = True

        # Mark stale data
        if AnomalyType.STALE_DATA in anomalies:
            sanitized["_stale_data_warning"] = True

        sanitized["_sanitized"] = True

        return sanitized

    def get_statistics(self) -> Dict[str, Any]:
        """Get validation statistics."""
        if not self._validation_history:
            return {"total_validations": 0}

        status_counts = {}
        anomaly_counts = {}

        for result in self._validation_history:
            status = result.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            for anomaly in result.anomalies:
                a = anomaly.value
                anomaly_counts[a] = anomaly_counts.get(a, 0) + 1

        return {
            "total_validations": len(self._validation_history),
            "status_distribution": status_counts,
            "anomaly_distribution": anomaly_counts,
            "avg_confidence": sum(r.confidence for r in self._validation_history) / len(self._validation_history)
        }

    def clear_history(self):
        """Clear validation and price history."""
        self._validation_history.clear()
        self._price_history.clear()


class SecureToolWrapper:
    """
    Wrapper that applies validation to all tool calls.

    Usage:
        wrapper = SecureToolWrapper(validator)
        safe_response = await wrapper.call_tool(tool_name, args)
    """

    def __init__(
        self,
        validator: ToolResponseValidator,
        tool_registry: Any = None
    ):
        self.validator = validator
        self.tool_registry = tool_registry

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Tuple[Any, ValidationResult]:
        """
        Call a tool with validation.

        Returns:
            Tuple of (response, validation_result)
        """
        # Call the actual tool
        if self.tool_registry:
            response = await self.tool_registry.run(tool_name, arguments)
        else:
            response = {"error": "no_registry"}

        # Validate response
        result = self.validator.validate(tool_name, response)

        # Return sanitized if needed
        if result.status == ValidationStatus.BLOCKED:
            return {"error": "response_blocked", "reason": [a.value for a in result.anomalies]}, result

        if result.sanitized_response:
            return result.sanitized_response, result

        return response, result
