"""
Routed Order Subscriber

Subscribes to routed orders from the router.
"""

import zmq
import zmq.asyncio
import orjson
import asyncio
from typing import Optional

from pkg.common import get_logger, get_metrics_collector, get_timestamp_ns, calculate_latency_us
from pkg.schemas import OrderIntent, Side, OrderType, TimeInForce


class RoutedOrderSubscriber:
    """
    Subscriber for routed orders.
    
    Receives OrderIntent messages from router.
    """
    
    def __init__(self, config, execution_engine):
        self.config = config
        self.execution_engine = execution_engine
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("exec_cex")
        
        self.context: Optional[zmq.asyncio.Context] = None
        self.socket: Optional[zmq.asyncio.Socket] = None
        self.running = False
        
    async def start(self):
        """Start the subscriber"""
        if self.config.ipc.transport == "zmq":
            await self._start_zmq()
        else:
            raise NotImplementedError(f"Transport {self.config.ipc.transport} not implemented")
        
        self.logger.info("routed_order_subscriber_started", transport=self.config.ipc.transport)
        
        # Start receiving loop
        asyncio.create_task(self._receive_loop())
    
    async def stop(self):
        """Stop the subscriber"""
        self.running = False
        
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        self.logger.info("routed_order_subscriber_stopped")
    
    async def _start_zmq(self):
        """Start ZeroMQ subscriber"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.SUB)
        
        # Connect to router
        port = self.config.ipc.zmq_base_port + 20 + 2  # Router publishes on +2
        connect_addr = f"tcp://127.0.0.1:{port}"
        self.socket.connect(connect_addr)
        
        # Subscribe to all routed orders
        self.socket.setsockopt(zmq.SUBSCRIBE, b"routed_")
        
        self.logger.info("zmq_routed_order_subscriber_connected", address=connect_addr)
        self.running = True
    
    async def _receive_loop(self):
        """Receive loop for processing routed orders"""
        self.logger.info("routed_order_receive_loop_started")
        
        while self.running:
            try:
                # Receive message
                message = await self.socket.recv_multipart()
                
                if len(message) != 2:
                    self.logger.warning("invalid_message_format", parts=len(message))
                    continue
                
                topic, payload = message
                
                # Parse OrderIntent
                order = self._parse_order(payload)
                if order:
                    # Calculate latency
                    receive_ts = get_timestamp_ns()
                    latency_us = calculate_latency_us(order.ts_ns, receive_ts)
                    
                    # Record metrics
                    self.metrics.increment_received("RoutedOrder")
                    self.metrics.record_latency("routed_receive", latency_us)
                    
                    # Execute the order
                    await self.execution_engine.execute_order(order)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("receive_error", error=str(e), exc_info=True)
                self.metrics.record_error("receive_failed")
                await asyncio.sleep(0.1)  # Back off on error
        
        self.logger.info("routed_order_receive_loop_stopped")
    
    def _parse_order(self, payload: bytes) -> Optional[OrderIntent]:
        """Parse OrderIntent from JSON payload"""
        try:
            data = orjson.loads(payload)
            
            return OrderIntent(
                ts_ns=data['ts_ns'],
                client_id=data['client_id'],
                symbol_id=data['symbol_id'],
                side=Side(data['side']),
                order_type=OrderType(data['order_type']),
                qty=data['qty'],
                price=data.get('price'),
                tif=TimeInForce(data['tif']),
                route=data['route'],
                decision_layer=data.get('decision_layer', 0),
                confidence=data.get('confidence', 0.0)
            )
        except Exception as e:
            self.logger.error("parse_error", error=str(e))
            self.metrics.record_error("parse_failed")
            return None
