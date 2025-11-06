"""
Book Publisher

Publishes TopOfBook and BookDelta messages to stream 11.
"""

import zmq
import zmq.asyncio
import orjson
from typing import Optional

from pkg.common import get_logger, get_metrics_collector
from pkg.schemas import TopOfBook, BookDelta


class BookPublisher:
    """
    Publisher for order book updates.
    
    Sends TopOfBook and BookDelta messages to stream 11.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("book_shard")
        
        self.context: Optional[zmq.asyncio.Context] = None
        self.socket: Optional[zmq.asyncio.Socket] = None
        
    async def start(self):
        """Start the publisher"""
        if self.config.ipc.transport == "zmq":
            await self._start_zmq()
        else:
            raise NotImplementedError(f"Transport {self.config.ipc.transport} not implemented")
        
        self.logger.info("book_publisher_started", transport=self.config.ipc.transport)
    
    async def stop(self):
        """Stop the publisher"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        self.logger.info("book_publisher_stopped")
    
    async def _start_zmq(self):
        """Start ZeroMQ publisher"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.PUB)
        
        # Bind to stream 11 (book)
        port = self.config.ipc.zmq_base_port + 11
        bind_addr = f"tcp://127.0.0.1:{port}"
        self.socket.bind(bind_addr)
        
        self.logger.info("zmq_book_publisher_bound", address=bind_addr)
    
    async def publish_tob(self, tob: TopOfBook):
        """
        Publish top of book update.
        
        Args:
            tob: TopOfBook message to publish
        """
        try:
            # Serialize to JSON for Profile A
            payload = orjson.dumps({
                'ts_ns': tob.ts_ns,
                'symbol_id': tob.symbol_id,
                'bid_px': float(tob.bid_px),
                'bid_sz': float(tob.bid_sz),
                'ask_px': float(tob.ask_px),
                'ask_sz': float(tob.ask_sz),
                'spread': float(tob.spread),
                'mid_price': float(tob.mid_price),
                'micro_price': float(tob.micro_price)
            })
            
            # Publish with topic
            topic = b"tob"
            await self.socket.send_multipart([topic, payload])
            
            # Update metrics
            self.metrics.increment_sent("TopOfBook")
            
        except Exception as e:
            self.logger.error("publish_tob_error", error=str(e))
            self.metrics.record_error("publish_tob_failed")
            raise
    
    async def publish_delta(self, delta: BookDelta):
        """
        Publish book delta update.
        
        Args:
            delta: BookDelta message to publish
        """
        try:
            # Serialize to JSON for Profile A
            payload = orjson.dumps({
                'ts_ns': delta.ts_ns,
                'symbol_id': delta.symbol_id,
                'is_bid': delta.is_bid,
                'price': float(delta.price),
                'size': float(delta.size)
            })
            
            # Publish with topic
            topic = b"delta"
            await self.socket.send_multipart([topic, payload])
            
            # Update metrics
            self.metrics.increment_sent("BookDelta")
            
        except Exception as e:
            self.logger.error("publish_delta_error", error=str(e))
            self.metrics.record_error("publish_delta_failed")
            raise
