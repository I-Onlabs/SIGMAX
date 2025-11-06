"""
News Sentiment Scanner

Monitors crypto news and computes sentiment scores.
Publishes NEWS signal events.

TODO: Integrate with actual news APIs (CoinDesk, CoinTelegraph, etc.)
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


class NewsSentimentScanner:
    """News sentiment scanner signal module"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("news_sentiment")
        
        # Publisher
        self.publisher = SignalPublisher(config, "news_sentiment")
        
        self.running = False
        
    async def start(self):
        """Start the scanner"""
        self.logger.info("starting_news_sentiment_scanner")
        
        self.metrics.set_info(
            service="news_sentiment",
            status="stub"  # Stub implementation
        )
        
        # Start publisher
        await self.publisher.start()
        
        self.running = True
        
        # Start polling loop (stub)
        asyncio.create_task(self._poll_loop())
        
        self.logger.info("news_sentiment_scanner_started")
        
    async def stop(self):
        """Stop the scanner"""
        self.logger.info("stopping_news_sentiment_scanner")
        self.running = False
        
        await self.publisher.stop()
        
        self.logger.info("news_sentiment_scanner_stopped")
    
    async def _poll_loop(self):
        """Poll for news (stub implementation)"""
        self.logger.info("poll_loop_started")
        
        while self.running:
            try:
                # TODO: Implement actual news fetching and sentiment analysis
                # For now, just sleep
                await asyncio.sleep(60)  # Poll every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("poll_error", error=str(e))
                await asyncio.sleep(60)
        
        self.logger.info("poll_loop_stopped")


async def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="SIGMAX News Sentiment Scanner")
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
    logger.info("sigmax_news_sentiment_starting")
    
    scanner = NewsSentimentScanner(config)
    
    def signal_handler(sig, frame):
        logger.info("received_signal", signal=sig)
        asyncio.create_task(scanner.stop())
    
    signal_module.signal(signal_module.SIGINT, signal_handler)
    signal_module.signal(signal_module.SIGTERM, signal_handler)
    
    try:
        await scanner.start()
        while scanner.running:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error("service_error", error=str(e), exc_info=True)
        raise
    finally:
        logger.info("sigmax_news_sentiment_stopped")


if __name__ == "__main__":
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass
    
    asyncio.run(main())
