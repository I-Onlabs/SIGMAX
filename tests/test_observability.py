"""
Tests for SigNoz Observability Module

Tests OpenTelemetry instrumentation, tracing, metrics, and SigNoz integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from core.modules.observability import (
    SigNozConfig,
    ObservabilityManager,
    trace_async,
    trace_sync,
    initialize_observability,
    get_observability,
    shutdown_observability,
    OTEL_AVAILABLE
)


class TestSigNozConfig:
    """Test SigNoz configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = SigNozConfig()
        assert config.service_name == "sigmax"
        assert config.service_version == "1.0.0"
        assert config.environment == "development"
        assert config.enable_traces is True
        assert config.enable_metrics is True
        assert config.enable_logs is True

    def test_custom_config(self):
        """Test custom configuration"""
        config = SigNozConfig(
            endpoint="http://custom:4318",
            service_name="test-service",
            service_version="2.0.0",
            environment="production",
            enable_console=True
        )
        assert config.endpoint == "http://custom:4318"
        assert config.service_name == "test-service"
        assert config.service_version == "2.0.0"
        assert config.environment == "production"
        assert config.enable_console is True

    def test_config_to_dict(self):
        """Test configuration serialization"""
        config = SigNozConfig(service_name="test")
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["service_name"] == "test"
        assert "endpoint" in config_dict
        assert "enable_traces" in config_dict


class TestObservabilityManager:
    """Test observability manager"""

    def test_manager_initialization_without_otel(self):
        """Test manager initialization when OpenTelemetry not available"""
        if not OTEL_AVAILABLE:
            manager = ObservabilityManager()
            assert manager.is_initialized is False
            assert manager.tracer is None
            assert manager.meter is None

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_manager_initialization_with_otel(self):
        """Test manager initialization with OpenTelemetry"""
        config = SigNozConfig(enable_console=True)
        manager = ObservabilityManager(config)

        assert manager.is_initialized is True
        assert manager.config == config

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_trace_operation_context_manager(self):
        """Test trace operation context manager"""
        config = SigNozConfig(enable_console=True)
        manager = ObservabilityManager(config)

        with manager.trace_operation("test_operation", {"key": "value"}):
            # Operation code
            pass

        # Should complete without errors

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_record_trade(self):
        """Test recording trade metrics"""
        config = SigNozConfig(enable_console=True)
        manager = ObservabilityManager(config)

        # Should not raise errors
        manager.record_trade(
            symbol="BTC/USDT",
            side="buy",
            quantity=1.0,
            price=50000.0,
            latency_ms=100.5,
            success=True
        )

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_record_position_change(self):
        """Test recording position changes"""
        config = SigNozConfig(enable_console=True)
        manager = ObservabilityManager(config)

        manager.record_position_change("BTC/USDT", +1)  # Open position
        manager.record_position_change("ETH/USDT", -1)  # Close position

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_record_pnl(self):
        """Test recording profit/loss"""
        config = SigNozConfig(enable_console=True)
        manager = ObservabilityManager(config)

        manager.record_pnl("BTC/USDT", 1000.0)   # Profit
        manager.record_pnl("ETH/USDT", -500.0)   # Loss

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_record_error(self):
        """Test recording errors"""
        config = SigNozConfig(enable_console=True)
        manager = ObservabilityManager(config)

        manager.record_error("ConnectionError", "execution_module")
        manager.record_error("ValidationError", "compliance_module")

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_shutdown(self):
        """Test observability shutdown"""
        config = SigNozConfig(enable_console=True)
        manager = ObservabilityManager(config)

        # Should shutdown without errors
        manager.shutdown()


class TestTraceDecorators:
    """Test tracing decorators"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    async def test_trace_async_decorator(self):
        """Test async function tracing decorator"""
        config = SigNozConfig(enable_console=True)
        manager = ObservabilityManager(config)

        @trace_async("async_operation")
        async def async_function(x, y):
            await asyncio.sleep(0.01)
            return x + y

        result = await async_function(1, 2)
        assert result == 3

    @pytest.mark.asyncio
    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    async def test_trace_async_decorator_with_exception(self):
        """Test async decorator handles exceptions"""
        config = SigNozConfig(enable_console=True)
        manager = ObservabilityManager(config)

        @trace_async("failing_async_operation")
        async def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await failing_function()

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_trace_sync_decorator(self):
        """Test sync function tracing decorator"""
        config = SigNozConfig(enable_console=True)
        manager = ObservabilityManager(config)

        @trace_sync("sync_operation")
        def sync_function(x, y):
            return x * y

        result = sync_function(3, 4)
        assert result == 12

    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    def test_trace_sync_decorator_with_exception(self):
        """Test sync decorator handles exceptions"""
        config = SigNozConfig(enable_console=True)
        manager = ObservabilityManager(config)

        @trace_sync("failing_sync_operation")
        def failing_function():
            raise RuntimeError("Test error")

        with pytest.raises(RuntimeError, match="Test error"):
            failing_function()


class TestGlobalObservability:
    """Test global observability functions"""

    def test_initialize_and_get_observability(self):
        """Test initializing and getting global observability"""
        config = SigNozConfig(service_name="global_test")
        manager = initialize_observability(config)

        assert manager is not None
        assert get_observability() == manager

        # Cleanup
        shutdown_observability()
        assert get_observability() is None

    def test_shutdown_without_initialization(self):
        """Test shutdown without initialization"""
        # Should not raise errors
        shutdown_observability()


class TestIntegration:
    """Test integration scenarios"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not OTEL_AVAILABLE, reason="OpenTelemetry not available")
    async def test_full_trading_workflow(self):
        """Test full trading workflow with observability"""
        # Initialize
        config = SigNozConfig(
            service_name="test_trading",
            enable_console=True
        )
        manager = initialize_observability(config)

        # Simulate trading operations
        @trace_async("execute_trade")
        async def execute_trade(symbol, side, quantity):
            await asyncio.sleep(0.01)  # Simulate execution
            manager.record_trade(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=50000.0,
                latency_ms=10.0,
                success=True
            )
            return {"success": True, "order_id": "12345"}

        # Execute trade
        result = await execute_trade("BTC/USDT", "buy", 1.0)
        assert result["success"] is True

        # Record position change
        manager.record_position_change("BTC/USDT", +1)

        # Record PnL
        manager.record_pnl("BTC/USDT", 500.0)

        # Cleanup
        shutdown_observability()

    def test_observability_disabled_gracefully(self):
        """Test that code works when observability is disabled"""
        @trace_sync("operation")
        def some_operation(x):
            return x * 2

        @trace_async("async_operation")
        async def some_async_operation(x):
            return x * 3

        # Should work even without observability initialized
        assert some_operation(5) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
