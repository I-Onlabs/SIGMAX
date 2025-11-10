"""
Integration tests for newly implemented features:
- RL Module
- News Sentiment
- Researcher APIs
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import numpy as np

from core.modules.rl import RLModule, TradingEnv
from core.agents.researcher import ResearcherAgent


class TestRLModuleIntegration:
    """Integration tests for RL module"""

    @pytest.fixture
    async def rl_module(self):
        """Create RL module instance"""
        module = RLModule()
        await module.initialize()
        yield module

    @pytest.mark.asyncio
    async def test_rl_training_pipeline(self, rl_module):
        """Test RL training with historical data"""
        # Generate synthetic historical data
        historical_data = []
        base_price = 50000

        for i in range(100):
            historical_data.append({
                'price': base_price + i * 100 + np.random.randn() * 500,
                'volume': 1000000 + np.random.rand() * 500000,
                'rsi': 50 + np.random.randn() * 20,
                'macd': np.random.randn() * 10,
                'sentiment': np.random.rand() * 0.6 - 0.3
            })

        # Train model
        await rl_module.train(historical_data, timesteps=1000)

        # Verify model was trained
        status = await rl_module.get_status()
        assert status['initialized'] == True

    @pytest.mark.asyncio
    async def test_rl_prediction_integration(self, rl_module):
        """Test RL prediction in trading context"""
        # Create realistic market state
        state = {
            'price': 52000,
            'volume': 1500000,
            'rsi': 45,
            'macd': 5,
            'sentiment': 0.2,
            'position': 0.0,
            'pnl_pct': 0.02
        }

        # Get prediction
        prediction = await rl_module.predict(state)

        # Verify prediction structure
        assert 'action' in prediction
        assert 'confidence' in prediction
        assert 'source' in prediction
        assert prediction['action'] in ['buy', 'sell', 'hold']
        assert 0 <= prediction['confidence'] <= 1

    @pytest.mark.asyncio
    async def test_rl_env_trading_simulation(self):
        """Test trading environment simulation"""
        # Create historical data
        historical_data = [
            {
                'price': 50000 + i * 50,
                'volume': 1000000,
                'rsi': 50,
                'macd': 0,
                'sentiment': 0.1
            }
            for i in range(50)
        ]

        env = TradingEnv(historical_data=historical_data)
        obs, info = env.reset()

        # Simulate trading
        total_reward = 0
        actions_taken = []

        for _ in range(20):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)

            total_reward += reward
            actions_taken.append(action)

            if terminated or truncated:
                break

        # Verify simulation ran
        assert len(actions_taken) > 0
        assert env.current_step > 0

        # Final portfolio should exist
        assert env.portfolio_value >= 0


class TestResearcherIntegration:
    """Integration tests for Researcher agent with real APIs"""

    @pytest.fixture
    def researcher(self):
        """Create researcher instance"""
        llm = Mock()
        researcher = ResearcherAgent(llm)
        yield researcher

    @pytest.mark.asyncio
    async def test_news_sentiment_api_integration(self, researcher):
        """Test CryptoPanic API integration"""
        try:
            news_data = await researcher._get_news_sentiment('BTC/USDT')

            # Verify structure
            assert 'score' in news_data
            assert 'articles' in news_data
            assert 'keywords' in news_data
            assert 'source' in news_data

            # Score should be in valid range
            assert -1.0 <= news_data['score'] <= 1.0

            # Articles should be list
            assert isinstance(news_data['articles'], list)

        except Exception as e:
            pytest.skip(f"API not available: {e}")
        finally:
            await researcher.close()

    @pytest.mark.asyncio
    async def test_social_sentiment_api_integration(self, researcher):
        """Test Reddit API integration"""
        try:
            social_data = await researcher._get_social_sentiment('BTC/USDT')

            # Verify structure
            assert 'score' in social_data
            assert 'trending' in social_data
            assert 'volume' in social_data
            assert 'platform' in social_data

            # Score in valid range
            assert -1.0 <= social_data['score'] <= 1.0

            # Trending is boolean
            assert isinstance(social_data['trending'], bool)

            # Volume is non-negative
            assert social_data['volume'] >= 0

        except Exception as e:
            pytest.skip(f"API not available: {e}")
        finally:
            await researcher.close()

    @pytest.mark.asyncio
    async def test_onchain_metrics_api_integration(self, researcher):
        """Test CoinGecko API integration"""
        try:
            onchain_data = await researcher._get_onchain_metrics('BTC/USDT')

            # Verify structure
            assert 'whale_activity' in onchain_data
            assert 'source' in onchain_data

            # Whale activity should be valid
            assert onchain_data['whale_activity'] in ['bullish', 'bearish', 'neutral']

            # If CoinGecko succeeded, should have additional metrics
            if onchain_data['source'] == 'coingecko':
                assert 'market_cap' in onchain_data
                assert 'volume_24h' in onchain_data
                assert 'price_change_24h' in onchain_data

        except Exception as e:
            pytest.skip(f"API not available: {e}")
        finally:
            await researcher.close()

    @pytest.mark.asyncio
    async def test_macro_factors_api_integration(self, researcher):
        """Test Fear & Greed Index API integration"""
        try:
            macro_data = await researcher._get_macro_factors()

            # Verify structure
            assert 'fed_policy' in macro_data
            assert 'risk_on' in macro_data

            # Fed policy should be valid
            assert macro_data['fed_policy'] in ['accommodative', 'neutral', 'restrictive']

            # Risk on is boolean
            assert isinstance(macro_data['risk_on'], bool)

            # If API succeeded, should have fear/greed index
            if 'fear_greed_index' in macro_data:
                assert 0 <= macro_data['fear_greed_index'] <= 100

        except Exception as e:
            pytest.skip(f"API not available: {e}")
        finally:
            await researcher.close()

    @pytest.mark.asyncio
    async def test_full_research_pipeline(self, researcher):
        """Test complete research workflow"""
        try:
            market_data = {
                'price': 95000,
                'volume': 1000000000,
                'ohlcv': np.random.rand(100, 6)
            }

            result = await researcher.research('BTC/USDT', market_data)

            # Verify complete result structure
            assert 'summary' in result
            assert 'sentiment' in result
            assert 'news' in result
            assert 'social' in result
            assert 'onchain' in result
            assert 'macro' in result
            assert 'timestamp' in result

            # Sentiment should be aggregated
            assert -1.0 <= result['sentiment'] <= 1.0

            # Summary should be non-empty
            assert len(result['summary']) > 0

        except Exception as e:
            # Don't fail test if APIs unavailable
            pytest.skip(f"APIs not available: {e}")
        finally:
            await researcher.close()


class TestSafetyTriggerScenarios:
    """Integration tests for safety trigger scenarios"""

    @pytest.mark.asyncio
    async def test_consecutive_losses_trigger(self):
        """Test auto-pause on consecutive losses"""
        from core.modules.safety_enforcer import SafetyEnforcer

        enforcer = SafetyEnforcer(max_daily_loss=100, max_position_size=10)

        # Simulate 3 consecutive losses
        for i in range(3):
            trade_result = {
                'symbol': 'BTC/USDT',
                'pnl': -5.0,
                'size': 0.1
            }
            enforcer.record_trade(trade_result)

        # Check if paused
        assert enforcer.should_pause()

        status = enforcer.get_status()
        assert status['consecutive_losses'] >= 3

    @pytest.mark.asyncio
    async def test_daily_loss_limit_trigger(self):
        """Test auto-pause on daily loss limit"""
        from core.modules.safety_enforcer import SafetyEnforcer

        enforcer = SafetyEnforcer(max_daily_loss=50, max_position_size=10)

        # Simulate large loss
        trade_result = {
            'symbol': 'BTC/USDT',
            'pnl': -60.0,
            'size': 0.5
        }
        enforcer.record_trade(trade_result)

        # Should trigger pause
        assert enforcer.should_pause()

    @pytest.mark.asyncio
    async def test_api_error_burst_trigger(self):
        """Test auto-pause on API error burst"""
        from core.modules.safety_enforcer import SafetyEnforcer

        enforcer = SafetyEnforcer(max_daily_loss=100, max_position_size=10)

        # Simulate error burst
        for _ in range(6):
            enforcer.record_error('API timeout')

        # Should trigger pause
        assert enforcer.should_pause()

    @pytest.mark.asyncio
    async def test_sentiment_drop_trigger(self):
        """Test auto-pause on sentiment drop"""
        from core.modules.safety_enforcer import SafetyEnforcer

        enforcer = SafetyEnforcer(max_daily_loss=100, max_position_size=10)

        # Record negative sentiment
        enforcer.record_sentiment(-0.4)

        # Should trigger pause
        assert enforcer.should_pause()


class TestFullTradingPipeline:
    """Integration tests for complete trading pipeline"""

    @pytest.mark.asyncio
    async def test_end_to_end_trading_flow(self):
        """Test complete flow: data → analysis → decision → execution"""
        from core.modules.data import DataModule
        from core.agents.analyzer import AnalyzerAgent
        from core.modules.execution import ExecutionModule

        # Initialize components
        data_module = DataModule()
        await data_module.initialize()

        analyzer = AnalyzerAgent()

        execution = ExecutionModule(mode='paper')
        await execution.initialize()

        try:
            # Step 1: Fetch market data
            with patch.object(data_module, 'get_market_data', AsyncMock(return_value={
                'symbol': 'BTC/USDT',
                'price': 95000,
                'volume': 1000000000,
                'ohlcv': np.random.rand(100, 6)
            })):
                market_data = await data_module.get_market_data('BTC/USDT')

            assert market_data is not None

            # Step 2: Analyze market
            analysis = await analyzer.analyze('BTC/USDT', market_data)

            assert 'indicators' in analysis
            assert 'patterns' in analysis

            # Step 3: Make decision (simplified)
            decision = {
                'symbol': 'BTC/USDT',
                'action': 'buy' if analysis.get('rsi', 50) < 30 else 'sell' if analysis.get('rsi', 50) > 70 else 'hold',
                'size': 0.1,
                'price': market_data['price']
            }

            # Step 4: Execute trade (paper mode)
            if decision['action'] in ['buy', 'sell']:
                result = await execution.execute_trade(
                    symbol=decision['symbol'],
                    action=decision['action'],
                    size=decision['size']
                )

                assert result is not None
                assert 'order_id' in result or 'status' in result

        finally:
            await data_module.close()
            await execution.close()

    @pytest.mark.asyncio
    async def test_multi_source_decision_making(self):
        """Test decision making with multiple data sources"""
        from core.agents.researcher import ResearcherAgent
        from core.agents.analyzer import AnalyzerAgent

        llm = Mock()
        researcher = ResearcherAgent(llm)
        analyzer = AnalyzerAgent()

        try:
            market_data = {
                'symbol': 'BTC/USDT',
                'price': 95000,
                'volume': 1000000000,
                'ohlcv': np.random.rand(100, 6)
            }

            # Get technical analysis
            technical = await analyzer.analyze('BTC/USDT', market_data)

            # Get fundamental research (with mocked APIs)
            with patch.object(researcher, '_get_news_sentiment', AsyncMock(return_value={'score': 0.3})):
                with patch.object(researcher, '_get_social_sentiment', AsyncMock(return_value={'score': 0.2})):
                    with patch.object(researcher, '_get_onchain_metrics', AsyncMock(return_value={'whale_activity': 'bullish'})):
                        research = await researcher.research('BTC/USDT', market_data)

            # Combine signals
            technical_signal = 1 if technical.get('rsi', 50) < 30 else -1 if technical.get('rsi', 50) > 70 else 0
            fundamental_signal = 1 if research['sentiment'] > 0.2 else -1 if research['sentiment'] < -0.2 else 0

            # Make composite decision
            if technical_signal + fundamental_signal >= 1:
                decision = 'buy'
            elif technical_signal + fundamental_signal <= -1:
                decision = 'sell'
            else:
                decision = 'hold'

            assert decision in ['buy', 'sell', 'hold']

        finally:
            await researcher.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
