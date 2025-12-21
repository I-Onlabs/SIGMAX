"""
Main entry point for market data ingestion service.

Subscribes to exchange websocket feeds and publishes normalized
market data updates to the IPC layer.
"""

import asyncio
import sys
import signal
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pkg.common import setup_logging, get_logger, load_config, get_metrics_collector
from .feed_manager import FeedManager
from .publisher import MarketDataPublisher


class IngestService:
    """Market data ingestion service"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("ingest_cex")
        
        # Initialize components
        self.publisher = MarketDataPublisher(config)
        self.feed_manager = FeedManager(config, self.publisher)
        
        self.running = False
        
    async def start(self):
        """Start the ingestion service"""
        self.logger.info("starting_ingest_service", profile=self.config.profile)
        
        # Set service info
        self.metrics.set_info(
            service="ingest_cex",
            profile=self.config.profile,
            symbols=",".join(self.config.symbols)
        )
        
        self.running = True
        
        # Start publisher
        await self.publisher.start()
        
        # Start feed manager
        await self.feed_manager.start()
        
        self.logger.info("ingest_service_started")
        
    async def stop(self):
        """Stop the ingestion service"""
        self.logger.info("stopping_ingest_service")
        self.running = False
        
        # Stop feed manager
        await self.feed_manager.stop()
        
        # Stop publisher
        await self.publisher.stop()
        
        self.logger.info("ingest_service_stopped")
    
    async def run(self):
        """Run the service until stopped"""
        await self.start()
        
        try:
            # Keep running
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()


async def main():
    """Main entry point"""
    # Parse args
    import argparse
    parser = argparse.ArgumentParser(description="SIGMAX Market Data Ingestion")
    parser.add_argument("--profile", default="a", choices=["a", "b"], 
                       help="Profile to use (a=simple, b=performance)")
    parser.add_argument("--config", help="Config file path")
    args = parser.parse_args()
    
    # Load config
    config = load_config(profile=args.profile, config_path=args.config)
    
    # Setup logging
    setup_logging(
        level=config.observability.log_level,
        log_path=config.observability.log_path,
        json_logs=config.is_production()
    )
    
    logger = get_logger(__name__)
    logger.info("sigmax_ingest_starting", 
                profile=config.profile, 
                environment=config.environment)
    
    # Create service
    service = IngestService(config)
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("received_signal", signal=sig)
        asyncio.create_task(service.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run service
    try:
        await service.run()
    except Exception as e:
        logger.error("service_error", error=str(e), exc_info=True)
        raise
    finally:
        logger.info("sigmax_ingest_stopped")


if __name__ == "__main__":
    try:
        # Use uvloop for better async performance if available
        import uvloop
        uvloop.install()
    except ImportError:
        pass
    
    asyncio.run(main())
