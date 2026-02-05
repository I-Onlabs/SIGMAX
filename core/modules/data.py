"""
Data Module - Market Data Fetching & Management
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import asyncio
from loguru import logger
import os
from .chain_data import ChainDataModule


class DataModule:
    """
    Data Module - Fetches and manages market data from multiple sources

    Sources:
    - CCXT (CEX data)
    - Blockchain RPC (DEX data)
    - News APIs
    - Social media APIs
    """

    def __init__(self):
        self.exchange = None
        self.exchanges: Dict[str, Any] = {}
        self.chain_module: Optional[ChainDataModule] = None
        self.cache = {}
        self.cache_ttl = 60  # seconds
        self._cache_cleanup_task = None

        logger.info("✓ Data module created")

    async def initialize(self):
        """Initialize data sources"""
        try:
            import ccxt.async_support as ccxt

            exchange_name = os.getenv("EXCHANGE", "binance").lower()
            exchange_list = [
                name.strip().lower()
                for name in os.getenv("EXCHANGES", "").split(",")
                if name.strip()
            ]
            testnet = os.getenv("TESTNET", "true").lower() == "true"
            chains = [
                name.strip().lower()
                for name in os.getenv("CHAINS", "").split(",")
                if name.strip()
            ]

            async def create_exchange(name: str):
                if name == "binance":
                    return ccxt.binance({
                        'apiKey': os.getenv("API_KEY"),
                        'secret': os.getenv("API_SECRET"),
                        'enableRateLimit': True,
                        'options': {
                            'defaultType': 'future' if testnet else 'spot',
                            'test': testnet
                        }
                    })
                exchange_class = getattr(ccxt, name)
                return exchange_class({
                    'apiKey': os.getenv("API_KEY"),
                    'secret': os.getenv("API_SECRET"),
                    'enableRateLimit': True
                })

            if exchange_list:
                for name in exchange_list:
                    try:
                        ex = await create_exchange(name)
                        await ex.load_markets()
                        self.exchanges[name] = ex
                        logger.info(f"✓ Data exchange initialized: {name}")
                    except Exception as e:
                        logger.warning(f"Failed to initialize exchange {name}: {e}")

                self.exchange = self.exchanges.get(exchange_name) or next(
                    iter(self.exchanges.values()), None
                )
                if self.exchange:
                    logger.info(f"✓ Data module initialized with {len(self.exchanges)} exchanges")
                else:
                    logger.warning("No exchanges available after initialization")
            else:
                self.exchange = await create_exchange(exchange_name)
                await self.exchange.load_markets()
                logger.info(f"✓ Data module initialized with {exchange_name}")

            if chains:
                self.chain_module = ChainDataModule(chains=chains)
                await self.chain_module.initialize()
                logger.info(f"✓ Chain data module initialized with {len(chains)} chains")

        except Exception as e:
            logger.warning(f"Could not initialize CCXT: {e}. Using mock data.")
            self.exchange = None

        # Start cache cleanup task
        self._cache_cleanup_task = asyncio.create_task(self._cleanup_cache_loop())
        logger.debug("✓ Cache cleanup task started")

    async def get_market_data(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get comprehensive market data for a symbol

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe
            limit: Number of candles

        Returns:
            Market data dictionary
        """
        exchange, normalized_symbol, exchange_id = self._select_exchange(symbol)
        cache_key = f"{exchange_id or 'default'}:{normalized_symbol}_{timeframe}"

        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < self.cache_ttl:
                return cached_data

        try:
            if exchange:
                # Fetch real data
                ticker = await exchange.fetch_ticker(normalized_symbol)
                ohlcv = await exchange.fetch_ohlcv(normalized_symbol, timeframe, limit=limit)
                orderbook = await exchange.fetch_order_book(normalized_symbol, limit=20)

                data = {
                    "symbol": normalized_symbol,
                    "exchange": exchange_id,
                    "price": ticker['last'],
                    "volume_24h": ticker['quoteVolume'],
                    "change_24h": ticker['percentage'],
                    "high_24h": ticker['high'],
                    "low_24h": ticker['low'],
                    "bid": ticker['bid'],
                    "ask": ticker['ask'],
                    "spread": ticker['ask'] - ticker['bid'] if ticker['ask'] and ticker['bid'] else 0,
                    "ohlcv": ohlcv,
                    "orderbook": orderbook,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Mock data
                data = self._generate_mock_data(normalized_symbol)

            if self.chain_module:
                try:
                    data["onchain"] = await self.chain_module.get_onchain_snapshot()
                except Exception as e:
                    logger.warning(f"Failed to fetch onchain snapshot: {e}")

            # Cache it
            self.cache[cache_key] = (data, datetime.now())

            return data

        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return self._generate_mock_data(normalized_symbol)

    def _generate_mock_data(self, symbol: str) -> Dict[str, Any]:
        """Generate mock market data for testing"""
        from core.testing.fixtures import MockMarketData

        return MockMarketData.generate_market_data_dict(symbol)

    async def get_historical_data(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: str = "1h"
    ) -> List[List[float]]:
        """Get historical OHLCV data"""
        exchange, normalized_symbol, _ = self._select_exchange(symbol)
        if not exchange:
            return []

        try:
            since = int(start.timestamp() * 1000)
            all_ohlcv = []

            while since < int(end.timestamp() * 1000):
                ohlcv = await exchange.fetch_ohlcv(
                    normalized_symbol,
                    timeframe,
                    since=since,
                    limit=1000
                )

                if not ohlcv:
                    break

                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + 1

                await asyncio.sleep(exchange.rateLimit / 1000)

            return all_ohlcv

        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return []

    async def _cleanup_cache_loop(self):
        """Periodic cache cleanup to prevent memory leaks"""
        try:
            while True:
                await asyncio.sleep(60)  # Run every minute

                now = datetime.now()
                expired_keys = [
                    key for key, (_, timestamp) in self.cache.items()
                    if (now - timestamp).total_seconds() > self.cache_ttl
                ]

                for key in expired_keys:
                    del self.cache[key]

                if expired_keys:
                    logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")
        except asyncio.CancelledError:
            logger.debug("Cache cleanup task cancelled")
        except Exception as e:
            logger.error(f"Error in cache cleanup: {e}")

    async def close(self):
        """Close connections"""
        # Cancel cleanup task
        if self._cache_cleanup_task:
            self._cache_cleanup_task.cancel()
            try:
                await self._cache_cleanup_task
            except asyncio.CancelledError:
                pass

        # Close exchanges
        for exchange in self.exchanges.values():
            await exchange.close()
        if self.exchange and not self.exchanges:
            await self.exchange.close()

        logger.info("✓ Data module closed")

    def _select_exchange(self, symbol: str) -> Tuple[Optional[Any], str, Optional[str]]:
        """
        Resolve exchange based on symbol prefix or default exchange.

        Supports 'exchange:symbol' format when multiple exchanges are configured.
        """
        if ":" in symbol:
            exchange_id, normalized_symbol = symbol.split(":", 1)
            exchange_id = exchange_id.lower()
            exchange = self.exchanges.get(exchange_id)
            if exchange:
                return exchange, normalized_symbol, exchange_id
            logger.warning(
                f"Exchange prefix '{exchange_id}' not configured; falling back to default exchange."
            )
            symbol = normalized_symbol

        exchange_id = None
        if self.exchange:
            exchange_id = getattr(self.exchange, "id", None)
        return self.exchange, symbol, exchange_id
