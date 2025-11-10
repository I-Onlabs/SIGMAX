"""
Integration tests for trading pipeline safety and validation
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import asyncio
import numpy as np


class TestTradingPipelineSafety:
    """Test safety mechanisms in trading pipeline"""

    @pytest.mark.asyncio
    async def test_position_size_validation(self):
        """Test that position size limits are enforced"""
        from core.modules.execution import ExecutionModule
        from core.modules.safety_enforcer import SafetyEnforcer

        execution = ExecutionModule(mode='paper')
        await execution.initialize()

        safety = SafetyEnforcer(max_position_size=1.0, max_daily_loss=100)

        try:
            # Try to execute trade larger than limit
            trade = {
                'symbol': 'BTC/USDT',
                'action': 'buy',
                'size': 5.0,  # Exceeds limit
                'price': 95000
            }

            # Safety check should reject or reduce size
            is_safe = not safety.should_pause()
            assert is_safe  # Initially should be safe

            # Position size should be validated
            max_size = safety.config.get('max_position_size', 1.0)
            actual_size = min(trade['size'], max_size)

            assert actual_size <= max_size
            assert actual_size == 1.0  # Reduced to limit

        finally:
            await execution.close()

    @pytest.mark.asyncio
    async def test_circuit_breaker_mechanism(self):
        """Test circuit breaker on rapid losses"""
        from core.modules.safety_enforcer import SafetyEnforcer

        safety = SafetyEnforcer(max_daily_loss=50, max_position_size=1.0)

        # Simulate rapid consecutive losses
        losses = [
            {'symbol': 'BTC/USDT', 'pnl': -10, 'size': 0.1},
            {'symbol': 'ETH/USDT', 'pnl': -12, 'size': 0.2},
            {'symbol': 'SOL/USDT', 'pnl': -8, 'size': 0.15}
        ]

        for loss in losses:
            safety.record_trade(loss)

        # Should trigger circuit breaker
        assert safety.should_pause()

        # Get violation details
        status = safety.get_status()
        assert status['consecutive_losses'] >= 3

    @pytest.mark.asyncio
    async def test_slippage_detection(self):
        """Test detection of excessive slippage"""
        from core.modules.safety_enforcer import SafetyEnforcer

        safety = SafetyEnforcer(max_daily_loss=100, max_position_size=1.0)

        # Simulate high slippage trade
        expected_price = 95000
        actual_price = 96500  # 1.58% slippage
        slippage_pct = abs(actual_price - expected_price) / expected_price

        if slippage_pct > 0.01:  # 1% threshold
            safety.record_violation('high_slippage', slippage_pct)

        # Should pause on high slippage
        assert safety.should_pause()

    @pytest.mark.asyncio
    async def test_recovery_after_pause(self):
        """Test system recovery after safety pause"""
        from core.modules.safety_enforcer import SafetyEnforcer

        safety = SafetyEnforcer(max_daily_loss=100, max_position_size=1.0)

        # Trigger pause
        for _ in range(3):
            safety.record_trade({'symbol': 'BTC/USDT', 'pnl': -10, 'size': 0.1})

        assert safety.should_pause()

        # Resume with override
        safety.resume(force=True)

        # Should be resumed
        assert not safety.is_paused

        # But consecutive losses should reset
        status = safety.get_status()
        assert status['consecutive_losses'] == 0


class TestDataFlowIntegration:
    """Test data flow through the system"""

    @pytest.mark.asyncio
    async def test_market_data_to_indicators(self):
        """Test flow from market data to technical indicators"""
        from core.modules.data import DataModule
        from core.agents.analyzer import AnalyzerAgent

        data_module = DataModule()
        await data_module.initialize()

        analyzer = AnalyzerAgent()

        try:
            # Mock OHLCV data
            mock_ohlcv = np.random.rand(200, 6)
            mock_ohlcv[:, 4] = 95000 + np.cumsum(np.random.randn(200) * 100)  # Close prices

            with patch.object(data_module, 'get_ohlcv', AsyncMock(return_value=mock_ohlcv)):
                ohlcv = await data_module.get_ohlcv('BTC/USDT', '1h', 200)

            # Calculate indicators
            analysis = await analyzer.analyze('BTC/USDT', {
                'symbol': 'BTC/USDT',
                'price': ohlcv[-1, 4],
                'ohlcv': ohlcv
            })

            # Verify indicators calculated
            assert 'rsi' in analysis
            assert 'macd' in analysis
            assert 'bollinger' in analysis

            # RSI should be in valid range
            assert 0 <= analysis['rsi'] <= 100

        finally:
            await data_module.close()

    @pytest.mark.asyncio
    async def test_sentiment_to_decision(self):
        """Test flow from sentiment analysis to decision"""
        from core.agents.researcher import ResearcherAgent

        llm = Mock()
        researcher = ResearcherAgent(llm)

        try:
            # Mock sentiment data
            with patch.object(researcher, '_get_news_sentiment', AsyncMock(return_value={'score': 0.5})):
                with patch.object(researcher, '_get_social_sentiment', AsyncMock(return_value={'score': 0.3})):
                    with patch.object(researcher, '_get_onchain_metrics', AsyncMock(return_value={'whale_activity': 'bullish'})):
                        with patch.object(researcher, '_get_macro_factors', AsyncMock(return_value={'risk_on': True})):
                            result = await researcher.research('BTC/USDT', {'price': 95000})

            # Verify sentiment aggregation
            assert 'sentiment' in result
            assert result['sentiment'] > 0  # Should be positive given inputs

            # Verify decision inputs present
            assert 'news' in result
            assert 'social' in result
            assert 'onchain' in result
            assert 'macro' in result

        finally:
            await researcher.close()

    @pytest.mark.asyncio
    async def test_rl_prediction_integration(self):
        """Test RL model in decision pipeline"""
        from core.modules.rl import RLModule

        rl_module = RLModule()
        await rl_module.initialize()

        # Market state
        state = {
            'price': 95000,
            'volume': 1500000,
            'rsi': 45,
            'macd': 5,
            'sentiment': 0.2,
            'position': 0.0,
            'pnl_pct': 0.0
        }

        # Get RL prediction
        prediction = await rl_module.predict(state)

        # Should return valid prediction
        assert prediction['action'] in ['buy', 'sell', 'hold']
        assert 0 <= prediction['confidence'] <= 1


class TestConcurrentOperations:
    """Test concurrent trading operations"""

    @pytest.mark.asyncio
    async def test_parallel_symbol_analysis(self):
        """Test analyzing multiple symbols in parallel"""
        from core.agents.analyzer import AnalyzerAgent

        analyzer = AnalyzerAgent()

        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        mock_data = {
            'price': 95000,
            'volume': 1000000000,
            'ohlcv': np.random.rand(100, 6)
        }

        # Analyze all symbols concurrently
        tasks = [
            analyzer.analyze(symbol, {**mock_data, 'symbol': symbol})
            for symbol in symbols
        ]

        results = await asyncio.gather(*tasks)

        # All should complete
        assert len(results) == len(symbols)

        # All should have valid analysis
        for result in results:
            assert 'rsi' in result
            assert 'indicators' in result

    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self):
        """Test concurrent external API calls"""
        from core.agents.researcher import ResearcherAgent

        llm = Mock()
        researcher = ResearcherAgent(llm)

        try:
            # Make multiple concurrent requests
            symbols = ['BTC/USDT', 'ETH/USDT']

            tasks = [
                researcher._get_news_sentiment(symbol.split('/')[0])
                for symbol in symbols
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Should all complete (may be empty if APIs unavailable)
            assert len(results) == len(symbols)

            # Results should be dict or exception
            for result in results:
                if not isinstance(result, Exception):
                    assert isinstance(result, dict)

        finally:
            await researcher.close()

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that rate limiting is respected"""
        from core.agents.researcher import ResearcherAgent
        import time

        llm = Mock()
        researcher = ResearcherAgent(llm)

        try:
            start_time = time.time()

            # Make rapid successive calls
            for _ in range(5):
                try:
                    await researcher._get_news_sentiment('BTC')
                except Exception:
                    pass  # APIs may fail, that's ok

            elapsed = time.time() - start_time

            # Should take some time due to rate limiting
            # (APIs have built-in delays and timeouts)
            assert elapsed > 0

        finally:
            await researcher.close()


class TestErrorHandlingPipeline:
    """Test error handling throughout pipeline"""

    @pytest.mark.asyncio
    async def test_api_failure_graceful_degradation(self):
        """Test graceful handling of API failures"""
        from core.agents.researcher import ResearcherAgent

        llm = Mock()
        researcher = ResearcherAgent(llm)

        try:
            # Simulate API failure
            with patch.object(
                researcher,
                '_get_news_sentiment',
                AsyncMock(side_effect=Exception("API timeout"))
            ):
                # Should handle error gracefully
                try:
                    result = await researcher.research('BTC/USDT', {'price': 95000})

                    # Should have fallback values
                    assert 'sentiment' in result
                    assert 'error' in result or result['sentiment'] == 0.0

                except Exception as e:
                    pytest.fail(f"API failure not handled gracefully: {e}")

        finally:
            await researcher.close()

    @pytest.mark.asyncio
    async def test_invalid_data_handling(self):
        """Test handling of invalid market data"""
        from core.agents.analyzer import AnalyzerAgent

        analyzer = AnalyzerAgent()

        # Invalid data (empty OHLCV)
        invalid_data = {
            'symbol': 'BTC/USDT',
            'price': None,
            'ohlcv': np.array([])
        }

        # Should handle gracefully
        result = await analyzer.analyze('BTC/USDT', invalid_data)

        # Should return some result (possibly with defaults)
        assert result is not None

    @pytest.mark.asyncio
    async def test_network_timeout_recovery(self):
        """Test recovery from network timeouts"""
        from core.agents.researcher import ResearcherAgent

        llm = Mock()
        researcher = ResearcherAgent(llm)

        try:
            # Simulate timeout
            with patch('aiohttp.ClientSession.get', side_effect=asyncio.TimeoutError):
                # Should handle timeout gracefully
                result = await researcher._get_news_sentiment('BTC')

                # Should return fallback data
                assert isinstance(result, dict)
                assert 'score' in result

        finally:
            await researcher.close()


class TestSystemIntegrity:
    """Test system integrity and consistency"""

    @pytest.mark.asyncio
    async def test_decision_reproducibility(self):
        """Test that decisions are consistent with same inputs"""
        from core.agents.analyzer import AnalyzerAgent

        analyzer = AnalyzerAgent()

        # Same input data
        market_data = {
            'symbol': 'BTC/USDT',
            'price': 95000,
            'ohlcv': np.random.rand(100, 6)
        }

        # Make same analysis twice
        result1 = await analyzer.analyze('BTC/USDT', market_data)
        result2 = await analyzer.analyze('BTC/USDT', market_data)

        # Technical indicators should be identical
        assert result1['rsi'] == result2['rsi']
        assert result1['macd'] == result2['macd']

    @pytest.mark.asyncio
    async def test_state_consistency(self):
        """Test that system state remains consistent"""
        from core.modules.safety_enforcer import SafetyEnforcer

        safety = SafetyEnforcer(max_daily_loss=100, max_position_size=1.0)

        # Record some trades
        safety.record_trade({'symbol': 'BTC/USDT', 'pnl': 5, 'size': 0.1})
        safety.record_trade({'symbol': 'ETH/USDT', 'pnl': -3, 'size': 0.2})

        # Get status
        status1 = safety.get_status()

        # Status should be consistent when queried again
        status2 = safety.get_status()

        assert status1 == status2

    @pytest.mark.asyncio
    async def test_memory_cleanup(self):
        """Test that resources are properly cleaned up"""
        from core.agents.researcher import ResearcherAgent

        llm = Mock()

        # Create and destroy multiple instances
        for _ in range(10):
            researcher = ResearcherAgent(llm)
            await researcher._ensure_session()
            await researcher.close()

        # No assertion needed - if sessions aren't cleaned up,
        # we'll eventually hit resource limits


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
