"""
Arbitrage Module - Multi-chain DEX/CEX Scanner
"""

from typing import Dict, Any, List, Optional
from loguru import logger
import asyncio
import ccxt.async_support as ccxt
from datetime import datetime


class ArbitrageModule:
    """
    Arbitrage Module - Scans for arbitrage opportunities

    Sources:
    - CEX: Binance, Coinbase, Kraken
    - DEX: Uniswap, Sushiswap, PancakeSwap
    - Cross-chain: Across chains
    """

    def __init__(self, min_profit_percentage: float = 0.5):
        self.opportunities = []
        self.min_profit_percentage = min_profit_percentage
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.supported_exchanges = ['binance', 'coinbase', 'kraken']
        self.trading_pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
        logger.info("✓ Arbitrage module created")

    async def initialize(self):
        """Initialize arbitrage scanner with exchange connections"""
        logger.info("Initializing arbitrage scanner...")

        # Initialize exchange connections (testnet/sandbox where available)
        for exchange_id in self.supported_exchanges:
            try:
                exchange_class = getattr(ccxt, exchange_id)
                exchange = exchange_class({
                    'enableRateLimit': True,
                    'timeout': 30000,
                })

                # Load markets
                await exchange.load_markets()
                self.exchanges[exchange_id] = exchange
                logger.info(f"✓ Connected to {exchange_id}")

            except Exception as e:
                logger.warning(f"Failed to connect to {exchange_id}: {e}")

        logger.info(f"✓ Arbitrage module initialized with {len(self.exchanges)} exchanges")

    async def scan_opportunities(self) -> List[Dict[str, Any]]:
        """
        Scan for arbitrage opportunities across multiple exchanges

        Returns:
            List of arbitrage opportunities with:
            - symbol: Trading pair
            - buy_exchange: Where to buy
            - sell_exchange: Where to sell
            - buy_price: Buy price
            - sell_price: Sell price
            - profit_percentage: Expected profit %
            - timestamp: When opportunity was detected
        """
        if len(self.exchanges) < 2:
            logger.warning("Need at least 2 exchanges for arbitrage scanning")
            return []

        opportunities = []

        for symbol in self.trading_pairs:
            try:
                # Fetch prices from all exchanges concurrently
                price_tasks = []
                exchange_names = []

                for exchange_name, exchange in self.exchanges.items():
                    if symbol in exchange.symbols:
                        price_tasks.append(self._fetch_ticker(exchange, symbol))
                        exchange_names.append(exchange_name)

                if len(price_tasks) < 2:
                    continue

                # Get all prices
                prices = await asyncio.gather(*price_tasks, return_exceptions=True)

                # Build price map
                price_map = {}
                for i, price_result in enumerate(prices):
                    if isinstance(price_result, Exception):
                        logger.debug(f"Failed to fetch {symbol} from {exchange_names[i]}: {price_result}")
                        continue
                    if price_result:
                        price_map[exchange_names[i]] = price_result

                # Find arbitrage opportunities
                if len(price_map) >= 2:
                    opportunity = self._find_best_arbitrage(symbol, price_map)
                    if opportunity:
                        opportunities.append(opportunity)
                        logger.info(f"🎯 Arbitrage opportunity: {opportunity['symbol']} - "
                                  f"Buy {opportunity['buy_exchange']} @ ${opportunity['buy_price']:.2f}, "
                                  f"Sell {opportunity['sell_exchange']} @ ${opportunity['sell_price']:.2f} "
                                  f"({opportunity['profit_percentage']:.2f}% profit)")

            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")

        self.opportunities = opportunities
        return opportunities

    async def _fetch_ticker(self, exchange: ccxt.Exchange, symbol: str) -> Optional[Dict[str, float]]:
        """Fetch ticker data from an exchange"""
        try:
            ticker = await exchange.fetch_ticker(symbol)
            return {
                'bid': ticker['bid'],  # Best bid (buy) price
                'ask': ticker['ask'],  # Best ask (sell) price
                'last': ticker['last'],  # Last traded price
            }
        except Exception as e:
            logger.debug(f"Failed to fetch ticker for {symbol} from {exchange.id}: {e}")
            return None

    def _find_best_arbitrage(self, symbol: str, price_map: Dict[str, Dict[str, float]]) -> Optional[Dict[str, Any]]:
        """
        Find the best arbitrage opportunity for a given symbol

        Strategy: Buy at lowest ask price, sell at highest bid price
        """
        best_opportunity = None
        max_profit_pct = 0

        exchange_list = list(price_map.items())

        # Compare all exchange pairs
        for i, (buy_exchange, buy_prices) in enumerate(exchange_list):
            for sell_exchange, sell_prices in exchange_list[i+1:]:
                # Calculate profit for both directions

                # Direction 1: Buy from buy_exchange, sell to sell_exchange
                profit_pct_1 = self._calculate_profit_percentage(
                    buy_price=buy_prices['ask'],
                    sell_price=sell_prices['bid'],
                    buy_exchange=buy_exchange,
                    sell_exchange=sell_exchange
                )

                if profit_pct_1 > max_profit_pct and profit_pct_1 >= self.min_profit_percentage:
                    max_profit_pct = profit_pct_1
                    best_opportunity = {
                        'symbol': symbol,
                        'buy_exchange': buy_exchange,
                        'sell_exchange': sell_exchange,
                        'buy_price': buy_prices['ask'],
                        'sell_price': sell_prices['bid'],
                        'profit_percentage': profit_pct_1,
                        'timestamp': datetime.utcnow().isoformat(),
                        'status': 'detected'
                    }

                # Direction 2: Buy from sell_exchange, sell to buy_exchange
                profit_pct_2 = self._calculate_profit_percentage(
                    buy_price=sell_prices['ask'],
                    sell_price=buy_prices['bid'],
                    buy_exchange=sell_exchange,
                    sell_exchange=buy_exchange
                )

                if profit_pct_2 > max_profit_pct and profit_pct_2 >= self.min_profit_percentage:
                    max_profit_pct = profit_pct_2
                    best_opportunity = {
                        'symbol': symbol,
                        'buy_exchange': sell_exchange,
                        'sell_exchange': buy_exchange,
                        'buy_price': sell_prices['ask'],
                        'sell_price': buy_prices['bid'],
                        'profit_percentage': profit_pct_2,
                        'timestamp': datetime.utcnow().isoformat(),
                        'status': 'detected'
                    }

        return best_opportunity

    def _calculate_profit_percentage(self, buy_price: float, sell_price: float,
                                     buy_exchange: str, sell_exchange: str) -> float:
        """
        Calculate profit percentage after fees

        Assumptions:
        - Trading fee: 0.1% per trade (typical for most exchanges)
        - Withdrawal fee: 0.05% (network fees)
        """
        trading_fee = 0.001  # 0.1% per trade
        withdrawal_fee = 0.0005  # 0.05%

        # Total cost including fees
        buy_cost = buy_price * (1 + trading_fee)

        # Revenue after fees
        sell_revenue = sell_price * (1 - trading_fee - withdrawal_fee)

        # Profit percentage
        profit_pct = ((sell_revenue - buy_cost) / buy_cost) * 100

        return profit_pct

    async def execute_arbitrage(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute arbitrage trade (atomic or near-atomic)

        Strategy:
        1. Pre-validate balances and prices
        2. Execute buy order
        3. Wait for confirmation
        4. Execute sell order
        5. Verify completion

        Returns:
            Execution result with status and details
        """
        logger.info(f"🚀 Executing arbitrage: {opportunity}")

        try:
            buy_exchange_id = opportunity['buy_exchange']
            sell_exchange_id = opportunity['sell_exchange']
            symbol = opportunity['symbol']

            buy_exchange = self.exchanges.get(buy_exchange_id)
            sell_exchange = self.exchanges.get(sell_exchange_id)

            if not buy_exchange or not sell_exchange:
                return {
                    'status': 'failed',
                    'reason': 'Exchange not available',
                    'opportunity': opportunity
                }

            # Step 1: Validate current prices are still profitable
            current_prices = await asyncio.gather(
                self._fetch_ticker(buy_exchange, symbol),
                self._fetch_ticker(sell_exchange, symbol)
            )

            current_buy_price = current_prices[0]['ask'] if current_prices[0] else None
            current_sell_price = current_prices[1]['bid'] if current_prices[1] else None

            if not current_buy_price or not current_sell_price:
                return {
                    'status': 'failed',
                    'reason': 'Could not fetch current prices',
                    'opportunity': opportunity
                }

            # Recalculate profit with current prices
            current_profit_pct = self._calculate_profit_percentage(
                current_buy_price, current_sell_price,
                buy_exchange_id, sell_exchange_id
            )

            if current_profit_pct < self.min_profit_percentage:
                logger.warning(f"Opportunity expired: profit dropped to {current_profit_pct:.2f}%")
                return {
                    'status': 'expired',
                    'reason': f'Profit dropped to {current_profit_pct:.2f}%',
                    'opportunity': opportunity
                }

            # Step 2-5: Execute trades (PAPER TRADING MODE - NO ACTUAL ORDERS)
            logger.info("📝 PAPER TRADE: Would execute the following:")
            logger.info(f"   BUY {symbol} on {buy_exchange_id} @ ${current_buy_price:.2f}")
            logger.info(f"   SELL {symbol} on {sell_exchange_id} @ ${current_sell_price:.2f}")
            logger.info(f"   Expected profit: {current_profit_pct:.2f}%")

            # Simulate execution result
            result = {
                'status': 'simulated',
                'opportunity': opportunity,
                'execution': {
                    'buy_order': {
                        'exchange': buy_exchange_id,
                        'symbol': symbol,
                        'price': current_buy_price,
                        'status': 'simulated'
                    },
                    'sell_order': {
                        'exchange': sell_exchange_id,
                        'symbol': symbol,
                        'price': current_sell_price,
                        'status': 'simulated'
                    },
                    'profit_percentage': current_profit_pct,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }

            logger.info(f"✅ Arbitrage simulation completed: {current_profit_pct:.2f}% profit")
            return result

        except Exception as e:
            logger.error(f"Arbitrage execution error: {e}")
            return {
                'status': 'error',
                'reason': str(e),
                'opportunity': opportunity
            }

    async def close(self):
        """Close all exchange connections"""
        for exchange_id, exchange in self.exchanges.items():
            try:
                await exchange.close()
                logger.debug(f"Closed connection to {exchange_id}")
            except Exception as e:
                logger.warning(f"Error closing {exchange_id}: {e}")
