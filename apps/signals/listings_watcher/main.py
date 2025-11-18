"""
Listings Watcher

Monitors exchanges for new coin listings and trading pairs.
Publishes LISTING signal events.

TODO: Integrate with exchange APIs to detect new listings
For now, this is a stub implementation.
"""

import asyncio
import sys
import signal as signal_module
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from pkg.common import setup_logging, get_logger, load_config, get_metrics_collector
from pkg.schemas import SignalEvent, SignalType
from apps.signals.common import SignalPublisher


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
        
        self.running = False
        
    async def start(self):
        """Start the watcher"""
        self.logger.info("starting_listings_watcher")
        
        self.metrics.set_info(
            service="listings_watcher",
            status="stub"  # Stub implementation
        )
        
        # Start publisher
        await self.publisher.start()
        
        self.running = True
        
        # Start polling loop (stub)
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

        # Initialize CCXT exchange connections
        import ccxt.async_support as ccxt

        # Configure exchanges to monitor
        exchanges_config = {
            'binance': ccxt.binance({'enableRateLimit': True}),
            'coinbase': ccxt.coinbase({'enableRateLimit': True}),
        }

        while self.running:
            try:
                # Poll each exchange for new markets
                for exchange_name, exchange in exchanges_config.items():
                    try:
                        markets = await exchange.fetch_markets()
                        current_symbols = {m['symbol'] for m in markets if m.get('active', False)}

                        # Detect new listings
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
                                signal_event = SignalEvent(
                                    type=SignalType.LISTING,
                                    symbol=symbol,
                                    exchange=exchange_name,
                                    metadata={
                                        'detected_at': asyncio.get_event_loop().time(),
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
                # Cleanup: close exchange connections
                for exchange in exchanges_config.values():
                    await exchange.close()
                break
            except Exception as e:
                self.logger.error("poll_error", error=str(e))
                await asyncio.sleep(300)

        self.logger.info("poll_loop_stopped")


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
