"""Test fixtures and mock data for development"""

from typing import Dict, List
import random
from datetime import datetime, timedelta


class MockMarketData:
    """Centralized mock market data generator"""

    # Base prices - single source of truth
    BASE_PRICES = {
        "BTC/USDT": 95000.0,
        "ETH/USDT": 3500.0,
        "SOL/USDT": 180.0,
        "USDT": 1.0
    }

    @classmethod
    def get_price(cls, symbol: str, volatility: float = 0.02) -> float:
        """
        Get mock price with random walk

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            volatility: Price volatility as decimal (default 2%)

        Returns:
            Current mock price
        """
        base_price = cls.BASE_PRICES.get(symbol, 100.0)
        return base_price * (1 + random.uniform(-volatility, volatility))

    @classmethod
    def generate_ohlcv(
        cls,
        symbol: str,
        periods: int = 100,
        timeframe_minutes: int = 60
    ) -> List[List[float]]:
        """
        Generate realistic OHLCV data with random walk

        Args:
            symbol: Trading pair
            periods: Number of candles to generate
            timeframe_minutes: Minutes per candle

        Returns:
            List of OHLCV candles [timestamp, open, high, low, close, volume]
        """
        base_price = cls.BASE_PRICES.get(symbol, 100.0)

        ohlcv = []
        current_price = base_price
        timestamp = datetime.now() - timedelta(minutes=periods * timeframe_minutes)

        for _ in range(periods):
            # Random walk with slight upward drift
            change = random.gauss(0.0002, 0.015)  # Slight upward bias
            current_price *= (1 + change)

            # Generate OHLCV
            open_price = current_price
            high = open_price * random.uniform(1.0, 1.02)
            low = open_price * random.uniform(0.98, 1.0)
            close = random.uniform(low, high)
            volume = random.uniform(1e6, 1e8)

            ohlcv.append([
                int(timestamp.timestamp() * 1000),
                open_price,
                high,
                low,
                close,
                volume
            ])

            current_price = close
            timestamp += timedelta(minutes=timeframe_minutes)

        return ohlcv

    @classmethod
    def generate_market_data_dict(cls, symbol: str) -> Dict:
        """
        Generate complete market data dict

        Args:
            symbol: Trading pair

        Returns:
            Market data dict matching DataModule format
        """
        price = cls.get_price(symbol)

        return {
            "symbol": symbol,
            "price": price,
            "volume_24h": random.uniform(1e8, 1e9),
            "change_24h": random.uniform(-5, 5),
            "high_24h": price * 1.03,
            "low_24h": price * 0.97,
            "bid": price * 0.999,
            "ask": price * 1.001,
            "spread": price * 0.002,
            "ohlcv": cls.generate_ohlcv(symbol),
            "orderbook": {"bids": [], "asks": []},
            "timestamp": datetime.now().isoformat()
        }

    @classmethod
    def generate_orderbook(
        cls,
        symbol: str,
        depth: int = 20
    ) -> Dict:
        """
        Generate realistic orderbook

        Args:
            symbol: Trading pair
            depth: Number of levels per side

        Returns:
            Orderbook with bids and asks
        """
        price = cls.get_price(symbol)
        tick_size = price * 0.0001  # 0.01% tick size

        bids = []
        asks = []

        for i in range(depth):
            # Bids below current price
            bid_price = price - (i + 1) * tick_size
            bid_size = random.uniform(0.1, 5.0)
            bids.append([bid_price, bid_size])

            # Asks above current price
            ask_price = price + (i + 1) * tick_size
            ask_size = random.uniform(0.1, 5.0)
            asks.append([ask_price, ask_size])

        return {
            "bids": bids,
            "asks": asks,
            "timestamp": int(datetime.now().timestamp() * 1000)
        }

    @classmethod
    def generate_portfolio(
        cls,
        total_value_usd: float = 50.0,
        symbols: List[str] = None
    ) -> Dict[str, float]:
        """
        Generate random portfolio allocation

        Args:
            total_value_usd: Total portfolio value in USD
            symbols: List of symbols to include

        Returns:
            Dict mapping symbol to value in USD
        """
        if not symbols:
            symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

        # Generate random weights that sum to 1
        weights = [random.random() for _ in symbols]
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        portfolio = {}
        for symbol, weight in zip(symbols, weights):
            portfolio[symbol] = total_value_usd * weight

        return portfolio

    @classmethod
    def generate_trade_history(
        cls,
        count: int = 10,
        symbols: List[str] = None
    ) -> List[Dict]:
        """
        Generate mock trade history

        Args:
            count: Number of trades to generate
            symbols: List of symbols to trade

        Returns:
            List of trade dicts
        """
        if not symbols:
            symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

        trades = []
        timestamp = datetime.now() - timedelta(days=1)

        for _ in range(count):
            symbol = random.choice(symbols)
            action = random.choice(["buy", "sell"])
            size = random.uniform(0.001, 0.1)
            price = cls.get_price(symbol)

            trades.append({
                "symbol": symbol,
                "action": action,
                "size": size,
                "price": price,
                "timestamp": timestamp.isoformat(),
                "pnl": random.uniform(-5, 10) if random.random() > 0.5 else 0
            })

            timestamp += timedelta(minutes=random.randint(10, 120))

        return trades


class MockLLMResponses:
    """Mock LLM responses for testing agents"""

    BULL_RESPONSES = [
        "Strong bullish momentum detected. Price breaking key resistance with high volume. "
        "Technical indicators show RSI at 65 and MACD crossover. Confidence: 0.75",

        "Excellent accumulation phase observed. Whale wallets increasing positions by 15% in 24h. "
        "On-chain metrics strongly bullish. Score: 0.8/10",

        "Positive market structure. Higher lows forming on 4H chart. "
        "Fibonacci retracement holding at 0.618 level. Buy signal confirmed."
    ]

    BEAR_RESPONSES = [
        "Bearish divergence on RSI. Price making higher highs but RSI making lower highs. "
        "Warning sign of trend exhaustion. Confidence: 0.7",

        "High risk of pullback. Price extended 25% above 200-day MA. "
        "Historical data shows corrections typically follow. Score: -0.65",

        "Negative funding rates and increasing short positions. "
        "Sell pressure building. Avoid at current levels."
    ]

    RESEARCH_RESPONSES = [
        "Market sentiment analysis: Twitter mentions up 45%, 65% positive. "
        "News coverage trending positive with 3 major announcements this week. "
        "Overall sentiment: 0.6",

        "On-chain analysis shows 12,000 BTC withdrawn from exchanges (bullish). "
        "Active addresses up 8%. Network growth strong. Aggregate score: 0.55",

        "Mixed signals: Social sentiment positive but derivatives market showing caution. "
        "Funding rates neutral. Recommendation: wait for confirmation."
    ]

    @classmethod
    def get_random_response(cls, agent_type: str) -> str:
        """Get random response for agent type"""
        if agent_type == "bull":
            return random.choice(cls.BULL_RESPONSES)
        elif agent_type == "bear":
            return random.choice(cls.BEAR_RESPONSES)
        elif agent_type == "research":
            return random.choice(cls.RESEARCH_RESPONSES)
        else:
            return "Analysis completed successfully."
