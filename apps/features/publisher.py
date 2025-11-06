"""
Feature Publisher

Publishes FeatureFrame messages to stream 12.
"""

import zmq
import zmq.asyncio
import orjson
from typing import Optional

from pkg.common import get_logger, get_metrics_collector
from pkg.schemas import FeatureFrame


class FeaturePublisher:
    """
    Publisher for feature frames.
    
    Sends FeatureFrame messages to stream 12.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("features")
        
        self.context: Optional[zmq.asyncio.Context] = None
        self.socket: Optional[zmq.asyncio.Socket] = None
        
    async def start(self):
        """Start the publisher"""
        if self.config.ipc.transport == "zmq":
            await self._start_zmq()
        else:
            raise NotImplementedError(f"Transport {self.config.ipc.transport} not implemented")
        
        self.logger.info("feature_publisher_started", transport=self.config.ipc.transport)
    
    async def stop(self):
        """Stop the publisher"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        self.logger.info("feature_publisher_stopped")
    
    async def _start_zmq(self):
        """Start ZeroMQ publisher"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.PUB)
        
        # Bind to stream 12 (features)
        port = self.config.ipc.zmq_base_port + 12
        bind_addr = f"tcp://127.0.0.1:{port}"
        self.socket.bind(bind_addr)
        
        self.logger.info("zmq_feature_publisher_bound", address=bind_addr)
    
    async def publish(self, features: FeatureFrame):
        """
        Publish feature frame.
        
        Args:
            features: FeatureFrame message to publish
        """
        try:
            # Serialize to JSON for Profile A
            payload = orjson.dumps({
                'ts_ns': features.ts_ns,
                'symbol_id': features.symbol_id,
                'mid_price': float(features.mid_price),
                'micro_price': float(features.micro_price),
                'spread': float(features.spread),
                'spread_bps': float(features.spread_bps),
                'bid_volume': float(features.bid_volume),
                'ask_volume': float(features.ask_volume),
                'imbalance': float(features.imbalance),
                'realized_vol': float(features.realized_vol),
                'price_range': float(features.price_range),
                'price_change': float(features.price_change),
                'price_change_pct': float(features.price_change_pct),
                'regime_bits': features.regime_bits
            })
            
            # Publish with topic
            topic = b"features"
            await self.socket.send_multipart([topic, payload])
            
            # Update metrics
            self.metrics.increment_sent("FeatureFrame")
            
        except Exception as e:
            self.logger.error("publish_error", error=str(e))
            self.metrics.record_error("publish_failed")
            raise
