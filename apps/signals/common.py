"""
Common utilities for signal modules.
"""

import zmq
import zmq.asyncio
import orjson
from typing import Optional

from pkg.common import get_logger, get_metrics_collector
from pkg.schemas import SignalEvent


class SignalPublisher:
    """
    Common publisher for all signal modules.
    
    Sends SignalEvent messages to stream 13.
    """
    
    def __init__(self, config, service_name: str):
        self.config = config
        self.service_name = service_name
        self.logger = get_logger(service_name)
        self.metrics = get_metrics_collector(service_name)
        
        self.context: Optional[zmq.asyncio.Context] = None
        self.socket: Optional[zmq.asyncio.Socket] = None
        
    async def start(self):
        """Start the publisher"""
        if self.config.ipc.transport == "zmq":
            await self._start_zmq()
        else:
            raise NotImplementedError(f"Transport {self.config.ipc.transport} not implemented")
        
        self.logger.info("signal_publisher_started", transport=self.config.ipc.transport)
    
    async def stop(self):
        """Stop the publisher"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        self.logger.info("signal_publisher_stopped")
    
    async def _start_zmq(self):
        """Start ZeroMQ publisher"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.PUB)
        
        # Bind to stream 13 (signals)
        port = self.config.ipc.zmq_base_port + 13
        bind_addr = f"tcp://127.0.0.1:{port}"
        self.socket.bind(bind_addr)
        
        self.logger.info("zmq_signal_publisher_bound", address=bind_addr)
    
    async def publish(self, signal: SignalEvent):
        """
        Publish signal event.
        
        Args:
            signal: SignalEvent message to publish
        """
        try:
            # Serialize to JSON for Profile A
            payload = orjson.dumps({
                'ts_ns': signal.ts_ns,
                'symbol_id': signal.symbol_id,
                'sig_type': signal.sig_type,
                'value': float(signal.value),
                'meta_code': signal.meta_code,
                'confidence': float(signal.confidence)
            })
            
            # Publish with topic
            topic = b"signals"
            await self.socket.send_multipart([topic, payload])
            
            # Update metrics
            self.metrics.increment_sent("SignalEvent")
            
            self.logger.debug("signal_published",
                            symbol_id=signal.symbol_id,
                            sig_type=signal.sig_type,
                            value=signal.value)
            
        except Exception as e:
            self.logger.error("publish_error", error=str(e))
            self.metrics.record_error("publish_failed")
            raise
