"""
Execution Publisher

Publishes fills, acks, and rejections to stream 21.
"""

import zmq
import zmq.asyncio
import orjson
from typing import Optional

from pkg.common import get_logger, get_metrics_collector
from pkg.schemas import OrderAck, Fill, Reject


class ExecutionPublisher:
    """
    Publisher for execution results.
    
    Publishes OrderAck, Fill, and Reject messages to stream 21.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("exec_cex")
        
        self.context: Optional[zmq.asyncio.Context] = None
        self.socket: Optional[zmq.asyncio.Socket] = None
        
    async def start(self):
        """Start the publisher"""
        if self.config.ipc.transport == "zmq":
            await self._start_zmq()
        else:
            raise NotImplementedError(f"Transport {self.config.ipc.transport} not implemented")
        
        self.logger.info("execution_publisher_started", transport=self.config.ipc.transport)
    
    async def stop(self):
        """Stop the publisher"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        self.logger.info("execution_publisher_stopped")
    
    async def _start_zmq(self):
        """Start ZeroMQ publisher"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.PUB)
        
        # Bind to stream 21 (acks/fills)
        port = self.config.ipc.zmq_base_port + 21
        bind_addr = f"tcp://127.0.0.1:{port}"
        self.socket.bind(bind_addr)
        
        self.logger.info("zmq_execution_publisher_bound", address=bind_addr)
    
    async def publish_ack(self, ack: OrderAck):
        """
        Publish order acknowledgment.
        
        Args:
            ack: OrderAck message
        """
        try:
            payload = orjson.dumps({
                'ts_ns': ack.ts_ns,
                'client_id': ack.client_id,
                'exchange_order_id': ack.exchange_order_id,
                'status': ack.status,
                'venue_code': ack.venue_code,
                'submit_ts_ns': ack.submit_ts_ns,
                'latency_us': ack.latency_us
            })
            
            topic = b"acks"
            await self.socket.send_multipart([topic, payload])
            
            self.metrics.increment_sent("OrderAck")
            
        except Exception as e:
            self.logger.error("publish_ack_error", error=str(e))
            self.metrics.record_error("publish_ack_failed")
            raise
    
    async def publish_fill(self, fill: Fill):
        """
        Publish order fill.
        
        Args:
            fill: Fill message
        """
        try:
            payload = orjson.dumps({
                'ts_ns': fill.ts_ns,
                'client_id': fill.client_id,
                'exchange_order_id': fill.exchange_order_id,
                'price': float(fill.price),
                'qty': float(fill.qty),
                'fee': float(fill.fee),
                'fee_currency': fill.fee_currency,
                'venue_code': fill.venue_code,
                'is_maker': fill.is_maker,
                'trade_id': fill.trade_id
            })
            
            topic = b"fills"
            await self.socket.send_multipart([topic, payload])
            
            self.metrics.increment_sent("Fill")
            
        except Exception as e:
            self.logger.error("publish_fill_error", error=str(e))
            self.metrics.record_error("publish_fill_failed")
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
            await self.socket.send_multipart([topic, payload])
            
            self.metrics.increment_sent("Reject")
            
        except Exception as e:
            self.logger.error("publish_rejection_error", error=str(e))
            self.metrics.record_error("publish_rejection_failed")
            raise
