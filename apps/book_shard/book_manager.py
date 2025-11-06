"""
Book Manager

Maintains single-writer L2 order books for each symbol.
Publishes TopOfBook and BookDelta messages.
"""

import asyncio
from typing import Dict, Optional
from collections import deque

from pkg.common import get_logger, get_metrics_collector, get_timestamp_ns, calculate_latency_us
from pkg.schemas import MdUpdate, L2Book, TopOfBook, BookLevel, BookDelta


class BookManager:
    """
    Manages L2 order books for assigned symbols.
    
    Single-writer architecture: one shard per symbol to avoid locking.
    """
    
    def __init__(self, config, publisher):
        self.config = config
        self.publisher = publisher
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("book_shard")
        
        # Order books keyed by symbol_id
        self.books: Dict[int, L2Book] = {}
        
        # Recent updates for each symbol (for gap recovery)
        self.recent_updates: Dict[int, deque] = {}
        self.max_recent_updates = 1000
        
        self.running = False
        
    async def start(self):
        """Start the book manager"""
        # Initialize books for configured symbols
        for symbol in self.config.symbols:
            symbol_id = self._get_symbol_id(symbol)
            self.books[symbol_id] = L2Book(symbol_id=symbol_id)
            self.recent_updates[symbol_id] = deque(maxlen=self.max_recent_updates)
        
        self.running = True
        self.logger.info("book_manager_started", num_books=len(self.books))
    
    async def stop(self):
        """Stop the book manager"""
        self.running = False
        self.logger.info("book_manager_stopped")
    
    async def process_update(self, update: MdUpdate):
        """
        Process market data update and maintain order book.
        
        Args:
            update: MdUpdate from ingestion service
        """
        try:
            start_ts = get_timestamp_ns()
            
            # Get or create book
            symbol_id = update.symbol_id
            if symbol_id not in self.books:
                self.books[symbol_id] = L2Book(symbol_id=symbol_id)
                self.recent_updates[symbol_id] = deque(maxlen=self.max_recent_updates)
            
            book = self.books[symbol_id]
            
            # Store recent update
            self.recent_updates[symbol_id].append(update)
            
            # Update book state
            # For simplified implementation, we'll just update top level
            # In production, would maintain full L2 book with insert/update/delete
            book.bids = [BookLevel(price=update.bid_px, size=update.bid_sz)]
            book.asks = [BookLevel(price=update.ask_px, size=update.ask_sz)]
            book.last_update_ns = update.ts_ns
            book.sequence = update.seq
            
            # Get top of book
            tob = book.get_top_of_book()
            if tob:
                # Publish TopOfBook
                await self.publisher.publish_tob(tob)
                
                # Log book metrics
                self.logger.debug("book_updated",
                                symbol_id=symbol_id,
                                mid=tob.mid_price,
                                spread=tob.spread,
                                imbalance=book.get_imbalance())
            
            # Record latency
            end_ts = get_timestamp_ns()
            apply_latency_us = calculate_latency_us(start_ts, end_ts)
            total_latency_us = calculate_latency_us(update.ts_ns, end_ts)
            
            self.metrics.record_latency("book_apply", apply_latency_us)
            self.metrics.record_latency("md_to_book", total_latency_us)
            
        except Exception as e:
            self.logger.error("process_update_error", 
                            symbol_id=update.symbol_id,
                            error=str(e),
                            exc_info=True)
            self.metrics.record_error("process_update_failed")
    
    def get_book(self, symbol_id: int) -> Optional[L2Book]:
        """Get order book for symbol"""
        return self.books.get(symbol_id)
    
    def get_all_books(self) -> Dict[int, L2Book]:
        """Get all order books"""
        return self.books
    
    def _get_symbol_id(self, symbol: str) -> int:
        """Get symbol ID (simplified for now)"""
        # TODO: Lookup from database
        symbol_map = {
            "BTC/USDT": 1,
            "ETH/USDT": 2,
            "SOL/USDT": 3,
            "BNB/USDT": 4,
            "XRP/USDT": 5,
        }
        return symbol_map.get(symbol, 0)
