"""
Listings Watcher

Monitors exchanges for new coin listings and trading pairs.
Publishes LISTING signal events.
"""

import asyncio
import sys
import signal as signal_module
import time
import zlib
from pathlib import Path
from typing import Optional, Dict

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from pkg.common import setup_logging, get_logger, load_config, get_metrics_collector
from pkg.schemas import SignalEvent, SignalType
from pkg.schemas.signals import ListingMetaCode
from apps.signals.common import SignalPublisher
import ccxt.async_support as ccxt


class ListingsWatcher:
    """Listings watcher signal module"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("listings_watcher")
        
        # Publisher
        self.publisher = SignalPublisher(config, "listings_watcher")
        
        # Track known symbols
        self.known_symbols = set()
        
        # Track initialized exchanges to prevent false positives
        self.initialized_exchanges = set()

        self.running = False
        
        # Cache for symbol IDs
        self._symbol_cache: Dict[str, int] = {}
        self._symbol_id_counter = 1000

    async def start(self):
        """Start the watcher"""
        self.logger.info("starting_listings_watcher")
        
        self.metrics.set_info(
            service="listings_watcher",
            status="active"
        )
        
        # Start publisher
        await self.publisher.start()
        
        self.running = True
        
        # Start polling loop
        asyncio.create_task(self._poll_loop())
        
        self.logger.info("listings_watcher_started")
        
    async def stop(self):
        """Stop the watcher"""
        self.logger.info("stopping_listings_watcher")
        self.running = False
        
        await self.publisher.stop()
        
        self.logger.info("listings_watcher_stopped")
    
    async def _poll_loop(self):
        """Poll for new listings from exchanges"""
        self.logger.info("poll_loop_started")

        # Configure exchanges to monitor
        exchanges_config = {
            'binance': ccxt.binance({'enableRateLimit': True}),
            'coinbase': ccxt.coinbase({'enableRateLimit': True}),
        }

        # Initial fetch to populate known symbols
        await self._initialize_symbols(exchanges_config)

        while self.running:
            try:
                # Poll each exchange for new markets
                for exchange_name, exchange in exchanges_config.items():
                    # Skip uninitialized exchanges to avoid false positives
                    if exchange_name not in self.initialized_exchanges:
                        await self._try_initialize_exchange(exchange_name, exchange)
                        continue

                    try:
                        markets = await exchange.fetch_markets()
                        current_symbols = {m['symbol'] for m in markets if m.get('active', False)}

                        # Detect new listings
                        # Only check against known symbols if we have some knowledge (which we should if initialized)
                        # But strictly speaking, new_symbols is strictly strictly local difference
                        new_symbols = current_symbols - self.known_symbols

                        if new_symbols:
                            self.logger.info(
                                "new_listings_detected",
                                exchange=exchange_name,
                                count=len(new_symbols),
                                symbols=list(new_symbols)[:10]  # Log first 10
                            )

                            # Publish signal events for new listings
                            for symbol in new_symbols:
                                # Get or create symbol ID
                                symbol_id = await self._get_symbol_id(symbol)

                                # Create proper SignalEvent
                                signal_event = SignalEvent.create(
                                    symbol_id=symbol_id,
                                    sig_type=SignalType.LISTING,
                                    value=1.0,  # 1.0 indicates presence/listing
                                    meta_code=ListingMetaCode.NEW_LISTING,
                                    confidence=1.0,
                                    metadata={
                                        'symbol': symbol,
                                        'exchange': exchange_name,
                                        'detected_at': time.time(),
                                        'source': 'listings_watcher'
                                    }
                                )
                                await self.publisher.publish(signal_event)

                            self.metrics.increment_counter(
                                f"listings_detected_{exchange_name}",
                                len(new_symbols)
                            )

                        # Update known symbols
                        self.known_symbols.update(current_symbols)

                    except Exception as e:
                        self.logger.error(
                            "exchange_poll_error",
                            exchange=exchange_name,
                            error=str(e)
                        )

                # Poll every 5 minutes
                await asyncio.sleep(300)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("poll_error", error=str(e))
                await asyncio.sleep(300)

        # Cleanup: close exchange connections
        for exchange in exchanges_config.values():
            await exchange.close()

        self.logger.info("poll_loop_stopped")

    async def _initialize_symbols(self, exchanges_config):
        """Initialize known symbols from exchanges"""
        self.logger.info("initializing_known_symbols")
        for exchange_name, exchange in exchanges_config.items():
            await self._try_initialize_exchange(exchange_name, exchange)

        self.logger.info("initialization_complete",
                        known_symbols_count=len(self.known_symbols),
                        initialized_exchanges=list(self.initialized_exchanges))

    async def _try_initialize_exchange(self, exchange_name, exchange):
        """Try to initialize a single exchange"""
        try:
            markets = await exchange.fetch_markets()
            current_symbols = {m['symbol'] for m in markets if m.get('active', False)}
            self.known_symbols.update(current_symbols)
            self.initialized_exchanges.add(exchange_name)
            self.logger.info("initialized_exchange_symbols",
                           exchange=exchange_name,
                           count=len(current_symbols))
        except Exception as e:
            self.logger.error("initialization_error",
                            exchange=exchange_name,
                            error=str(e))

    async def _get_symbol_id(self, symbol: str) -> int:
        """
        Get symbol ID from cache or database

        Uses in-memory cache with database fallback.
        """
        if symbol in self._symbol_cache:
            return self._symbol_cache[symbol]

        # Try database lookup (non-blocking)
        symbol_id = await self._lookup_symbol_from_db(symbol)

        if symbol_id is None:
            # Fallback to static mapping (basic majors)
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
                # Use deterministic hash for fallback ID to ensure consistency across restarts
                # Use absolute value of adler32 to get a positive integer
                # Add offset to avoid conflict with low IDs (1-1000 reserved)
                symbol_id = 10000 + (zlib.adler32(symbol.encode('utf-8')) & 0xFFFFFFFF) % 100000
                self.logger.info("assigned_deterministic_symbol_id", symbol=symbol, symbol_id=symbol_id)

        # Cache result
        self._symbol_cache[symbol] = symbol_id
        return symbol_id

    async def _lookup_symbol_from_db(self, symbol: str) -> Optional[int]:
        """
        Lookup symbol ID from database (async wrapper)

        Returns:
            Symbol ID if found, None otherwise
        """
        return await asyncio.to_thread(self._lookup_symbol_from_db_sync, symbol)

    def _lookup_symbol_from_db_sync(self, symbol: str) -> Optional[int]:
        """Synchronous DB lookup"""
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


async def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="SIGMAX Listings Watcher")
    parser.add_argument("--profile", default="a", choices=["a", "b"])
    parser.add_argument("--config", help="Config file path")
    args = parser.parse_args()
    
    config = load_config(profile=args.profile, config_path=args.config)
    
    setup_logging(
        level=config.observability.log_level,
        log_path=config.observability.log_path,
        json_logs=config.is_production()
    )
    
    logger = get_logger(__name__)
    logger.info("sigmax_listings_watcher_starting")
    
    watcher = ListingsWatcher(config)
    
    def signal_handler(sig, frame):
        logger.info("received_signal", signal=sig)
        asyncio.create_task(watcher.stop())
    
    signal_module.signal(signal_module.SIGINT, signal_handler)
    signal_module.signal(signal_module.SIGTERM, signal_handler)
    
    try:
        await watcher.start()
        while watcher.running:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error("service_error", error=str(e), exc_info=True)
        raise
    finally:
        logger.info("sigmax_listings_watcher_stopped")


if __name__ == "__main__":
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass
    
    asyncio.run(main())
