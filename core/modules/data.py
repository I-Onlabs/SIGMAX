"""
Data Module - Market Data Fetching & Management
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
from loguru import logger
import os


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
        self.cache = {}
        self.cache_ttl = 60  # seconds

        logger.info("✓ Data module created")

    async def initialize(self):
        """Initialize data sources"""
        try:
            import ccxt.async_support as ccxt

            exchange_name = os.getenv("EXCHANGE", "binance").lower()
            testnet = os.getenv("TESTNET", "true").lower() == "true"

            if exchange_name == "binance":
                self.exchange = ccxt.binance({
                    'apiKey': os.getenv("API_KEY"),
                    'secret': os.getenv("API_SECRET"),
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'future' if testnet else 'spot',
                        'test': testnet
                    }
                })
            else:
                # Generic exchange
                exchange_class = getattr(ccxt, exchange_name)
                self.exchange = exchange_class({
                    'apiKey': os.getenv("API_KEY"),
                    'secret': os.getenv("API_SECRET"),
                    'enableRateLimit': True
                })

            # Load markets
            await self.exchange.load_markets()

            logger.info(f"✓ Data module initialized with {exchange_name}")

        except Exception as e:
            logger.warning(f"Could not initialize CCXT: {e}. Using mock data.")
            self.exchange = None

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
        cache_key = f"{symbol}_{timeframe}"

        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < self.cache_ttl:
                return cached_data

        try:
            if self.exchange:
                # Fetch real data
                ticker = await self.exchange.fetch_ticker(symbol)
                ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                orderbook = await self.exchange.fetch_order_book(symbol, limit=20)

                data = {
                    "symbol": symbol,
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
                data = self._generate_mock_data(symbol)

            # Cache it
            self.cache[cache_key] = (data, datetime.now())

            return data

        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return self._generate_mock_data(symbol)

    def _generate_mock_data(self, symbol: str) -> Dict[str, Any]:
        """Generate mock market data for testing"""
        import random

        base_prices = {
            "BTC/USDT": 95000,
            "ETH/USDT": 3500,
            "SOL/USDT": 180
        }

        base_price = base_prices.get(symbol, 100)
        price = base_price * (1 + random.uniform(-0.02, 0.02))

        return {
            "symbol": symbol,
            "price": price,
            "volume_24h": random.uniform(1e8, 1e9),
            "change_24h": random.uniform(-5, 5),
            "high_24h": price * 1.03,
            "low_24h": price * 0.97,
            "bid": price * 0.999,
            "ask": price * 1.001,
            "spread": price * 0.002,
            "ohlcv": [],
            "orderbook": {"bids": [], "asks": []},
            "timestamp": datetime.now().isoformat()
        }

    async def get_historical_data(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: str = "1h"
    ) -> List[List[float]]:
        """Get historical OHLCV data"""
        if not self.exchange:
            return []

        try:
            since = int(start.timestamp() * 1000)
            all_ohlcv = []

            while since < int(end.timestamp() * 1000):
                ohlcv = await self.exchange.fetch_ohlcv(
                    symbol,
                    timeframe,
                    since=since,
                    limit=1000
                )

                if not ohlcv:
                    break

                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + 1

                await asyncio.sleep(self.exchange.rateLimit / 1000)

            return all_ohlcv

        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return []

    async def close(self):
        """Close connections"""
        if self.exchange:
            await self.exchange.close()
