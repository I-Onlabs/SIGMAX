"""
RL Module - Reinforcement Learning for Strategy Optimization

Implements reinforcement learning for autonomous trading strategy optimization
using Stable Baselines 3 (PPO algorithm).
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import numpy as np
from loguru import logger
import gymnasium as gym
from gymnasium import spaces
import os


class TradingEnv(gym.Env):
    """
    Custom trading environment for RL training

    State space: [price, volume, rsi, macd, sentiment, position, pnl]
    Action space: [buy, sell, hold]
    Reward: PnL change + penalties for high risk
    """

    metadata = {"render_modes": ["human"]}

    def __init__(self, historical_data: Optional[List[Dict[str, Any]]] = None):
        super().__init__()

        self.historical_data = historical_data or []
        self.current_step = 0
        self.max_steps = len(self.historical_data) if self.historical_data else 1000

        # Trading state
        self.position = 0.0  # -1 (short) to 1 (long)
        self.cash = 10000.0  # Starting capital
        self.initial_cash = 10000.0
        self.portfolio_value = self.cash
        self.entry_price = 0.0
        self.total_trades = 0
        self.winning_trades = 0

        # Define action and observation space
        # Actions: 0=hold, 1=buy, 2=sell
        self.action_space = spaces.Discrete(3)

        # Observations: [price_norm, volume_norm, rsi, macd, sentiment, position, pnl_pct]
        self.observation_space = spaces.Box(
            low=np.array([-10, 0, 0, -1, -1, -1, -1], dtype=np.float32),
            high=np.array([10, 10, 100, 1, 1, 1, 10], dtype=np.float32),
            dtype=np.float32
        )

    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None):
        """Reset environment to initial state"""
        super().reset(seed=seed)

        self.current_step = 0
        self.position = 0.0
        self.cash = self.initial_cash
        self.portfolio_value = self.cash
        self.entry_price = 0.0
        self.total_trades = 0
        self.winning_trades = 0

        return self._get_observation(), {}

    def _get_observation(self) -> np.ndarray:
        """Get current observation (state)"""
        if self.historical_data and self.current_step < len(self.historical_data):
            data = self.historical_data[self.current_step]

            # Normalize price (z-score relative to recent mean)
            price = data.get('price', 50000)
            price_norm = (price - 50000) / 10000  # Rough normalization

            # Volume normalized
            volume = data.get('volume', 1000000)
            volume_norm = min(volume / 10000000, 10)  # Cap at 10

            # Technical indicators
            rsi = data.get('rsi', 50)
            macd = data.get('macd', 0)
            macd_norm = max(min(macd / 100, 1), -1)  # Normalize to [-1, 1]

            # Sentiment
            sentiment = data.get('sentiment', 0)

        else:
            # Fallback for missing data
            price_norm = 0.0
            volume_norm = 1.0
            rsi = 50.0
            macd_norm = 0.0
            sentiment = 0.0

        # Portfolio state
        pnl_pct = (self.portfolio_value - self.initial_cash) / self.initial_cash

        return np.array([
            price_norm,
            volume_norm,
            rsi / 100,  # Normalize RSI to [0, 1]
            macd_norm,
            sentiment,
            self.position,
            pnl_pct
        ], dtype=np.float32)

    def step(self, action: int):
        """Execute one time step"""
        # Get current price
        if self.historical_data and self.current_step < len(self.historical_data):
            current_price = self.historical_data[self.current_step].get('price', 50000)
        else:
            # Random walk for mock data
            current_price = 50000 * (1 + np.random.normal(0, 0.02))

        # Execute action
        old_portfolio_value = self.portfolio_value
        reward = 0.0

        if action == 1:  # Buy
            if self.position < 0.5:  # Not already long
                trade_size = min(self.cash * 0.1, self.cash)  # 10% of cash
                if trade_size > 0:
                    shares = trade_size / current_price
                    self.cash -= trade_size
                    self.position = min(self.position + shares / 10, 1.0)  # Normalize position
                    self.entry_price = current_price
                    self.total_trades += 1

        elif action == 2:  # Sell
            if self.position > -0.5:  # Not already short
                if self.position > 0:
                    # Close long position
                    pnl = self.position * 10 * (current_price - self.entry_price)
                    self.cash += pnl + (self.position * 10 * self.entry_price)
                    if pnl > 0:
                        self.winning_trades += 1
                    self.position = 0.0
                    self.total_trades += 1
                else:
                    # Short sell
                    trade_size = min(self.cash * 0.1, self.cash)
                    if trade_size > 0:
                        shares = trade_size / current_price
                        self.cash += trade_size
                        self.position = max(self.position - shares / 10, -1.0)
                        self.entry_price = current_price
                        self.total_trades += 1

        # Calculate portfolio value
        if self.position > 0:
            # Long position
            self.portfolio_value = self.cash + (self.position * 10 * current_price)
        elif self.position < 0:
            # Short position
            self.portfolio_value = self.cash + (self.position * 10 * (2 * self.entry_price - current_price))
        else:
            self.portfolio_value = self.cash

        # Calculate reward (PnL change)
        reward = (self.portfolio_value - old_portfolio_value) / self.initial_cash * 100

        # Penalty for excessive trading
        if action != 0:  # Not hold
            reward -= 0.01  # Small trading cost

        # Bonus for risk-adjusted returns
        if self.total_trades > 10:
            win_rate = self.winning_trades / self.total_trades
            reward += win_rate * 0.1

        # Move to next step
        self.current_step += 1

        # Check if done
        terminated = self.current_step >= self.max_steps
        truncated = self.portfolio_value < self.initial_cash * 0.5  # 50% loss = stop

        return self._get_observation(), reward, terminated, truncated, {}

    def render(self):
        """Render environment state"""
        print(f"Step: {self.current_step}, Position: {self.position:.2f}, "
              f"Portfolio: ${self.portfolio_value:.2f}, "
              f"PnL: {((self.portfolio_value/self.initial_cash - 1) * 100):.2f}%")


class RLModule:
    """
    RL Module - Uses reinforcement learning to optimize trading strategies

    Algorithms:
    - PPO (Proximal Policy Optimization) - Default
    - A2C (Advantage Actor-Critic) - Alternative
    - SAC (Soft Actor-Critic) - For continuous actions
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.env = None
        self.model_path = model_path or "models/rl_ppo_trading"
        self.algorithm = "PPO"  # Default algorithm
        logger.info("✓ RL module created")

    async def initialize(self):
        """Initialize RL environment and model"""
        try:
            from stable_baselines3 import PPO

            # Create environment
            self.env = TradingEnv()

            # Load or create model
            model_file = Path(self.model_path + ".zip")

            if model_file.exists():
                logger.info(f"Loading existing RL model from {model_file}")
                self.model = PPO.load(str(model_file), env=self.env)
            else:
                logger.info("Creating new RL model (PPO)")
                self.model = PPO(
                    "MlpPolicy",
                    self.env,
                    verbose=0,
                    learning_rate=0.0003,
                    n_steps=2048,
                    batch_size=64,
                    n_epochs=10,
                    gamma=0.99,
                    gae_lambda=0.95,
                    clip_range=0.2,
                    ent_coef=0.01,
                )

            logger.info("✓ RL module initialized with PPO")

        except ImportError as e:
            logger.warning(f"Stable Baselines 3 not available: {e}")
            self.model = None
            self.env = None
        except Exception as e:
            logger.warning(f"RL initialization failed: {e}")
            self.model = None
            self.env = None

    async def train(self, historical_data: List[Dict[str, Any]], timesteps: int = 10000):
        """
        Train RL model on historical data

        Args:
            historical_data: List of market data dictionaries with price, volume, indicators
            timesteps: Number of training timesteps
        """
        if self.model is None:
            logger.warning("RL model not initialized, skipping training")
            return

        try:
            logger.info(f"Starting RL training with {len(historical_data)} data points...")

            # Create new environment with historical data
            self.env = TradingEnv(historical_data=historical_data)
            self.model.set_env(self.env)

            # Train model
            self.model.learn(total_timesteps=timesteps, progress_bar=False)

            # Save model
            Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
            self.model.save(self.model_path)

            logger.info(f"✓ RL training complete. Model saved to {self.model_path}")

        except Exception as e:
            logger.error(f"RL training failed: {e}")

    async def predict(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get RL model prediction

        Args:
            state: Current market state with price, volume, indicators, etc.

        Returns:
            Dictionary with action and confidence
        """
        if self.model is None:
            # Fallback: random action with low confidence
            return {
                "action": "hold",
                "confidence": 0.3,
                "source": "fallback"
            }

        try:
            # Convert state to observation
            obs = np.array([
                (state.get('price', 50000) - 50000) / 10000,  # Normalized price
                min(state.get('volume', 1000000) / 10000000, 10),  # Normalized volume
                state.get('rsi', 50) / 100,  # RSI
                max(min(state.get('macd', 0) / 100, 1), -1),  # MACD normalized
                state.get('sentiment', 0),  # Sentiment
                state.get('position', 0),  # Current position
                state.get('pnl_pct', 0)  # PnL percentage
            ], dtype=np.float32)

            # Get action from model
            action, _states = self.model.predict(obs, deterministic=True)

            # Convert action to string
            action_map = {0: "hold", 1: "buy", 2: "sell"}
            action_str = action_map.get(int(action), "hold")

            # Estimate confidence based on action probabilities
            # For deterministic policy, use high confidence
            confidence = 0.75

            logger.debug(f"RL prediction: {action_str} (confidence: {confidence:.2f})")

            return {
                "action": action_str,
                "confidence": confidence,
                "source": "rl_ppo"
            }

        except Exception as e:
            logger.error(f"RL prediction failed: {e}")
            return {
                "action": "hold",
                "confidence": 0.3,
                "source": "error_fallback"
            }

    async def get_status(self) -> Dict[str, Any]:
        """Get RL module status"""
        return {
            "initialized": self.model is not None,
            "algorithm": self.algorithm,
            "model_path": self.model_path,
            "model_exists": Path(self.model_path + ".zip").exists()
        }
