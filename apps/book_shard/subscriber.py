"""
MdUpdate Subscriber

Subscribes to market data updates from the ingestion service (stream 10).
"""

import zmq
import zmq.asyncio
import orjson
import asyncio
from typing import Optional

from pkg.common import get_logger, get_metrics_collector, get_timestamp_ns, calculate_latency_us
from pkg.schemas import MdUpdate


class MdUpdateSubscriber:
    """
    Subscriber for market data updates.
    
    Receives MdUpdate messages from stream 10 (ticks).
    """
    
    def __init__(self, config, book_manager):
        self.config = config
        self.book_manager = book_manager
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("book_shard")
        
        self.context: Optional[zmq.asyncio.Context] = None
        self.socket: Optional[zmq.asyncio.Socket] = None
        self.running = False
        
    async def start(self):
        """Start the subscriber"""
        if self.config.ipc.transport == "zmq":
            await self._start_zmq()
        else:
            raise NotImplementedError(f"Transport {self.config.ipc.transport} not implemented")
        
        self.logger.info("subscriber_started", transport=self.config.ipc.transport)
        
        # Start receiving loop
        asyncio.create_task(self._receive_loop())
    
    async def stop(self):
        """Stop the subscriber"""
        self.running = False
        
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        self.logger.info("subscriber_stopped")
    
    async def _start_zmq(self):
        """Start ZeroMQ subscriber"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.SUB)
        
        # Connect to stream 10 (ticks)
        port = self.config.ipc.zmq_base_port + 10
        connect_addr = f"tcp://127.0.0.1:{port}"
        self.socket.connect(connect_addr)
        
        # Subscribe to ticks topic
        self.socket.setsockopt(zmq.SUBSCRIBE, b"ticks")
        
        self.logger.info("zmq_subscriber_connected", address=connect_addr)
        self.running = True
    
    async def _receive_loop(self):
        """Receive loop for processing updates"""
        self.logger.info("receive_loop_started")
        
        while self.running:
            try:
                # Receive message
                message = await self.socket.recv_multipart()
                
                if len(message) != 2:
                    self.logger.warning("invalid_message_format", parts=len(message))
                    continue
                
                topic, payload = message
                
                # Parse MdUpdate
                update = self._parse_update(payload)
                if update:
                    # Calculate ingestion latency
                    receive_ts = get_timestamp_ns()
                    latency_us = calculate_latency_us(update.ts_ns, receive_ts)
                    
                    # Record metrics
                    self.metrics.increment_received("MdUpdate")
                    self.metrics.record_latency("md_receive", latency_us)
                    
                    # Process update
                    await self.book_manager.process_update(update)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("receive_error", error=str(e), exc_info=True)
                self.metrics.record_error("receive_failed")
                await asyncio.sleep(0.1)  # Back off on error
        
        self.logger.info("receive_loop_stopped")
    
    def _parse_update(self, payload: bytes) -> Optional[MdUpdate]:
        """Parse MdUpdate from JSON payload"""
        try:
            data = orjson.loads(payload)
            
            return MdUpdate(
                ts_ns=data['ts_ns'],
                symbol_id=data['symbol_id'],
                bid_px=data['bid_px'],
                bid_sz=data['bid_sz'],
                ask_px=data['ask_px'],
                ask_sz=data['ask_sz'],
                seq=data['seq']
            )
        except Exception as e:
            self.logger.error("parse_error", error=str(e))
            self.metrics.record_error("parse_failed")
            return None
