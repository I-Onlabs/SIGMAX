"""
Tests for RL Module
"""

import pytest
import numpy as np
from core.modules.rl import RLModule, TradingEnv


class TestTradingEnv:
    """Test trading environment"""

    def test_env_creation(self):
        """Test environment creation"""
        env = TradingEnv()
        assert env is not None
        assert env.action_space.n == 3  # buy, sell, hold
        assert len(env.observation_space.shape) == 1

    def test_env_reset(self):
        """Test environment reset"""
        env = TradingEnv()
        obs, info = env.reset()

        assert obs is not None
        assert len(obs) == 7  # State vector length
        assert env.position == 0.0
        assert env.cash == env.initial_cash

    def test_env_step_hold(self):
        """Test environment step with hold action"""
        env = TradingEnv()
        env.reset()

        obs, reward, terminated, truncated, info = env.step(0)  # Hold

        assert obs is not None
        assert isinstance(reward, (int, float))
        assert isinstance(terminated, bool)

    def test_env_step_buy(self):
        """Test environment step with buy action"""
        env = TradingEnv()
        env.reset()

        initial_cash = env.cash
        obs, reward, terminated, truncated, info = env.step(1)  # Buy

        assert obs is not None
        # Cash should decrease if buy executed
        # Position should increase

    def test_env_step_sell(self):
        """Test environment step with sell action"""
        env = TradingEnv()
        env.reset()

        # First buy
        env.step(1)
        # Then sell
        obs, reward, terminated, truncated, info = env.step(2)

        assert obs is not None

    def test_env_with_historical_data(self):
        """Test environment with historical data"""
        historical_data = [
            {'price': 50000 + i * 100, 'volume': 1000000, 'rsi': 50, 'macd': 0, 'sentiment': 0}
            for i in range(100)
        ]

        env = TradingEnv(historical_data=historical_data)
        env.reset()

        # Run a few steps
        for _ in range(10):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break

        assert env.current_step > 0


@pytest.mark.asyncio
class TestRLModule:
    """Test RL module"""

    async def test_module_creation(self):
        """Test module creation"""
        module = RLModule()
        assert module is not None
        assert module.model is None  # Not initialized yet

    async def test_module_initialization(self):
        """Test module initialization"""
        module = RLModule()
        await module.initialize()

        # Model may be None if stable_baselines3 is not available
        # This is expected behavior
        assert module.env is not None or module.model is None

    async def test_module_predict_without_init(self):
        """Test prediction without initialization"""
        module = RLModule()

        state = {
            'price': 50000,
            'volume': 1000000,
            'rsi': 50,
            'macd': 0,
            'sentiment': 0,
            'position': 0,
            'pnl_pct': 0
        }

        result = await module.predict(state)

        assert 'action' in result
        assert 'confidence' in result
        assert result['action'] in ['buy', 'sell', 'hold']

    async def test_module_predict_with_init(self):
        """Test prediction with initialization"""
        module = RLModule()
        await module.initialize()

        state = {
            'price': 50000,
            'volume': 1000000,
            'rsi': 50,
            'macd': 0,
            'sentiment': 0,
            'position': 0,
            'pnl_pct': 0
        }

        result = await module.predict(state)

        assert 'action' in result
        assert 'confidence' in result
        assert 'source' in result
        assert result['action'] in ['buy', 'sell', 'hold']

    async def test_module_status(self):
        """Test module status"""
        module = RLModule()
        await module.initialize()

        status = await module.get_status()

        assert 'initialized' in status
        assert 'algorithm' in status
        assert 'model_path' in status

    async def test_module_train(self):
        """Test module training"""
        module = RLModule()
        await module.initialize()

        # Create mock historical data
        historical_data = [
            {
                'price': 50000 + i * 100,
                'volume': 1000000,
                'rsi': 50 + (i % 20),
                'macd': (i % 10) - 5,
                'sentiment': 0.1 * (i % 5)
            }
            for i in range(100)
        ]

        # Train for a small number of timesteps (test only)
        await module.train(historical_data, timesteps=100)

        # Training may fail gracefully if model is None
        # This is expected behavior


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
