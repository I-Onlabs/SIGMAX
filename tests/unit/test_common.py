"""
Unit tests for common utilities.
"""

import pytest
import time
from pkg.common import (
    Clock, get_timestamp_ns, calculate_latency_us, calculate_latency_ms,
    LatencyTracker, Config, load_config
)


class TestTiming:
    """Test timing utilities"""
    
    def test_get_timestamp_ns(self):
        """Test timestamp generation"""
        ts1 = get_timestamp_ns()
        time.sleep(0.001)
        ts2 = get_timestamp_ns()
        
        assert ts2 > ts1
        assert ts2 - ts1 > 1_000_000  # > 1ms in nanoseconds
    
    def test_clock_simulation(self):
        """Test simulated clock for replay"""
        start_time = 1000000000000000000  # Fixed time
        
        Clock.enable_simulation(start_time)
        
        ts1 = Clock.get_time_ns()
        assert ts1 == start_time
        
        Clock.advance_time(1_000_000)  # Advance 1ms
        ts2 = Clock.get_time_ns()
        assert ts2 == start_time + 1_000_000
        
        Clock.disable_simulation()
    
    def test_latency_calculation(self):
        """Test latency calculations"""
        start_ns = time.time_ns()
        time.sleep(0.001)  # 1ms delay
        end_ns = time.time_ns()
        
        latency_us = calculate_latency_us(start_ns, end_ns)
        latency_ms = calculate_latency_ms(start_ns, end_ns)
        
        assert latency_us > 1000  # > 1ms in microseconds
        assert latency_ms > 1  # > 1ms
    
    def test_latency_tracker(self):
        """Test LatencyTracker"""
        tracker = LatencyTracker("test_operation")
        
        tracker.checkpoint("parse")
        time.sleep(0.001)
        tracker.checkpoint("process")
        time.sleep(0.001)
        tracker.checkpoint("publish")
        
        latencies = tracker.get_all_latencies()
        
        assert "start→parse" in latencies
        assert "parse→process" in latencies
        assert "process→publish" in latencies
        
        total = tracker.get_latency_us()
        assert total > 2000  # > 2ms


class TestConfig:
    """Test configuration management"""
    
    def test_config_defaults(self):
        """Test default configuration"""
        config = Config()
        
        assert config.profile == "a"
        assert config.environment == "development"
        assert not config.is_production()
        assert config.is_profile_a()
        assert not config.is_profile_b()
    
    def test_risk_config_defaults(self):
        """Test risk configuration defaults"""
        config = Config()
        
        assert config.risk.max_position_usd == 10000.0
        assert config.risk.max_order_usd == 1000.0
        assert config.risk.max_leverage == 1.0
        assert config.risk.price_band_pct == 5.0


class TestDecisionLogic:
    """Test decision layer logic"""
    
    def test_l0_constraints(self):
        """Test L0 safety constraints"""
        from apps.decision.decision_engine import L0Constraints, DecisionContext
        from pkg.schemas import FeatureFrame
        
        config = Config()
        l0 = L0Constraints(config)
        
        # Valid feature frame
        features = FeatureFrame.create_empty(1)
        features.spread_bps = 5.0
        features.mid_price = 50000.0
        features.realized_vol = 0.005
        
        ctx = DecisionContext(features=features)
        assert l0.check(ctx) == True
        
        # Invalid - spread too small
        features.spread_bps = 0.5
        ctx = DecisionContext(features=features)
        assert l0.check(ctx) == False


class TestRiskEngine:
    """Test risk engine checks"""
    
    def test_risk_position_limit(self):
        """Test position limit check"""
        from apps.risk.risk_engine import RiskEngine
        from pkg.schemas import OrderIntent, Side, OrderType, TimeInForce
        
        config = Config()
        config.risk.max_position_usd = 1000.0
        config.risk.max_order_usd = 500.0
        
        engine = RiskEngine(config, None)
        
        # Valid order
        order = OrderIntent.create(
            symbol_id=1,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            qty=0.01,
            price=50000.0
        )
        
        passed, code, msg = engine._perform_checks(order)
        assert passed == True
        
        # Order too large
        order.qty = 100.0  # 100 * 50000 = 5M USD
        passed, code, msg = engine._perform_checks(order)
        assert passed == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
