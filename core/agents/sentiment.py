"""
Sentiment Agent - Advanced Multi-Source Sentiment Analysis
"""

from typing import Dict, Any
from datetime import datetime
from loguru import logger
import os


class SentimentAgent:
    """
    Sentiment Agent - Aggregates sentiment from multiple sources

    Sources:
    - News headlines (CryptoPanic, NewsAPI)
    - Social media (Twitter, Reddit)
    - On-chain metrics (whale movements, exchange flows)
    - Fear & Greed index
    - Google Trends
    """

    def __init__(self, llm):
        self.llm = llm
        self.sentiment_history = []

        # Sentiment keyword dictionaries
        self.bullish_keywords = {
            'strong': 2, 'bullish': 2, 'moon': 2, 'rally': 2, 'surge': 2,
            'breakout': 1.5, 'upturn': 1.5, 'growth': 1, 'gain': 1, 'rise': 1,
            'green': 1, 'pump': 1, 'hodl': 1, 'buy': 1, 'accumulate': 1.5
        }

        self.bearish_keywords = {
            'weak': -2, 'bearish': -2, 'crash': -2, 'dump': -2, 'plunge': -2,
            'breakdown': -1.5, 'decline': -1.5, 'loss': -1, 'fall': -1, 'drop': -1,
            'red': -1, 'sell': -1, 'fear': -1, 'panic': -1.5, 'liquidation': -2
        }

        logger.info("✓ Sentiment agent initialized")

    async def analyze(
        self,
        symbol: str,
        lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Analyze sentiment from multiple sources

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            lookback_hours: Hours to look back for sentiment

        Returns:
            Comprehensive sentiment analysis
        """
        logger.info(f"📊 Analyzing sentiment for {symbol}...")

        base_symbol = symbol.split('/')[0]

        # Gather sentiment from various sources
        news_sentiment = await self._analyze_news(base_symbol, lookback_hours)
        social_sentiment = await self._analyze_social(base_symbol, lookback_hours)
        onchain_sentiment = await self._analyze_onchain(base_symbol)
        fear_greed = await self._get_fear_greed_index()

        # Weighted aggregation
        weights = {
            'news': 0.3,
            'social': 0.25,
            'onchain': 0.25,
            'fear_greed': 0.2
        }

        aggregate_score = (
            news_sentiment['score'] * weights['news'] +
            social_sentiment['score'] * weights['social'] +
            onchain_sentiment['score'] * weights['onchain'] +
            fear_greed['normalized_score'] * weights['fear_greed']
        )

        # Classify sentiment
        sentiment_label = self._classify_sentiment(aggregate_score)

        # Generate LLM-based summary if available
        summary = await self._generate_summary(
            symbol=symbol,
            aggregate_score=aggregate_score,
            news=news_sentiment,
            social=social_sentiment,
            onchain=onchain_sentiment,
            fear_greed=fear_greed
        )

        result = {
            "symbol": symbol,
            "aggregate_score": aggregate_score,
            "sentiment_label": sentiment_label,
            "classification": sentiment_label,  # Alias for backwards compatibility with tests
            "confidence": self._calculate_confidence(
                news_sentiment,
                social_sentiment,
                onchain_sentiment
            ),
            "sources": {
                "news": news_sentiment,
                "social": social_sentiment,
                "onchain": onchain_sentiment,
                "fear_greed": fear_greed
            },
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }

        # Store in history
        self.sentiment_history.append(result)

        # Keep only last 100 entries
        if len(self.sentiment_history) > 100:
            self.sentiment_history.pop(0)

        return result

    async def _analyze_news(
        self,
        symbol: str,
        lookback_hours: int
    ) -> Dict[str, Any]:
        """Analyze news sentiment using NewsAPI"""

        newsapi_key = os.getenv("NEWSAPI_KEY", "")

        headlines = []
        source = "news_aggregator_fallback"

        # Try NewsAPI if key is available
        if newsapi_key and newsapi_key != "":
            try:
                import aiohttp
                from datetime import datetime, timedelta

                # Calculate from date
                from_date = (datetime.now() - timedelta(hours=lookback_hours)).strftime("%Y-%m-%d")

                # Build query for crypto news about this symbol
                query = f"{symbol} OR cryptocurrency OR crypto"
                if symbol in ["BTC", "Bitcoin"]:
                    query = "Bitcoin OR BTC"
                elif symbol in ["ETH", "Ethereum"]:
                    query = "Ethereum OR ETH"

                async with aiohttp.ClientSession() as session:
                    params = {
                        "q": query,
                        "from": from_date,
                        "language": "en",
                        "sortBy": "publishedAt",
                        "pageSize": 20,
                        "apiKey": newsapi_key
                    }

                    async with session.get(
                        "https://newsapi.org/v2/everything",
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()

                            if data.get("status") == "ok" and data.get("articles"):
                                for article in data["articles"]:
                                    title = article.get("title", "")
                                    description = article.get("description", "")
                                    text = f"{title}. {description}"

                                    if text and len(text) > 10:
                                        headlines.append(text)

                                source = "newsapi"
                                logger.info(f"✓ Fetched {len(headlines)} news articles from NewsAPI")

                        elif response.status == 429:
                            logger.warning("NewsAPI rate limit exceeded")
                        elif response.status == 401:
                            logger.warning("NewsAPI authentication failed - check NEWSAPI_KEY")
                        else:
                            logger.warning(f"NewsAPI returned status {response.status}")

            except Exception as e:
                logger.warning(f"NewsAPI request failed: {e}")

        # Fallback to mock headlines if no real data
        if not headlines:
            headlines = [
                f"{symbol} breaks resistance, traders optimistic",
                f"Institutions accumulating {symbol}",
                f"{symbol} faces headwinds from regulation",
            ]
            source = "news_aggregator_fallback"
            logger.info("Using fallback news headlines")

        # Calculate sentiment from headlines
        total_score = 0
        headline_scores = []

        for headline in headlines:
            score = self._score_text(headline)
            headline_scores.append({
                "headline": headline[:100],  # Truncate long headlines
                "score": score
            })
            total_score += score

        avg_score = total_score / len(headlines) if headlines else 0

        return {
            "score": avg_score,
            "article_count": len(headlines),
            "top_headlines": headline_scores[:5],
            "source": source
        }

    async def _analyze_social(
        self,
        symbol: str,
        lookback_hours: int
    ) -> Dict[str, Any]:
        """Analyze social media sentiment using Reddit"""

        posts = []
        source = "social_media_fallback"

        # Try Reddit public JSON API (no auth required for read-only)
        try:
            import aiohttp
            import time

            # Map symbols to common crypto subreddits
            subreddits = ["cryptocurrency", "CryptoMarkets"]

            if symbol in ["BTC", "Bitcoin"]:
                subreddits.insert(0, "Bitcoin")
            elif symbol in ["ETH", "Ethereum"]:
                subreddits.insert(0, "ethereum")

            # Calculate time threshold
            time_threshold = time.time() - (lookback_hours * 3600)

            async with aiohttp.ClientSession() as session:
                for subreddit in subreddits[:2]:  # Limit to 2 subreddits
                    try:
                        # Search for symbol mentions
                        search_query = symbol.split("/")[0]  # Get base symbol (BTC from BTC/USDT)

                        url = f"https://www.reddit.com/r/{subreddit}/search.json"
                        params = {
                            "q": search_query,
                            "restrict_sr": "1",
                            "sort": "new",
                            "limit": 25,
                            "t": "day" if lookback_hours <= 24 else "week"
                        }

                        headers = {
                            "User-Agent": "SIGMAX-Trading-Bot/1.0"
                        }

                        async with session.get(
                            url,
                            params=params,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()

                                if data.get("data") and data["data"].get("children"):
                                    for post_data in data["data"]["children"]:
                                        post = post_data.get("data", {})

                                        # Check if post is within time range
                                        created = post.get("created_utc", 0)
                                        if created < time_threshold:
                                            continue

                                        # Get title and selftext
                                        title = post.get("title", "")
                                        body = post.get("selftext", "")
                                        text = f"{title}. {body}"[:500]  # Limit length

                                        if text and len(text) > 10:
                                            posts.append(text)

                                    source = "reddit"

                            elif response.status == 429:
                                logger.warning(f"Reddit rate limit exceeded for r/{subreddit}")
                            else:
                                logger.debug(f"Reddit API returned status {response.status} for r/{subreddit}")

                    except Exception as e:
                        logger.debug(f"Failed to fetch from r/{subreddit}: {e}")

                if posts:
                    logger.info(f"✓ Fetched {len(posts)} social posts from Reddit")

        except Exception as e:
            logger.warning(f"Reddit API request failed: {e}")

        # Fallback to mock posts if no real data
        if not posts:
            posts = [
                f"{symbol} to the moon! 🚀",
                f"Selling my {symbol}, too risky",
                f"{symbol} looking strong on the charts",
            ]
            source = "social_media_fallback"
            logger.info("Using fallback social posts")

        # Calculate sentiment from posts
        total_score = 0
        post_scores = []

        for post in posts:
            score = self._score_text(post)
            post_scores.append({
                "text": post[:100],  # Truncate for display
                "score": score
            })
            total_score += score

        avg_score = total_score / len(posts) if posts else 0

        # Check if trending (high volume or extreme sentiment)
        trending = (len(posts) > 20) or (abs(avg_score) > 0.5)

        return {
            "score": avg_score,
            "mention_count": len(posts),
            "trending": trending,
            "top_posts": post_scores[:5],
            "source": source
        }

    async def _analyze_onchain(
        self,
        symbol: str,
        rpc_snapshot: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze on-chain metrics for sentiment using GoldRush API"""

        goldrush_key = os.getenv("GOLDRUSH_API_KEY", "")

        # Mock metrics structure (will be populated from API if available)
        inflow = 1000
        outflow = 1500
        whale_transactions = 50
        active_addresses = 95000
        transaction_volume = 5000000
        source = "onchain_fallback"

        # Map symbols to contract addresses for major tokens
        # For now, we'll use simplified approach focusing on major chains
        base_symbol = symbol.split("/")[0].upper()

        # Try GoldRush API if key is available
        if goldrush_key and goldrush_key != "":
            try:
                import aiohttp

                # Map crypto symbols to chain names for GoldRush
                chain_map = {
                    "ETH": "eth-mainnet",
                    "BTC": None,  # Bitcoin not directly supported, use exchange data
                    "MATIC": "matic-mainnet",
                    "BNB": "bsc-mainnet",
                }

                chain_name = chain_map.get(base_symbol)

                if chain_name:
                    async with aiohttp.ClientSession() as session:
                        headers = {
                            "Authorization": f"Bearer {goldrush_key}"
                        }

                        # Fetch chain status for network activity metrics
                        url = f"https://api.covalenthq.com/v1/{chain_name}/block_v2/latest/"

                        async with session.get(
                            url,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=15)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()

                                if data.get("data") and data["data"].get("items"):
                                    block_data = data["data"]["items"][0]

                                    # Use block metrics as proxy for activity
                                    gas_used = block_data.get("gas_used", 0)
                                    gas_limit = block_data.get("gas_limit", 1)

                                    # High gas usage = high activity
                                    utilization = gas_used / gas_limit if gas_limit > 0 else 0

                                    # Simulate metrics based on chain activity
                                    if utilization > 0.7:
                                        active_addresses = 120000
                                        transaction_volume = 8000000
                                    elif utilization > 0.4:
                                        active_addresses = 95000
                                        transaction_volume = 5000000
                                    else:
                                        active_addresses = 70000
                                        transaction_volume = 3000000

                                    source = "goldrush"
                                    logger.info(f"✓ Fetched on-chain metrics from GoldRush ({chain_name})")

                            elif response.status == 401:
                                logger.warning("GoldRush API authentication failed - check GOLDRUSH_API_KEY")
                            elif response.status == 429:
                                logger.warning("GoldRush API rate limit exceeded")
                            else:
                                logger.debug(f"GoldRush API returned status {response.status}")

            except Exception as e:
                logger.warning(f"GoldRush API request failed: {e}")

        # If no API data, use mock values
        if source == "onchain_fallback":
            logger.info("Using fallback on-chain metrics")

        # Calculate sentiment from flows
        net_flow = outflow - inflow
        flow_score = np.tanh(net_flow / 1000)  # Normalize with tanh

        # Whale activity (neutral to bullish if accumulating)
        whale_score = 0.3 if whale_transactions > 40 else 0

        # Active addresses (more activity = bullish)
        activity_score = 0.2 if active_addresses > 90000 else -0.1

        total_score = (flow_score * 0.5 + whale_score * 0.3 + activity_score * 0.2)

        # Optional: adjust with RPC snapshot freshness/latency if provided.
        rpc_adjustment = 0.0
        if rpc_snapshot:
            latencies = []
            for chain_data in rpc_snapshot.values():
                latency = chain_data.get("rpc_latency_ms")
                if isinstance(latency, (int, float)):
                    latencies.append(latency)

            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                # High latency reduces confidence slightly.
                if avg_latency > 1000:
                    rpc_adjustment = -0.05
                elif avg_latency < 200:
                    rpc_adjustment = 0.02

        total_score = max(-1.0, min(1.0, total_score + rpc_adjustment))

        return {
            "score": total_score,
            "exchange_flow": {
                "inflow": inflow,
                "outflow": outflow,
                "net": net_flow
            },
            "metrics": {
                "whale_transactions": whale_transactions,
                "active_addresses": active_addresses,
                "transaction_volume": transaction_volume
            },
            "interpretation": {
                "flow": "bullish" if net_flow > 0 else "bearish",
                "whale_activity": "active" if whale_score > 0 else "quiet",
                "network_activity": "high" if activity_score > 0 else "low"
            },
            "source": source,
            "rpc_snapshot": rpc_snapshot or {},
            "rpc_adjustment": rpc_adjustment
        }

    async def _get_fear_greed_index(self) -> Dict[str, Any]:
        """Get Fear & Greed index from alternative.me API"""

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.alternative.me/fng/",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # API returns: {"data": [{"value": "55", "value_classification": "Neutral", "timestamp": "..."}]}
                        if data.get("data") and len(data["data"]) > 0:
                            fng_data = data["data"][0]
                            index = int(fng_data.get("value", 50))

                            # Normalize to -1 to 1 scale
                            normalized = (index - 50) / 50

                            classification = fng_data.get("value_classification", "neutral").lower().replace(" ", "_")

                            logger.info(f"✓ Fear & Greed Index: {index}/100 ({classification})")

                            return {
                                "index": index,
                                "normalized_score": normalized,
                                "classification": classification,
                                "timestamp": fng_data.get("timestamp"),
                                "source": "fear_greed_index"
                            }

                    logger.warning(f"Fear & Greed API returned status {response.status}")

        except Exception as e:
            logger.warning(f"Failed to fetch Fear & Greed index: {e}")

        # Fallback to neutral if API fails
        return {
            "index": 50,
            "normalized_score": 0.0,
            "classification": "neutral",
            "source": "fear_greed_index_fallback"
        }

    def _score_text(self, text: str) -> float:
        """Score text sentiment using keyword matching"""
        text_lower = text.lower()
        score = 0

        # Count bullish keywords
        for keyword, weight in self.bullish_keywords.items():
            if keyword in text_lower:
                score += weight

        # Count bearish keywords
        for keyword, weight in self.bearish_keywords.items():
            if keyword in text_lower:
                score += weight  # Already negative

        # Normalize to -1 to 1 range
        normalized_score = np.tanh(score / 5)

        return normalized_score

    def _classify_sentiment(self, score: float) -> str:
        """Classify aggregate sentiment score"""
        if score > 0.5:
            return "very_bullish"
        elif score > 0.2:
            return "bullish"
        elif score > -0.2:
            return "neutral"
        elif score > -0.5:
            return "bearish"
        else:
            return "very_bearish"

    def _calculate_confidence(
        self,
        news: Dict[str, Any],
        social: Dict[str, Any],
        onchain: Dict[str, Any]
    ) -> float:
        """Calculate confidence in sentiment analysis"""
        # High confidence if all sources agree
        scores = [news['score'], social['score'], onchain['score']]

        # Check agreement (low variance = high confidence)
        variance = np.var(scores)
        confidence = 1 / (1 + variance)

        # Boost confidence if there's a lot of data
        data_volume = (
            news.get('article_count', 0) +
            social.get('mention_count', 0)
        )

        volume_boost = min(data_volume / 100, 0.2)  # Max 0.2 boost

        return min(confidence + volume_boost, 1.0)

    async def _generate_summary(
        self,
        symbol: str,
        aggregate_score: float,
        news: Dict[str, Any],
        social: Dict[str, Any],
        onchain: Dict[str, Any],
        fear_greed: Dict[str, Any]
    ) -> str:
        """Generate LLM-based sentiment summary"""

        if self.llm:
            try:
                from langchain_core.messages import HumanMessage, SystemMessage

                prompt = f"""
Summarize the market sentiment for {symbol}:

Aggregate Sentiment Score: {aggregate_score:.2f}
News Sentiment: {news['score']:.2f} ({news['article_count']} articles)
Social Sentiment: {social['score']:.2f} ({social['mention_count']} mentions)
On-Chain: {onchain['score']:.2f}
Fear & Greed: {fear_greed['classification']} ({fear_greed['index']}/100)

Provide a 2-3 sentence summary of overall market sentiment and what it means for traders.
"""

                response = await self.llm.ainvoke([
                    SystemMessage(content="You are a market sentiment analyst"),
                    HumanMessage(content=prompt)
                ])

                return response.content

            except Exception as e:
                logger.warning(f"LLM summary failed: {e}")

        # Fallback summary
        sentiment_label = self._classify_sentiment(aggregate_score)

        return f"""
{symbol} Sentiment Analysis:

Overall: {sentiment_label.upper().replace('_', ' ')} ({aggregate_score:+.2f})

Market mood is {sentiment_label.replace('_', ' ')} with Fear & Greed at {fear_greed['index']}/100.
News coverage is {('positive' if news['score'] > 0 else 'negative')},
social media is {('bullish' if social['score'] > 0 else 'bearish')},
and on-chain metrics show {onchain['interpretation']['flow']} flow.
"""

    async def get_sentiment_trend(self, periods: int = 10) -> Dict[str, Any]:
        """Get sentiment trend over recent periods"""
        if len(self.sentiment_history) < 2:
            return {"trend": "unknown", "change": 0}

        recent = self.sentiment_history[-periods:]
        scores = [s['aggregate_score'] for s in recent]

        # Calculate trend
        if len(scores) < 2:
            return {"trend": "unknown", "change": 0}

        change = scores[-1] - scores[0]

        trend = (
            "improving" if change > 0.1 else
            "deteriorating" if change < -0.1 else
            "stable"
        )

        return {
            "trend": trend,
            "change": change,
            "current": scores[-1],
            "previous": scores[0],
            "volatility": np.std(scores)
        }


# Helper function for numpy operations
import numpy as np
