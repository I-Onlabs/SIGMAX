"""
Unit tests for Market Regime Detector
"""

import pytest
import numpy as np

from core.modules.regime_detector import RegimeDetector, MarketRegime


class TestRegimeDetector:
    """Tests for RegimeDetector"""

    @pytest.fixture
    def regime_detector(self):
        """Create RegimeDetector instance"""
        return RegimeDetector()

    @pytest.fixture
    def bull_trending_data(self):
        """Generate bull trending market data"""
        np.random.seed(42)
        n_candles = 200

        # Consistent uptrend
        base_price = 50000
        trend = np.linspace(0, 0.5, n_candles)
        noise = np.random.randn(n_candles) * 0.01
        prices = base_price * np.exp(trend + noise)

        ohlcv = np.zeros((n_candles, 6))
        ohlcv[:, 0] = np.arange(n_candles) * 3600
        ohlcv[:, 4] = prices  # Close
        ohlcv[:, 1] = prices * 1.005  # High
        ohlcv[:, 2] = prices * 0.995  # Low
        ohlcv[:, 3] = prices  # Open
        ohlcv[:, 5] = np.random.rand(n_candles) * 1000  # Volume

        return ohlcv

    @pytest.fixture
    def bear_trending_data(self):
        """Generate bear trending market data"""
        np.random.seed(43)
        n_candles = 200

        # Consistent downtrend
        base_price = 50000
        trend = np.linspace(0, -0.3, n_candles)
        noise = np.random.randn(n_candles) * 0.01
        prices = base_price * np.exp(trend + noise)

        ohlcv = np.zeros((n_candles, 6))
        ohlcv[:, 0] = np.arange(n_candles) * 3600
        ohlcv[:, 4] = prices
        ohlcv[:, 1] = prices * 1.005
        ohlcv[:, 2] = prices * 0.995
        ohlcv[:, 3] = prices
        ohlcv[:, 5] = np.random.rand(n_candles) * 1000

        return ohlcv

    @pytest.fixture
    def sideways_data(self):
        """Generate sideways market data"""
        np.random.seed(44)
        n_candles = 200

        # No trend, just noise
        base_price = 50000
        noise = np.random.randn(n_candles) * 0.02
        prices = base_price * (1 + noise)

        ohlcv = np.zeros((n_candles, 6))
        ohlcv[:, 0] = np.arange(n_candles) * 3600
        ohlcv[:, 4] = prices
        ohlcv[:, 1] = prices * 1.01
        ohlcv[:, 2] = prices * 0.99
        ohlcv[:, 3] = prices
        ohlcv[:, 5] = np.random.rand(n_candles) * 1000

        return ohlcv

    @pytest.fixture
    def high_volatility_data(self):
        """Generate high volatility market data"""
        np.random.seed(45)
        n_candles = 200

        # High volatility swings
        base_price = 50000
        noise = np.random.randn(n_candles) * 0.05  # 5% volatility
        prices = base_price * np.cumprod(1 + noise)

        ohlcv = np.zeros((n_candles, 6))
        ohlcv[:, 0] = np.arange(n_candles) * 3600
        ohlcv[:, 4] = prices
        ohlcv[:, 1] = prices * 1.03
        ohlcv[:, 2] = prices * 0.97
        ohlcv[:, 3] = prices
        ohlcv[:, 5] = np.random.rand(n_candles) * 1000

        return ohlcv

    def test_initialization(self, regime_detector):
        """Test regime detector initialization"""
        assert regime_detector is not None

    @pytest.mark.asyncio
    async def test_detect_bull_trending(self, regime_detector, bull_trending_data):
        """Test detection of bull trending regime"""
        result = await regime_detector.detect_regime(bull_trending_data, lookback=100)

        assert result is not None
        assert 'regime' in result
        assert 'confidence' in result
        assert 'indicators' in result

        # Should detect bullish trend
        assert result['regime'] in [MarketRegime.BULL_TRENDING.value, MarketRegime.LOW_VOLATILITY.value]
        assert result['confidence'] > 0.5

    @pytest.mark.asyncio
    async def test_detect_bear_trending(self, regime_detector, bear_trending_data):
        """Test detection of bear trending regime"""
        result = await regime_detector.detect_regime(bear_trending_data, lookback=100)

        assert result is not None
        # Should detect bearish trend
        assert result['regime'] in [MarketRegime.BEAR_TRENDING.value, MarketRegime.SIDEWAYS.value]

    @pytest.mark.asyncio
    async def test_detect_sideways(self, regime_detector, sideways_data):
        """Test detection of sideways regime"""
        result = await regime_detector.detect_regime(sideways_data, lookback=100)

        assert result is not None
        # Should detect sideways or low volatility
        assert result['regime'] in [MarketRegime.SIDEWAYS.value, MarketRegime.LOW_VOLATILITY.value]

    @pytest.mark.asyncio
    async def test_detect_high_volatility(self, regime_detector, high_volatility_data):
        """Test detection of high volatility regime"""
        result = await regime_detector.detect_regime(high_volatility_data, lookback=100)

        assert result is not None
        # High volatility should be detected
        assert 'volatility' in result['indicators']

    @pytest.mark.asyncio
    async def test_insufficient_data(self, regime_detector):
        """Test with insufficient data"""
        short_data = np.random.rand(10, 6)

        result = await regime_detector.detect_regime(short_data, lookback=100)

        assert result is not None
        assert result['regime'] == MarketRegime.UNCERTAIN.value

    @pytest.mark.asyncio
    async def test_trend_analysis(self, regime_detector, bull_trending_data):
        """Test trend analysis indicators"""
        result = await regime_detector.detect_regime(bull_trending_data)

        indicators = result['indicators']
        assert 'sma_trend' in indicators
        assert 'price_vs_sma' in indicators
        assert 'trend_strength' in indicators

    @pytest.mark.asyncio
    async def test_volatility_analysis(self, regime_detector, high_volatility_data):
        """Test volatility analysis"""
        result = await regime_detector.detect_regime(high_volatility_data)

        indicators = result['indicators']
        assert 'volatility' in indicators
        assert 'volatility_percentile' in indicators

        # High volatility data should show high volatility indicator
        assert indicators['volatility'] > indicators.get('volatility_20_sma', 0) * 0.5

    @pytest.mark.asyncio
    async def test_momentum_analysis(self, regime_detector, bull_trending_data):
        """Test momentum indicators"""
        result = await regime_detector.detect_regime(bull_trending_data)

        indicators = result['indicators']
        assert 'rsi' in indicators
        assert 'macd' in indicators

        # RSI should be between 0 and 100
        assert 0 <= indicators['rsi'] <= 100

    @pytest.mark.asyncio
    async def test_volume_analysis(self, regime_detector, bull_trending_data):
        """Test volume analysis"""
        result = await regime_detector.detect_regime(bull_trending_data)

        indicators = result['indicators']
        assert 'volume_trend' in indicators

    @pytest.mark.asyncio
    async def test_confidence_calculation(self, regime_detector, bull_trending_data):
        """Test confidence score calculation"""
        result = await regime_detector.detect_regime(bull_trending_data)

        assert 0 <= result['confidence'] <= 1

        # Strong trends should have higher confidence
        if result['regime'] == MarketRegime.BULL_TRENDING.value:
            assert result['confidence'] > 0.4

    @pytest.mark.asyncio
    async def test_regime_change_detection(self, regime_detector):
        """Test detection of regime changes"""
        # Create data that transitions from bull to bear
        n_candles = 200
        np.random.seed(46)

        # First half: uptrend
        bull_prices = 50000 * np.exp(np.linspace(0, 0.3, 100))

        # Second half: downtrend
        bear_prices = bull_prices[-1] * np.exp(np.linspace(0, -0.2, 100))

        all_prices = np.concatenate([bull_prices, bear_prices])

        ohlcv = np.zeros((n_candles, 6))
        ohlcv[:, 0] = np.arange(n_candles) * 3600
        ohlcv[:, 4] = all_prices
        ohlcv[:, 1] = all_prices * 1.005
        ohlcv[:, 2] = all_prices * 0.995
        ohlcv[:, 3] = all_prices
        ohlcv[:, 5] = np.random.rand(n_candles) * 1000

        # Analyze recent data (should detect bear trend)
        result = await regime_detector.detect_regime(ohlcv, lookback=100)

        assert result is not None

    @pytest.mark.asyncio
    async def test_different_lookback_periods(self, regime_detector, bull_trending_data):
        """Test different lookback periods"""
        result_short = await regime_detector.detect_regime(bull_trending_data, lookback=50)
        result_long = await regime_detector.detect_regime(bull_trending_data, lookback=150)

        assert result_short is not None
        assert result_long is not None

        # Both should return valid regimes
        assert result_short['regime'] in [r.value for r in MarketRegime]
        assert result_long['regime'] in [r.value for r in MarketRegime]

    @pytest.mark.asyncio
    async def test_all_regime_types_valid(self, regime_detector, bull_trending_data):
        """Test that regime detector returns only valid regime types"""
        result = await regime_detector.detect_regime(bull_trending_data)

        valid_regimes = [r.value for r in MarketRegime]
        assert result['regime'] in valid_regimes

    @pytest.mark.asyncio
    async def test_indicator_completeness(self, regime_detector, bull_trending_data):
        """Test that all expected indicators are present"""
        result = await regime_detector.detect_regime(bull_trending_data)

        indicators = result['indicators']
        expected_indicators = [
            'sma_trend',
            'price_vs_sma',
            'trend_strength',
            'volatility',
            'rsi',
            'macd',
            'volume_trend'
        ]

        for indicator in expected_indicators:
            assert indicator in indicators

    @pytest.mark.asyncio
    async def test_concurrent_detection(self, regime_detector, bull_trending_data, bear_trending_data):
        """Test concurrent regime detection"""
        import asyncio

        tasks = [
            regime_detector.detect_regime(bull_trending_data),
            regime_detector.detect_regime(bear_trending_data)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 2
        # Should potentially detect different regimes
        assert all('regime' in r for r in results)
