"""
Router Publisher

Publishes routed orders to execution gateways.
"""

import zmq
import zmq.asyncio
import orjson
from typing import Optional

from pkg.common import get_logger, get_metrics_collector
from pkg.schemas import OrderIntent


class RouterPublisher:
    """
    Publisher for routed orders.
    
    Sends orders to execution gateways based on venue.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("router")
        
        self.context: Optional[zmq.asyncio.Context] = None
        self.socket: Optional[zmq.asyncio.Socket] = None
        
    async def start(self):
        """Start the publisher"""
        if self.config.ipc.transport == "zmq":
            await self._start_zmq()
        else:
            raise NotImplementedError(f"Transport {self.config.ipc.transport} not implemented")
        
        self.logger.info("router_publisher_started", transport=self.config.ipc.transport)
    
    async def stop(self):
        """Stop the publisher"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        self.logger.info("router_publisher_stopped")
    
    async def _start_zmq(self):
        """Start ZeroMQ publisher"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.PUB)
        
        # Bind to stream 20 (routed orders to execution)
        port = self.config.ipc.zmq_base_port + 20 + 2  # +2 for router output
        bind_addr = f"tcp://127.0.0.1:{port}"
        self.socket.bind(bind_addr)
        
        self.logger.info("zmq_router_publisher_bound", address=bind_addr)
    
    async def publish(self, order: OrderIntent, venue: str):
        """
        Publish routed order to execution gateway.
        
        Args:
            order: OrderIntent to publish
            venue: Target venue
        """
        try:
            # Serialize to JSON for Profile A
            payload = orjson.dumps({
                'ts_ns': order.ts_ns,
                'client_id': order.client_id,
                'symbol_id': order.symbol_id,
                'side': order.side,
                'order_type': order.order_type,
                'qty': float(order.qty),
                'price': float(order.price) if order.price else None,
                'tif': order.tif,
                'route': order.route,
                'decision_layer': order.decision_layer,
                'confidence': float(order.confidence)
            })
            
            # Publish with venue-specific topic
            topic = f"routed_{venue}".encode()
            await self.socket.send_multipart([topic, payload])
            
            # Update metrics
            self.metrics.increment_sent("RoutedOrder")
            
            self.logger.debug("routed_order_published",
                            client_id=order.client_id,
                            venue=venue)
            
        except Exception as e:
            self.logger.error("publish_error", error=str(e))
            self.metrics.record_error("publish_failed")
            raise
