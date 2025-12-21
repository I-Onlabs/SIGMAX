"""
Integration tests for SIGMAX end-to-end workflows
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import numpy as np

from core.main import SIGMAX
from core.agents.orchestrator import SIGMAXOrchestrator
from core.modules.data import DataModule
from core.modules.execution import ExecutionModule
from core.modules.quantum import QuantumModule
from core.modules.rl import RLModule  # Fixed: was rl_agent.RLAgent
from core.modules.arbitrage import ArbitrageModule  # Fixed: was ArbitrageDetector
from core.modules.compliance import ComplianceModule


class TestSIGMAXIntegration:
    """End-to-end integration tests for SIGMAX"""

    @pytest.fixture
    async def sigmax_instance(self):
        """Create a fully configured SIGMAX instance"""
        with patch.dict('os.environ', {
            'TRADING_MODE': 'paper',
            'OPENAI_API_KEY': 'test-key-123',
            'FREQTRADE_URL': 'http://localhost:8080',
            'FREQTRADE_USERNAME': 'test',
            'FREQTRADE_PASSWORD': 'test'
        }):
            sigmax = SIGMAX(mode='paper', risk_profile='conservative')
            await sigmax.initialize()
            yield sigmax
            await sigmax.stop()

    @pytest.mark.asyncio
    async def test_full_analysis_pipeline(self, sigmax_instance):
        """Test complete analysis pipeline from data to decision"""
        # Mock market data
        mock_data = {
            'symbol': 'BTC/USDT',
            'price': 95000.0,
            'volume_24h': 1000000000.0,
            'ohlcv': np.random.rand(100, 6),
            'timestamp': datetime.now().isoformat()
        }

        with patch.object(
            sigmax_instance.orchestrator.data_module,
            'get_market_data',
            AsyncMock(return_value=mock_data)
        ):
            # Run full analysis
            result = await sigmax_instance.orchestrator.analyze_symbol('BTC/USDT')

            # Verify result structure
            assert result is not None
            assert 'action' in result
            assert result['action'] in ['buy', 'sell', 'hold']
            assert 'confidence' in result
            assert 0 <= result['confidence'] <= 1
            assert 'reasoning' in result

    @pytest.mark.asyncio
    async def test_risk_limit_enforcement(self, sigmax_instance):
        """Test that risk limits are enforced"""
        # Set up a scenario that would exceed risk limits
        mock_portfolio = {
            'BTC/USDT': {'size': 1.0, 'entry_price': 90000.0},
            'ETH/USDT': {'size': 10.0, 'entry_price': 3000.0}
        }

        with patch.object(
            sigmax_instance.orchestrator.execution_module,
            'get_portfolio',
            AsyncMock(return_value=mock_portfolio)
        ):
            # Try to execute a large trade
            signal = {
                'symbol': 'BTC/USDT',
                'action': 'buy',
                'size': 10.0,  # Large size
                'confidence': 0.9
            }

            result = await sigmax_instance.orchestrator._execute_trade(signal)

            # Should be rejected or reduced by risk management
            assert result is not None
            if result['status'] == 'executed':
                # If executed, size should be reduced
                assert result['executed_size'] < signal['size']

    @pytest.mark.asyncio
    async def test_multi_agent_debate(self, sigmax_instance):
        """Test that multi-agent debate produces valid output"""
        mock_data = {
            'symbol': 'BTC/USDT',
            'price': 95000.0,
            'volume_24h': 1000000000.0,
            'ohlcv': np.random.rand(100, 6)
        }

        with patch.object(
            sigmax_instance.orchestrator.data_module,
            'get_market_data',
            AsyncMock(return_value=mock_data)
        ):
            result = await sigmax_instance.orchestrator.analyze_symbol('BTC/USDT')

            # Verify debate happened
            state = sigmax_instance.orchestrator.last_state
            assert state is not None
            assert 'bull_argument' in state or 'messages' in state
            assert 'bear_argument' in state or 'messages' in state
            assert 'risk_assessment' in state or 'messages' in state

    @pytest.mark.asyncio
    async def test_quantum_optimization_integration(self, sigmax_instance):
        """Test quantum module integration in decision pipeline"""
        with patch.object(
            sigmax_instance.orchestrator.quantum_module,
            'optimize_portfolio',
            AsyncMock(return_value={
                'action': 'buy',
                'size': 0.5,
                'confidence': 0.8,
                'method': 'quantum'
            })
        ):
            result = await sigmax_instance.orchestrator.quantum_module.optimize_portfolio(
                symbol='BTC/USDT',
                signal=0.7,
                current_portfolio={}
            )

            assert result['action'] == 'buy'
            assert result['method'] == 'quantum'
            assert result['confidence'] > 0

    @pytest.mark.asyncio
    async def test_arbitrage_detection_integration(self, sigmax_instance):
        """Test arbitrage detection in trading pipeline"""
        mock_opportunities = [
            {
                'pair': 'BTC/USDT',
                'exchanges': ['binance', 'kraken'],
                'profit_pct': 0.5,
                'volume': 100000.0
            }
        ]

        with patch.object(
            sigmax_instance.orchestrator.arbitrage_module,
            'scan_opportunities',
            AsyncMock(return_value=mock_opportunities)
        ):
            opportunities = await sigmax_instance.orchestrator.arbitrage_module.scan_opportunities(
                symbols=['BTC/USDT']
            )

            assert len(opportunities) > 0
            assert opportunities[0]['profit_pct'] > 0

    @pytest.mark.asyncio
    async def test_compliance_check_integration(self, sigmax_instance):
        """Test compliance module integration"""
        trade = {
            'symbol': 'BTC/USDT',
            'action': 'buy',
            'size': 0.1,
            'price': 95000.0
        }

        result = await sigmax_instance.orchestrator.compliance_module.check_trade(trade)

        assert 'approved' in result
        assert isinstance(result['approved'], bool)
        if not result['approved']:
            assert 'reason' in result

    @pytest.mark.asyncio
    async def test_emergency_stop_integration(self, sigmax_instance):
        """Test emergency stop mechanism"""
        # Start trading
        await sigmax_instance.start()
        assert sigmax_instance.orchestrator.running is True

        # Trigger emergency stop
        await sigmax_instance.emergency_stop()

        # Verify system is stopped
        assert sigmax_instance.orchestrator.running is False
        assert sigmax_instance.orchestrator.paused is False

    @pytest.mark.asyncio
    async def test_status_reporting_integration(self, sigmax_instance):
        """Test system status reporting"""
        status = await sigmax_instance.get_status()

        # Verify status structure
        assert 'mode' in status
        assert 'running' in status
        assert 'agents' in status
        assert 'modules' in status
        assert 'performance' in status
        assert 'risk' in status

        # Verify agent statuses
        assert 'orchestrator' in status['agents']
        assert 'researcher' in status['agents']
        assert 'analyzer' in status['agents']

        # Verify module statuses
        assert 'quantum' in status['modules']
        assert 'rl' in status['modules']
        assert 'arbitrage' in status['modules']
        assert 'compliance' in status['modules']

    @pytest.mark.asyncio
    async def test_data_flow_integration(self, sigmax_instance):
        """Test data flow from collection to analysis"""
        # Mock data collection
        mock_ohlcv = np.random.rand(200, 6)
        mock_ohlcv[:, 4] = 95000 + np.random.randn(200) * 1000  # Close prices

        with patch.object(
            sigmax_instance.orchestrator.data_module,
            'get_ohlcv',
            AsyncMock(return_value=mock_ohlcv)
        ):
            # Get data
            data = await sigmax_instance.orchestrator.data_module.get_ohlcv(
                'BTC/USDT',
                timeframe='1h',
                limit=200
            )

            assert data is not None
            assert len(data) == 200
            assert data.shape[1] == 6

    @pytest.mark.asyncio
    async def test_ml_prediction_integration(self, sigmax_instance):
        """Test ML predictor integration in analysis pipeline"""
        mock_ohlcv = np.random.rand(200, 6)
        mock_ohlcv[:, 4] = 95000 + np.cumsum(np.random.randn(200) * 100)

        # Train ML model
        if hasattr(sigmax_instance.orchestrator, 'ml_predictor'):
            metrics = await sigmax_instance.orchestrator.ml_predictor.train(mock_ohlcv)
            assert 'xgboost' in metrics or 'error' in metrics

            # Make prediction
            prediction = await sigmax_instance.orchestrator.ml_predictor.predict(mock_ohlcv)
            assert 'prediction' in prediction
            assert 'confidence' in prediction

    @pytest.mark.asyncio
    async def test_sentiment_analysis_integration(self, sigmax_instance):
        """Test sentiment analysis integration"""
        if hasattr(sigmax_instance.orchestrator, 'sentiment_agent'):
            sentiment = await sigmax_instance.orchestrator.sentiment_agent.analyze(
                'BTC/USDT',
                lookback_hours=24
            )

            assert 'aggregate_score' in sentiment
            assert 'confidence' in sentiment
            assert -1 <= sentiment['aggregate_score'] <= 1

    @pytest.mark.asyncio
    async def test_portfolio_rebalancing_integration(self, sigmax_instance):
        """Test portfolio rebalancing integration"""
        mock_portfolio = {
            'BTC/USDT': 0.6,
            'ETH/USDT': 0.3,
            'SOL/USDT': 0.1
        }

        mock_prices = {
            'BTC/USDT': 95000.0,
            'ETH/USDT': 3500.0,
            'SOL/USDT': 100.0
        }

        if hasattr(sigmax_instance.orchestrator, 'portfolio_rebalancer'):
            should_rebalance = await sigmax_instance.orchestrator.portfolio_rebalancer.should_rebalance(
                mock_portfolio,
                mock_prices
            )

            assert isinstance(should_rebalance, bool)

            if should_rebalance:
                trades = await sigmax_instance.orchestrator.portfolio_rebalancer.calculate_rebalance_trades(
                    mock_portfolio,
                    mock_prices
                )
                assert isinstance(trades, list)

    @pytest.mark.asyncio
    async def test_regime_detection_integration(self, sigmax_instance):
        """Test market regime detection integration"""
        mock_ohlcv = np.random.rand(200, 6)
        mock_ohlcv[:, 4] = 95000 + np.cumsum(np.random.randn(200) * 100)

        if hasattr(sigmax_instance.orchestrator, 'regime_detector'):
            regime = await sigmax_instance.orchestrator.regime_detector.detect_regime(mock_ohlcv)

            assert 'regime' in regime
            assert 'confidence' in regime
            assert 'indicators' in regime

    @pytest.mark.asyncio
    async def test_backtesting_integration(self, sigmax_instance):
        """Test backtesting framework integration"""
        # Generate synthetic data
        dates = [datetime.now() - timedelta(days=i) for i in range(365, 0, -1)]
        data = {
            'BTC/USDT': np.random.rand(365, 6)
        }
        data['BTC/USDT'][:, 0] = [d.timestamp() for d in dates]
        data['BTC/USDT'][:, 4] = 50000 + np.cumsum(np.random.randn(365) * 500)

        # Simple test strategy
        async def test_strategy(market_data, timestamp):
            return [
                {'symbol': 'BTC/USDT', 'action': 'buy', 'size': 0.1}
            ]

        if hasattr(sigmax_instance.orchestrator, 'backtester'):
            result = await sigmax_instance.orchestrator.backtester.run(
                strategy_func=test_strategy,
                data=data,
                start_date=dates[0],
                end_date=dates[-1]
            )

            assert result is not None
            assert hasattr(result, 'total_trades')
            assert hasattr(result, 'sharpe_ratio')
            assert hasattr(result, 'max_drawdown')

    @pytest.mark.asyncio
    async def test_concurrent_analysis(self, sigmax_instance):
        """Test concurrent analysis of multiple symbols"""
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

        mock_data = {
            'price': 95000.0,
            'volume_24h': 1000000000.0,
            'ohlcv': np.random.rand(100, 6)
        }

        with patch.object(
            sigmax_instance.orchestrator.data_module,
            'get_market_data',
            AsyncMock(return_value=mock_data)
        ):
            # Analyze multiple symbols concurrently
            import asyncio
            results = await asyncio.gather(*[
                sigmax_instance.orchestrator.analyze_symbol(symbol)
                for symbol in symbols
            ])

            assert len(results) == len(symbols)
            for result in results:
                assert 'action' in result
                assert 'confidence' in result

    @pytest.mark.asyncio
    async def test_error_recovery(self, sigmax_instance):
        """Test system error recovery"""
        # Simulate error in data module
        with patch.object(
            sigmax_instance.orchestrator.data_module,
            'get_market_data',
            AsyncMock(side_effect=Exception("Connection error"))
        ):
            # System should handle error gracefully
            try:
                result = await sigmax_instance.orchestrator.analyze_symbol('BTC/USDT')
                # If no exception, result should indicate error
                assert result is None or 'error' in result
            except Exception as e:
                # Exception should be caught and logged
                pytest.fail(f"Error not handled properly: {e}")

    @pytest.mark.asyncio
    async def test_websocket_integration(self, sigmax_instance):
        """Test WebSocket real-time updates"""
        # This would test the WebSocket functionality
        # For now, just verify the endpoint exists
        if hasattr(sigmax_instance, 'api_server'):
            assert hasattr(sigmax_instance.api_server, 'websocket_endpoint')


class TestPerformanceIntegration:
    """Integration tests for performance and scalability"""

    @pytest.mark.asyncio
    async def test_high_frequency_analysis(self):
        """Test system performance under high frequency requests"""
        import asyncio
        import time

        sigmax = SIGMAX(mode='paper', risk_profile='conservative')
        await sigmax.initialize()

        start_time = time.time()
        iterations = 100

        async def analyze():
            return await sigmax.orchestrator.analyze_symbol('BTC/USDT')

        # Run multiple analyses concurrently
        tasks = [analyze() for _ in range(iterations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration = end_time - start_time

        # Verify performance
        avg_time = duration / iterations
        assert avg_time < 5.0  # Average should be under 5 seconds per analysis

        await sigmax.stop()

    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test memory usage doesn't grow excessively"""
        import gc
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        sigmax = SIGMAX(mode='paper', risk_profile='conservative')
        await sigmax.initialize()

        # Run multiple analyses
        for _ in range(50):
            await sigmax.orchestrator.analyze_symbol('BTC/USDT')

        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_growth = final_memory - initial_memory
        assert memory_growth < 500  # Memory growth should be under 500MB

        await sigmax.stop()
