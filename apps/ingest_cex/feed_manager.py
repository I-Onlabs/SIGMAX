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
                    # TODO: Trigger gap recovery
            
            if seq > 0:
                self.last_seq[symbol] = seq
            
            # Create MdUpdate
            update = MdUpdate(
                ts_ns=get_timestamp_ns(),
                symbol_id=self._get_symbol_id(symbol),
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
    
    def _get_symbol_id(self, symbol: str) -> int:
        """Get symbol ID (simplified for now)"""
        # TODO: Lookup from database
        symbol_map = {
            "BTC/USDT": 1,
            "ETH/USDT": 2,
            "SOL/USDT": 3,
            "BNB/USDT": 4,
            "XRP/USDT": 5,
        }
        return symbol_map.get(symbol, 0)


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
