"""
Market Data Publisher

Publishes MdUpdate messages to IPC layer (ZeroMQ or Aeron).
"""

import zmq
import zmq.asyncio
import orjson
from typing import Optional

from pkg.common import get_logger, get_metrics_collector
from pkg.schemas import MdUpdate


class MarketDataPublisher:
    """
    Publisher for market data updates.
    
    Sends MdUpdate messages to stream 10 in the IPC topology.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("ingest_cex")
        
        self.context: Optional[zmq.asyncio.Context] = None
        self.socket: Optional[zmq.asyncio.Socket] = None
        
    async def start(self):
        """Start the publisher"""
        if self.config.ipc.transport == "zmq":
            await self._start_zmq()
        else:
            raise NotImplementedError(f"Transport {self.config.ipc.transport} not implemented")
        
        self.logger.info("publisher_started", transport=self.config.ipc.transport)
    
    async def stop(self):
        """Stop the publisher"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        self.logger.info("publisher_stopped")
    
    async def _start_zmq(self):
        """Start ZeroMQ publisher"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.PUB)
        
        # Bind to stream 10 (ticks)
        port = self.config.ipc.zmq_base_port + 10
        bind_addr = f"tcp://127.0.0.1:{port}"
        self.socket.bind(bind_addr)
        
        self.logger.info("zmq_publisher_bound", address=bind_addr)
    
    async def publish(self, update: MdUpdate):
        """
        Publish market data update.
        
        Args:
            update: MdUpdate message to publish
        """
        try:
            # Serialize to JSON for Profile A (will use SBE in Profile B)
            payload = orjson.dumps({
                'ts_ns': update.ts_ns,
                'symbol_id': update.symbol_id,
                'bid_px': float(update.bid_px),
                'bid_sz': float(update.bid_sz),
                'ask_px': float(update.ask_px),
                'ask_sz': float(update.ask_sz),
                'seq': update.seq
            })
            
            # Publish with topic
            topic = b"ticks"
            await self.socket.send_multipart([topic, payload])
            
            # Update metrics
            self.metrics.increment_sent("MdUpdate")
            
        except Exception as e:
            self.logger.error("publish_error", error=str(e))
            self.metrics.record_error("publish_failed")
            raise
