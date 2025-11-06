"""
Execution Module - Trade Execution via Freqtrade/CCXT
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
import os


class ExecutionModule:
    """
    Execution Module - Handles trade execution

    Modes:
    - paper: Simulated trading
    - live: Real trading via exchange API
    """

    def __init__(self, mode: str = "paper"):
        self.mode = mode
        self.exchange = None
        self.paper_balance = {
            "USDT": float(os.getenv("TOTAL_CAPITAL", 50)),
            "BTC": 0.0,
            "ETH": 0.0
        }
        self.open_orders = []
        self.trade_history = []

        # Risk limits
        self.max_position_size = float(os.getenv("MAX_POSITION_SIZE", 15))
        self.max_daily_loss = float(os.getenv("MAX_DAILY_LOSS", 10))
        self.stop_loss_pct = float(os.getenv("STOP_LOSS_PCT", 1.5))

        logger.info(f"✓ Execution module created in {mode} mode")

    async def initialize(self):
        """Initialize execution engine"""
        if self.mode == "live":
            try:
                import ccxt.async_support as ccxt

                exchange_name = os.getenv("EXCHANGE", "binance")
                self.exchange = getattr(ccxt, exchange_name)({
                    'apiKey': os.getenv("API_KEY"),
                    'secret': os.getenv("API_SECRET"),
                    'enableRateLimit': True
                })

                await self.exchange.load_markets()
                logger.info(f"✓ Live execution initialized with {exchange_name}")

            except Exception as e:
                logger.error(f"Failed to initialize live trading: {e}")
                self.mode = "paper"
                logger.warning("Falling back to paper trading")

        logger.info(f"✓ Execution module initialized ({self.mode})")

    async def execute_trade(
        self,
        symbol: str,
        action: str,
        size: float,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute a trade

        Args:
            symbol: Trading pair
            action: 'buy' or 'sell'
            size: Position size (in base currency)
            price: Limit price (None for market order)

        Returns:
            Trade result
        """
        logger.info(f"Executing {action} {size} {symbol} @ {price or 'market'}")

        # Validate trade
        if not await self._validate_trade(symbol, action, size):
            return {
                "success": False,
                "error": "Trade validation failed"
            }

        try:
            if self.mode == "paper":
                result = await self._execute_paper_trade(symbol, action, size, price)
            else:
                result = await self._execute_live_trade(symbol, action, size, price)

            # Record trade
            self.trade_history.append({
                "symbol": symbol,
                "action": action,
                "size": size,
                "price": result.get("price"),
                "timestamp": datetime.now().isoformat(),
                "mode": self.mode
            })

            return result

        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _validate_trade(
        self,
        symbol: str,
        action: str,
        size: float
    ) -> bool:
        """Validate trade against risk limits"""

        # Check position size
        if size > self.max_position_size:
            logger.warning(f"Position size {size} exceeds limit {self.max_position_size}")
            return False

        # Check daily loss limit
        daily_pnl = await self._calculate_daily_pnl()
        if daily_pnl < -self.max_daily_loss:
            logger.warning(
                f"Daily loss ${abs(daily_pnl):.2f} exceeds limit ${self.max_daily_loss}. "
                f"Trade blocked."
            )
            return False

        # Check if we're approaching the limit with this trade
        # Assume worst case: full stop loss on this trade
        potential_loss = size * self.stop_loss_pct / 100
        if (daily_pnl - potential_loss) < -self.max_daily_loss:
            logger.warning(
                f"Trade could push daily loss to ${abs(daily_pnl - potential_loss):.2f}, "
                f"exceeding limit ${self.max_daily_loss}"
            )
            return False

        return True

    async def _calculate_daily_pnl(self) -> float:
        """Calculate profit/loss for current day"""
        from datetime import datetime, timedelta

        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Filter trades from today
        today_trades = [
            t for t in self.trade_history
            if datetime.fromisoformat(t['timestamp']) >= today_start
        ]

        # Calculate PnL (simplified - in production, track entry/exit pairs)
        pnl = 0.0
        for trade in today_trades:
            # This is simplified; real implementation needs matched pairs
            if trade.get('pnl'):
                pnl += trade['pnl']

        return pnl

    async def _execute_paper_trade(
        self,
        symbol: str,
        action: str,
        size: float,
        price: Optional[float]
    ) -> Dict[str, Any]:
        """Execute paper trade"""
        from core.testing.fixtures import MockMarketData

        # Use mock price if not provided
        if not price:
            price = MockMarketData.get_price(symbol)

        base, quote = symbol.split("/")

        if action == "buy":
            cost = size * price
            if self.paper_balance.get(quote, 0) >= cost:
                self.paper_balance[quote] -= cost
                self.paper_balance[base] = self.paper_balance.get(base, 0) + size

                logger.info(f"Paper trade: Bought {size} {base} for {cost} {quote}")
                return {
                    "success": True,
                    "action": "buy",
                    "symbol": symbol,
                    "size": size,
                    "price": price,
                    "cost": cost
                }
            else:
                return {
                    "success": False,
                    "error": "Insufficient balance"
                }

        elif action == "sell":
            if self.paper_balance.get(base, 0) >= size:
                self.paper_balance[base] -= size
                proceeds = size * price
                self.paper_balance[quote] = self.paper_balance.get(quote, 0) + proceeds

                logger.info(f"Paper trade: Sold {size} {base} for {proceeds} {quote}")
                return {
                    "success": True,
                    "action": "sell",
                    "symbol": symbol,
                    "size": size,
                    "price": price,
                    "proceeds": proceeds
                }
            else:
                return {
                    "success": False,
                    "error": "Insufficient balance"
                }

        return {"success": False, "error": "Invalid action"}

    async def _execute_live_trade(
        self,
        symbol: str,
        action: str,
        size: float,
        price: Optional[float]
    ) -> Dict[str, Any]:
        """Execute live trade"""
        if not self.exchange:
            return {"success": False, "error": "Exchange not initialized"}

        try:
            order_type = "limit" if price else "market"
            side = "buy" if action == "buy" else "sell"

            order = await self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=size,
                price=price
            )

            return {
                "success": True,
                "order_id": order['id'],
                "action": action,
                "symbol": symbol,
                "size": size,
                "price": order.get('price'),
                "status": order.get('status')
            }

        except Exception as e:
            logger.error(f"Live trade error: {e}")
            return {"success": False, "error": str(e)}

    async def close_all_positions(self):
        """Emergency close all positions"""
        logger.warning("🚨 Closing all positions!")

        closed_positions = []
        errors = []

        try:
            if self.mode == "live" and self.exchange:
                # Fetch all open positions
                positions = await self.exchange.fetch_positions()

                for position in positions:
                    if position['contracts'] > 0:
                        symbol = position['symbol']
                        size = position['contracts']
                        side = 'sell' if position['side'] == 'long' else 'buy'

                        try:
                            result = await self.exchange.create_order(
                                symbol=symbol,
                                type='market',
                                side=side,
                                amount=size
                            )
                            closed_positions.append(result)
                            logger.info(f"✓ Closed {symbol}: {size} @ market")
                        except Exception as e:
                            error_msg = f"Failed to close {symbol}: {e}"
                            logger.error(error_msg)
                            errors.append(error_msg)

            elif self.mode == "paper":
                # Close paper positions by selling all holdings
                for asset, balance in list(self.paper_balance.items()):
                    if asset != "USDT" and balance > 0:
                        # Market sell everything
                        symbol = f"{asset}/USDT"
                        result = await self._execute_paper_trade(symbol, "sell", balance, None)
                        closed_positions.append(result)
                        logger.info(f"✓ Paper closed: {symbol}")

            self.open_orders = []

            if errors:
                raise Exception(f"Closed {len(closed_positions)} positions with {len(errors)} errors: {errors}")

            logger.info(f"✓ Emergency close completed: {len(closed_positions)} positions closed")
            return {
                "success": True,
                "closed_count": len(closed_positions),
                "positions": closed_positions
            }

        except Exception as e:
            logger.error(f"Emergency close error: {e}")
            return {
                "success": False,
                "error": str(e),
                "closed_count": len(closed_positions),
                "failed_count": len(errors)
            }

    async def get_status(self) -> Dict[str, Any]:
        """Get execution module status"""
        return {
            "mode": self.mode,
            "balance": self.paper_balance if self.mode == "paper" else {},
            "open_orders": len(self.open_orders),
            "trade_count": len(self.trade_history)
        }
