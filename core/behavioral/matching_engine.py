"""
Order Book Matching Engine - Realistic Order Simulation
Inspired by TwinMarket's market microstructure simulation

Features:
- Limit and market order support
- Price-time priority matching
- Order book visualization
- Trade execution simulation
- Market impact modeling
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import heapq
import uuid
from loguru import logger


class OrderSide(Enum):
    """Order side (buy/sell)."""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type."""
    LIMIT = "limit"
    MARKET = "market"
    STOP_LIMIT = "stop_limit"
    STOP_MARKET = "stop_market"


class OrderStatus(Enum):
    """Order status."""
    PENDING = "pending"
    OPEN = "open"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """A trading order."""
    order_id: str
    agent_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None  # None for market orders
    stop_price: Optional[float] = None  # For stop orders
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    fills: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def remaining_quantity(self) -> float:
        return self.quantity - self.filled_quantity

    @property
    def is_active(self) -> bool:
        return self.status in [OrderStatus.OPEN, OrderStatus.PARTIAL]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "agent_id": self.agent_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "price": self.price,
            "stop_price": self.stop_price,
            "filled_quantity": round(self.filled_quantity, 8),
            "filled_price": round(self.filled_price, 8) if self.filled_price else 0,
            "remaining_quantity": round(self.remaining_quantity, 8),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "fills": self.fills
        }


@dataclass
class Trade:
    """An executed trade."""
    trade_id: str
    symbol: str
    buyer_order_id: str
    seller_order_id: str
    buyer_agent_id: str
    seller_agent_id: str
    price: float
    quantity: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "buyer_order_id": self.buyer_order_id,
            "seller_order_id": self.seller_order_id,
            "buyer_agent_id": self.buyer_agent_id,
            "seller_agent_id": self.seller_agent_id,
            "price": round(self.price, 8),
            "quantity": round(self.quantity, 8),
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class OrderBookLevel:
    """A price level in the order book."""
    price: float
    quantity: float
    order_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "price": round(self.price, 8),
            "quantity": round(self.quantity, 8),
            "order_count": self.order_count
        }


class OrderBook:
    """
    Order book for a single trading pair.

    Maintains price-time priority matching.
    """

    def __init__(self, symbol: str):
        """
        Initialize order book.

        Args:
            symbol: Trading pair symbol
        """
        self.symbol = symbol

        # Bids: max heap (negate prices for max behavior)
        # Format: (-price, timestamp, order_id, order)
        self._bids: List[Tuple[float, datetime, str, Order]] = []

        # Asks: min heap
        # Format: (price, timestamp, order_id, order)
        self._asks: List[Tuple[float, datetime, str, Order]] = []

        # Order lookup
        self._orders: Dict[str, Order] = {}

        # Trade history
        self._trades: List[Trade] = []

        # Last trade price
        self.last_price: Optional[float] = None

    def add_order(self, order: Order) -> List[Trade]:
        """
        Add an order to the book and attempt matching.

        Args:
            order: Order to add

        Returns:
            List of trades executed
        """
        if order.symbol != self.symbol:
            raise ValueError(f"Order symbol {order.symbol} doesn't match book {self.symbol}")

        order.status = OrderStatus.OPEN
        order.updated_at = datetime.utcnow()
        self._orders[order.order_id] = order

        trades = []

        # Try to match
        if order.order_type == OrderType.MARKET:
            trades = self._match_market_order(order)
        elif order.order_type == OrderType.LIMIT:
            trades = self._match_limit_order(order)

        # Add remaining to book if limit order
        if order.remaining_quantity > 0 and order.order_type == OrderType.LIMIT:
            self._add_to_book(order)

        return trades

    def _match_market_order(self, order: Order) -> List[Trade]:
        """Match a market order against the book."""
        trades = []
        opposite_side = self._asks if order.side == OrderSide.BUY else self._bids

        while order.remaining_quantity > 0 and opposite_side:
            if order.side == OrderSide.BUY:
                price, timestamp, order_id, resting_order = heapq.heappop(self._asks)
            else:
                neg_price, timestamp, order_id, resting_order = heapq.heappop(self._bids)
                price = -neg_price

            # Skip cancelled/filled orders
            if not resting_order.is_active:
                continue

            trade = self._execute_match(order, resting_order, price)
            if trade:
                trades.append(trade)

            # Re-add resting order if not fully filled
            if resting_order.remaining_quantity > 0:
                self._add_to_book(resting_order)

        if order.remaining_quantity > 0:
            order.status = OrderStatus.CANCELLED  # No more liquidity
        elif order.filled_quantity > 0:
            order.status = OrderStatus.FILLED

        return trades

    def _match_limit_order(self, order: Order) -> List[Trade]:
        """Match a limit order against the book."""
        trades = []

        if order.side == OrderSide.BUY:
            # Buy limit: match against asks at or below limit price
            while order.remaining_quantity > 0 and self._asks:
                price, timestamp, order_id, resting_order = self._asks[0]

                if price > order.price:
                    break  # No more matchable orders

                heapq.heappop(self._asks)

                if not resting_order.is_active:
                    continue

                trade = self._execute_match(order, resting_order, price)
                if trade:
                    trades.append(trade)

                if resting_order.remaining_quantity > 0:
                    self._add_to_book(resting_order)

        else:  # SELL
            # Sell limit: match against bids at or above limit price
            while order.remaining_quantity > 0 and self._bids:
                neg_price, timestamp, order_id, resting_order = self._bids[0]
                price = -neg_price

                if price < order.price:
                    break

                heapq.heappop(self._bids)

                if not resting_order.is_active:
                    continue

                trade = self._execute_match(order, resting_order, price)
                if trade:
                    trades.append(trade)

                if resting_order.remaining_quantity > 0:
                    self._add_to_book(resting_order)

        return trades

    def _execute_match(
        self,
        aggressor: Order,
        resting: Order,
        price: float
    ) -> Optional[Trade]:
        """Execute a match between two orders."""
        fill_qty = min(aggressor.remaining_quantity, resting.remaining_quantity)

        if fill_qty <= 0:
            return None

        trade_id = str(uuid.uuid4())[:8]

        # Determine buyer/seller
        if aggressor.side == OrderSide.BUY:
            buyer_order = aggressor
            seller_order = resting
        else:
            buyer_order = resting
            seller_order = aggressor

        trade = Trade(
            trade_id=trade_id,
            symbol=self.symbol,
            buyer_order_id=buyer_order.order_id,
            seller_order_id=seller_order.order_id,
            buyer_agent_id=buyer_order.agent_id,
            seller_agent_id=seller_order.agent_id,
            price=price,
            quantity=fill_qty
        )

        # Update orders
        for order in [aggressor, resting]:
            order.filled_quantity += fill_qty
            total_value = order.filled_price * (order.filled_quantity - fill_qty) + price * fill_qty
            order.filled_price = total_value / order.filled_quantity
            order.updated_at = datetime.utcnow()
            order.fills.append({
                "trade_id": trade_id,
                "price": price,
                "quantity": fill_qty,
                "timestamp": trade.timestamp.isoformat()
            })

            if order.remaining_quantity == 0:
                order.status = OrderStatus.FILLED
            else:
                order.status = OrderStatus.PARTIAL

        self._trades.append(trade)
        self.last_price = price

        return trade

    def _add_to_book(self, order: Order):
        """Add an order to the order book."""
        if order.side == OrderSide.BUY:
            heapq.heappush(
                self._bids,
                (-order.price, order.created_at, order.order_id, order)
            )
        else:
            heapq.heappush(
                self._asks,
                (order.price, order.created_at, order.order_id, order)
            )

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancelled successfully
        """
        if order_id not in self._orders:
            return False

        order = self._orders[order_id]
        if not order.is_active:
            return False

        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.utcnow()
        return True

    def get_best_bid(self) -> Optional[float]:
        """Get best bid price."""
        # Clean up inactive orders
        while self._bids and not self._bids[0][3].is_active:
            heapq.heappop(self._bids)

        if self._bids:
            return -self._bids[0][0]
        return None

    def get_best_ask(self) -> Optional[float]:
        """Get best ask price."""
        while self._asks and not self._asks[0][3].is_active:
            heapq.heappop(self._asks)

        if self._asks:
            return self._asks[0][0]
        return None

    def get_spread(self) -> Optional[Tuple[float, float]]:
        """Get bid-ask spread (absolute and percentage)."""
        bid = self.get_best_bid()
        ask = self.get_best_ask()

        if bid is None or ask is None:
            return None

        spread_abs = ask - bid
        spread_pct = spread_abs / ((bid + ask) / 2) * 100

        return (spread_abs, spread_pct)

    def get_depth(self, levels: int = 5) -> Dict[str, List[OrderBookLevel]]:
        """
        Get order book depth.

        Args:
            levels: Number of price levels to return

        Returns:
            Dictionary with bids and asks
        """
        bid_levels = defaultdict(lambda: {"quantity": 0.0, "count": 0})
        ask_levels = defaultdict(lambda: {"quantity": 0.0, "count": 0})

        for neg_price, _, _, order in self._bids:
            if order.is_active:
                price = -neg_price
                bid_levels[price]["quantity"] += order.remaining_quantity
                bid_levels[price]["count"] += 1

        for price, _, _, order in self._asks:
            if order.is_active:
                ask_levels[price]["quantity"] += order.remaining_quantity
                ask_levels[price]["count"] += 1

        # Sort and limit
        sorted_bids = sorted(bid_levels.items(), key=lambda x: -x[0])[:levels]
        sorted_asks = sorted(ask_levels.items(), key=lambda x: x[0])[:levels]

        return {
            "bids": [
                OrderBookLevel(price=p, quantity=d["quantity"], order_count=d["count"]).to_dict()
                for p, d in sorted_bids
            ],
            "asks": [
                OrderBookLevel(price=p, quantity=d["quantity"], order_count=d["count"]).to_dict()
                for p, d in sorted_asks
            ],
            "last_price": self.last_price,
            "spread": self.get_spread()
        }

    def get_recent_trades(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent trades."""
        return [t.to_dict() for t in self._trades[-limit:]]


class MatchingEngine:
    """
    Multi-symbol matching engine.

    Usage:
        engine = MatchingEngine()

        # Submit orders
        order = engine.submit_order(
            agent_id="agent1",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=150.00
        )

        # Get order book
        depth = engine.get_order_book("AAPL")

        # Get trades
        trades = engine.get_trades("AAPL")
    """

    def __init__(self, enable_logging: bool = True):
        """
        Initialize matching engine.

        Args:
            enable_logging: Enable trade logging
        """
        self.enable_logging = enable_logging
        self._books: Dict[str, OrderBook] = {}
        self._agent_orders: Dict[str, List[str]] = defaultdict(list)
        self._order_count = 0

    def _get_or_create_book(self, symbol: str) -> OrderBook:
        """Get or create an order book for a symbol."""
        if symbol not in self._books:
            self._books[symbol] = OrderBook(symbol)
        return self._books[symbol]

    def submit_order(
        self,
        agent_id: str,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Tuple[Order, List[Trade]]:
        """
        Submit an order to the matching engine.

        Args:
            agent_id: Agent submitting the order
            symbol: Trading symbol
            side: Buy or sell
            order_type: Order type
            quantity: Order quantity
            price: Limit price (required for limit orders)
            stop_price: Stop price (for stop orders)

        Returns:
            Tuple of (Order, List[Trade])
        """
        self._order_count += 1
        order_id = f"ORD-{self._order_count:08d}"

        order = Order(
            order_id=order_id,
            agent_id=agent_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price
        )

        # Validate
        if order_type == OrderType.LIMIT and price is None:
            order.status = OrderStatus.REJECTED
            return order, []

        if quantity <= 0:
            order.status = OrderStatus.REJECTED
            return order, []

        # Submit to book
        book = self._get_or_create_book(symbol)
        trades = book.add_order(order)

        self._agent_orders[agent_id].append(order_id)

        if self.enable_logging:
            logger.debug(
                f"Order {order_id}: {side.value.upper()} {quantity} {symbol} "
                f"@ {price or 'MARKET'} -> {order.status.value}"
            )
            if trades:
                logger.debug(f"  Executed {len(trades)} trades")

        return order, trades

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order ID
            symbol: Symbol (for book lookup)

        Returns:
            True if cancelled
        """
        if symbol not in self._books:
            return False

        return self._books[symbol].cancel_order(order_id)

    def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """Get an order by ID."""
        if symbol not in self._books:
            return None
        return self._books[symbol]._orders.get(order_id)

    def get_order_book(self, symbol: str, levels: int = 5) -> Dict[str, Any]:
        """Get order book depth."""
        if symbol not in self._books:
            return {"symbol": symbol, "bids": [], "asks": []}

        depth = self._books[symbol].get_depth(levels)
        depth["symbol"] = symbol
        return depth

    def get_trades(
        self,
        symbol: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent trades for a symbol."""
        if symbol not in self._books:
            return []
        return self._books[symbol].get_recent_trades(limit)

    def get_agent_orders(
        self,
        agent_id: str,
        symbol: Optional[str] = None,
        active_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get orders for an agent."""
        order_ids = self._agent_orders.get(agent_id, [])
        orders = []

        for oid in order_ids:
            for book in self._books.values():
                if symbol and book.symbol != symbol:
                    continue
                order = book._orders.get(oid)
                if order:
                    if active_only and not order.is_active:
                        continue
                    orders.append(order.to_dict())

        return orders

    def get_market_summary(self, symbol: str) -> Dict[str, Any]:
        """Get market summary for a symbol."""
        if symbol not in self._books:
            return {"symbol": symbol, "error": "no_book"}

        book = self._books[symbol]
        trades = book._trades

        if not trades:
            return {
                "symbol": symbol,
                "last_price": None,
                "volume_24h": 0,
                "trade_count_24h": 0,
                "bid": book.get_best_bid(),
                "ask": book.get_best_ask()
            }

        # Calculate 24h stats
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_trades = [t for t in trades if t.timestamp > cutoff]

        volume = sum(t.quantity for t in recent_trades)
        high = max((t.price for t in recent_trades), default=0)
        low = min((t.price for t in recent_trades), default=0)

        return {
            "symbol": symbol,
            "last_price": book.last_price,
            "bid": book.get_best_bid(),
            "ask": book.get_best_ask(),
            "spread": book.get_spread(),
            "volume_24h": round(volume, 8),
            "trade_count_24h": len(recent_trades),
            "high_24h": high,
            "low_24h": low
        }

    def simulate_market_impact(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float
    ) -> Dict[str, Any]:
        """
        Simulate market impact of a large order.

        Args:
            symbol: Trading symbol
            side: Buy or sell
            quantity: Order quantity

        Returns:
            Impact analysis
        """
        if symbol not in self._books:
            return {"error": "no_book"}

        book = self._books[symbol]
        depth = book.get_depth(20)

        levels = depth["asks"] if side == OrderSide.BUY else depth["bids"]
        if not levels:
            return {"error": "no_liquidity"}

        remaining = quantity
        total_cost = 0.0
        levels_consumed = 0

        for level in levels:
            take_qty = min(remaining, level["quantity"])
            total_cost += take_qty * level["price"]
            remaining -= take_qty
            levels_consumed += 1

            if remaining <= 0:
                break

        if remaining > 0:
            return {
                "error": "insufficient_liquidity",
                "available": quantity - remaining,
                "shortfall": remaining
            }

        avg_price = total_cost / quantity
        best_price = levels[0]["price"]
        slippage = abs(avg_price - best_price) / best_price * 100

        return {
            "symbol": symbol,
            "side": side.value,
            "quantity": quantity,
            "estimated_avg_price": round(avg_price, 8),
            "best_available_price": best_price,
            "slippage_percent": round(slippage, 4),
            "levels_consumed": levels_consumed,
            "total_cost": round(total_cost, 8)
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics."""
        total_orders = sum(len(b._orders) for b in self._books.values())
        total_trades = sum(len(b._trades) for b in self._books.values())

        return {
            "symbols": list(self._books.keys()),
            "total_orders": total_orders,
            "total_trades": total_trades,
            "active_agents": len(self._agent_orders)
        }

    def clear_symbol(self, symbol: str):
        """Clear all data for a symbol."""
        if symbol in self._books:
            del self._books[symbol]

    def clear_all(self):
        """Clear all order books."""
        self._books.clear()
        self._agent_orders.clear()
        self._order_count = 0
