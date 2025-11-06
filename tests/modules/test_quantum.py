"""
Unit tests for Quantum Module
"""

import pytest
from unittest.mock import Mock, patch
import numpy as np

from core.modules.quantum import QuantumModule


class TestQuantumModule:
    """Test suite for quantum portfolio optimization"""

    @pytest.fixture
    def quantum_module(self):
        """Create quantum module instance"""
        return QuantumModule()

    @pytest.mark.asyncio
    async def test_quantum_module_initialization(self, quantum_module):
        """Test quantum module initializes"""
        await quantum_module.initialize()

        assert quantum_module is not None

    @pytest.mark.asyncio
    async def test_optimize_portfolio_returns_result(self, quantum_module):
        """Test portfolio optimization returns a result"""
        await quantum_module.initialize()

        result = await quantum_module.optimize_portfolio(
            symbol='BTC/USDT',
            signal=0.5,
            current_portfolio={}
        )

        assert 'action' in result
        assert 'size' in result
        assert 'confidence' in result

    @pytest.mark.asyncio
    async def test_optimize_portfolio_buy_signal(self, quantum_module):
        """Test optimization with strong buy signal"""
        await quantum_module.initialize()

        result = await quantum_module.optimize_portfolio(
            symbol='BTC/USDT',
            signal=0.8,  # Strong positive signal
            current_portfolio={}
        )

        assert result['action'] == 'buy'
        assert result['size'] > 0

    @pytest.mark.asyncio
    async def test_optimize_portfolio_sell_signal(self, quantum_module):
        """Test optimization with strong sell signal"""
        await quantum_module.initialize()

        result = await quantum_module.optimize_portfolio(
            symbol='BTC/USDT',
            signal=-0.8,  # Strong negative signal
            current_portfolio={}
        )

        assert result['action'] == 'sell'

    @pytest.mark.asyncio
    async def test_optimize_portfolio_hold_signal(self, quantum_module):
        """Test optimization with neutral signal"""
        await quantum_module.initialize()

        result = await quantum_module.optimize_portfolio(
            symbol='BTC/USDT',
            signal=0.1,  # Weak signal
            current_portfolio={}
        )

        assert result['action'] == 'hold'

    @pytest.mark.asyncio
    async def test_circuit_generation(self, quantum_module):
        """Test quantum circuit is generated"""
        await quantum_module.initialize()

        if quantum_module.enabled:
            signal = 0.5
            circuit = await quantum_module._build_optimization_circuit(signal)

            assert circuit is not None
            assert circuit.num_qubits == 3  # As per design

    @pytest.mark.asyncio
    async def test_classical_fallback(self, quantum_module):
        """Test classical fallback when quantum unavailable"""
        quantum_module.enabled = False

        result = quantum_module._classical_fallback(0.6)

        assert result['action'] == 'buy'
        assert result['method'] == 'classical'

    @pytest.mark.asyncio
    async def test_get_status(self, quantum_module):
        """Test getting quantum module status"""
        await quantum_module.initialize()

        status = await quantum_module.get_status()

        assert 'enabled' in status
        assert 'backend' in status
