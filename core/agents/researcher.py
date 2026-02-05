"""
Researcher Agent - Gathers market intelligence
"""

from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
import aiohttp
import os


class ResearcherAgent:
    """
    Researcher Agent - Gathers and synthesizes market intelligence

    Sources:
    - News sentiment (CryptoPanic, NewsAPI)
    - Social media trends (Reddit public API)
    - On-chain metrics (CoinGecko, blockchain explorers)
    - Economic indicators (Public APIs)
    """

    def __init__(self, llm):
        self.llm = llm
        self.session: Optional[aiohttp.ClientSession] = None

        # API keys (optional)
        self.newsapi_key = os.getenv("NEWSAPI_KEY", "")
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID", "")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")

        # Symbol mapping for social media
        self.symbol_map = {
            'BTC': ['bitcoin', 'btc'],
            'ETH': ['ethereum', 'eth'],
            'SOL': ['solana', 'sol'],
            'BNB': ['binance', 'bnb'],
            'ADA': ['cardano', 'ada'],
            'DOT': ['polkadot', 'dot'],
            'MATIC': ['polygon', 'matic'],
            'AVAX': ['avalanche', 'avax']
        }

        logger.info("✓ Researcher agent initialized")

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def research(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Conduct research on a symbol

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            market_data: Current market data

        Returns:
            Research summary with sentiment score
        """
        logger.info(f"🔍 Researching {symbol}...")

        try:
            # Gather multi-source intelligence
            news_sentiment = await self._get_news_sentiment(symbol)
            social_sentiment = await self._get_social_sentiment(symbol)
            onchain_metrics = await self._get_onchain_metrics(symbol)
            rpc_snapshot = market_data.get("onchain", {}) if isinstance(market_data, dict) else {}
            if rpc_snapshot:
                onchain_metrics["rpc_snapshot"] = rpc_snapshot
                onchain_metrics["rpc_source"] = "chain_rpc"
            macro_factors = await self._get_macro_factors()

            # Calculate aggregate sentiment
            sentiment = self._calculate_sentiment(
                news_sentiment,
                social_sentiment,
                onchain_metrics
            )

            # Generate summary
            summary = await self._generate_summary(
                symbol=symbol,
                news=news_sentiment,
                social=social_sentiment,
                onchain=onchain_metrics,
                macro=macro_factors,
                sentiment=sentiment
            )

            return {
                "summary": summary,
                "sentiment": sentiment,
                "news": news_sentiment,
                "social": social_sentiment,
                "onchain": onchain_metrics,
                "macro": macro_factors,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Research error: {e}", exc_info=True)
            return {
                "summary": f"Research failed for {symbol}: {str(e)}",
                "sentiment": 0.0,
                "error": str(e)
            }

    async def _get_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get news sentiment from various sources"""
        await self._ensure_session()

        base_symbol = symbol.split("/")[0]
        search_terms = self.symbol_map.get(base_symbol, [base_symbol.lower()])

        articles = []
        total_sentiment = 0.0
        sentiment_count = 0

        try:
            # Fetch from CryptoPanic (free public API)
            crypto_panic_url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                'auth_token': 'free',  # Public free tier
                'currencies': base_symbol,
                'kind': 'news',
                'filter': 'important'
            }

            async with self.session.get(crypto_panic_url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    for post in data.get('results', [])[:10]:
                        # Simple sentiment based on votes
                        votes = post.get('votes', {})
                        positive = votes.get('positive', 0)
                        negative = votes.get('negative', 0)

                        if positive + negative > 0:
                            sentiment = (positive - negative) / (positive + negative)
                        else:
                            sentiment = 0.0

                        articles.append({
                            'title': post.get('title', ''),
                            'url': post.get('url', ''),
                            'published_at': post.get('published_at', ''),
                            'sentiment': sentiment
                        })

                        total_sentiment += sentiment
                        sentiment_count += 1

        except Exception as e:
            logger.debug(f"CryptoPanic API error: {e}")

        # Calculate average sentiment
        avg_sentiment = total_sentiment / sentiment_count if sentiment_count > 0 else 0.0

        # Extract keywords from titles
        keywords = self._extract_keywords(articles)

        return {
            "score": max(-1.0, min(1.0, avg_sentiment)),
            "articles": articles[:5],  # Top 5 articles
            "keywords": keywords,
            "source": "cryptopanic"
        }

    async def _get_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get social media sentiment from Reddit"""
        await self._ensure_session()

        base_symbol = symbol.split("/")[0]
        search_terms = self.symbol_map.get(base_symbol, [base_symbol.lower()])

        # Reddit subreddits to check
        subreddits = ['CryptoCurrency', 'Bitcoin', 'ethereum', 'CryptoMarkets']

        total_posts = 0
        total_sentiment = 0.0
        trending_score = 0

        try:
            for subreddit in subreddits:
                # Use Reddit's public JSON API (no auth required)
                url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                headers = {'User-Agent': 'SIGMAX Bot 1.0'}

                async with self.session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()

                        for post in data.get('data', {}).get('children', []):
                            post_data = post.get('data', {})
                            title = post_data.get('title', '').lower()

                            # Check if post mentions our symbol
                            if any(term in title for term in search_terms):
                                total_posts += 1

                                # Simple sentiment from upvote ratio
                                upvote_ratio = post_data.get('upvote_ratio', 0.5)
                                sentiment = (upvote_ratio - 0.5) * 2  # Scale to [-1, 1]

                                total_sentiment += sentiment

                                # Award count indicates trending
                                awards = post_data.get('total_awards_received', 0)
                                trending_score += awards

        except Exception as e:
            logger.debug(f"Reddit API error: {e}")

        # Calculate metrics
        avg_sentiment = total_sentiment / total_posts if total_posts > 0 else 0.0
        is_trending = trending_score > 5 or total_posts > 10

        return {
            "score": max(-1.0, min(1.0, avg_sentiment)),
            "trending": is_trending,
            "volume": total_posts,
            "platform": "reddit",
            "trending_score": trending_score
        }

    async def _get_onchain_metrics(self, symbol: str) -> Dict[str, Any]:
        """Get on-chain metrics from CoinGecko"""
        await self._ensure_session()

        base_symbol = symbol.split("/")[0]

        if base_symbol in symbol and not symbol.endswith("/USDT") and "/" not in symbol:
            base_symbol = symbol

        # CoinGecko coin ID mapping
        coin_id_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'SOL': 'solana',
            'BNB': 'binancecoin',
            'ADA': 'cardano',
            'DOT': 'polkadot',
            'MATIC': 'matic-network',
            'AVAX': 'avalanche-2'
        }

        coin_id = coin_id_map.get(base_symbol, base_symbol.lower())

        try:
            # Get on-chain data from CoinGecko (free tier)
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'community_data': 'true',
                'developer_data': 'true'
            }

            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    # Extract metrics
                    market_data = data.get('market_data', {})
                    community_data = data.get('community_data', {})
                    developer_data = data.get('developer_data', {})

                    # Estimate whale activity from price change and volume
                    price_change_24h = market_data.get('price_change_percentage_24h', 0)
                    volume_24h = market_data.get('total_volume', {}).get('usd', 0)
                    market_cap = market_data.get('market_cap', {}).get('usd', 1)

                    volume_to_mcap = volume_24h / market_cap if market_cap > 0 else 0

                    # Classify whale activity
                    if volume_to_mcap > 0.3 and price_change_24h > 5:
                        whale_activity = "bullish"
                    elif volume_to_mcap > 0.3 and price_change_24h < -5:
                        whale_activity = "bearish"
                    else:
                        whale_activity = "neutral"

                    return {
                        "market_cap": market_cap,
                        "volume_24h": volume_24h,
                        "price_change_24h": price_change_24h,
                        "whale_activity": whale_activity,
                        "volume_to_mcap_ratio": volume_to_mcap,
                        "reddit_subscribers": community_data.get('reddit_subscribers', 0),
                        "twitter_followers": community_data.get('twitter_followers', 0),
                        "github_commits_4w": developer_data.get('commit_count_4_weeks', 0),
                        "source": "coingecko"
                    }

        except Exception as e:
            logger.debug(f"CoinGecko API error: {e}")

        # Fallback
        return {
            "active_addresses": 0,
            "transaction_volume": 0.0,
            "whale_activity": "neutral",
            "exchange_flows": {"inflow": 0.0, "outflow": 0.0},
            "source": "fallback"
        }

    async def _get_macro_factors(self) -> Dict[str, Any]:
        """Get macroeconomic factors from public APIs"""
        await self._ensure_session()

        macro_data = {
            "fed_policy": "neutral",
            "dxy": 0.0,
            "vix": 0.0,
            "risk_on": True,
            "gold_price": 0.0,
            "spy_change": 0.0
        }

        try:
            # Get Fear & Greed Index
            url = "https://api.alternative.me/fng/"
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    fng_value = int(data['data'][0]['value'])

                    # Map fear/greed to risk sentiment
                    if fng_value > 60:
                        macro_data['risk_on'] = True
                        macro_data['fed_policy'] = "accommodative"
                    elif fng_value < 40:
                        macro_data['risk_on'] = False
                        macro_data['fed_policy'] = "restrictive"
                    else:
                        macro_data['risk_on'] = True
                        macro_data['fed_policy'] = "neutral"

                    macro_data['fear_greed_index'] = fng_value

        except Exception as e:
            logger.debug(f"Macro data fetch error: {e}")

        return macro_data

    def _extract_keywords(self, articles: list) -> list:
        """Extract common keywords from article titles"""
        from collections import Counter
        import re

        # Common words to exclude
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'as'}

        all_words = []
        for article in articles:
            title = article.get('title', '').lower()
            words = re.findall(r'\b\w+\b', title)
            all_words.extend([w for w in words if w not in stop_words and len(w) > 3])

        # Get top 5 most common keywords
        word_counts = Counter(all_words)
        return [word for word, count in word_counts.most_common(5)]

    def _calculate_sentiment(
        self,
        news: Dict[str, Any],
        social: Dict[str, Any],
        onchain: Dict[str, Any]
    ) -> float:
        """
        Calculate aggregate sentiment score

        Returns:
            Float between -1.0 (very bearish) and 1.0 (very bullish)
        """
        weights = {
            "news": 0.4,
            "social": 0.3,
            "onchain": 0.3
        }

        sentiment = (
            news.get("score", 0.0) * weights["news"] +
            social.get("score", 0.0) * weights["social"] +
            self._onchain_to_sentiment(onchain) * weights["onchain"]
        )

        return max(-1.0, min(1.0, sentiment))

    def _onchain_to_sentiment(self, onchain: Dict[str, Any]) -> float:
        """Convert on-chain metrics to sentiment score"""
        # Simple heuristic: more whale activity = more bullish
        whale_map = {
            "bullish": 0.5,
            "neutral": 0.0,
            "bearish": -0.5
        }

        return whale_map.get(onchain.get("whale_activity", "neutral"), 0.0)

    async def _generate_summary(
        self,
        symbol: str,
        news: Dict[str, Any],
        social: Dict[str, Any],
        onchain: Dict[str, Any],
        macro: Dict[str, Any],
        sentiment: float
    ) -> str:
        """Generate human-readable research summary"""

        if self.llm:
            prompt = f"""
Summarize the market intelligence for {symbol}:

News Sentiment: {news.get('score', 0.0):.2f}
Social Sentiment: {social.get('score', 0.0):.2f}
On-Chain Activity: {onchain.get('whale_activity', 'neutral')}
Macro Environment: {macro.get('fed_policy', 'neutral')}

Aggregate Sentiment: {sentiment:.2f}

Provide a 2-3 sentence summary of the key findings and overall market sentiment.
"""
            try:
                from langchain_core.messages import HumanMessage, SystemMessage
                response = await self.llm.ainvoke([
                    SystemMessage(content="You are a market research analyst"),
                    HumanMessage(content=prompt)
                ])
                return response.content
            except Exception as e:
                logger.warning(f"LLM summary failed: {e}")

        # Fallback summary
        sentiment_label = "BULLISH" if sentiment > 0.2 else "BEARISH" if sentiment < -0.2 else "NEUTRAL"

        return f"""
{symbol} Market Research Summary:

Overall Sentiment: {sentiment_label} ({sentiment:.2f})
- News sentiment: {news.get('score', 0.0):.2f}
- Social buzz: {'High' if social.get('trending') else 'Normal'}
- On-chain activity: {onchain.get('whale_activity', 'neutral')}
- Macro environment: {macro.get('fed_policy', 'neutral')}

Key Insight: Market sentiment is {sentiment_label.lower()} based on multi-source intelligence.
"""
