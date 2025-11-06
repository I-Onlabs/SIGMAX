"""
Book Subscriber

Subscribes to TopOfBook messages from book_shard service (stream 11).
"""

import zmq
import zmq.asyncio
import orjson
import asyncio
from typing import Optional

from pkg.common import get_logger, get_metrics_collector, get_timestamp_ns, calculate_latency_us
from pkg.schemas import TopOfBook


class BookSubscriber:
    """
    Subscriber for order book updates.
    
    Receives TopOfBook messages from stream 11.
    """
    
    def __init__(self, config, feature_engine):
        self.config = config
        self.feature_engine = feature_engine
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("features")
        
        self.context: Optional[zmq.asyncio.Context] = None
        self.socket: Optional[zmq.asyncio.Socket] = None
        self.running = False
        
    async def start(self):
        """Start the subscriber"""
        if self.config.ipc.transport == "zmq":
            await self._start_zmq()
        else:
            raise NotImplementedError(f"Transport {self.config.ipc.transport} not implemented")
        
        self.logger.info("book_subscriber_started", transport=self.config.ipc.transport)
        
        # Start receiving loop
        asyncio.create_task(self._receive_loop())
    
    async def stop(self):
        """Stop the subscriber"""
        self.running = False
        
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        self.logger.info("book_subscriber_stopped")
    
    async def _start_zmq(self):
        """Start ZeroMQ subscriber"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.SUB)
        
        # Connect to stream 11 (book)
        port = self.config.ipc.zmq_base_port + 11
        connect_addr = f"tcp://127.0.0.1:{port}"
        self.socket.connect(connect_addr)
        
        # Subscribe to tob topic
        self.socket.setsockopt(zmq.SUBSCRIBE, b"tob")
        
        self.logger.info("zmq_book_subscriber_connected", address=connect_addr)
        self.running = True
    
    async def _receive_loop(self):
        """Receive loop for processing updates"""
        self.logger.info("book_receive_loop_started")
        
        while self.running:
            try:
                # Receive message
                message = await self.socket.recv_multipart()
                
                if len(message) != 2:
                    self.logger.warning("invalid_message_format", parts=len(message))
                    continue
                
                topic, payload = message
                
                # Parse TopOfBook
                tob = self._parse_tob(payload)
                if tob:
                    # Calculate latency
                    receive_ts = get_timestamp_ns()
                    latency_us = calculate_latency_us(tob.ts_ns, receive_ts)
                    
                    # Record metrics
                    self.metrics.increment_received("TopOfBook")
                    self.metrics.record_latency("book_receive", latency_us)
                    
                    # Process in feature engine
                    await self.feature_engine.process_tob(tob)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("receive_error", error=str(e), exc_info=True)
                self.metrics.record_error("receive_failed")
                await asyncio.sleep(0.1)  # Back off on error
        
        self.logger.info("book_receive_loop_stopped")
    
    def _parse_tob(self, payload: bytes) -> Optional[TopOfBook]:
        """Parse TopOfBook from JSON payload"""
        try:
            data = orjson.loads(payload)
            
            return TopOfBook(
                ts_ns=data['ts_ns'],
                symbol_id=data['symbol_id'],
                bid_px=data['bid_px'],
                bid_sz=data['bid_sz'],
                ask_px=data['ask_px'],
                ask_sz=data['ask_sz']
            )
        except Exception as e:
            self.logger.error("parse_error", error=str(e))
            self.metrics.record_error("parse_failed")
            return None
