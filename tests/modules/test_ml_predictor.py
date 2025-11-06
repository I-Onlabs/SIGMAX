"""
Unit tests for ML Predictor module
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, AsyncMock

from core.modules.ml_predictor import MLPredictor


class TestMLPredictor:
    """Tests for MLPredictor"""

    @pytest.fixture
    def ml_predictor(self):
        """Create MLPredictor instance"""
        return MLPredictor()

    @pytest.fixture
    def sample_ohlcv(self):
        """Generate sample OHLCV data"""
        np.random.seed(42)
        n_candles = 200

        # Generate realistic price data
        base_price = 50000
        returns = np.random.randn(n_candles) * 0.02
        prices = base_price * np.cumprod(1 + returns)

        ohlcv = np.zeros((n_candles, 6))
        ohlcv[:, 0] = np.arange(n_candles) * 3600  # Timestamps
        ohlcv[:, 4] = prices  # Close prices
        ohlcv[:, 1] = prices * 1.01  # High
        ohlcv[:, 2] = prices * 0.99  # Low
        ohlcv[:, 3] = prices * 1.005  # Open
        ohlcv[:, 5] = np.random.rand(n_candles) * 1000  # Volume

        return ohlcv

    def test_initialization(self, ml_predictor):
        """Test ML predictor initialization"""
        assert ml_predictor is not None
        assert len(ml_predictor.models) == 4
        assert 'xgboost' in ml_predictor.models
        assert 'lightgbm' in ml_predictor.models
        assert 'random_forest' in ml_predictor.models
        assert 'gradient_boosting' in ml_predictor.models

    def test_feature_engineering(self, ml_predictor, sample_ohlcv):
        """Test feature engineering"""
        features = ml_predictor.engineer_features(sample_ohlcv, lookback=50)

        assert features is not None
        assert features.shape[0] == len(sample_ohlcv) - 50
        assert features.shape[1] == 12  # 12 technical indicators

    def test_feature_engineering_invalid_data(self, ml_predictor):
        """Test feature engineering with insufficient data"""
        short_ohlcv = np.random.rand(10, 6)

        features = ml_predictor.engineer_features(short_ohlcv, lookback=50)
        assert features.size == 0

    @pytest.mark.asyncio
    async def test_train_models(self, ml_predictor, sample_ohlcv):
        """Test model training"""
        metrics = await ml_predictor.train(sample_ohlcv, lookback=50)

        assert 'xgboost' in metrics
        assert 'lightgbm' in metrics
        assert 'random_forest' in metrics
        assert 'gradient_boosting' in metrics

        # Check that all models trained successfully
        for model_name, model_metrics in metrics.items():
            assert 'mse' in model_metrics
            assert 'mae' in model_metrics
            assert model_metrics['mse'] >= 0
            assert model_metrics['mae'] >= 0

    @pytest.mark.asyncio
    async def test_predict_without_training(self, ml_predictor, sample_ohlcv):
        """Test prediction without training"""
        result = await ml_predictor.predict(sample_ohlcv)

        assert 'prediction' in result
        assert 'confidence' in result
        assert isinstance(result['prediction'], float)
        assert 0 <= result['confidence'] <= 1

    @pytest.mark.asyncio
    async def test_predict_after_training(self, ml_predictor, sample_ohlcv):
        """Test prediction after training"""
        # Train models first
        await ml_predictor.train(sample_ohlcv, lookback=50)

        # Make prediction
        result = await ml_predictor.predict(sample_ohlcv)

        assert 'prediction' in result
        assert 'confidence' in result
        assert 'models' in result
        assert isinstance(result['prediction'], float)
        assert 0 <= result['confidence'] <= 1

    @pytest.mark.asyncio
    async def test_predict_insufficient_data(self, ml_predictor):
        """Test prediction with insufficient data"""
        short_ohlcv = np.random.rand(10, 6)

        result = await ml_predictor.predict(short_ohlcv)

        assert 'error' in result

    def test_returns_calculation(self, ml_predictor):
        """Test returns calculation"""
        prices = np.array([100, 105, 103, 108, 110])
        returns = ml_predictor._returns(prices, period=1)

        assert len(returns) == len(prices)
        assert returns[0] == 0  # First return should be 0
        assert abs(returns[1] - 0.05) < 0.001  # 5% gain

    def test_rsi_calculation(self, ml_predictor):
        """Test RSI calculation"""
        # Create trending up data
        prices = np.array([100 + i for i in range(20)])
        rsi = ml_predictor._rsi(prices, period=14)

        assert len(rsi) == len(prices)
        # RSI should be high for uptrend
        assert rsi[-1] > 50

    def test_macd_calculation(self, ml_predictor):
        """Test MACD calculation"""
        prices = np.random.rand(100) * 100 + 50000
        macd = ml_predictor._macd(prices)

        assert len(macd) == len(prices)

    def test_bollinger_bands(self, ml_predictor):
        """Test Bollinger Bands calculation"""
        prices = np.random.rand(100) * 100 + 50000
        bb_position = ml_predictor._bollinger_bands(prices, period=20, std_dev=2)

        assert len(bb_position) == len(prices)
        # Position should be between -1 and 1
        assert all(-1.5 <= x <= 1.5 for x in bb_position if not np.isnan(x))

    def test_atr_calculation(self, ml_predictor, sample_ohlcv):
        """Test ATR calculation"""
        highs = sample_ohlcv[:, 1]
        lows = sample_ohlcv[:, 2]
        closes = sample_ohlcv[:, 4]

        atr = ml_predictor._atr(highs, lows, closes, period=14)

        assert len(atr) == len(sample_ohlcv)
        assert all(x >= 0 for x in atr if not np.isnan(x))

    def test_volume_ma_ratio(self, ml_predictor, sample_ohlcv):
        """Test volume moving average ratio"""
        volumes = sample_ohlcv[:, 5]
        ratio = ml_predictor._volume_ma_ratio(volumes, period=20)

        assert len(ratio) == len(volumes)

    @pytest.mark.asyncio
    async def test_ensemble_weights(self, ml_predictor, sample_ohlcv):
        """Test that ensemble uses configurable weights"""
        # Train with custom weights
        ml_predictor.weights = {
            'xgboost': 0.4,
            'lightgbm': 0.3,
            'random_forest': 0.2,
            'gradient_boosting': 0.1
        }

        await ml_predictor.train(sample_ohlcv)
        result = await ml_predictor.predict(sample_ohlcv)

        assert result['prediction'] is not None

    @pytest.mark.asyncio
    async def test_concurrent_predictions(self, ml_predictor, sample_ohlcv):
        """Test making multiple predictions concurrently"""
        import asyncio

        tasks = [ml_predictor.predict(sample_ohlcv) for _ in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for result in results:
            assert 'prediction' in result
            assert 'confidence' in result

    def test_nan_handling(self, ml_predictor):
        """Test handling of NaN values"""
        prices = np.array([100, 105, np.nan, 108, 110])

        # RSI should handle NaN
        rsi = ml_predictor._rsi(prices, period=3)
        assert len(rsi) == len(prices)

    @pytest.mark.asyncio
    async def test_model_persistence(self, ml_predictor, sample_ohlcv):
        """Test that trained models persist across predictions"""
        # Train once
        metrics1 = await ml_predictor.train(sample_ohlcv)

        # Predict multiple times
        result1 = await ml_predictor.predict(sample_ohlcv)
        result2 = await ml_predictor.predict(sample_ohlcv)

        # Should use same trained models
        assert result1['prediction'] == result2['prediction']
