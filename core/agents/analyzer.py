"""
Analyzer Agent - Technical + Sentiment Analysis
"""

from typing import Dict, Any, Optional, List
from loguru import logger
import numpy as np


class AnalyzerAgent:
    """
    Analyzer Agent - Performs technical and sentiment analysis
    """

    def __init__(self, llm, data_module):
        self.llm = llm
        self.data_module = data_module
        logger.info("✓ Analyzer agent initialized")

    async def analyze(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        bull_case: Optional[str] = None,
        bear_case: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze symbol with technical indicators

        Args:
            symbol: Trading pair
            market_data: Market data
            bull_case: Bull argument (for context)
            bear_case: Bear argument (for context)

        Returns:
            Analysis summary with indicators
        """
        logger.info(f"📊 Analyzing {symbol}...")

        try:
            # Technical indicators
            indicators = await self._calculate_indicators(symbol, market_data)

            # Pattern recognition
            patterns = await self._detect_patterns(market_data)

            # Support/resistance
            levels = await self._find_support_resistance(market_data)

            # Generate summary
            summary = await self._generate_analysis(
                symbol=symbol,
                indicators=indicators,
                patterns=patterns,
                levels=levels,
                bull_case=bull_case,
                bear_case=bear_case
            )

            return {
                "summary": summary,
                "indicators": indicators,
                "patterns": patterns,
                "levels": levels,
                "sentiment": self._calculate_technical_sentiment(indicators)
            }

        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {
                "summary": f"Analysis failed: {e}",
                "sentiment": 0.0,
                "error": str(e)
            }

    async def _calculate_indicators(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate technical indicators using numpy

        Supports both historical data and single price points
        """
        current_price = market_data.get("price", 0.0)

        # Check if we have historical data
        prices = market_data.get("prices", [])
        volumes = market_data.get("volumes", [])

        if not prices or len(prices) < 2:
            # Use current price only - return neutral indicators
            logger.debug(f"No historical data for {symbol}, using neutral indicators")
            return {
                "rsi": 50.0,
                "macd": 0.0,
                "macd_signal": 0.0,
                "macd_histogram": 0.0,
                "bb_upper": current_price * 1.02,
                "bb_middle": current_price,
                "bb_lower": current_price * 0.98,
                "ema_20": current_price,
                "ema_50": current_price,
                "sma_20": current_price,
                "sma_50": current_price,
                "volume_sma": volumes[0] if volumes else 0.0,
                "atr": current_price * 0.02  # 2% ATR estimate
            }

        prices_array = np.array(prices)

        # RSI (Relative Strength Index)
        rsi = self._calculate_rsi(prices_array, period=14)

        # MACD (Moving Average Convergence Divergence)
        macd, macd_signal, macd_histogram = self._calculate_macd(prices_array)

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(prices_array, period=20, std=2)

        # EMAs (Exponential Moving Averages)
        ema_20 = self._calculate_ema(prices_array, period=20)
        ema_50 = self._calculate_ema(prices_array, period=50)

        # SMAs (Simple Moving Averages)
        sma_20 = self._calculate_sma(prices_array, period=20)
        sma_50 = self._calculate_sma(prices_array, period=50)

        # Volume SMA
        volume_sma = 0.0
        if volumes and len(volumes) >= 20:
            volume_sma = float(np.mean(volumes[-20:]))

        # ATR (Average True Range)
        atr = self._calculate_atr(prices_array, period=14)

        indicators = {
            "rsi": float(rsi),
            "macd": float(macd),
            "macd_signal": float(macd_signal),
            "macd_histogram": float(macd_histogram),
            "bb_upper": float(bb_upper),
            "bb_middle": float(bb_middle),
            "bb_lower": float(bb_lower),
            "ema_20": float(ema_20),
            "ema_50": float(ema_50),
            "sma_20": float(sma_20),
            "sma_50": float(sma_50),
            "volume_sma": float(volume_sma),
            "atr": float(atr)
        }

        logger.debug(f"Calculated indicators for {symbol}: RSI={rsi:.1f}, MACD={macd:.4f}")
        return indicators

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_macd(self, prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """Calculate MACD, Signal, and Histogram"""
        if len(prices) < slow:
            return 0.0, 0.0, 0.0

        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)

        macd_line = ema_fast - ema_slow

        # Calculate signal line (EMA of MACD)
        # For simplicity, use SMA approximation
        macd_signal = macd_line  # Simplified - would need historical MACD for true EMA

        macd_histogram = macd_line - macd_signal

        return macd_line, macd_signal, macd_histogram

    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, std: float = 2.0) -> tuple:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            current = prices[-1]
            return current * 1.02, current, current * 0.98

        sma = np.mean(prices[-period:])
        std_dev = np.std(prices[-period:])

        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        return upper, sma, lower

    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return float(np.mean(prices))

        multiplier = 2 / (period + 1)
        ema = np.mean(prices[:period])  # Start with SMA

        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def _calculate_sma(self, prices: np.ndarray, period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return float(np.mean(prices))

        return float(np.mean(prices[-period:]))

    def _calculate_atr(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(prices) < 2:
            return prices[-1] * 0.02 if len(prices) > 0 else 0.0

        # Simplified ATR using price differences
        high_low = np.abs(np.diff(prices))

        if len(high_low) < period:
            return float(np.mean(high_low))

        return float(np.mean(high_low[-period:]))

    async def _detect_patterns(self, market_data: Dict[str, Any]) -> List[str]:
        """
        Detect chart patterns using algorithmic analysis

        Detects:
        - Double Top/Bottom
        - Head and Shoulders (bullish/bearish)
        - Triangle patterns (ascending/descending/symmetrical)
        - Breakouts
        - Trend reversals
        """
        patterns = []

        prices = market_data.get("prices", [])
        if not prices or len(prices) < 10:
            return patterns

        prices_array = np.array(prices)
        current_price = prices_array[-1]

        # Calculate price swings (local maxima and minima)
        highs, lows = self._find_swing_points(prices_array)

        # Double Top Pattern
        if self._detect_double_top(prices_array, highs):
            patterns.append("Double Top (Bearish)")

        # Double Bottom Pattern
        if self._detect_double_bottom(prices_array, lows):
            patterns.append("Double Bottom (Bullish)")

        # Head and Shoulders
        if self._detect_head_and_shoulders(prices_array, highs):
            patterns.append("Head and Shoulders (Bearish)")

        # Inverse Head and Shoulders
        if self._detect_inverse_head_and_shoulders(prices_array, lows):
            patterns.append("Inverse Head and Shoulders (Bullish)")

        # Triangle Patterns
        triangle = self._detect_triangle(prices_array)
        if triangle:
            patterns.append(triangle)

        # Breakout patterns
        breakout = self._detect_breakout(prices_array)
        if breakout:
            patterns.append(breakout)

        # Trend analysis
        trend = self._detect_trend(prices_array)
        if trend:
            patterns.append(trend)

        # Consolidation
        if self._detect_consolidation(prices_array):
            patterns.append("Consolidation/Range-bound")

        logger.debug(f"Detected patterns: {patterns}")
        return patterns

    def _find_swing_points(self, prices: np.ndarray, window: int = 3) -> tuple:
        """Find local maxima (highs) and minima (lows)"""
        highs = []
        lows = []

        for i in range(window, len(prices) - window):
            # Local maximum
            if all(prices[i] >= prices[i-window:i]) and all(prices[i] >= prices[i+1:i+window+1]):
                highs.append(i)

            # Local minimum
            if all(prices[i] <= prices[i-window:i]) and all(prices[i] <= prices[i+1:i+window+1]):
                lows.append(i)

        return highs, lows

    def _detect_double_top(self, prices: np.ndarray, highs: List[int]) -> bool:
        """Detect double top pattern (bearish reversal)"""
        if len(highs) < 2:
            return False

        # Check last two peaks
        last_two_highs = highs[-2:]
        if len(last_two_highs) < 2:
            return False

        peak1_price = prices[last_two_highs[0]]
        peak2_price = prices[last_two_highs[1]]

        # Peaks should be at similar levels (within 2%)
        price_similarity = abs(peak1_price - peak2_price) / peak1_price
        if price_similarity < 0.02:
            # Current price should be below the peaks
            if prices[-1] < min(peak1_price, peak2_price) * 0.95:
                return True

        return False

    def _detect_double_bottom(self, prices: np.ndarray, lows: List[int]) -> bool:
        """Detect double bottom pattern (bullish reversal)"""
        if len(lows) < 2:
            return False

        # Check last two troughs
        last_two_lows = lows[-2:]
        if len(last_two_lows) < 2:
            return False

        trough1_price = prices[last_two_lows[0]]
        trough2_price = prices[last_two_lows[1]]

        # Troughs should be at similar levels (within 2%)
        price_similarity = abs(trough1_price - trough2_price) / trough1_price
        if price_similarity < 0.02:
            # Current price should be above the troughs
            if prices[-1] > max(trough1_price, trough2_price) * 1.05:
                return True

        return False

    def _detect_head_and_shoulders(self, prices: np.ndarray, highs: List[int]) -> bool:
        """Detect head and shoulders pattern (bearish)"""
        if len(highs) < 3:
            return False

        # Need 3 consecutive peaks: left shoulder, head, right shoulder
        last_three = highs[-3:]
        if len(last_three) < 3:
            return False

        left = prices[last_three[0]]
        head = prices[last_three[1]]
        right = prices[last_three[2]]

        # Head should be higher than both shoulders
        # Shoulders should be at similar levels
        if head > left and head > right:
            shoulder_similarity = abs(left - right) / left
            if shoulder_similarity < 0.05:  # Within 5%
                return True

        return False

    def _detect_inverse_head_and_shoulders(self, prices: np.ndarray, lows: List[int]) -> bool:
        """Detect inverse head and shoulders pattern (bullish)"""
        if len(lows) < 3:
            return False

        # Need 3 consecutive troughs
        last_three = lows[-3:]
        if len(last_three) < 3:
            return False

        left = prices[last_three[0]]
        head = prices[last_three[1]]
        right = prices[last_three[2]]

        # Head should be lower than both shoulders
        if head < left and head < right:
            shoulder_similarity = abs(left - right) / left
            if shoulder_similarity < 0.05:
                return True

        return False

    def _detect_triangle(self, prices: np.ndarray) -> Optional[str]:
        """Detect triangle patterns"""
        if len(prices) < 20:
            return None

        recent_prices = prices[-20:]

        # Calculate trend lines for highs and lows
        highs_trend = np.polyfit(range(len(recent_prices)),
                                  [max(recent_prices[max(0, i-2):i+3]) for i in range(len(recent_prices))],
                                  1)[0]
        lows_trend = np.polyfit(range(len(recent_prices)),
                                 [min(recent_prices[max(0, i-2):i+3]) for i in range(len(recent_prices))],
                                 1)[0]

        # Ascending Triangle: flat top, rising bottom
        if abs(highs_trend) < 0.001 and lows_trend > 0.001:
            return "Ascending Triangle (Bullish)"

        # Descending Triangle: falling top, flat bottom
        if highs_trend < -0.001 and abs(lows_trend) < 0.001:
            return "Descending Triangle (Bearish)"

        # Symmetrical Triangle: converging trends
        if highs_trend < -0.001 and lows_trend > 0.001:
            return "Symmetrical Triangle (Continuation)"

        return None

    def _detect_breakout(self, prices: np.ndarray) -> Optional[str]:
        """Detect breakout from consolidation"""
        if len(prices) < 20:
            return None

        recent = prices[-20:]
        current = prices[-1]

        # Calculate recent high and low
        recent_high = np.max(recent[:-5])
        recent_low = np.min(recent[:-5])
        range_size = recent_high - recent_low

        # Breakout above resistance
        if current > recent_high * 1.02:  # 2% above
            return "Breakout Above Resistance (Bullish)"

        # Breakdown below support
        if current < recent_low * 0.98:  # 2% below
            return "Breakdown Below Support (Bearish)"

        return None

    def _detect_trend(self, prices: np.ndarray) -> Optional[str]:
        """Detect overall trend"""
        if len(prices) < 10:
            return None

        # Linear regression on recent prices
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]

        avg_price = np.mean(prices)
        slope_pct = (slope / avg_price) * 100

        if slope_pct > 0.5:
            return "Strong Uptrend"
        elif slope_pct > 0.1:
            return "Uptrend"
        elif slope_pct < -0.5:
            return "Strong Downtrend"
        elif slope_pct < -0.1:
            return "Downtrend"

        return None

    def _detect_consolidation(self, prices: np.ndarray) -> bool:
        """Detect if price is consolidating"""
        if len(prices) < 10:
            return False

        recent = prices[-10:]
        volatility = np.std(recent) / np.mean(recent)

        # Low volatility indicates consolidation
        return volatility < 0.02  # Less than 2% volatility

    async def _find_support_resistance(
        self,
        market_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Find support and resistance levels"""
        price = market_data.get("price", 0.0)
        return {
            "support_1": price * 0.95,
            "support_2": price * 0.90,
            "resistance_1": price * 1.05,
            "resistance_2": price * 1.10
        }

    def _calculate_technical_sentiment(self, indicators: Dict[str, float]) -> float:
        """Calculate sentiment from technical indicators"""
        rsi = indicators.get("rsi", 50.0)

        if rsi > 70:
            return -0.5  # Overbought (bearish)
        elif rsi < 30:
            return 0.5  # Oversold (bullish)
        else:
            return (50 - rsi) / 100  # Neutral

    async def _generate_analysis(
        self,
        symbol: str,
        indicators: Dict[str, float],
        patterns: list,
        levels: Dict[str, float],
        bull_case: Optional[str],
        bear_case: Optional[str]
    ) -> str:
        """Generate comprehensive analysis summary"""

        rsi = indicators.get("rsi", 50.0)
        rsi_signal = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"

        macd = indicators.get("macd", 0.0)
        macd_signal = "Bullish" if macd > 0 else "Bearish" if macd < 0 else "Neutral"

        ema_20 = indicators.get("ema_20", 0.0)
        ema_50 = indicators.get("ema_50", 0.0)
        ma_trend = "Bullish crossover" if ema_20 > ema_50 else "Bearish crossover" if ema_20 < ema_50 else "Neutral"

        bb_upper = indicators.get("bb_upper", 0.0)
        bb_lower = indicators.get("bb_lower", 0.0)
        bb_middle = indicators.get("bb_middle", 0.0)

        return f"""
Technical Analysis for {symbol}:

📊 Momentum Indicators:
  • RSI(14): {rsi:.1f} - {rsi_signal}
  • MACD: {macd:.4f} - {macd_signal}
  • MACD Histogram: {indicators.get('macd_histogram', 0.0):.4f}

📈 Moving Averages:
  • EMA(20): ${ema_20:.2f}
  • EMA(50): ${ema_50:.2f}
  • Trend: {ma_trend}

📉 Bollinger Bands:
  • Upper: ${bb_upper:.2f}
  • Middle: ${bb_middle:.2f}
  • Lower: ${bb_lower:.2f}

🎯 Support/Resistance:
  • Support: ${levels.get('support_1', 0):.2f} / ${levels.get('support_2', 0):.2f}
  • Resistance: ${levels.get('resistance_1', 0):.2f} / ${levels.get('resistance_2', 0):.2f}

📐 Chart Patterns:
  {chr(10).join(['  • ' + p for p in patterns]) if patterns else '  • No patterns detected'}

💡 Summary:
Technical bias is {rsi_signal.lower()} with RSI at {rsi:.1f}.
Moving averages show {ma_trend.lower()}.
{len(patterns)} pattern(s) detected.
"""
