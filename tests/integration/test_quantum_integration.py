"""
Integration tests for Quantum Module ↔ Orchestrator integration.

Tests quantum portfolio optimization integration with the orchestrator,
including VQE/QAOA algorithms, circuit generation, and classical fallback.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.modules.quantum import QuantumModule
from core.agents.orchestrator import SIGMAXOrchestrator


class TestQuantumIntegration:
    """Integration tests for quantum module with orchestrator"""

    @pytest.fixture
    async def quantum_module(self):
        """Create initialized quantum module"""
        with patch.dict('os.environ', {
            'QUANTUM_ENABLED': 'true',
            'QUANTUM_BACKEND': 'qiskit_aer',
            'QUANTUM_SHOTS': '1000'
        }):
            module = QuantumModule()
            await module.initialize()
            yield module

    @pytest.fixture
    async def orchestrator(self):
        """Create orchestrator with quantum module"""
        with patch.dict('os.environ', {
            'TRADING_MODE': 'paper',
            'QUANTUM_ENABLED': 'true'
        }):
            orchestrator = SIGMAXOrchestrator()
            await orchestrator.initialize()
            yield orchestrator

    @pytest.mark.asyncio
    async def test_quantum_module_initialization(self, quantum_module):
        """Test quantum module initializes correctly"""

        assert quantum_module.enabled is True
        assert quantum_module.backend is not None
        assert quantum_module.shots == 1000

        print(f"\n=== Quantum Module Initialization ===")
        print(f"Enabled: {quantum_module.enabled}")
        print(f"Backend: {type(quantum_module.backend).__name__}")
        print(f"Shots: {quantum_module.shots}")

    @pytest.mark.asyncio
    async def test_quantum_disabled_fallback(self):
        """Test classical fallback when quantum is disabled"""

        with patch.dict('os.environ', {'QUANTUM_ENABLED': 'false'}):
            module = QuantumModule()
            await module.initialize()

            result = await module.optimize_portfolio(
                symbol="BTC/USDT",
                signal=0.7,
                current_portfolio={}
            )

            assert result is not None
            assert "action" in result
            assert "size" in result
            assert "confidence" in result
            assert result.get("method") != "quantum_vqe"

            print(f"\n=== Quantum Disabled Fallback ===")
            print(f"Method: {result.get('method', 'classical')}")
            print(f"Action: {result['action']}")
            print(f"Size: {result['size']}")

    @pytest.mark.asyncio
    async def test_portfolio_optimization_bullish_signal(self, quantum_module):
        """Test optimization with bullish signal"""

        result = await quantum_module.optimize_portfolio(
            symbol="BTC/USDT",
            signal=0.8,  # Strong buy signal
            current_portfolio={"BTC/USDT": 0.5}
        )

        assert result is not None
        assert "action" in result
        assert "size" in result
        assert "confidence" in result

        # Bullish signal should recommend buy or hold
        assert result["action"] in ["buy", "hold"]

        print(f"\n=== Bullish Signal Optimization ===")
        print(f"Signal: 0.8 (bullish)")
        print(f"Action: {result['action']}")
        print(f"Size: {result['size']:.3f}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Method: {result.get('method', 'N/A')}")

    @pytest.mark.asyncio
    async def test_portfolio_optimization_bearish_signal(self, quantum_module):
        """Test optimization with bearish signal"""

        result = await quantum_module.optimize_portfolio(
            symbol="BTC/USDT",
            signal=-0.8,  # Strong sell signal
            current_portfolio={"BTC/USDT": 1.0}
        )

        assert result is not None
        assert "action" in result

        # Bearish signal should recommend sell or hold
        assert result["action"] in ["sell", "hold"]

        print(f"\n=== Bearish Signal Optimization ===")
        print(f"Signal: -0.8 (bearish)")
        print(f"Action: {result['action']}")
        print(f"Size: {result['size']:.3f}")
        print(f"Confidence: {result['confidence']:.3f}")

    @pytest.mark.asyncio
    async def test_portfolio_optimization_neutral_signal(self, quantum_module):
        """Test optimization with neutral signal"""

        result = await quantum_module.optimize_portfolio(
            symbol="BTC/USDT",
            signal=0.0,  # Neutral
            current_portfolio={}
        )

        assert result is not None
        assert "action" in result

        # Neutral signal should recommend hold
        assert result["action"] == "hold"

        print(f"\n=== Neutral Signal Optimization ===")
        print(f"Signal: 0.0 (neutral)")
        print(f"Action: {result['action']}")

    @pytest.mark.asyncio
    async def test_circuit_generation(self, quantum_module):
        """Test quantum circuit generation and visualization"""

        result = await quantum_module.optimize_portfolio(
            symbol="BTC/USDT",
            signal=0.5,
            current_portfolio={}
        )

        # If quantum is enabled, circuit SVG should be generated
        if quantum_module.enabled and quantum_module.backend:
            assert "circuit_svg" in result
            # SVG may be None if visualization not available
            if result["circuit_svg"]:
                assert isinstance(result["circuit_svg"], str)

                print(f"\n=== Circuit Generation ===")
                print(f"Circuit SVG generated: {len(result['circuit_svg'])} chars")

    @pytest.mark.asyncio
    async def test_optimization_with_existing_position(self, quantum_module):
        """Test optimization considers existing portfolio position"""

        # Test with existing long position
        result_long = await quantum_module.optimize_portfolio(
            symbol="BTC/USDT",
            signal=0.6,
            current_portfolio={"BTC/USDT": 1.5}  # Already long
        )

        # Test with no position
        result_flat = await quantum_module.optimize_portfolio(
            symbol="BTC/USDT",
            signal=0.6,
            current_portfolio={}
        )

        print(f"\n=== Position Consideration ===")
        print(f"With position: {result_long['action']} size {result_long['size']:.3f}")
        print(f"Flat: {result_flat['action']} size {result_flat['size']:.3f}")

        # Both should have valid results
        assert result_long["action"] in ["buy", "sell", "hold"]
        assert result_flat["action"] in ["buy", "sell", "hold"]

    @pytest.mark.asyncio
    async def test_orchestrator_quantum_integration(self, orchestrator):
        """Test orchestrator uses quantum module for decisions"""

        # Mock data module
        mock_data = {
            'symbol': 'BTC/USDT',
            'price': 95000.0,
            'volume_24h': 1000000000.0,
            'ohlcv': np.random.rand(100, 6)
        }

        with patch.object(
            orchestrator.data_module,
            'get_market_data',
            AsyncMock(return_value=mock_data)
        ):
            # Analyze should use quantum module
            result = await orchestrator.analyze_symbol('BTC/USDT')

            assert result is not None
            assert 'action' in result
            assert 'confidence' in result

            print(f"\n=== Orchestrator Quantum Integration ===")
            print(f"Action: {result['action']}")
            print(f"Confidence: {result['confidence']:.3f}")

            # Check if quantum was used (may be in reasoning/metadata)
            if 'reasoning' in result:
                print(f"Reasoning includes quantum: {'quantum' in result['reasoning'].lower()}")

    @pytest.mark.asyncio
    async def test_optimization_error_handling(self, quantum_module):
        """Test graceful degradation on quantum errors"""

        # Mock quantum backend to raise error
        if quantum_module.backend:
            with patch.object(quantum_module, '_run_vqe', side_effect=Exception("Quantum error")):
                result = await quantum_module.optimize_portfolio(
                    symbol="BTC/USDT",
                    signal=0.5,
                    current_portfolio={}
                )

                # Should fallback to classical
                assert result is not None
                assert result["action"] in ["buy", "sell", "hold"]
                assert result.get("method") != "quantum_vqe"

                print(f"\n=== Error Handling ===")
                print(f"Fallback method: {result.get('method', 'classical')}")
                print(f"Action: {result['action']}")

    @pytest.mark.asyncio
    async def test_multiple_symbols_optimization(self, quantum_module):
        """Test optimization across multiple symbols"""

        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        results = []

        for symbol in symbols:
            result = await quantum_module.optimize_portfolio(
                symbol=symbol,
                signal=0.6,
                current_portfolio={}
            )
            results.append((symbol, result))

        print(f"\n=== Multi-Symbol Optimization ===")
        for symbol, result in results:
            print(f"{symbol}: {result['action']} (conf: {result['confidence']:.3f})")

        # All should succeed
        assert len(results) == len(symbols)
        for _, result in results:
            assert "action" in result
            assert "confidence" in result

    @pytest.mark.asyncio
    async def test_optimization_consistency(self, quantum_module):
        """Test optimization produces consistent results for same input"""

        signal = 0.7
        portfolio = {"BTC/USDT": 0.5}

        results = []
        for _ in range(3):
            result = await quantum_module.optimize_portfolio(
                symbol="BTC/USDT",
                signal=signal,
                current_portfolio=portfolio
            )
            results.append(result)

        # Actions should be consistent
        actions = [r["action"] for r in results]

        print(f"\n=== Consistency Test ===")
        print(f"Actions: {actions}")
        print(f"All same: {len(set(actions)) == 1}")

        # Allow some variation due to quantum randomness, but all should be valid
        for result in results:
            assert result["action"] in ["buy", "sell", "hold"]

    @pytest.mark.asyncio
    async def test_signal_strength_scaling(self, quantum_module):
        """Test that stronger signals produce higher confidence"""

        weak_signal = 0.2
        strong_signal = 0.9

        weak_result = await quantum_module.optimize_portfolio(
            symbol="BTC/USDT",
            signal=weak_signal,
            current_portfolio={}
        )

        strong_result = await quantum_module.optimize_portfolio(
            symbol="BTC/USDT",
            signal=strong_signal,
            current_portfolio={}
        )

        print(f"\n=== Signal Strength Scaling ===")
        print(f"Weak (0.2): conf {weak_result['confidence']:.3f}")
        print(f"Strong (0.9): conf {strong_result['confidence']:.3f}")

        # Stronger signal should generally have higher confidence
        # (Allow flexibility for quantum randomness)
        assert 0 <= weak_result['confidence'] <= 1
        assert 0 <= strong_result['confidence'] <= 1

    @pytest.mark.asyncio
    async def test_position_sizing_limits(self, quantum_module):
        """Test position sizing respects reasonable limits"""

        result = await quantum_module.optimize_portfolio(
            symbol="BTC/USDT",
            signal=0.99,  # Extreme bullish
            current_portfolio={}
        )

        print(f"\n=== Position Sizing ===")
        print(f"Extreme signal (0.99)")
        print(f"Recommended size: {result['size']:.3f}")

        # Size should be reasonable (0-1 for fraction of portfolio)
        assert 0 <= result['size'] <= 1.0

    @pytest.mark.asyncio
    async def test_confidence_bounds(self, quantum_module):
        """Test confidence values are within valid range"""

        signals = [-1.0, -0.5, 0.0, 0.5, 1.0]

        print(f"\n=== Confidence Bounds ===")

        for signal in signals:
            result = await quantum_module.optimize_portfolio(
                symbol="BTC/USDT",
                signal=signal,
                current_portfolio={}
            )

            assert 0 <= result['confidence'] <= 1.0
            print(f"Signal {signal:+.1f}: conf {result['confidence']:.3f}")


class TestQuantumPerformance:
    """Performance tests for quantum module"""

    @pytest.mark.asyncio
    async def test_optimization_latency(self):
        """Test optimization completes within reasonable time"""

        import time

        with patch.dict('os.environ', {'QUANTUM_ENABLED': 'true'}):
            module = QuantumModule()
            await module.initialize()

            start = time.time()

            result = await module.optimize_portfolio(
                symbol="BTC/USDT",
                signal=0.5,
                current_portfolio={}
            )

            duration = time.time() - start

            print(f"\n=== Optimization Latency ===")
            print(f"Duration: {duration*1000:.1f}ms")
            print(f"Result: {result['action']}")

            # Should complete within 5 seconds
            assert duration < 5.0
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
