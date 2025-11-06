#!/usr/bin/env python3
"""
Trade Analysis Tool

Analyzes historical trades and computes performance metrics.
"""

import sys
import argparse
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class Trade:
    """Completed trade"""
    timestamp: datetime
    symbol: str
    side: str
    qty: float
    price: float
    fee: float
    pnl: float = 0.0
    strategy: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Trading performance metrics"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    total_fees: float
    volume_traded: float


class TradeAnalyzer:
    """
    Analyze trading performance from historical data.

    Computes:
    - P&L (realized and unrealized)
    - Win rate and profit factor
    - Sharpe ratio and max drawdown
    - Strategy-level breakdowns
    - Symbol-level breakdowns
    """

    def __init__(self, db_config: Optional[Dict] = None):
        self.db_config = db_config or {
            'host': 'localhost',
            'port': 5432,
            'database': 'sigmax',
            'user': 'sigmax',
            'password': 'sigmax_dev_password'
        }
        self.trades: List[Trade] = []

    async def load_trades(self, start_date: datetime, end_date: datetime) -> int:
        """
        Load trades from database.

        Returns:
            Number of trades loaded
        """
        try:
            import psycopg2
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            query = """
                SELECT
                    f.created_at,
                    s.symbol,
                    f.side,
                    f.qty,
                    f.price,
                    f.fee,
                    o.strategy
                FROM fills f
                JOIN symbols s ON f.symbol_id = s.id
                LEFT JOIN orders o ON f.client_id = o.client_id
                WHERE f.created_at BETWEEN %s AND %s
                ORDER BY f.created_at
            """

            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()

            self.trades = []
            for row in rows:
                self.trades.append(Trade(
                    timestamp=row[0],
                    symbol=row[1],
                    side=row[2],
                    qty=row[3],
                    price=row[4],
                    fee=row[5],
                    strategy=row[6]
                ))

            cursor.close()
            conn.close()

            return len(self.trades)

        except ImportError:
            print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
            return 0
        except Exception as e:
            print(f"Error loading trades: {e}")
            return 0

    def calculate_pnl(self) -> Dict[str, float]:
        """
        Calculate P&L by matching buy/sell pairs.

        Returns:
            Dict with realized_pnl, unrealized_pnl, total_fees
        """
        positions: Dict[str, List[Trade]] = defaultdict(list)  # symbol -> [buys]
        realized_pnl = 0.0
        total_fees = 0.0

        for trade in self.trades:
            total_fees += trade.fee

            if trade.side == 'buy':
                # Add to position
                positions[trade.symbol].append(trade)
            else:
                # Match with buys (FIFO)
                remaining_qty = trade.qty
                sell_price = trade.price

                while remaining_qty > 0 and positions[trade.symbol]:
                    buy_trade = positions[trade.symbol][0]

                    if buy_trade.qty <= remaining_qty:
                        # Full close
                        qty = buy_trade.qty
                        pnl = (sell_price - buy_trade.price) * qty
                        realized_pnl += pnl
                        trade.pnl += pnl
                        remaining_qty -= qty
                        positions[trade.symbol].pop(0)
                    else:
                        # Partial close
                        qty = remaining_qty
                        pnl = (sell_price - buy_trade.price) * qty
                        realized_pnl += pnl
                        trade.pnl += pnl
                        buy_trade.qty -= qty
                        remaining_qty = 0

        # Calculate unrealized P&L (requires current prices - simplified here)
        unrealized_pnl = 0.0

        return {
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'total_fees': total_fees,
            'net_pnl': realized_pnl - total_fees
        }

    def calculate_metrics(self) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        if not self.trades:
            return PerformanceMetrics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_pnl=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                total_fees=0.0,
                volume_traded=0.0
            )

        pnl_data = self.calculate_pnl()

        # Winning/losing trades
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]

        total_wins = sum(t.pnl for t in winning_trades) if winning_trades else 0
        total_losses = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0

        # Volume traded
        volume_traded = sum(t.qty * t.price for t in self.trades)

        # Profit factor
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')

        # Max drawdown (simplified)
        cumulative_pnl = []
        running_pnl = 0.0
        for trade in self.trades:
            running_pnl += trade.pnl
            cumulative_pnl.append(running_pnl)

        max_drawdown = 0.0
        peak = 0.0
        for pnl in cumulative_pnl:
            if pnl > peak:
                peak = pnl
            drawdown = peak - pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # Sharpe ratio (simplified - assumes daily returns)
        if len(self.trades) > 1:
            daily_returns = []
            current_date = self.trades[0].timestamp.date()
            daily_pnl = 0.0

            for trade in self.trades:
                if trade.timestamp.date() == current_date:
                    daily_pnl += trade.pnl
                else:
                    daily_returns.append(daily_pnl)
                    current_date = trade.timestamp.date()
                    daily_pnl = trade.pnl

            daily_returns.append(daily_pnl)

            if len(daily_returns) > 1:
                import statistics
                mean_return = statistics.mean(daily_returns)
                std_return = statistics.stdev(daily_returns)
                sharpe_ratio = (mean_return / std_return) * (252 ** 0.5) if std_return > 0 else 0.0
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0

        return PerformanceMetrics(
            total_trades=len(self.trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=len(winning_trades) / len(self.trades) * 100 if self.trades else 0.0,
            total_pnl=pnl_data['net_pnl'],
            avg_win=total_wins / len(winning_trades) if winning_trades else 0.0,
            avg_loss=total_losses / len(losing_trades) if losing_trades else 0.0,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            total_fees=pnl_data['total_fees'],
            volume_traded=volume_traded
        )

    def breakdown_by_strategy(self) -> Dict[str, PerformanceMetrics]:
        """Get performance breakdown by strategy"""
        strategies = {}
        by_strategy = defaultdict(list)

        for trade in self.trades:
            strategy = trade.strategy or 'unknown'
            by_strategy[strategy].append(trade)

        for strategy, trades in by_strategy.items():
            analyzer = TradeAnalyzer()
            analyzer.trades = trades
            strategies[strategy] = analyzer.calculate_metrics()

        return strategies

    def breakdown_by_symbol(self) -> Dict[str, PerformanceMetrics]:
        """Get performance breakdown by symbol"""
        symbols = {}
        by_symbol = defaultdict(list)

        for trade in self.trades:
            by_symbol[trade.symbol].append(trade)

        for symbol, trades in by_symbol.items():
            analyzer = TradeAnalyzer()
            analyzer.trades = trades
            symbols[symbol] = analyzer.calculate_metrics()

        return symbols

    def print_report(self):
        """Print comprehensive performance report"""
        print("\n" + "=" * 80)
        print("TRADING PERFORMANCE REPORT")
        print("=" * 80)

        if not self.trades:
            print("\nNo trades found in the specified period.")
            return

        # Overall metrics
        metrics = self.calculate_metrics()

        print("\n📊 OVERALL PERFORMANCE")
        print("-" * 80)
        print(f"Total Trades:      {metrics.total_trades}")
        print(f"Winning Trades:    {metrics.winning_trades} ({metrics.win_rate:.1f}%)")
        print(f"Losing Trades:     {metrics.losing_trades}")
        print(f"\nTotal P&L:         ${metrics.total_pnl:,.2f}")
        print(f"Total Fees:        ${metrics.total_fees:,.2f}")
        print(f"Net P&L:           ${metrics.total_pnl:,.2f}")
        print(f"Volume Traded:     ${metrics.volume_traded:,.2f}")
        print(f"\nAverage Win:       ${metrics.avg_win:,.2f}")
        print(f"Average Loss:      ${metrics.avg_loss:,.2f}")
        print(f"Profit Factor:     {metrics.profit_factor:.2f}")
        print(f"Max Drawdown:      ${metrics.max_drawdown:,.2f}")
        print(f"Sharpe Ratio:      {metrics.sharpe_ratio:.2f}")

        # Strategy breakdown
        print("\n📈 PERFORMANCE BY STRATEGY")
        print("-" * 80)
        print(f"{'Strategy':<20} {'Trades':<10} {'Win Rate':<12} {'P&L':<15} {'Profit Factor':<15}")
        print("-" * 80)

        by_strategy = self.breakdown_by_strategy()
        for strategy, metrics in sorted(by_strategy.items()):
            print(f"{strategy:<20} {metrics.total_trades:<10} "
                  f"{metrics.win_rate:>6.1f}%     "
                  f"${metrics.total_pnl:>10,.2f}   "
                  f"{metrics.profit_factor:>10.2f}")

        # Symbol breakdown
        print("\n🪙 PERFORMANCE BY SYMBOL")
        print("-" * 80)
        print(f"{'Symbol':<20} {'Trades':<10} {'Win Rate':<12} {'P&L':<15} {'Volume':<15}")
        print("-" * 80)

        by_symbol = self.breakdown_by_symbol()
        for symbol, metrics in sorted(by_symbol.items()):
            print(f"{symbol:<20} {metrics.total_trades:<10} "
                  f"{metrics.win_rate:>6.1f}%     "
                  f"${metrics.total_pnl:>10,.2f}   "
                  f"${metrics.volume_traded:>10,.2f}")

        print("=" * 80 + "\n")


async def run_analysis(args):
    """Run trade analysis"""
    analyzer = TradeAnalyzer()

    # Parse dates
    if args.days:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
    else:
        start_date = datetime.fromisoformat(args.start)
        end_date = datetime.fromisoformat(args.end)

    print(f"\nAnalyzing trades from {start_date} to {end_date}...")

    # Load trades
    count = await analyzer.load_trades(start_date, end_date)
    print(f"Loaded {count} trades\n")

    if count > 0:
        # Print report
        analyzer.print_report()

        # Export to CSV if requested
        if args.export:
            analyzer.export_csv(args.export)
            print(f"\nExported to {args.export}")


def main():
    parser = argparse.ArgumentParser(description='SIGMAX Trade Analysis')
    parser.add_argument('--days', type=int, help='Analyze last N days')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--export', type=str, help='Export to CSV file')

    args = parser.parse_args()

    if not args.days and not (args.start and args.end):
        parser.error('Either --days or both --start and --end must be specified')

    asyncio.run(run_analysis(args))


if __name__ == "__main__":
    main()
