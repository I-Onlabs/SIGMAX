"""
Feature Engine

Computes features from order book data over micro-windows (200-500ms).
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional
from collections import deque

from pkg.common import get_logger, get_metrics_collector, get_timestamp_ns, calculate_latency_us
from pkg.schemas import TopOfBook, FeatureFrame


class SymbolWindow:
    """Window of TopOfBook updates for a single symbol"""
    
    def __init__(self, symbol_id: int, window_ms: int = 500):
        self.symbol_id = symbol_id
        self.window_ns = window_ms * 1_000_000  # Convert to nanoseconds
        self.updates: deque[TopOfBook] = deque()
        
    def add_update(self, tob: TopOfBook):
        """Add TopOfBook update to window"""
        self.updates.append(tob)
        
        # Remove old updates outside window
        cutoff_ns = tob.ts_ns - self.window_ns
        while self.updates and self.updates[0].ts_ns < cutoff_ns:
            self.updates.popleft()
    
    def get_updates(self) -> List[TopOfBook]:
        """Get all updates in window"""
        return list(self.updates)
    
    def get_price_series(self) -> np.ndarray:
        """Get mid price series"""
        return np.array([u.mid_price for u in self.updates])
    
    def get_spread_series(self) -> np.ndarray:
        """Get spread series"""
        return np.array([u.spread for u in self.updates])


class FeatureEngine:
    """
    Feature extraction engine.
    
    Computes features over micro-windows for each symbol.
    """
    
    def __init__(self, config, publisher):
        self.config = config
        self.publisher = publisher
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("features")
        
        # Get window size from config
        window_ms = 500  # Default
        if hasattr(config, 'features') and hasattr(config.features, 'window_ms'):
            window_ms = config.features.window_ms
        
        # Windows for each symbol
        self.windows: Dict[int, SymbolWindow] = {}
        self.window_ms = window_ms
        
        # Previous features for change calculation
        self.prev_features: Dict[int, FeatureFrame] = {}
        
        self.running = False
        
    async def start(self):
        """Start the feature engine"""
        # Initialize windows for configured symbols
        for symbol in self.config.symbols:
            symbol_id = self._get_symbol_id(symbol)
            self.windows[symbol_id] = SymbolWindow(symbol_id, self.window_ms)
        
        self.running = True
        self.logger.info("feature_engine_started", 
                        window_ms=self.window_ms,
                        num_symbols=len(self.windows))
    
    async def stop(self):
        """Stop the feature engine"""
        self.running = False
        self.logger.info("feature_engine_stopped")
    
    async def process_tob(self, tob: TopOfBook):
        """
        Process TopOfBook update and compute features.
        
        Args:
            tob: TopOfBook update from book_shard
        """
        try:
            start_ts = get_timestamp_ns()
            
            # Get or create window
            symbol_id = tob.symbol_id
            if symbol_id not in self.windows:
                self.windows[symbol_id] = SymbolWindow(symbol_id, self.window_ms)
            
            window = self.windows[symbol_id]
            
            # Add update to window
            window.add_update(tob)
            
            # Compute features
            features = self._compute_features(tob, window)
            
            if features:
                # Store for next iteration
                self.prev_features[symbol_id] = features
                
                # Publish features
                await self.publisher.publish(features)
                
                # Log
                self.logger.debug("features_computed",
                                symbol_id=symbol_id,
                                spread_bps=features.spread_bps,
                                imbalance=features.imbalance,
                                realized_vol=features.realized_vol)
            
            # Record latency
            end_ts = get_timestamp_ns()
            compute_latency_us = calculate_latency_us(start_ts, end_ts)
            total_latency_us = calculate_latency_us(tob.ts_ns, end_ts)
            
            self.metrics.record_latency("feature_compute", compute_latency_us)
            self.metrics.record_latency("book_to_features", total_latency_us)
            
        except Exception as e:
            self.logger.error("process_tob_error", 
                            symbol_id=tob.symbol_id,
                            error=str(e),
                            exc_info=True)
            self.metrics.record_error("process_tob_failed")
    
    def _compute_features(self, tob: TopOfBook, window: SymbolWindow) -> Optional[FeatureFrame]:
        """Compute feature frame from window"""
        try:
            # Create feature frame
            features = FeatureFrame.create_empty(tob.symbol_id)
            features.ts_ns = tob.ts_ns
            
            # Price features
            features.mid_price = tob.mid_price
            features.micro_price = tob.micro_price
            features.spread = tob.spread
            features.spread_bps = (tob.spread / tob.mid_price) * 10000 if tob.mid_price > 0 else 0
            
            # Volume features
            features.bid_volume = tob.bid_sz
            features.ask_volume = tob.ask_sz
            total_volume = tob.bid_sz + tob.ask_sz
            features.imbalance = (tob.bid_sz - tob.ask_sz) / total_volume if total_volume > 0 else 0
            
            # Volatility features
            price_series = window.get_price_series()
            if len(price_series) > 1:
                # Realized volatility (std of returns)
                returns = np.diff(price_series) / price_series[:-1]
                features.realized_vol = float(np.std(returns)) if len(returns) > 0 else 0.0
                
                # Price range
                features.price_range = float(np.max(price_series) - np.min(price_series))
            
            # Momentum features (change from previous)
            prev = self.prev_features.get(tob.symbol_id)
            if prev:
                features.price_change = tob.mid_price - prev.mid_price
                features.price_change_pct = (features.price_change / prev.mid_price * 100) if prev.mid_price > 0 else 0
            
            return features
            
        except Exception as e:
            self.logger.error("compute_features_error", error=str(e), exc_info=True)
            return None
    
    def _get_symbol_id(self, symbol: str) -> int:
        """Get symbol ID (simplified for now)"""
        symbol_map = {
            "BTC/USDT": 1,
            "ETH/USDT": 2,
            "SOL/USDT": 3,
            "BNB/USDT": 4,
            "XRP/USDT": 5,
        }
        return symbol_map.get(symbol, 0)
