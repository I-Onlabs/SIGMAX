"""
Risk Publisher

Publishes approved orders to router (stream 20) and rejections (stream 21).
"""

import zmq
import zmq.asyncio
import orjson
from typing import Optional

from pkg.common import get_logger, get_metrics_collector
from pkg.schemas import OrderIntent, Reject


class RiskPublisher:
    """
    Publisher for risk engine outputs.
    
    Publishes approved orders and rejections.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("risk")
        
        self.context: Optional[zmq.asyncio.Context] = None
        self.approved_socket: Optional[zmq.asyncio.Socket] = None
        self.reject_socket: Optional[zmq.asyncio.Socket] = None
        
    async def start(self):
        """Start the publisher"""
        if self.config.ipc.transport == "zmq":
            await self._start_zmq()
        else:
            raise NotImplementedError(f"Transport {self.config.ipc.transport} not implemented")
        
        self.logger.info("risk_publisher_started", transport=self.config.ipc.transport)
    
    async def stop(self):
        """Stop the publisher"""
        if self.approved_socket:
            self.approved_socket.close()
        if self.reject_socket:
            self.reject_socket.close()
        if self.context:
            self.context.term()
        
        self.logger.info("risk_publisher_stopped")
    
    async def _start_zmq(self):
        """Start ZeroMQ publisher"""
        self.context = zmq.asyncio.Context()
        
        # Socket for approved orders (to router via stream 20)
        self.approved_socket = self.context.socket(zmq.PUB)
        port_approved = self.config.ipc.zmq_base_port + 20
        bind_addr_approved = f"tcp://127.0.0.1:{port_approved + 1}"  # +1 to not conflict
        self.approved_socket.bind(bind_addr_approved)
        
        # Socket for rejections (stream 21)
        self.reject_socket = self.context.socket(zmq.PUB)
        port_reject = self.config.ipc.zmq_base_port + 21
        bind_addr_reject = f"tcp://127.0.0.1:{port_reject}"
        self.reject_socket.bind(bind_addr_reject)
        
        self.logger.info("zmq_risk_publisher_bound",
                        approved_address=bind_addr_approved,
                        reject_address=bind_addr_reject)
    
    async def publish_approved(self, order: OrderIntent):
        """
        Publish approved order intent to router.
        
        Args:
            order: OrderIntent that passed risk checks
        """
        try:
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
            
            topic = b"approved"
            await self.approved_socket.send_multipart([topic, payload])
            
            self.metrics.increment_sent("OrderApproved")
            
        except Exception as e:
            self.logger.error("publish_approved_error", error=str(e))
            self.metrics.record_error("publish_approved_failed")
            raise
    
    async def publish_rejection(self, reject: Reject):
        """
        Publish order rejection.
        
        Args:
            reject: Rejection message
        """
        try:
            payload = orjson.dumps({
                'ts_ns': reject.ts_ns,
                'client_id': reject.client_id,
                'reason_code': reject.reason_code,
                'reason_msg': reject.reason_msg,
                'source': reject.source,
                'venue_code': reject.venue_code
            })
            
            topic = b"rejects"
            await self.reject_socket.send_multipart([topic, payload])
            
            self.metrics.increment_sent("Reject")
            
        except Exception as e:
            self.logger.error("publish_rejection_error", error=str(e))
            self.metrics.record_error("publish_rejection_failed")
            raise
