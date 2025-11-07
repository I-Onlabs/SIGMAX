"""
Main entry point for decision layer service.

Subscribes to FeatureFrame messages and generates OrderIntent messages
using the hybrid L0-L5 decision architecture.
"""

import asyncio
import sys
import signal
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pkg.common import setup_logging, get_logger, load_config, get_metrics_collector
from .subscriber import FeatureSubscriber
from .decision_engine import DecisionEngine
from .publisher import DecisionPublisher


class DecisionService:
    """Decision layer service"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("decision")
        
        # Initialize components
        self.publisher = DecisionPublisher(config)
        self.engine = DecisionEngine(config, self.publisher)
        self.subscriber = FeatureSubscriber(config, self.engine)
        
        self.running = False
        
    async def start(self):
        """Start the decision service"""
        self.logger.info("starting_decision_service", profile=self.config.profile)
        
        # Set service info
        enabled_layers = self.config.decision.enabled_layers if hasattr(self.config, 'decision') else [0, 1, 2]
        self.metrics.set_info(
            service="decision",
            profile=self.config.profile,
            enabled_layers=",".join(map(str, enabled_layers))
        )
        
        self.running = True
        
        # Start publisher
        await self.publisher.start()
        
        # Start engine
        await self.engine.start()
        
        # Start subscriber
        await self.subscriber.start()
        
        self.logger.info("decision_service_started")
        
    async def stop(self):
        """Stop the decision service"""
        self.logger.info("stopping_decision_service")
        self.running = False
        
        # Stop subscriber
        await self.subscriber.stop()
        
        # Stop engine
        await self.engine.stop()
        
        # Stop publisher
        await self.publisher.stop()
        
        self.logger.info("decision_service_stopped")
    
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
    parser = argparse.ArgumentParser(description="SIGMAX Decision Layer")
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
    logger.info("sigmax_decision_starting", 
                profile=config.profile, 
                environment=config.environment)
    
    # Create service
    service = DecisionService(config)
    
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
        logger.info("sigmax_decision_stopped")


if __name__ == "__main__":
    try:
        # Use uvloop for better async performance if available
        import uvloop
        uvloop.install()
    except ImportError:
        pass
    
    asyncio.run(main())
