"""
SIGMAX Observability Module - SigNoz Integration

This module provides production-grade observability for SIGMAX using OpenTelemetry
and SigNoz, an open-source observability platform.

Features:
- Distributed tracing for request flows
- Custom metrics for trading operations
- Structured logging with trace correlation
- Automatic instrumentation for common libraries
- SigNoz backend integration
- Performance monitoring and alerting

Components:
- Tracer: Distributed tracing for operations
- Metrics: Custom metrics for trading performance
- Logger: Structured logging with trace context
- Instrumentors: Automatic instrumentation

See docs/SIGNOZ_INTEGRATION.md for usage and configuration.
"""

import functools
import os
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional

from loguru import logger

# Try to import OpenTelemetry components
OTEL_AVAILABLE = False
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"OpenTelemetry not available: {e}")


class SigNozConfig:
    """Configuration for SigNoz observability"""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        service_name: str = "sigmax",
        service_version: str = "1.0.0",
        environment: str = "development",
        enable_traces: bool = True,
        enable_metrics: bool = True,
        enable_logs: bool = True,
        enable_console: bool = False,
        export_interval_millis: int = 30000
    ):
        """
        Initialize SigNoz configuration

        Args:
            endpoint: SigNoz collector endpoint (e.g., "http://localhost:4318")
            service_name: Name of the service
            service_version: Version of the service
            environment: Deployment environment (dev, staging, prod)
            enable_traces: Enable distributed tracing
            enable_metrics: Enable metrics collection
            enable_logs: Enable log instrumentation
            enable_console: Enable console exporters (for debugging)
            export_interval_millis: Metric export interval in milliseconds
        """
        self.endpoint = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.enable_traces = enable_traces
        self.enable_metrics = enable_metrics
        self.enable_logs = enable_logs
        self.enable_console = enable_console
        self.export_interval_millis = export_interval_millis

        # Derived endpoints
        self.traces_endpoint = f"{self.endpoint}/v1/traces"
        self.metrics_endpoint = f"{self.endpoint}/v1/metrics"

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "endpoint": self.endpoint,
            "service_name": self.service_name,
            "service_version": self.service_version,
            "environment": self.environment,
            "enable_traces": self.enable_traces,
            "enable_metrics": self.enable_metrics,
            "enable_logs": self.enable_logs,
            "enable_console": self.enable_console,
            "export_interval_millis": self.export_interval_millis
        }


class ObservabilityManager:
    """
    Main observability manager for SIGMAX

    Handles initialization and management of OpenTelemetry instrumentation
    for distributed tracing, metrics, and logging.
    """

    def __init__(self, config: Optional[SigNozConfig] = None):
        """
        Initialize observability manager

        Args:
            config: SigNoz configuration
        """
        self.config = config or SigNozConfig()
        self.tracer: Optional[Any] = None
        self.meter: Optional[Any] = None
        self.is_initialized = False

        # Metric instruments
        self.trade_counter = None
        self.trade_latency_histogram = None
        self.position_gauge = None
        self.pnl_histogram = None
        self.error_counter = None

        if OTEL_AVAILABLE:
            self._initialize_otel()
        else:
            logger.warning("OpenTelemetry not available, observability disabled")

    def _create_resource(self) -> Any:
        """Create OpenTelemetry resource with service information"""
        if not OTEL_AVAILABLE:
            return None

        return Resource.create({
            SERVICE_NAME: self.config.service_name,
            SERVICE_VERSION: self.config.service_version,
            "deployment.environment": self.config.environment,
            "service.namespace": "trading",
            "service.instance.id": os.getenv("HOSTNAME", "local")
        })

    def _initialize_otel(self):
        """Initialize OpenTelemetry SDK with SigNoz exporters"""
        if not OTEL_AVAILABLE:
            return

        resource = self._create_resource()

        # Initialize tracing
        if self.config.enable_traces:
            self._initialize_tracing(resource)

        # Initialize metrics
        if self.config.enable_metrics:
            self._initialize_metrics(resource)

        # Initialize logging instrumentation
        if self.config.enable_logs:
            self._initialize_logging()

        # Auto-instrument common libraries
        self._auto_instrument()

        self.is_initialized = True
        logger.info(f"✓ Observability initialized (SigNoz: {self.config.endpoint})")

    def _initialize_tracing(self, resource: Any):
        """Initialize distributed tracing"""
        if not OTEL_AVAILABLE:
            return

        # Create trace provider
        trace_provider = TracerProvider(resource=resource)

        # Add span processors
        if self.config.enable_console:
            # Console exporter for debugging
            trace_provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )

        # OTLP exporter for SigNoz
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.config.traces_endpoint,
                timeout=10
            )
            trace_provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
            logger.info(f"✓ Trace exporter configured: {self.config.traces_endpoint}")
        except Exception as e:
            logger.warning(f"Failed to configure OTLP trace exporter: {e}")

        # Set global trace provider
        trace.set_tracer_provider(trace_provider)
        self.tracer = trace.get_tracer(__name__)

    def _initialize_metrics(self, resource: Any):
        """Initialize metrics collection"""
        if not OTEL_AVAILABLE:
            return

        # Create metric readers
        readers = []

        if self.config.enable_console:
            # Console exporter for debugging
            readers.append(
                PeriodicExportingMetricReader(
                    ConsoleMetricExporter(),
                    export_interval_millis=self.config.export_interval_millis
                )
            )

        # OTLP exporter for SigNoz
        try:
            otlp_exporter = OTLPMetricExporter(
                endpoint=self.config.metrics_endpoint,
                timeout=10
            )
            readers.append(
                PeriodicExportingMetricReader(
                    otlp_exporter,
                    export_interval_millis=self.config.export_interval_millis
                )
            )
            logger.info(f"✓ Metric exporter configured: {self.config.metrics_endpoint}")
        except Exception as e:
            logger.warning(f"Failed to configure OTLP metric exporter: {e}")

        # Create meter provider
        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=readers
        )

        # Set global meter provider
        metrics.set_meter_provider(meter_provider)
        self.meter = metrics.get_meter(__name__)

        # Create metric instruments
        self._create_metric_instruments()

    def _create_metric_instruments(self):
        """Create custom metric instruments for trading"""
        if not OTEL_AVAILABLE or not self.meter:
            return

        # Trade counter
        self.trade_counter = self.meter.create_counter(
            name="sigmax.trades.total",
            description="Total number of trades executed",
            unit="1"
        )

        # Trade latency
        self.trade_latency_histogram = self.meter.create_histogram(
            name="sigmax.trade.latency",
            description="Trade execution latency",
            unit="ms"
        )

        # Position gauge
        self.position_gauge = self.meter.create_up_down_counter(
            name="sigmax.positions.count",
            description="Current number of open positions",
            unit="1"
        )

        # PnL histogram
        self.pnl_histogram = self.meter.create_histogram(
            name="sigmax.pnl",
            description="Profit and loss distribution",
            unit="USD"
        )

        # Error counter
        self.error_counter = self.meter.create_counter(
            name="sigmax.errors.total",
            description="Total number of errors",
            unit="1"
        )

        logger.info("✓ Custom metrics instruments created")

    def _initialize_logging(self):
        """Initialize logging instrumentation"""
        if not OTEL_AVAILABLE:
            return

        try:
            LoggingInstrumentor().instrument(set_logging_format=True)
            logger.info("✓ Logging instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument logging: {e}")

    def _auto_instrument(self):
        """Automatically instrument common libraries"""
        if not OTEL_AVAILABLE:
            return

        try:
            # Instrument aiohttp client
            AioHttpClientInstrumentor().instrument()
            logger.info("✓ aiohttp instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument aiohttp: {e}")

    @contextmanager
    def trace_operation(
        self,
        operation_name: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for tracing operations

        Usage:
            with observability.trace_operation("execute_trade", {"symbol": "BTC/USDT"}):
                # ... operation code ...

        Args:
            operation_name: Name of the operation
            attributes: Additional attributes to attach to span
        """
        if not OTEL_AVAILABLE or not self.tracer:
            yield
            return

        with self.tracer.start_as_current_span(operation_name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)

            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def record_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        latency_ms: float,
        success: bool = True
    ):
        """
        Record trade metrics

        Args:
            symbol: Trading symbol
            side: Trade side (buy/sell)
            quantity: Trade quantity
            price: Trade price
            latency_ms: Execution latency in milliseconds
            success: Whether trade succeeded
        """
        if not OTEL_AVAILABLE or not self.trade_counter:
            return

        attributes = {
            "symbol": symbol,
            "side": side,
            "success": str(success)
        }

        # Increment trade counter
        self.trade_counter.add(1, attributes)

        # Record latency
        if self.trade_latency_histogram:
            self.trade_latency_histogram.record(latency_ms, attributes)

    def record_position_change(self, symbol: str, change: int):
        """
        Record position count change

        Args:
            symbol: Trading symbol
            change: Change in position count (+1 for open, -1 for close)
        """
        if not OTEL_AVAILABLE or not self.position_gauge:
            return

        self.position_gauge.add(change, {"symbol": symbol})

    def record_pnl(self, symbol: str, pnl: float):
        """
        Record profit and loss

        Args:
            symbol: Trading symbol
            pnl: Profit/loss amount
        """
        if not OTEL_AVAILABLE or not self.pnl_histogram:
            return

        self.pnl_histogram.record(pnl, {"symbol": symbol})

    def record_error(self, error_type: str, component: str):
        """
        Record error occurrence

        Args:
            error_type: Type of error
            component: Component where error occurred
        """
        if not OTEL_AVAILABLE or not self.error_counter:
            return

        self.error_counter.add(1, {
            "error_type": error_type,
            "component": component
        })

    def shutdown(self):
        """Shutdown observability and flush pending data"""
        if not OTEL_AVAILABLE:
            return

        try:
            # Shutdown trace provider
            if self.config.enable_traces:
                trace.get_tracer_provider().shutdown()

            # Shutdown meter provider
            if self.config.enable_metrics:
                metrics.get_meter_provider().shutdown()

            logger.info("✓ Observability shutdown complete")
        except Exception as e:
            logger.error(f"Error during observability shutdown: {e}")


def trace_async(operation_name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator for tracing async functions

    Usage:
        @trace_async("execute_trade")
        async def execute_trade(symbol, quantity):
            # ... implementation ...

    Args:
        operation_name: Name of the operation (defaults to function name)
        attributes: Additional attributes for the span
    """
    def decorator(func: Callable):
        nonlocal operation_name
        if operation_name is None:
            operation_name = func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not OTEL_AVAILABLE:
                return await func(*args, **kwargs)

            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(operation_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return wrapper
    return decorator


def trace_sync(operation_name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator for tracing synchronous functions

    Usage:
        @trace_sync("calculate_risk")
        def calculate_risk(portfolio):
            # ... implementation ...

    Args:
        operation_name: Name of the operation (defaults to function name)
        attributes: Additional attributes for the span
    """
    def decorator(func: Callable):
        nonlocal operation_name
        if operation_name is None:
            operation_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not OTEL_AVAILABLE:
                return func(*args, **kwargs)

            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(operation_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return wrapper
    return decorator


# Global observability instance
_global_observability: Optional[ObservabilityManager] = None


def initialize_observability(config: Optional[SigNozConfig] = None) -> ObservabilityManager:
    """
    Initialize global observability manager

    Args:
        config: SigNoz configuration

    Returns:
        ObservabilityManager instance
    """
    global _global_observability
    _global_observability = ObservabilityManager(config)
    return _global_observability


def get_observability() -> Optional[ObservabilityManager]:
    """
    Get global observability manager

    Returns:
        ObservabilityManager instance or None if not initialized
    """
    return _global_observability


def shutdown_observability():
    """Shutdown global observability manager"""
    global _global_observability
    if _global_observability:
        _global_observability.shutdown()
        _global_observability = None


__all__ = [
    'SigNozConfig',
    'ObservabilityManager',
    'trace_async',
    'trace_sync',
    'initialize_observability',
    'get_observability',
    'shutdown_observability',
    'OTEL_AVAILABLE'
]
