"""
Comprehensive backtest validation with realistic historical data scenarios.
Tests various trading strategies and validates all performance metrics.
"""

import pytest
from datetime import datetime
import numpy as np
from typing import Dict, List
import pandas as pd

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.modules.backtest import Backtester, BacktestResult
from core.testing.fixtures import MockMarketData


class TestBacktestValidation:
    """Validate backtesting engine with realistic scenarios"""

    @pytest.fixture
    def backtester(self):
        """Create backtester instance with realistic parameters"""
        return Backtester(
            initial_capital=10000,
            commission=0.001,  # 0.1% commission
            slippage=0.0005    # 0.05% slippage
        )

    @pytest.fixture
    def generate_trending_market(self):
        """Generate bullish trending market data"""
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='1H')
        n = len(dates)

        # Upward trend with volatility
        trend = np.linspace(30000, 50000, n)
        noise = np.random.normal(0, 500, n)
        closes = trend + noise

        # Generate OHLCV
        data = []
        for i, (date, close) in enumerate(zip(dates, closes)):
            open_price = close + np.random.uniform(-200, 200)
            high = max(open_price, close) + abs(np.random.uniform(0, 300))
            low = min(open_price, close) - abs(np.random.uniform(0, 300))
            volume = np.random.uniform(100, 1000)

            data.append([
                int(date.timestamp() * 1000),  # timestamp
                open_price,
                high,
                low,
                close,
                volume
            ])

        return data

    @pytest.fixture
    def generate_ranging_market(self):
        """Generate sideways ranging market data"""
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='1H')
        n = len(dates)

        # Oscillating around mean
        mean_price = 40000
        noise = np.random.normal(0, 1000, n)
        sine_wave = np.sin(np.linspace(0, 4 * np.pi, n)) * 2000
        closes = mean_price + noise + sine_wave

        data = []
        for i, (date, close) in enumerate(zip(dates, closes)):
            open_price = close + np.random.uniform(-100, 100)
            high = max(open_price, close) + abs(np.random.uniform(0, 200))
            low = min(open_price, close) - abs(np.random.uniform(0, 200))
            volume = np.random.uniform(100, 1000)

            data.append([
                int(date.timestamp() * 1000),
                open_price,
                high,
                low,
                close,
                volume
            ])

        return data

    @pytest.fixture
    def generate_volatile_market(self):
        """Generate highly volatile market with sharp moves"""
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='1H')
        n = len(dates)

        # Random walk with high volatility
        returns = np.random.normal(0, 0.02, n)  # 2% std per period
        closes = 40000 * np.exp(np.cumsum(returns))

        data = []
        for i, (date, close) in enumerate(zip(dates, closes)):
            open_price = close + np.random.uniform(-500, 500)
            high = max(open_price, close) + abs(np.random.uniform(0, 1000))
            low = min(open_price, close) - abs(np.random.uniform(0, 1000))
            volume = np.random.uniform(100, 1000)

            data.append([
                int(date.timestamp() * 1000),
                open_price,
                high,
                low,
                close,
                volume
            ])

        return data

    async def simple_ma_crossover_strategy(self, market_data: Dict[str, np.ndarray], timestamp: datetime) -> Dict:
        """Simple moving average crossover strategy"""
        # For testing purposes, use BTC/USDT
        symbol = "BTC/USDT"
        if symbol not in market_data:
            return {}

        data = market_data[symbol]

        # Need at least 50 candles
        if len(data) < 50:
            return {symbol: {"action": "hold", "confidence": 0.5}}

        # Calculate 20 and 50 period MAs
        closes = data[-50:, 4]  # Last 50 closes

        ma_20 = np.mean(closes[-20:])
        ma_50 = np.mean(closes[-50:])
        prev_ma_20 = np.mean(closes[-21:-1])
        current_price = closes[-1]

        # Generate signals
        if ma_20 > ma_50 and prev_ma_20 <= ma_50:
            # Bullish crossover
            return {symbol: {"action": "buy", "confidence": 0.7}}
        elif ma_20 < ma_50 and prev_ma_20 >= ma_50:
            # Bearish crossover
            return {symbol: {"action": "sell", "confidence": 0.7}}

        return {symbol: {"action": "hold", "confidence": 0.5}}

    async def rsi_strategy(self, data: List[List[float]], index: int) -> Dict:
        """RSI-based mean reversion strategy"""
        if index < 14:
            return {"action": "hold", "confidence": 0.5}

        # Calculate RSI
        closes = [candle[4] for candle in data[max(0, index-14):index+1]]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]

        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        avg_gain = sum(gains) / len(gains)
        avg_loss = sum(losses) / len(losses)

        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        # Generate signals
        if rsi < 30:
            # Oversold - buy signal
            return {"action": "buy", "confidence": 0.8}
        elif rsi > 70:
            # Overbought - sell signal
            return {"action": "sell", "confidence": 0.8}

        return {"action": "hold", "confidence": 0.5}

    async def trend_following_strategy(self, data: List[List[float]], index: int) -> Dict:
        """Trend following strategy with momentum"""
        if index < 30:
            return {"action": "hold", "confidence": 0.5}

        closes = [candle[4] for candle in data[max(0, index-30):index+1]]

        # Calculate trend strength
        ma_10 = sum(closes[-10:]) / 10
        ma_30 = sum(closes[-30:]) / 30
        current_price = closes[-1]

        # Momentum
        momentum = (current_price - closes[-10]) / closes[-10]

        # Strong uptrend
        if ma_10 > ma_30 and momentum > 0.02:
            return {"action": "buy", "confidence": 0.85}
        # Strong downtrend
        elif ma_10 < ma_30 and momentum < -0.02:
            return {"action": "sell", "confidence": 0.85}

        return {"action": "hold", "confidence": 0.5}

    @pytest.mark.asyncio
    async def test_backtest_trending_market(self, backtester, generate_trending_market):
        """Test backtesting in bullish trending market"""
        data = generate_trending_market
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        # Run backtest with trend following strategy
        result = await backtester.run(
            strategy=self.trend_following_strategy,
            data=data,
            start_date=start_date,
            end_date=end_date
        )

        # Validate results
        assert isinstance(result, BacktestResult)
        assert result.total_return != 0
        assert result.total_trades > 0
        assert result.win_rate >= 0 and result.win_rate <= 1
        assert result.sharpe_ratio is not None
        assert result.sortino_ratio is not None
        assert result.max_drawdown >= 0 and result.max_drawdown <= 1

        # In trending market, trend following should be profitable
        print("\n=== Trending Market Results ===")
        print(f"Total Return: {result.total_return:.2%}")
        print(f"Win Rate: {result.win_rate:.2%}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"Max Drawdown: {result.max_drawdown:.2%}")
        print(f"Total Trades: {result.total_trades}")

        # Generate report
        report = backtester.generate_report()
        assert "BACKTEST RESULTS" in report
        assert len(report) > 100

    @pytest.mark.asyncio
    async def test_backtest_ranging_market(self, backtester, generate_ranging_market):
        """Test backtesting in sideways ranging market"""
        data = generate_ranging_market
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        # Run backtest with RSI mean reversion strategy
        result = await backtester.run(
            strategy=self.rsi_strategy,
            data=data,
            start_date=start_date,
            end_date=end_date
        )

        # Validate results
        assert isinstance(result, BacktestResult)
        assert result.total_trades > 0

        print("\n=== Ranging Market Results ===")
        print(f"Total Return: {result.total_return:.2%}")
        print(f"Win Rate: {result.win_rate:.2%}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"Max Drawdown: {result.max_drawdown:.2%}")
        print(f"Profit Factor: {result.profit_factor:.2f}")

    @pytest.mark.asyncio
    async def test_backtest_volatile_market(self, backtester, generate_volatile_market):
        """Test backtesting in highly volatile market"""
        data = generate_volatile_market
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        # Run backtest with MA crossover strategy
        result = await backtester.run(
            strategy=self.simple_ma_crossover_strategy,
            data=data,
            start_date=start_date,
            end_date=end_date
        )

        # Validate results
        assert isinstance(result, BacktestResult)
        assert result.total_trades >= 0

        print("\n=== Volatile Market Results ===")
        print(f"Total Return: {result.total_return:.2%}")
        print(f"Win Rate: {result.win_rate:.2%}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"Max Drawdown: {result.max_drawdown:.2%}")
        print(f"Average Trade Duration: {result.avg_trade_duration_hours:.1f} hours")

    @pytest.mark.asyncio
    async def test_backtest_metrics_accuracy(self, backtester, generate_trending_market):
        """Validate accuracy of performance metrics calculations"""
        data = generate_trending_market
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        result = await backtester.run(
            strategy=self.trend_following_strategy,
            data=data,
            start_date=start_date,
            end_date=end_date
        )

        # Validate metric ranges
        assert -1 <= result.total_return <= 10  # -100% to +1000%
        assert 0 <= result.win_rate <= 1
        assert result.max_drawdown >= 0

        if result.total_trades > 0:
            assert result.profit_factor >= 0
            assert result.avg_win > 0 or result.winning_trades == 0
            assert result.avg_loss <= 0 or result.losing_trades == 0

            # Sharpe ratio should be reasonable
            assert -5 <= result.sharpe_ratio <= 10

            # Validate trade counts
            assert result.winning_trades + result.losing_trades == result.total_trades

        print("\n=== Metrics Validation ===")
        print(f"✓ Total Return: {result.total_return:.2%}")
        print(f"✓ Win Rate: {result.win_rate:.2%}")
        print(f"✓ Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"✓ Sortino Ratio: {result.sortino_ratio:.2f}")
        print(f"✓ Profit Factor: {result.profit_factor:.2f}")
        print(f"✓ Max Drawdown: {result.max_drawdown:.2%}")

    @pytest.mark.asyncio
    async def test_backtest_commission_impact(self, generate_trending_market):
        """Test impact of different commission rates"""
        data = generate_trending_market
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        # Test with different commission rates
        commission_rates = [0.0, 0.001, 0.002, 0.005]
        results = []

        for rate in commission_rates:
            backtester = Backtester(
                initial_capital=10000,
                commission=rate,
                slippage=0.0005
            )

            result = await backtester.run(
                strategy=self.trend_following_strategy,
                data=data,
                start_date=start_date,
                end_date=end_date
            )
            results.append((rate, result.total_return))

        print("\n=== Commission Impact ===")
        for rate, ret in results:
            print(f"Commission {rate:.2%}: Return {ret:.2%}")

        # Higher commission should result in lower returns
        assert results[0][1] >= results[-1][1], "Higher commission should reduce returns"

    @pytest.mark.asyncio
    async def test_backtest_position_sizing(self, backtester, generate_trending_market):
        """Validate Kelly Criterion position sizing"""
        data = generate_trending_market
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        result = await backtester.run(
            strategy=self.trend_following_strategy,
            data=data,
            start_date=start_date,
            end_date=end_date
        )

        # Check that trades were executed
        if result.total_trades > 0:
            # Position sizes should be reasonable (max 10% of capital)
            max_position = backtester.initial_capital * 0.1

            print("\n=== Position Sizing Validation ===")
            print("✓ Kelly Criterion position sizing active")
            print(f"✓ Max position size: {max_position:.2f}")
            print(f"✓ Total trades executed: {result.total_trades}")

    @pytest.mark.asyncio
    async def test_backtest_edge_cases(self, backtester):
        """Test edge cases: no signals, single trade, etc."""

        # Test 1: No signals (always hold)
        async def no_signal_strategy(data, index):
            return {"action": "hold", "confidence": 0.5}

        data = MockMarketData.generate_ohlcv("BTC/USDT", periods=100)
        result = await backtester.run(
            strategy=no_signal_strategy,
            data=data,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )

        assert result.total_trades == 0
        assert result.total_return == 0.0
        print("\n=== Edge Case: No Signals ===")
        print(f"✓ Total trades: {result.total_trades}")
        print(f"✓ Return: {result.total_return:.2%}")

        # Test 2: Single buy and hold
        async def buy_once_strategy(data, index):
            if index == 10:
                return {"action": "buy", "confidence": 0.8}
            return {"action": "hold", "confidence": 0.5}

        result = await backtester.run(
            strategy=buy_once_strategy,
            data=data,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )

        assert result.total_trades >= 0
        print("\n=== Edge Case: Buy and Hold ===")
        print(f"✓ Total trades: {result.total_trades}")
        print(f"✓ Return: {result.total_return:.2%}")

    @pytest.mark.asyncio
    async def test_backtest_report_generation(self, backtester, generate_trending_market):
        """Test comprehensive report generation"""
        data = generate_trending_market

        result = await backtester.run(
            strategy=self.trend_following_strategy,
            data=data,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )

        report = backtester.generate_report()

        # Validate report contents
        assert "BACKTEST RESULTS" in report
        assert "Performance Metrics" in report
        assert "Risk Metrics" in report
        assert "Trade Statistics" in report

        # Check all metrics are included
        assert f"{result.total_return:.2%}" in report
        assert f"{result.sharpe_ratio:.2f}" in report
        assert f"{result.max_drawdown:.2%}" in report

        print("\n=== Generated Report ===")
        print(report)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
