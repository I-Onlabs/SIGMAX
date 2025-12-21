"""
Unit tests for data schemas.
"""

import pytest
import time
from pkg.schemas import (
    MdUpdate, TopOfBook, OrderIntent, OrderAck, FeatureFrame, SignalEvent, L2Book, BookLevel,
    Side, OrderType, TimeInForce, OrderStatus, SignalType
)


class TestMarketDataSchemas:
    """Test market data schemas"""
    
    def test_md_update_creation(self):
        """Test MdUpdate creation"""
        update = MdUpdate.now(
            symbol_id=1,
            bid_px=50000.0,
            bid_sz=1.5,
            ask_px=50010.0,
            ask_sz=2.0,
            seq=123
        )
        
        assert update.symbol_id == 1
        assert update.bid_px == 50000.0
        assert update.ask_px == 50010.0
        assert update.seq == 123
        assert update.ts_ns > 0
    
    def test_top_of_book_calculations(self):
        """Test TopOfBook derived values"""
        tob = TopOfBook(
            ts_ns=time.time_ns(),
            symbol_id=1,
            bid_px=50000.0,
            bid_sz=1.5,
            ask_px=50010.0,
            ask_sz=2.0
        )
        
        assert tob.spread == 10.0
        assert tob.mid_price == 50005.0
        
        # Microprice calculation
        expected_micro = (50000.0 * 2.0 + 50010.0 * 1.5) / 3.5
        assert abs(tob.micro_price - expected_micro) < 0.01
    
    def test_l2_book_operations(self):
        """Test L2 order book operations"""
        book = L2Book(symbol_id=1)
        
        # Add levels
        book.bids = [
            BookLevel(price=50000.0, size=1.5),
            BookLevel(price=49990.0, size=2.0)
        ]
        book.asks = [
            BookLevel(price=50010.0, size=2.0),
            BookLevel(price=50020.0, size=1.5)
        ]
        
        # Test top of book extraction
        tob = book.get_top_of_book()
        assert tob is not None
        assert tob.bid_px == 50000.0
        assert tob.ask_px == 50010.0
        
        # Test mid price
        assert book.get_mid_price() == 50005.0
        
        # Test spread
        assert book.get_spread() == 10.0
        
        # Test imbalance
        imbalance = book.get_imbalance(depth=2)
        expected = (3.5 - 3.5) / 7.0  # Equal volumes
        assert abs(imbalance - expected) < 0.01


class TestOrderSchemas:
    """Test order schemas"""
    
    def test_order_intent_creation(self):
        """Test OrderIntent creation"""
        order = OrderIntent.create(
            symbol_id=1,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            qty=1.0,
            price=50000.0,
            tif=TimeInForce.GTC
        )
        
        assert order.symbol_id == 1
        assert order.side == Side.BUY
        assert order.qty == 1.0
        assert order.price == 50000.0
        assert len(order.client_id) > 0  # UUID generated
    
    def test_order_ack_latency(self):
        """Test OrderAck latency calculation"""
        submit_ts = time.time_ns()
        time.sleep(0.001)  # 1ms delay
        ack_ts = time.time_ns()
        
        ack = OrderAck(
            ts_ns=ack_ts,
            client_id="test-123",
            exchange_order_id="EX-456",
            status=OrderStatus.SUBMITTED,
            venue_code=1,
            submit_ts_ns=submit_ts
        )
        
        latency = ack.latency_us
        assert latency is not None
        assert latency > 1000  # > 1ms in microseconds


class TestFeatureSchemas:
    """Test feature schemas"""
    
    def test_feature_frame_creation(self):
        """Test FeatureFrame creation"""
        features = FeatureFrame.create_empty(symbol_id=1)
        
        assert features.symbol_id == 1
        assert features.regime_bits == 0
    
    def test_feature_regime_flags(self):
        """Test regime flag operations"""
        features = FeatureFrame.create_empty(symbol_id=1)
        
        # Set flags
        features.set_regime(FeatureFrame.HIGH_VOL)
        features.set_regime(FeatureFrame.NEWS_POSITIVE)
        
        # Check flags
        assert features.has_regime(FeatureFrame.HIGH_VOL)
        assert features.has_regime(FeatureFrame.NEWS_POSITIVE)
        assert not features.has_regime(FeatureFrame.LISTING_WINDOW)
        
        # Clear flag
        features.clear_regime(FeatureFrame.HIGH_VOL)
        assert not features.has_regime(FeatureFrame.HIGH_VOL)
        assert features.has_regime(FeatureFrame.NEWS_POSITIVE)


class TestSignalSchemas:
    """Test signal schemas"""
    
    def test_signal_event_creation(self):
        """Test SignalEvent creation"""
        signal = SignalEvent.create(
            symbol_id=1,
            sig_type=SignalType.VOL,
            value=0.05,
            confidence=0.8,
            metadata={"source": "volatility_scanner"}
        )
        
        assert signal.symbol_id == 1
        assert signal.sig_type == SignalType.VOL
        assert signal.value == 0.05
        assert signal.confidence == 0.8
        assert signal.metadata["source"] == "volatility_scanner"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
