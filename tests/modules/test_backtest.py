"""
Unit tests for Backtesting Module
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

from core.modules.backtest import Backtester, BacktestResult


class TestBacktester:
    """Test suite for backtesting engine"""

    @pytest.fixture
    def backtester(self):
        """Create backtester instance"""
        return Backtester(
            initial_capital=10000,
            commission=0.001,
            slippage=0.0005
        )

    @pytest.fixture
    def sample_data(self):
        """Generate sample OHLCV data"""
        # Generate 100 days of fake data
        dates = [datetime.now() - timedelta(days=i) for i in range(100, 0, -1)]
        timestamps = np.array([int(d.timestamp() * 1000) for d in dates])

        # Random walk for prices
        np.random.seed(42)
        base_price = 50000
        returns = np.random.randn(100) * 0.02
        prices = base_price * np.exp(np.cumsum(returns))

        # OHLCV
        ohlcv = np.column_stack([
            timestamps,
            prices * 0.99,  # open
            prices * 1.01,  # high
            prices * 0.99,  # low
            prices,          # close
            np.random.rand(100) * 1000000  # volume
        ])

        return {'BTC/USDT': ohlcv}

    async def simple_strategy(self, market_data, timestamp):
        """Simple test strategy: buy when price > SMA, sell otherwise"""
        signals = {}

        for symbol, data in market_data.items():
            price = data[4]  # Close price

            # Simple moving average (mock)
            sma = 50000

            if price > sma:
                signals[symbol] = {'action': 'buy', 'confidence': 0.7}
            else:
                signals[symbol] = {'action': 'sell', 'confidence': 0.7}

        return signals

    @pytest.mark.asyncio
    async def test_backtester_initialization(self, backtester):
        """Test backtester initializes correctly"""
        assert backtester.initial_capital == 10000
        assert backtester.capital == 10000
        assert len(backtester.trades) == 0

    @pytest.mark.asyncio
    async def test_run_backtest(self, backtester, sample_data):
        """Test running a backtest"""
        start_date = datetime.now() - timedelta(days=90)
        end_date = datetime.now()

        result = await backtester.run(
            strategy_func=self.simple_strategy,
            data=sample_data,
            start_date=start_date,
            end_date=end_date
        )

        assert isinstance(result, BacktestResult)
        assert result.initial_capital == 10000

    @pytest.mark.asyncio
    async def test_position_sizing(self, backtester):
        """Test position size calculation"""
        price = 50000
        confidence = 0.7

        size = backtester._calculate_position_size(price, confidence)

        assert size > 0
        assert size * price <= backtester.capital * 0.1  # Max 10%

    @pytest.mark.asyncio
    async def test_sharpe_ratio_calculation(self, backtester):
        """Test Sharpe ratio calculation"""
        returns = np.random.randn(100) * 0.02

        sharpe = backtester._calculate_sharpe(returns)

        assert isinstance(sharpe, float)

    @pytest.mark.asyncio
    async def test_sortino_ratio_calculation(self, backtester):
        """Test Sortino ratio calculation"""
        returns = np.random.randn(100) * 0.02

        sortino = backtester._calculate_sortino(returns)

        assert isinstance(sortino, float)

    @pytest.mark.asyncio
    async def test_max_drawdown_calculation(self, backtester):
        """Test maximum drawdown calculation"""
        # Create equity curve with known drawdown
        backtester.equity_curve = [10000, 11000, 10500, 9000, 9500, 12000]

        max_dd, max_dd_pct = backtester._calculate_max_drawdown()

        assert max_dd < 0  # Drawdown should be negative
        assert max_dd_pct < 0

    def test_generate_report(self, backtester):
        """Test report generation"""
        result = BacktestResult(
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=0.6,
            total_pnl=500,
            total_return_pct=5.0,
            sharpe_ratio=1.2,
            sortino_ratio=1.5,
            max_drawdown=-200,
            max_drawdown_pct=-2.0,
            profit_factor=1.8,
            avg_win=150,
            avg_loss=-80,
            largest_win=300,
            largest_loss=-150,
            avg_trade_duration=timedelta(days=2),
            equity_curve=[10000, 10500],
            trades=[],
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            initial_capital=10000,
            final_capital=10500
        )

        report = backtester.generate_report(result)

        assert 'BACKTEST REPORT' in report
        assert 'Total Return' in report
        assert 'Sharpe Ratio' in report
