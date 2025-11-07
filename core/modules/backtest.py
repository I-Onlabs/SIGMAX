"""
Advanced Backtesting Framework with Performance Analytics
"""

from typing import Dict, Any, List, Optional, Tuple
import inspect
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
    max_drawdown_amount: float
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

    @property
    def total_return(self) -> float:
        """Return total return as a decimal for legacy compatibility."""
        return self.total_return_pct / 100

    @property
    def max_drawdown(self) -> float:
        """Return max drawdown as a decimal ratio."""
        return abs(self.max_drawdown_pct) / 100

    @property
    def avg_trade_duration_hours(self) -> float:
        """Return average trade duration in hours."""
        if self.avg_trade_duration.total_seconds() == 0:
            return 0.0
        return self.avg_trade_duration.total_seconds() / 3600


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

    DEFAULT_SYMBOL = "BTC/USDT"

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
        self._default_symbol: Optional[str] = self.DEFAULT_SYMBOL
        self.last_result: Optional[BacktestResult] = None

        logger.info(f"✓ Backtester initialized with ${initial_capital} capital")

    async def run(
        self,
        strategy_func=None,
        data: Optional[Dict[str, np.ndarray]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        *,
        strategy=None,
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
        strategy_callable = strategy or strategy_func
        if strategy_callable is None:
            raise ValueError("A strategy function must be provided")
        if data is None or start_date is None or end_date is None:
            raise ValueError("Data and date range are required for backtesting")

        logger.info(f"🔄 Running backtest from {start_date} to {end_date}...")

        self.capital = self.initial_capital
        self.equity_curve = [self.initial_capital]
        self.trades = []
        self.open_positions = {}

        normalized_data, raw_data_map = self._normalize_input_data(data)
        self._default_symbol = next(iter(normalized_data))

        strategy_mode = self._detect_strategy_mode(strategy_callable)

        # Iterate through time
        timestamps = self._get_timestamps(normalized_data, start_date, end_date)

        for index, timestamp in enumerate(timestamps):
            # Get current market data
            market_data = self._get_market_data_at(normalized_data, index)

            # Get strategy signals (modern timestamp-aware or legacy index-based)
            signals = await self._invoke_strategy(
                strategy_callable,
                strategy_mode,
                market_data,
                timestamp,
                index,
                raw_data_map,
            )

            # Execute trades based on signals
            for symbol, signal in signals.items():
                await self._execute_signal(symbol, signal, market_data[symbol], timestamp)

            # Update equity
            self._update_equity(market_data, timestamp)

        # Close any remaining open positions
        final_data = self._get_market_data_at(normalized_data, len(timestamps) - 1)
        await self._close_all_positions(final_data, end_date)

        # Calculate performance metrics
        result = self._calculate_metrics(start_date, end_date)
        self.last_result = result

        logger.info(f"✓ Backtest complete: {result.total_trades} trades, "
                   f"{result.win_rate:.1%} win rate, {result.total_return_pct:+.2%} return")

        return result

    def _normalize_input_data(
        self,
        data: Any
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, List[List[float]]]]:
        """Normalize incoming market data into internal structures."""
        if isinstance(data, dict):
            normalized: Dict[str, np.ndarray] = {}
            raw: Dict[str, List[List[float]]] = {}
            for symbol, values in data.items():
                array = np.array(values)
                normalized[symbol] = array
                if isinstance(values, list):
                    raw[symbol] = values
                else:
                    raw[symbol] = array.tolist()
            return normalized, raw

        if isinstance(data, list):
            symbol = self._default_symbol or self.DEFAULT_SYMBOL
            array = np.array(data)
            return {symbol: array}, {symbol: data}

        raise TypeError("Backtester data must be a dict or list of OHLCV rows.")

    def _detect_strategy_mode(self, strategy_callable: Any) -> str:
        """Inspect a strategy callable to determine the expected signature."""
        try:
            params = list(inspect.signature(strategy_callable).parameters.values())
        except (TypeError, ValueError):
            return "modern"

        # Skip the first parameter (typically market_data or data)
        for param in params[1:]:
            name = param.name.lower()
            if "index" in name or name in {"idx", "position"}:
                return "legacy"
        return "modern"

    async def _invoke_strategy(
        self,
        strategy_callable: Any,
        strategy_mode: str,
        market_data: Dict[str, np.ndarray],
        timestamp: datetime,
        index: int,
        raw_data_map: Dict[str, List[List[float]]]
    ) -> Dict[str, Dict[str, Any]]:
        """Call strategy with support for modern and legacy signatures."""
        default_symbol = self._default_symbol or self.DEFAULT_SYMBOL

        if strategy_mode == "legacy":
            legacy_payload = self._select_legacy_series(raw_data_map, default_symbol)
            legacy_signals = await strategy_callable(legacy_payload, index)
            return self._normalize_signals(legacy_signals, default_symbol)

        try:
            modern_signals = await strategy_callable(market_data, timestamp)
            return self._normalize_signals(modern_signals, default_symbol)
        except TypeError as exc:
            # Fallback to legacy signature if callable rejects timestamp form
            legacy_payload = self._select_legacy_series(raw_data_map, default_symbol)
            try:
                legacy_signals = await strategy_callable(legacy_payload, index)
            except TypeError:
                raise exc
            return self._normalize_signals(legacy_signals, default_symbol)

    def _select_legacy_series(
        self,
        raw_data_map: Dict[str, List[List[float]]],
        default_symbol: str
    ) -> List[List[float]]:
        """Choose the appropriate OHLCV series for legacy strategies."""
        if default_symbol in raw_data_map:
            return raw_data_map[default_symbol]
        return next(iter(raw_data_map.values()))

    def _normalize_signals(
        self,
        signals: Any,
        default_symbol: str
    ) -> Dict[str, Dict[str, Any]]:
        """Ensure strategy signals are keyed by symbol."""
        if not signals:
            return {}

        if isinstance(signals, dict):
            if "action" in signals:
                return {default_symbol: dict(signals)}

            normalized: Dict[str, Dict[str, Any]] = {}
            for symbol, payload in signals.items():
                if isinstance(payload, dict):
                    normalized[symbol] = dict(payload)
                else:
                    normalized[symbol] = {"action": payload}
            return normalized

        raise TypeError("Strategy must return a dictionary of signals.")

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
                max_drawdown_amount=0,
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
        max_drawdown_amount, max_drawdown_pct = self._calculate_max_drawdown()

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
            max_drawdown_amount=max_drawdown_amount,
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
        returns_list = returns.tolist() if hasattr(returns, "tolist") else list(returns)
        negative_returns = [value for value in returns_list if value < 0]
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
        drawdown = running_max - equity
        max_drawdown = np.max(drawdown)
        max_drawdown_pct = (max_drawdown / self.initial_capital) * 100 if self.initial_capital else 0

        return float(max_drawdown), float(max_drawdown_pct)

    def _get_timestamps(
        self,
        data: Dict[str, np.ndarray],
        start_date: datetime,
        end_date: datetime
    ) -> List[datetime]:
        """Extract timestamps from data"""
        # Get first symbol's timestamps
        first_symbol = next(iter(data))
        symbol_data = data[first_symbol]
        timestamps = [
            datetime.fromtimestamp(row[0] / 1000)  # Assuming milliseconds
            for row in symbol_data
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

    def generate_report(self, result: Optional[BacktestResult] = None) -> str:
        """Generate detailed backtest report."""
        result = result or self.last_result
        if result is None:
            raise ValueError("No backtest results available. Run a backtest first or provide a result.")

        lines = [
            "=== BACKTEST RESULTS ===",
            f"Period: {result.start_date.strftime('%Y-%m-%d')} to {result.end_date.strftime('%Y-%m-%d')}",
            f"Initial Capital: ${result.initial_capital:,.2f}",
            f"Final Capital: ${result.final_capital:,.2f}",
            "",
            "Performance Metrics",
            "-------------------",
            f"Total Return: {result.total_return:.2%}",
            f"Total PnL: ${result.total_pnl:+,.2f}",
            f"Sharpe Ratio: {result.sharpe_ratio:.2f}",
            f"Sortino Ratio: {result.sortino_ratio:.2f}",
            "",
            "Risk Metrics",
            "------------",
            f"Max Drawdown: {result.max_drawdown:.2%}",
            f"Max Drawdown ($): ${result.max_drawdown_amount:+,.2f}",
            "",
            "Trade Statistics",
            "----------------",
            f"Total Trades: {result.total_trades}",
            f"Winning Trades: {result.winning_trades}",
            f"Losing Trades: {result.losing_trades}",
            f"Win Rate: {result.win_rate:.2%}",
            f"Profit Factor: {result.profit_factor:.2f}",
            f"Average Win: ${result.avg_win:+,.2f}",
            f"Average Loss: ${result.avg_loss:+,.2f}",
            f"Largest Win: ${result.largest_win:+,.2f}",
            f"Largest Loss: ${result.largest_loss:+,.2f}",
            f"Average Trade Duration: {result.avg_trade_duration}",
        ]

        if result.trades:
            lines.append("")
            lines.append("Recent Trades")
            lines.append("-------------")
            for trade in result.trades[-10:]:
                lines.append(f"{trade.symbol} {trade.direction.upper()} @ ${trade.entry_price:.2f}")
                exit_info = trade.exit_time.strftime('%Y-%m-%d %H:%M') if trade.exit_time else 'Open'
                exit_price = trade.exit_price if trade.exit_price is not None else 0
                lines.append(f"Exit: {exit_info} @ ${exit_price:.2f}")
                lines.append(f"PnL: ${trade.pnl:+,.2f} ({trade.pnl_pct:+.2f}%)")
                lines.append("")

        return "\n".join(line for line in lines if line is not None)
