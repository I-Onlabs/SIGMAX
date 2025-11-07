"""
Decision Publisher

Publishes OrderIntent messages to stream 20.
"""

import zmq
import zmq.asyncio
import orjson
from typing import Optional

from pkg.common import get_logger, get_metrics_collector
from pkg.schemas import OrderIntent


class DecisionPublisher:
    """
    Publisher for order intents.
    
    Sends OrderIntent messages to stream 20.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("decision")
        
        self.context: Optional[zmq.asyncio.Context] = None
        self.socket: Optional[zmq.asyncio.Socket] = None
        
    async def start(self):
        """Start the publisher"""
        if self.config.ipc.transport == "zmq":
            await self._start_zmq()
        else:
            raise NotImplementedError(f"Transport {self.config.ipc.transport} not implemented")
        
        self.logger.info("decision_publisher_started", transport=self.config.ipc.transport)
    
    async def stop(self):
        """Stop the publisher"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        self.logger.info("decision_publisher_stopped")
    
    async def _start_zmq(self):
        """Start ZeroMQ publisher"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.PUB)
        
        # Bind to stream 20 (orders)
        port = self.config.ipc.zmq_base_port + 20
        bind_addr = f"tcp://127.0.0.1:{port}"
        self.socket.bind(bind_addr)
        
        self.logger.info("zmq_decision_publisher_bound", address=bind_addr)
    
    async def publish(self, order_intent: OrderIntent):
        """
        Publish order intent.
        
        Args:
            order_intent: OrderIntent message to publish
        """
        try:
            # Serialize to JSON for Profile A
            payload = orjson.dumps({
                'ts_ns': order_intent.ts_ns,
                'client_id': order_intent.client_id,
                'symbol_id': order_intent.symbol_id,
                'side': order_intent.side,
                'order_type': order_intent.order_type,
                'qty': float(order_intent.qty),
                'price': float(order_intent.price) if order_intent.price else None,
                'tif': order_intent.tif,
                'route': order_intent.route,
                'decision_layer': order_intent.decision_layer,
                'confidence': float(order_intent.confidence)
            })
            
            # Publish with topic
            topic = b"orders"
            await self.socket.send_multipart([topic, payload])
            
            # Update metrics
            self.metrics.increment_sent("OrderIntent")
            
            self.logger.debug("order_intent_published",
                            client_id=order_intent.client_id,
                            symbol_id=order_intent.symbol_id,
                            side=order_intent.side)
            
        except Exception as e:
            self.logger.error("publish_error", error=str(e))
            self.metrics.record_error("publish_failed")
            raise
