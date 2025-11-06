"""
Feature Subscriber

Subscribes to FeatureFrame messages from features service (stream 12).
"""

import zmq
import zmq.asyncio
import orjson
import asyncio
from typing import Optional

from pkg.common import get_logger, get_metrics_collector, get_timestamp_ns, calculate_latency_us
from pkg.schemas import FeatureFrame


class FeatureSubscriber:
    """
    Subscriber for feature frames.
    
    Receives FeatureFrame messages from stream 12.
    """
    
    def __init__(self, config, decision_engine):
        self.config = config
        self.decision_engine = decision_engine
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("decision")
        
        self.context: Optional[zmq.asyncio.Context] = None
        self.socket: Optional[zmq.asyncio.Socket] = None
        self.running = False
        
    async def start(self):
        """Start the subscriber"""
        if self.config.ipc.transport == "zmq":
            await self._start_zmq()
        else:
            raise NotImplementedError(f"Transport {self.config.ipc.transport} not implemented")
        
        self.logger.info("feature_subscriber_started", transport=self.config.ipc.transport)
        
        # Start receiving loop
        asyncio.create_task(self._receive_loop())
    
    async def stop(self):
        """Stop the subscriber"""
        self.running = False
        
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        self.logger.info("feature_subscriber_stopped")
    
    async def _start_zmq(self):
        """Start ZeroMQ subscriber"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.SUB)
        
        # Connect to stream 12 (features)
        port = self.config.ipc.zmq_base_port + 12
        connect_addr = f"tcp://127.0.0.1:{port}"
        self.socket.connect(connect_addr)
        
        # Subscribe to features topic
        self.socket.setsockopt(zmq.SUBSCRIBE, b"features")
        
        self.logger.info("zmq_feature_subscriber_connected", address=connect_addr)
        self.running = True
    
    async def _receive_loop(self):
        """Receive loop for processing features"""
        self.logger.info("feature_receive_loop_started")
        
        while self.running:
            try:
                # Receive message
                message = await self.socket.recv_multipart()
                
                if len(message) != 2:
                    self.logger.warning("invalid_message_format", parts=len(message))
                    continue
                
                topic, payload = message
                
                # Parse FeatureFrame
                features = self._parse_features(payload)
                if features:
                    # Calculate latency
                    receive_ts = get_timestamp_ns()
                    latency_us = calculate_latency_us(features.ts_ns, receive_ts)
                    
                    # Record metrics
                    self.metrics.increment_received("FeatureFrame")
                    self.metrics.record_latency("feature_receive", latency_us)
                    
                    # Process in decision engine
                    await self.decision_engine.process_features(features)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("receive_error", error=str(e), exc_info=True)
                self.metrics.record_error("receive_failed")
                await asyncio.sleep(0.1)  # Back off on error
        
        self.logger.info("feature_receive_loop_stopped")
    
    def _parse_features(self, payload: bytes) -> Optional[FeatureFrame]:
        """Parse FeatureFrame from JSON payload"""
        try:
            data = orjson.loads(payload)
            
            features = FeatureFrame.create_empty(data['symbol_id'])
            features.ts_ns = data['ts_ns']
            features.mid_price = data['mid_price']
            features.micro_price = data['micro_price']
            features.spread = data['spread']
            features.spread_bps = data['spread_bps']
            features.bid_volume = data['bid_volume']
            features.ask_volume = data['ask_volume']
            features.imbalance = data['imbalance']
            features.realized_vol = data['realized_vol']
            features.price_range = data['price_range']
            features.price_change = data['price_change']
            features.price_change_pct = data['price_change_pct']
            features.regime_bits = data['regime_bits']
            
            return features
        except Exception as e:
            self.logger.error("parse_error", error=str(e))
            self.metrics.record_error("parse_failed")
            return None
