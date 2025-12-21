"""
Feed Manager - Manages connections to exchange feeds.

Handles:
- WebSocket connections via CCXT
- Subscription management
- Gap detection and recovery
- Reconnection logic
"""

import asyncio
import ccxt.pro as ccxtpro
from typing import Dict, Set, Optional
from pkg.common import get_logger, get_timestamp_ns, LatencyTracker
from pkg.schemas import MdUpdate


class ExchangeFeed:
    """Single exchange feed handler"""
    
    def __init__(self, exchange_name: str, config, publisher):
        self.exchange_name = exchange_name
        self.config = config
        self.publisher = publisher
        self.logger = get_logger(f"feed.{exchange_name}")
        
        self.exchange: Optional[ccxtpro.Exchange] = None
        self.symbols: Set[str] = set()
        self.running = False
        self.last_seq: Dict[str, int] = {}
        
    async def start(self, symbols: list[str]):
        """Start the exchange feed"""
        self.symbols = set(symbols)
        self.running = True
        
        # Get exchange config
        ex_config = self.config.get_exchange(self.exchange_name)
        if not ex_config:
            self.logger.error("exchange_not_configured", exchange=self.exchange_name)
            return
        
        # Initialize exchange
        exchange_class = getattr(ccxtpro, self.exchange_name)
        self.exchange = exchange_class({
            'apiKey': ex_config.api_key,
            'secret': ex_config.api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        })
        
        if ex_config.testnet:
            self.exchange.set_sandbox_mode(True)
        
        self.logger.info("exchange_feed_started", 
                        exchange=self.exchange_name,
                        symbols=list(self.symbols))
        
        # Start watching ticker for each symbol
        tasks = [self._watch_ticker(symbol) for symbol in self.symbols]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self):
        """Stop the exchange feed"""
        self.running = False
        if self.exchange:
            await self.exchange.close()
        self.logger.info("exchange_feed_stopped", exchange=self.exchange_name)
    
    async def _watch_ticker(self, symbol: str):
        """Watch ticker updates for a symbol"""
        while self.running:
            try:
                ticker = await self.exchange.watch_ticker(symbol)
                await self._process_ticker(symbol, ticker)
            except Exception as e:
                self.logger.error("ticker_error", 
                                symbol=symbol, 
                                error=str(e))
                await asyncio.sleep(1)  # Back off on error
    
    async def _process_ticker(self, symbol: str, ticker: dict):
        """Process ticker update and publish MdUpdate"""
        try:
            latency_tracker = LatencyTracker(f"ticker_{symbol}")
            
            # Extract bid/ask
            bid_px = ticker.get('bid', 0.0)
            bid_sz = ticker.get('bidVolume', 0.0) or 0.0
            ask_px = ticker.get('ask', 0.0)
            ask_sz = ticker.get('askVolume', 0.0) or 0.0
            
            if bid_px == 0.0 or ask_px == 0.0:
                return  # Skip invalid tickers
            
            # Get sequence number (if available)
            seq = ticker.get('info', {}).get('u', 0)
            
            # Check for gaps
            if symbol in self.last_seq and seq > 0:
                expected_seq = self.last_seq[symbol] + 1
                if seq > expected_seq:
                    gap = seq - expected_seq
                    self.logger.warning("sequence_gap_detected",
                                      symbol=symbol,
                                      expected=expected_seq,
                                      received=seq,
                                      gap=gap)

                    # Trigger gap recovery
                    asyncio.create_task(self._recover_gap(symbol, expected_seq, seq))

            if seq > 0:
                self.last_seq[symbol] = seq
            
            # Create MdUpdate
            update = MdUpdate(
                ts_ns=get_timestamp_ns(),
                symbol_id=await self._get_symbol_id(symbol),
                bid_px=bid_px,
                bid_sz=bid_sz,
                ask_px=ask_px,
                ask_sz=ask_sz,
                seq=seq
            )
            
            latency_tracker.checkpoint("created")
            
            # Publish
            await self.publisher.publish(update)
            
            latency_tracker.checkpoint("published")
            
            # Log latency
            parse_latency = latency_tracker.get_latency_us("start", "created")
            total_latency = latency_tracker.get_latency_us()
            
            self.logger.debug("ticker_processed",
                            symbol=symbol,
                            parse_us=parse_latency,
                            total_us=total_latency)
            
        except Exception as e:
            self.logger.error("process_ticker_error",
                            symbol=symbol,
                            error=str(e),
                            exc_info=True)
    
    async def _recover_gap(self, symbol: str, start_seq: int, end_seq: int):
        """
        Recover missing market data from gap

        Strategies:
        1. Request snapshot from exchange (if supported)
        2. Fetch historical trades/orderbook updates
        3. Reconnect if gap is too large (>100 messages)

        Args:
            symbol: Trading symbol
            start_seq: Expected sequence number
            end_seq: Received sequence number (with gap)
        """
        try:
            gap_size = end_seq - start_seq

            self.logger.info("gap_recovery_started",
                           symbol=symbol,
                           gap_size=gap_size,
                           start_seq=start_seq,
                           end_seq=end_seq)

            # Strategy 1: If gap is small (<10), log and continue
            if gap_size < 10:
                self.logger.info("small_gap_ignored", symbol=symbol, gap_size=gap_size)
                return

            # Strategy 2: If gap is medium (10-100), try to fetch missed updates
            if gap_size < 100:
                await self._fetch_historical_orderbook(symbol)
                self.logger.info("gap_recovered_via_snapshot", symbol=symbol)
                return

            # Strategy 3: If gap is large (>100), reconnect to get fresh stream
            self.logger.warning("large_gap_detected_reconnecting",
                              symbol=symbol,
                              gap_size=gap_size)

            # Reconnect (will restart stream with fresh data)
            await self._reconnect_symbol(symbol)

        except Exception as e:
            self.logger.error("gap_recovery_failed",
                            symbol=symbol,
                            error=str(e),
                            exc_info=True)

    async def _fetch_historical_orderbook(self, symbol: str):
        """
        Fetch recent orderbook snapshot to fill gap

        This helps recover from small gaps by getting current orderbook state.
        """
        try:
            if not self.exchange:
                return

            # Fetch orderbook snapshot
            orderbook = await self.exchange.fetch_order_book(symbol, limit=20)

            # Get best bid/ask
            if orderbook.get('bids') and orderbook.get('asks'):
                best_bid = orderbook['bids'][0]
                best_ask = orderbook['asks'][0]

                # Create update with snapshot data
                update = MdUpdate(
                    ts_ns=get_timestamp_ns(),
                    symbol_id=await self._get_symbol_id(symbol),
                    bid_px=best_bid[0],
                    bid_sz=best_bid[1],
                    ask_px=best_ask[0],
                    ask_sz=best_ask[1],
                    seq=0  # Snapshot, no sequence
                )

                # Publish snapshot
                await self.publisher.publish(update)

                self.logger.debug("snapshot_fetched", symbol=symbol)

        except Exception as e:
            self.logger.warning("snapshot_fetch_failed",
                              symbol=symbol,
                              error=str(e))

    async def _reconnect_symbol(self, symbol: str):
        """
        Reconnect to exchange feed for a symbol

        Used for recovery from large gaps. Closes current connection
        and re-establishes fresh stream.
        """
        try:
            self.logger.info("reconnecting_symbol", symbol=symbol)

            # Close and reopen exchange connection
            if self.exchange:
                await self.exchange.close()

            # Reinitialize exchange
            ex_config = self.config.get_exchange(self.exchange_name)
            exchange_class = getattr(ccxtpro, self.exchange_name)
            self.exchange = exchange_class({
                'apiKey': ex_config.api_key,
                'secret': ex_config.api_secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })

            if ex_config.testnet:
                self.exchange.set_sandbox_mode(True)

            # Reset sequence tracking
            if symbol in self.last_seq:
                del self.last_seq[symbol]

            self.logger.info("symbol_reconnected", symbol=symbol)

        except Exception as e:
            self.logger.error("reconnect_failed",
                            symbol=symbol,
                            error=str(e),
                            exc_info=True)

    async def _get_symbol_id(self, symbol: str) -> int:
        """
        Get symbol ID from cache or database

        Uses in-memory cache with database fallback.
        """
        # Check cache
        if not hasattr(self, '_symbol_cache'):
            self._symbol_cache = {}
            self._symbol_id_counter = 1000

        if symbol in self._symbol_cache:
            return self._symbol_cache[symbol]

        # Try database lookup (run in executor to avoid blocking)
        symbol_id = await asyncio.to_thread(self._lookup_symbol_from_db, symbol)

        if symbol_id is None:
            # Fallback to static mapping
            static_map = {
                "BTC/USDT": 1,
                "ETH/USDT": 2,
                "SOL/USDT": 3,
                "BNB/USDT": 4,
                "XRP/USDT": 5,
                "ADA/USDT": 6,
                "DOT/USDT": 7,
                "MATIC/USDT": 8,
                "AVAX/USDT": 9,
                "LINK/USDT": 10,
            }

            symbol_id = static_map.get(symbol)

            if symbol_id is None:
                # Assign new ID
                symbol_id = self._symbol_id_counter
                self._symbol_id_counter += 1
                self.logger.info("assigned_new_symbol_id", symbol=symbol, symbol_id=symbol_id)

        # Cache result
        self._symbol_cache[symbol] = symbol_id
        return symbol_id

    def _lookup_symbol_from_db(self, symbol: str) -> Optional[int]:
        """
        Lookup symbol ID from database

        Returns:
            Symbol ID if found, None otherwise
        """
        try:
            import os
            db_url = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL')

            if not db_url:
                return None

            import psycopg2

            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id FROM symbols WHERE name = %s LIMIT 1",
                (symbol,)
            )

            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                return result[0]

            return None

        except ImportError:
            return None
        except Exception as e:
            self.logger.debug("db_lookup_error", symbol=symbol, error=str(e))
            return None


class FeedManager:
    """Manages all exchange feeds"""
    
    def __init__(self, config, publisher):
        self.config = config
        self.publisher = publisher
        self.logger = get_logger(__name__)
        
        self.feeds: Dict[str, ExchangeFeed] = {}
        
    async def start(self):
        """Start all configured exchange feeds"""
        # Create feed for each configured exchange
        for exchange_name in self.config.exchanges.keys():
            feed = ExchangeFeed(exchange_name, self.config, self.publisher)
            self.feeds[exchange_name] = feed
        
        # Start all feeds
        tasks = []
        for feed in self.feeds.values():
            task = feed.start(self.config.symbols)
            tasks.append(task)
        
        # Run feeds concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self):
        """Stop all feeds"""
        tasks = [feed.stop() for feed in self.feeds.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        self.logger.info("all_feeds_stopped")
