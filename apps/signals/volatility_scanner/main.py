"""
Volatility Scanner

Computes realized volatility and turnover over configurable windows.
Publishes VOL signal events when thresholds are exceeded.
"""

import asyncio
import sys
import signal as signal_module
from pathlib import Path
import numpy as np
from collections import deque
from typing import Dict

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from pkg.common import setup_logging, get_logger, load_config, get_metrics_collector, get_timestamp_ns
from pkg.schemas import SignalEvent, SignalType, TopOfBook
from apps.signals.common import SignalPublisher
import zmq
import zmq.asyncio
import orjson


class VolatilityScanner:
    """Volatility scanner signal module"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("volatility_scanner")
        
        # RV window configuration (from config or default to 5s)
        self.rv_window_ms = 5000
        if hasattr(config, 'signals') and hasattr(config.signals, 'volatility'):
            self.rv_window_ms = config.signals.volatility.get('rv_window_ms', 5000)
        
        self.rv_window_ns = self.rv_window_ms * 1_000_000
        
        # Price windows for each symbol
        self.price_windows: Dict[int, deque] = {}
        
        # Publisher
        self.publisher = SignalPublisher(config, "volatility_scanner")
        
        # ZMQ subscriber
        self.context: zmq.asyncio.Context = None
        self.socket: zmq.asyncio.Socket = None
        
        self.running = False
        
    async def start(self):
        """Start the scanner"""
        self.logger.info("starting_volatility_scanner", rv_window_ms=self.rv_window_ms)
        
        self.metrics.set_info(
            service="volatility_scanner",
            rv_window_ms=self.rv_window_ms
        )
        
        # Start publisher
        await self.publisher.start()
        
        # Start subscriber
        await self._start_subscriber()
        
        self.running = True
        
        # Start processing loop
        asyncio.create_task(self._receive_loop())
        
        self.logger.info("volatility_scanner_started")
        
    async def stop(self):
        """Stop the scanner"""
        self.logger.info("stopping_volatility_scanner")
        self.running = False
        
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        await self.publisher.stop()
        
        self.logger.info("volatility_scanner_stopped")
    
    async def _start_subscriber(self):
        """Subscribe to TopOfBook messages"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.SUB)
        
        # Connect to stream 11 (book)
        port = self.config.ipc.zmq_base_port + 11
        connect_addr = f"tcp://127.0.0.1:{port}"
        self.socket.connect(connect_addr)
        
        # Subscribe to tob topic
        self.socket.setsockopt(zmq.SUBSCRIBE, b"tob")
        
        self.logger.info("subscribed_to_book", address=connect_addr)
    
    async def _receive_loop(self):
        """Receive and process TopOfBook updates"""
        self.logger.info("receive_loop_started")
        
        while self.running:
            try:
                message = await self.socket.recv_multipart()
                
                if len(message) != 2:
                    continue
                
                topic, payload = message
                tob = self._parse_tob(payload)
                
                if tob:
                    await self._process_tob(tob)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("receive_error", error=str(e))
                await asyncio.sleep(0.1)
        
        self.logger.info("receive_loop_stopped")
    
    def _parse_tob(self, payload: bytes) -> TopOfBook:
        """Parse TopOfBook from JSON"""
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
            return None
    
    async def _process_tob(self, tob: TopOfBook):
        """Process TopOfBook and compute volatility"""
        try:
            symbol_id = tob.symbol_id
            
            # Get or create price window
            if symbol_id not in self.price_windows:
                self.price_windows[symbol_id] = deque()
            
            window = self.price_windows[symbol_id]
            
            # Add price to window
            window.append((tob.ts_ns, tob.mid_price))
            
            # Remove old prices
            cutoff_ns = tob.ts_ns - self.rv_window_ns
            while window and window[0][0] < cutoff_ns:
                window.popleft()
            
            # Compute RV if we have enough data
            if len(window) > 2:
                rv = self._compute_realized_vol(window)
                
                # Check if RV is high (> 2 std devs)
                # Simplified: threshold at 1% for now
                if rv > 0.01:  # 1% volatility
                    signal = SignalEvent.create(
                        symbol_id=symbol_id,
                        sig_type=SignalType.VOL,
                        value=rv,
                        confidence=min(rv * 100, 1.0),  # Scale to 0-1
                        meta_code=1  # RV_SPIKE
                    )
                    
                    await self.publisher.publish(signal)
                    
                    self.logger.info("volatility_signal",
                                   symbol_id=symbol_id,
                                   rv=rv)
                    
        except Exception as e:
            self.logger.error("process_tob_error", error=str(e), exc_info=True)
    
    def _compute_realized_vol(self, window: deque) -> float:
        """Compute realized volatility from price window"""
        try:
            prices = np.array([p[1] for p in window])
            
            if len(prices) < 2:
                return 0.0
            
            # Compute log returns
            log_returns = np.diff(np.log(prices))
            
            # Realized volatility (std of returns)
            rv = float(np.std(log_returns))
            
            return rv
            
        except Exception as e:
            self.logger.error("compute_rv_error", error=str(e))
            return 0.0


async def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="SIGMAX Volatility Scanner")
    parser.add_argument("--profile", default="a", choices=["a", "b"])
    parser.add_argument("--config", help="Config file path")
    args = parser.parse_args()
    
    config = load_config(profile=args.profile, config_path=args.config)
    
    setup_logging(
        level=config.observability.log_level,
        log_path=config.observability.log_path,
        json_logs=config.is_production()
    )
    
    logger = get_logger(__name__)
    logger.info("sigmax_volatility_scanner_starting")
    
    scanner = VolatilityScanner(config)
    
    def signal_handler(sig, frame):
        logger.info("received_signal", signal=sig)
        asyncio.create_task(scanner.stop())
    
    signal_module.signal(signal_module.SIGINT, signal_handler)
    signal_module.signal(signal_module.SIGTERM, signal_handler)
    
    try:
        await scanner.start()
        while scanner.running:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error("service_error", error=str(e), exc_info=True)
        raise
    finally:
        logger.info("sigmax_volatility_scanner_stopped")


if __name__ == "__main__":
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass
    
    asyncio.run(main())
