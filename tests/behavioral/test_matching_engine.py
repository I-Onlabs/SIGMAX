"""
Tests for MatchingEngine - Order Book Simulation
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.behavioral.matching_engine import (
    MatchingEngine,
    OrderBook,
    Order,
    Trade,
    OrderSide,
    OrderType,
    OrderStatus,
    OrderBookLevel
)


class TestOrderBook:
    """Test OrderBook for order matching."""

    @pytest.fixture
    def book(self):
        """Create an order book."""
        return OrderBook(symbol="BTC/USDT")

    def test_add_limit_order(self, book):
        """Test adding a limit order."""
        order = Order(
            order_id="ORD-001",
            agent_id="agent1",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=50000.0
        )

        trades = book.add_order(order)

        assert order.status == OrderStatus.OPEN
        assert len(trades) == 0
        assert book.get_best_bid() == 50000.0

    def test_match_market_order(self, book):
        """Test matching a market order."""
        # Add resting limit order
        limit_order = Order(
            order_id="ORD-001",
            agent_id="seller",
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=50000.0
        )
        book.add_order(limit_order)

        # Add market buy order
        market_order = Order(
            order_id="ORD-002",
            agent_id="buyer",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1.0
        )
        trades = book.add_order(market_order)

        assert len(trades) == 1
        assert trades[0].price == 50000.0
        assert trades[0].quantity == 1.0
        assert market_order.status == OrderStatus.FILLED

    def test_partial_fill(self, book):
        """Test partial order fill."""
        # Add small sell order
        sell_order = Order(
            order_id="ORD-001",
            agent_id="seller",
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=0.5,
            price=50000.0
        )
        book.add_order(sell_order)

        # Add larger buy order
        buy_order = Order(
            order_id="ORD-002",
            agent_id="buyer",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=50000.0
        )
        trades = book.add_order(buy_order)

        assert len(trades) == 1
        assert trades[0].quantity == 0.5
        assert buy_order.status == OrderStatus.PARTIAL
        assert buy_order.remaining_quantity == 0.5

    def test_price_time_priority(self, book):
        """Test price-time priority matching."""
        # Add two sell orders at different prices
        order1 = Order(
            order_id="ORD-001",
            agent_id="seller1",
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=50100.0
        )
        order2 = Order(
            order_id="ORD-002",
            agent_id="seller2",
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=50000.0  # Better price
        )

        book.add_order(order1)
        book.add_order(order2)

        # Market buy should match with better price first
        buy_order = Order(
            order_id="ORD-003",
            agent_id="buyer",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1.0
        )
        trades = book.add_order(buy_order)

        assert trades[0].price == 50000.0
        assert trades[0].seller_order_id == "ORD-002"

    def test_cancel_order(self, book):
        """Test order cancellation."""
        order = Order(
            order_id="ORD-001",
            agent_id="agent1",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=50000.0
        )
        book.add_order(order)

        result = book.cancel_order("ORD-001")

        assert result is True
        assert order.status == OrderStatus.CANCELLED

    def test_get_spread(self, book):
        """Test bid-ask spread calculation."""
        # Add bid
        book.add_order(Order(
            order_id="ORD-001",
            agent_id="buyer",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=49900.0
        ))

        # Add ask
        book.add_order(Order(
            order_id="ORD-002",
            agent_id="seller",
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=50100.0
        ))

        spread = book.get_spread()

        assert spread is not None
        assert spread[0] == 200.0  # Absolute spread
        assert spread[1] > 0  # Percentage spread

    def test_get_depth(self, book):
        """Test order book depth."""
        # Add multiple bids
        for i in range(5):
            book.add_order(Order(
                order_id=f"BID-{i}",
                agent_id=f"buyer{i}",
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=1.0,
                price=50000.0 - i * 100
            ))

        # Add multiple asks
        for i in range(5):
            book.add_order(Order(
                order_id=f"ASK-{i}",
                agent_id=f"seller{i}",
                symbol="BTC/USDT",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=1.0,
                price=50100.0 + i * 100
            ))

        depth = book.get_depth(levels=3)

        assert len(depth["bids"]) == 3
        assert len(depth["asks"]) == 3


class TestMatchingEngine:
    """Test MatchingEngine for multi-symbol order matching."""

    @pytest.fixture
    def engine(self):
        """Create a matching engine."""
        return MatchingEngine(enable_logging=False)

    def test_submit_order(self, engine):
        """Test submitting an order."""
        order, trades = engine.submit_order(
            agent_id="trader1",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=50000.0
        )

        assert order.status == OrderStatus.OPEN
        assert order.order_id is not None

    def test_order_matching(self, engine):
        """Test order matching across agents."""
        # Submit sell order
        sell_order, _ = engine.submit_order(
            agent_id="seller",
            symbol="ETH/USDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=10.0,
            price=3000.0
        )

        # Submit buy order that matches
        buy_order, trades = engine.submit_order(
            agent_id="buyer",
            symbol="ETH/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=10.0,
            price=3000.0
        )

        assert len(trades) == 1
        assert trades[0].buyer_agent_id == "buyer"
        assert trades[0].seller_agent_id == "seller"

    def test_reject_invalid_order(self, engine):
        """Test rejection of invalid orders."""
        # Zero quantity
        order, trades = engine.submit_order(
            agent_id="trader",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0,
            price=50000.0
        )

        assert order.status == OrderStatus.REJECTED

        # Limit order without price
        order2, trades2 = engine.submit_order(
            agent_id="trader",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=None
        )

        assert order2.status == OrderStatus.REJECTED

    def test_get_order_book(self, engine):
        """Test getting order book."""
        engine.submit_order(
            agent_id="trader1",
            symbol="SOL/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100.0,
            price=100.0
        )

        book = engine.get_order_book("SOL/USDT")

        assert book["symbol"] == "SOL/USDT"
        assert len(book["bids"]) > 0

    def test_get_trades(self, engine):
        """Test getting trade history."""
        # Create matching orders
        engine.submit_order("s", "DOGE/USDT", OrderSide.SELL, OrderType.LIMIT, 1000, 0.1)
        engine.submit_order("b", "DOGE/USDT", OrderSide.BUY, OrderType.LIMIT, 1000, 0.1)

        trades = engine.get_trades("DOGE/USDT")

        assert len(trades) == 1

    def test_get_agent_orders(self, engine):
        """Test getting orders for an agent."""
        engine.submit_order("agent1", "BTC/USDT", OrderSide.BUY, OrderType.LIMIT, 1.0, 50000)
        engine.submit_order("agent1", "ETH/USDT", OrderSide.BUY, OrderType.LIMIT, 10.0, 3000)
        engine.submit_order("agent2", "BTC/USDT", OrderSide.SELL, OrderType.LIMIT, 1.0, 51000)

        agent1_orders = engine.get_agent_orders("agent1")

        assert len(agent1_orders) == 2

    def test_market_impact_simulation(self, engine):
        """Test market impact simulation."""
        # Build order book
        for i in range(10):
            engine.submit_order(
                agent_id=f"mm{i}",
                symbol="BTC/USDT",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=0.5,
                price=50000 + i * 10
            )

        # Simulate large buy impact
        impact = engine.simulate_market_impact(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            quantity=3.0
        )

        assert "slippage_percent" in impact
        assert impact["slippage_percent"] > 0

    def test_market_summary(self, engine):
        """Test market summary."""
        # Create some activity
        engine.submit_order("s1", "BTC/USDT", OrderSide.SELL, OrderType.LIMIT, 1.0, 50000)
        engine.submit_order("b1", "BTC/USDT", OrderSide.BUY, OrderType.LIMIT, 1.0, 50000)

        summary = engine.get_market_summary("BTC/USDT")

        assert summary["symbol"] == "BTC/USDT"
        assert summary["last_price"] == 50000.0

    def test_statistics(self, engine):
        """Test engine statistics."""
        engine.submit_order("a", "BTC/USDT", OrderSide.BUY, OrderType.LIMIT, 1.0, 50000)
        engine.submit_order("b", "ETH/USDT", OrderSide.SELL, OrderType.LIMIT, 10.0, 3000)

        stats = engine.get_statistics()

        assert stats["total_orders"] >= 2
        assert len(stats["symbols"]) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
