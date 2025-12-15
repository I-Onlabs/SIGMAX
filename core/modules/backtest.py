"""
Advanced Backtesting Framework with Performance Analytics
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from loguru import logger


@dataclass
class Trade:
    """Trade record"""
    symbol: str
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime]
    exit_price: Optional[float]
    size: float
    direction: str  # 'long' or 'short'
    pnl: float = 0.0
    pnl_pct: float = 0.0
    fees: float = 0.0
    reason: str = ""


@dataclass
class BacktestResult:
    """Backtesting results with comprehensive metrics"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_trade_duration: timedelta
    equity_curve: List[float]
    trades: List[Trade]
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float


class Backtester:
    """
    Advanced backtesting engine

    Features:
    - Realistic slippage and fees
    - Position sizing
    - Risk management
    - Performance analytics
    - Walk-forward optimization
    """

    def __init__(
        self,
        initial_capital: float = 10000,
        commission: float = 0.001,  # 0.1%
        slippage: float = 0.0005   # 0.05%
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

        self.capital = initial_capital
        self.equity_curve = [initial_capital]
        self.trades: List[Trade] = []
        self.open_positions: Dict[str, Trade] = {}

        logger.info(f"✓ Backtester initialized with ${initial_capital} capital")

    async def run(
        self,
        strategy_func,
        data: Dict[str, np.ndarray],
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """
        Run backtest

        Args:
            strategy_func: Strategy function that returns signals
            data: Dict of symbol -> OHLCV data
            start_date: Backtest start date
            end_date: Backtest end date

        Returns:
            Comprehensive backtest results
        """
        logger.info(f"🔄 Running backtest from {start_date} to {end_date}...")

        self.capital = self.initial_capital
        self.equity_curve = [self.initial_capital]
        self.trades = []
        self.open_positions = {}

        # Iterate through time
        timestamps = self._get_timestamps(data, start_date, end_date)

        for i, timestamp in enumerate(timestamps):
            # Get current market data
            market_data = self._get_market_data_at(data, i)

            # Get strategy signals
            signals = await strategy_func(market_data, timestamp)

            # Execute trades based on signals
            for symbol, signal in signals.items():
                await self._execute_signal(symbol, signal, market_data[symbol], timestamp)

            # Update equity
            self._update_equity(market_data, timestamp)

        # Close any remaining open positions
        final_data = self._get_market_data_at(data, len(timestamps) - 1)
        await self._close_all_positions(final_data, end_date)

        # Calculate performance metrics
        result = self._calculate_metrics(start_date, end_date)

        logger.info(f"✓ Backtest complete: {result.total_trades} trades, "
                   f"{result.win_rate:.1%} win rate, {result.total_return_pct:+.2%} return")

        return result

    async def _execute_signal(
        self,
        symbol: str,
        signal: Dict[str, Any],
        market_data: np.ndarray,
        timestamp: datetime
    ):
        """Execute trading signal"""
        action = signal.get('action', 'hold')
        current_price = market_data[4]  # Close price

        if action == 'buy' and symbol not in self.open_positions:
            # Open long position
            size = self._calculate_position_size(
                current_price,
                signal.get('confidence', 0.5)
            )

            if size > 0:
                entry_price = current_price * (1 + self.slippage)  # Slippage
                cost = size * entry_price
                fees = cost * self.commission

                if self.capital >= (cost + fees):
                    trade = Trade(
                        symbol=symbol,
                        entry_time=timestamp,
                        entry_price=entry_price,
                        exit_time=None,
                        exit_price=None,
                        size=size,
                        direction='long',
                        fees=fees,
                        reason=signal.get('reason', '')
                    )

                    self.open_positions[symbol] = trade
                    self.capital -= (cost + fees)

        elif action == 'sell' and symbol in self.open_positions:
            # Close long position
            trade = self.open_positions[symbol]
            exit_price = current_price * (1 - self.slippage)  # Slippage

            proceeds = trade.size * exit_price
            fees = proceeds * self.commission

            trade.exit_time = timestamp
            trade.exit_price = exit_price
            trade.pnl = (exit_price - trade.entry_price) * trade.size - trade.fees - fees
            trade.pnl_pct = ((exit_price / trade.entry_price) - 1) * 100
            trade.fees += fees

            self.capital += proceeds - fees
            self.trades.append(trade)
            del self.open_positions[symbol]

    def _calculate_position_size(
        self,
        price: float,
        confidence: float
    ) -> float:
        """Calculate position size based on capital and confidence"""
        # Kelly Criterion with confidence adjustment
        max_position_pct = 0.1  # Max 10% of capital per trade
        adjusted_pct = max_position_pct * confidence

        max_amount = self.capital * adjusted_pct
        size = max_amount / price

        return size

    def _update_equity(self, market_data: Dict[str, np.ndarray], timestamp: datetime):
        """Update equity curve"""
        open_pnl = 0

        for symbol, trade in self.open_positions.items():
            if symbol in market_data:
                current_price = market_data[symbol][4]
                unrealized_pnl = (current_price - trade.entry_price) * trade.size
                open_pnl += unrealized_pnl

        current_equity = self.capital + open_pnl
        self.equity_curve.append(current_equity)

    async def _close_all_positions(
        self,
        market_data: Dict[str, np.ndarray],
        timestamp: datetime
    ):
        """Close all open positions at end of backtest"""
        symbols_to_close = list(self.open_positions.keys())

        for symbol in symbols_to_close:
            if symbol in market_data:
                signal = {'action': 'sell', 'reason': 'end_of_backtest'}
                await self._execute_signal(symbol, signal, market_data[symbol], timestamp)

    def _calculate_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Calculate comprehensive performance metrics"""

        if not self.trades:
            logger.warning("No trades executed during backtest")
            return BacktestResult(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0,
                total_pnl=0,
                total_return_pct=0,
                sharpe_ratio=0,
                sortino_ratio=0,
                max_drawdown=0,
                max_drawdown_pct=0,
                profit_factor=0,
                avg_win=0,
                avg_loss=0,
                largest_win=0,
                largest_loss=0,
                avg_trade_duration=timedelta(0),
                equity_curve=self.equity_curve,
                trades=[],
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.initial_capital,
                final_capital=self.capital
            )

        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.pnl > 0])
        losing_trades = len([t for t in self.trades if t.pnl <= 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # PnL metrics
        total_pnl = sum(t.pnl for t in self.trades)
        total_return_pct = (self.capital - self.initial_capital) / self.initial_capital * 100

        wins = [t.pnl for t in self.trades if t.pnl > 0]
        losses = [t.pnl for t in self.trades if t.pnl <= 0]

        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = min(losses) if losses else 0

        # Profit factor
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Risk-adjusted returns
        returns = np.diff(self.equity_curve) / self.equity_curve[:-1]

        sharpe_ratio = self._calculate_sharpe(returns)
        sortino_ratio = self._calculate_sortino(returns)

        # Drawdown
        max_drawdown, max_drawdown_pct = self._calculate_max_drawdown()

        # Average trade duration
        durations = [
            (t.exit_time - t.entry_time)
            for t in self.trades
            if t.exit_time
        ]
        avg_trade_duration = (
            sum(durations, timedelta(0)) / len(durations)
            if durations else timedelta(0)
        )

        return BacktestResult(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            total_return_pct=total_return_pct,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            avg_trade_duration=avg_trade_duration,
            equity_curve=self.equity_curve,
            trades=self.trades,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=self.capital
        )

    def _calculate_sharpe(self, returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) == 0:
            return 0

        # Annualized
        mean_return = np.mean(returns) * 252  # Assuming daily returns
        std_return = np.std(returns) * np.sqrt(252)

        if std_return == 0:
            return 0

        sharpe = (mean_return - risk_free_rate) / std_return
        return float(sharpe)

    def _calculate_sortino(self, returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (uses downside deviation)"""
        if len(returns) == 0:
            return 0

        mean_return = np.mean(returns) * 252

        # Downside deviation
        negative_returns = returns[returns < 0]
        downside_std = np.std(negative_returns) * np.sqrt(252) if len(negative_returns) > 0 else 0

        if downside_std == 0:
            return 0

        sortino = (mean_return - risk_free_rate) / downside_std
        return float(sortino)

    def _calculate_max_drawdown(self) -> Tuple[float, float]:
        """Calculate maximum drawdown"""
        if len(self.equity_curve) < 2:
            return 0, 0

        equity = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity)
        drawdown = equity - running_max
        max_drawdown = np.min(drawdown)
        max_drawdown_pct = (max_drawdown / self.initial_capital) * 100

        return float(max_drawdown), float(max_drawdown_pct)

    def _get_timestamps(
        self,
        data: Dict[str, np.ndarray],
        start_date: datetime,
        end_date: datetime
    ) -> List[datetime]:
        """Extract timestamps from data"""
        # Get first symbol's timestamps
        first_symbol = list(data.keys())[0]
        timestamps = [
            datetime.fromtimestamp(ts / 1000)  # Assuming milliseconds
            for ts in data[first_symbol][:, 0]
        ]

        # Filter by date range
        filtered = [
            ts for ts in timestamps
            if start_date <= ts <= end_date
        ]

        return filtered

    def _get_market_data_at(
        self,
        data: Dict[str, np.ndarray],
        index: int
    ) -> Dict[str, np.ndarray]:
        """Get market data at specific index"""
        return {
            symbol: ohlcv[index]
            for symbol, ohlcv in data.items()
            if index < len(ohlcv)
        }

    def generate_report(self, result: BacktestResult) -> str:
        """Generate detailed backtest report"""
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║              SIGMAX BACKTEST REPORT                          ║
╚══════════════════════════════════════════════════════════════╝

Period: {result.start_date.strftime('%Y-%m-%d')} to {result.end_date.strftime('%Y-%m-%d')}
Initial Capital: ${result.initial_capital:,.2f}
Final Capital: ${result.final_capital:,.2f}

═══════════════════════════════════════════════════════════════

PERFORMANCE SUMMARY
═══════════════════════════════════════════════════════════════

Total Return:        {result.total_return_pct:+.2f}%
Total PnL:           ${result.total_pnl:+,.2f}

Sharpe Ratio:        {result.sharpe_ratio:.2f}
Sortino Ratio:       {result.sortino_ratio:.2f}

Max Drawdown:        ${result.max_drawdown:,.2f} ({result.max_drawdown_pct:.2f}%)

═══════════════════════════════════════════════════════════════

TRADING STATISTICS
═══════════════════════════════════════════════════════════════

Total Trades:        {result.total_trades}
Winning Trades:      {result.winning_trades} ({result.win_rate:.1%})
Losing Trades:       {result.losing_trades}

Profit Factor:       {result.profit_factor:.2f}

Average Win:         ${result.avg_win:+,.2f}
Average Loss:        ${result.avg_loss:+,.2f}
Largest Win:         ${result.largest_win:+,.2f}
Largest Loss:        ${result.largest_loss:+,.2f}

Avg Trade Duration:  {result.avg_trade_duration}

═══════════════════════════════════════════════════════════════

RECENT TRADES (Last 10)
═══════════════════════════════════════════════════════════════
"""

        for trade in result.trades[-10:]:
            exit_time_str = trade.exit_time.strftime('%Y-%m-%d %H:%M') if trade.exit_time else 'Open'
            exit_price_val = trade.exit_price if trade.exit_price is not None else 0.0

            report += f"""
{trade.symbol}: {trade.direction.upper()}
Entry: {trade.entry_time.strftime('%Y-%m-%d %H:%M')} @ ${trade.entry_price:.2f}
Exit:  {exit_time_str} @ ${exit_price_val:.2f}
PnL:   ${trade.pnl:+,.2f} ({trade.pnl_pct:+.2f}%)
"""

        report += "\n═══════════════════════════════════════════════════════════════\n"

        return report
