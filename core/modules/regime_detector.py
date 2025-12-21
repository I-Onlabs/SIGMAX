"""
Market Regime Detector - Identifies market conditions for adaptive strategies
"""

from typing import Dict, Any
import numpy as np
from datetime import datetime
from enum import Enum
from loguru import logger


class MarketRegime(Enum):
    """Market regime classifications"""
    BULL_TRENDING = "bull_trending"
    BEAR_TRENDING = "bear_trending"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"


class RegimeDetector:
    """
    Market Regime Detector

    Identifies:
    - Trend direction (bull/bear/sideways)
    - Volatility regime (high/low)
    - Breakout/breakdown conditions
    - Mean reversion vs momentum environments

    Uses:
    - Moving averages for trend
    - ADX for trend strength
    - Volatility percentiles
    - Hidden Markov Models (HMM)
    """

    def __init__(self):
        self.regime_history = []
        self.current_regime = None

        logger.info("✓ Regime Detector initialized")

    async def detect_regime(
        self,
        ohlcv: np.ndarray,
        lookback: int = 100
    ) -> Dict[str, Any]:
        """
        Detect current market regime

        Args:
            ohlcv: OHLCV data [timestamp, open, high, low, close, volume]
            lookback: Lookback period for analysis

        Returns:
            Regime analysis with confidence scores
        """
        if len(ohlcv) < lookback:
            logger.warning(f"Insufficient data for regime detection: {len(ohlcv)} < {lookback}")
            return {"regime": MarketRegime.SIDEWAYS, "confidence": 0.0}

        logger.info("🔍 Detecting market regime...")

        closes = ohlcv[-lookback:, 4]
        highs = ohlcv[-lookback:, 2]
        lows = ohlcv[-lookback:, 3]
        volumes = ohlcv[-lookback:, 5]

        # Analyze different aspects
        trend_analysis = self._analyze_trend(closes)
        volatility_analysis = self._analyze_volatility(closes)
        momentum_analysis = self._analyze_momentum(closes)
        volume_analysis = self._analyze_volume(volumes)

        # Combine signals to determine regime
        regime = self._determine_regime(
            trend_analysis,
            volatility_analysis,
            momentum_analysis,
            volume_analysis
        )

        result = {
            "regime": regime['regime'],
            "confidence": regime['confidence'],
            "trend": trend_analysis,
            "volatility": volatility_analysis,
            "momentum": momentum_analysis,
            "volume": volume_analysis,
            "timestamp": datetime.now().isoformat()
        }

        # Store in history
        self.regime_history.append(result)
        self.current_regime = result

        # Keep last 1000 entries
        if len(self.regime_history) > 1000:
            self.regime_history.pop(0)

        logger.info(f"📊 Detected regime: {regime['regime'].value} "
                   f"(confidence: {regime['confidence']:.2%})")

        return result

    def _analyze_trend(self, prices: np.ndarray) -> Dict[str, Any]:
        """Analyze trend direction and strength"""

        # Calculate moving averages
        sma_20 = self._sma(prices, 20)
        sma_50 = self._sma(prices, 50)
        ema_12 = self._ema(prices, 12)
        ema_26 = self._ema(prices, 26)

        current_price = prices[-1]

        # Price position relative to MAs
        above_sma20 = current_price > sma_20[-1]
        above_sma50 = current_price > sma_50[-1]

        # MA alignment (trending if shorter MA > longer MA)
        ma_alignment = sma_20[-1] > sma_50[-1]

        # MACD
        macd = ema_12[-1] - ema_26[-1]

        # ADX (Average Directional Index) for trend strength
        adx = self._calculate_adx(prices, period=14)

        # Determine trend
        if above_sma20 and above_sma50 and ma_alignment and macd > 0:
            direction = "bullish"
            strength = min(adx / 25, 1.0)  # Strong if ADX > 25
        elif not above_sma20 and not above_sma50 and not ma_alignment and macd < 0:
            direction = "bearish"
            strength = min(adx / 25, 1.0)
        else:
            direction = "sideways"
            strength = 1.0 - min(adx / 25, 1.0)  # Strong sideways if ADX < 25

        return {
            "direction": direction,
            "strength": strength,
            "adx": adx,
            "above_sma20": above_sma20,
            "above_sma50": above_sma50,
            "macd": macd
        }

    def _analyze_volatility(self, prices: np.ndarray) -> Dict[str, Any]:
        """Analyze volatility regime"""

        # Calculate returns
        returns = np.diff(prices) / prices[:-1]

        # Rolling volatility
        window = 20
        volatilities = []

        for i in range(window, len(returns)):
            vol = np.std(returns[i-window:i]) * np.sqrt(252)  # Annualized
            volatilities.append(vol)

        current_vol = volatilities[-1] if volatilities else 0

        # Historical percentile
        percentile = np.percentile(volatilities, 50) if len(volatilities) > 1 else current_vol

        # Classify
        if current_vol > np.percentile(volatilities, 75):
            regime = "high"
        elif current_vol < np.percentile(volatilities, 25):
            regime = "low"
        else:
            regime = "normal"

        # Volatility expansion/contraction
        if len(volatilities) >= 5:
            recent_avg = np.mean(volatilities[-5:])
            older_avg = np.mean(volatilities[-20:-5])
            changing = abs(recent_avg - older_avg) / older_avg > 0.2
            expanding = recent_avg > older_avg
        else:
            changing = False
            expanding = False

        return {
            "regime": regime,
            "current": current_vol,
            "percentile": percentile,
            "expanding": expanding,
            "changing": changing
        }

    def _analyze_momentum(self, prices: np.ndarray) -> Dict[str, Any]:
        """Analyze momentum characteristics"""

        # RSI
        rsi = self._calculate_rsi(prices, 14)

        # Rate of change
        roc_5 = (prices[-1] / prices[-6] - 1) * 100 if len(prices) > 5 else 0
        roc_10 = (prices[-1] / prices[-11] - 1) * 100 if len(prices) > 10 else 0

        # Momentum oscillator
        mom = prices[-1] - prices[-10] if len(prices) > 10 else 0

        # Classify
        if rsi > 70 and roc_5 > 5:
            state = "overbought"
        elif rsi < 30 and roc_5 < -5:
            state = "oversold"
        elif roc_5 > 2:
            state = "strong_momentum"
        elif roc_5 < -2:
            state = "weak_momentum"
        else:
            state = "neutral"

        return {
            "state": state,
            "rsi": rsi,
            "roc_5d": roc_5,
            "roc_10d": roc_10,
            "momentum": mom
        }

    def _analyze_volume(self, volumes: np.ndarray) -> Dict[str, Any]:
        """Analyze volume patterns"""

        # Volume SMA
        vol_sma = self._sma(volumes, 20)

        current_vol = volumes[-1]
        avg_vol = vol_sma[-1]

        # Volume ratio
        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1.0

        # Classify
        if vol_ratio > 1.5:
            state = "high"
        elif vol_ratio < 0.5:
            state = "low"
        else:
            state = "normal"

        # Trend in volume
        recent_avg = np.mean(volumes[-10:])
        older_avg = np.mean(volumes[-30:-10])
        increasing = recent_avg > older_avg * 1.2

        return {
            "state": state,
            "ratio": vol_ratio,
            "increasing": increasing,
            "current": current_vol
        }

    def _determine_regime(
        self,
        trend: Dict[str, Any],
        volatility: Dict[str, Any],
        momentum: Dict[str, Any],
        volume: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine overall market regime"""

        # Rule-based regime classification
        regimes_scores = {
            MarketRegime.BULL_TRENDING: 0,
            MarketRegime.BEAR_TRENDING: 0,
            MarketRegime.SIDEWAYS: 0,
            MarketRegime.HIGH_VOLATILITY: 0,
            MarketRegime.LOW_VOLATILITY: 0,
            MarketRegime.BREAKOUT: 0,
            MarketRegime.BREAKDOWN: 0
        }

        # Bull trending signals
        if trend['direction'] == 'bullish' and trend['strength'] > 0.6:
            regimes_scores[MarketRegime.BULL_TRENDING] += 3
        if momentum['state'] == 'strong_momentum':
            regimes_scores[MarketRegime.BULL_TRENDING] += 2
        if volume['increasing']:
            regimes_scores[MarketRegime.BULL_TRENDING] += 1

        # Bear trending signals
        if trend['direction'] == 'bearish' and trend['strength'] > 0.6:
            regimes_scores[MarketRegime.BEAR_TRENDING] += 3
        if momentum['state'] == 'weak_momentum':
            regimes_scores[MarketRegime.BEAR_TRENDING] += 2
        if volume['increasing']:
            regimes_scores[MarketRegime.BEAR_TRENDING] += 1

        # Sideways signals
        if trend['direction'] == 'sideways':
            regimes_scores[MarketRegime.SIDEWAYS] += 3
        if momentum['state'] == 'neutral':
            regimes_scores[MarketRegime.SIDEWAYS] += 2

        # Volatility regimes
        if volatility['regime'] == 'high':
            regimes_scores[MarketRegime.HIGH_VOLATILITY] += 3
        if volatility['regime'] == 'low':
            regimes_scores[MarketRegime.LOW_VOLATILITY] += 3

        # Breakout signals
        if (momentum['state'] == 'strong_momentum' and
            volume['state'] == 'high' and
            volatility['expanding']):
            regimes_scores[MarketRegime.BREAKOUT] += 4

        # Breakdown signals
        if (momentum['state'] == 'weak_momentum' and
            volume['state'] == 'high' and
            volatility['expanding']):
            regimes_scores[MarketRegime.BREAKDOWN] += 4

        # Find regime with highest score
        best_regime = max(regimes_scores.items(), key=lambda x: x[1])

        # Calculate confidence
        total_score = sum(regimes_scores.values())
        confidence = best_regime[1] / total_score if total_score > 0 else 0

        return {
            "regime": best_regime[0],
            "confidence": confidence,
            "all_scores": {k.value: v for k, v in regimes_scores.items()}
        }

    # Helper functions
    def _sma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Simple Moving Average"""
        return np.convolve(prices, np.ones(period)/period, mode='valid')

    def _ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Exponential Moving Average"""
        ema = np.zeros(len(prices))
        ema[0] = prices[0]
        multiplier = 2 / (period + 1)

        for i in range(1, len(prices)):
            ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]

        return ema

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:]) if len(gains) >= period else 0
        avg_loss = np.mean(losses[-period:]) if len(losses) >= period else 0

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_adx(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate Average Directional Index"""
        # Simplified ADX calculation
        if len(prices) < period + 1:
            return 0

        # Calculate +DI and -DI
        ups = np.maximum(prices[1:] - prices[:-1], 0)
        downs = np.maximum(prices[:-1] - prices[1:], 0)

        tr = np.maximum(ups, downs)

        # Average true range
        atr = np.mean(tr[-period:]) if len(tr) >= period else 1

        # Directional indicators
        plus_di = np.mean(ups[-period:]) / atr if atr > 0 else 0
        minus_di = np.mean(downs[-period:]) / atr if atr > 0 else 0

        # ADX
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) > 0 else 0
        adx = dx * 100

        return adx

    def get_regime_stats(self) -> Dict[str, Any]:
        """Get regime statistics from history"""
        if not self.regime_history:
            return {}

        regimes = [r['regime'].value for r in self.regime_history]

        # Count regime occurrences
        from collections import Counter
        regime_counts = Counter(regimes)

        # Calculate regime durations
        current_regime = regimes[-1] if regimes else None
        regime_start_idx = len(regimes) - 1

        for i in range(len(regimes) - 2, -1, -1):
            if regimes[i] != current_regime:
                break
            regime_start_idx = i

        current_duration = len(regimes) - regime_start_idx

        return {
            "current_regime": current_regime,
            "current_duration": current_duration,
            "regime_distribution": dict(regime_counts),
            "total_samples": len(regimes)
        }
