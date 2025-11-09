"""
News Sentiment Scanner

Monitors crypto news and computes sentiment scores.
Publishes NEWS signal events.

Integrates with:
- NewsAPI (general crypto news)
- CoinDesk RSS feeds
- CoinTelegraph API
"""

import asyncio
import sys
import signal as signal_module
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import feedparser
from bs4 import BeautifulSoup
import re

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from pkg.common import setup_logging, get_logger, load_config, get_metrics_collector
from pkg.schemas import SignalEvent, SignalType
from apps.signals.common import SignalPublisher


class NewsSentimentScanner:
    """News sentiment scanner signal module"""

    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("news_sentiment")

        # Publisher
        self.publisher = SignalPublisher(config, "news_sentiment")

        # API configuration
        self.newsapi_key = config.get("newsapi_key", "")
        self.session: Optional[aiohttp.ClientSession] = None

        # News sources
        self.rss_feeds = [
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://cointelegraph.com/rss",
            "https://decrypt.co/feed",
        ]

        # Sentiment keywords for simple analysis
        self.positive_keywords = [
            'bullish', 'surge', 'rally', 'gain', 'profit', 'success', 'growth',
            'breakthrough', 'adoption', 'partnership', 'upgrade', 'innovation',
            'milestone', 'record', 'boom', 'soar', 'rise', 'pump', 'moon'
        ]

        self.negative_keywords = [
            'bearish', 'crash', 'drop', 'loss', 'scam', 'hack', 'theft', 'fraud',
            'regulation', 'ban', 'lawsuit', 'investigation', 'collapse', 'fail',
            'dump', 'plunge', 'decline', 'fear', 'panic', 'risk'
        ]

        # Coin/token mapping for detection
        self.coin_keywords = {
            'BTC': ['bitcoin', 'btc'],
            'ETH': ['ethereum', 'eth', 'ether'],
            'SOL': ['solana', 'sol'],
            'BNB': ['binance', 'bnb'],
            'ADA': ['cardano', 'ada'],
            'DOT': ['polkadot', 'dot'],
            'MATIC': ['polygon', 'matic'],
            'AVAX': ['avalanche', 'avax']
        }

        self.running = False
        self.last_fetch_time = None
        
    async def start(self):
        """Start the scanner"""
        self.logger.info("starting_news_sentiment_scanner")

        # Create aiohttp session
        self.session = aiohttp.ClientSession()

        self.metrics.set_info(
            service="news_sentiment",
            status="active"
        )

        # Start publisher
        await self.publisher.start()

        self.running = True

        # Start polling loop
        asyncio.create_task(self._poll_loop())

        self.logger.info("news_sentiment_scanner_started")
        
    async def stop(self):
        """Stop the scanner"""
        self.logger.info("stopping_news_sentiment_scanner")
        self.running = False

        await self.publisher.stop()

        if self.session:
            await self.session.close()

        self.logger.info("news_sentiment_scanner_stopped")
    
    async def _poll_loop(self):
        """Poll for news and analyze sentiment"""
        self.logger.info("poll_loop_started")

        while self.running:
            try:
                # Fetch news from all sources
                news_items = await self._fetch_all_news()

                if news_items:
                    self.logger.info(f"fetched_{len(news_items)}_news_items")

                    # Analyze sentiment for each news item
                    for news in news_items:
                        sentiment_score = self._analyze_sentiment(news['title'], news.get('description', ''))
                        affected_coins = self._detect_coins(news['title'], news.get('description', ''))

                        # Publish signal for affected coins
                        for coin in affected_coins:
                            await self._publish_signal(coin, sentiment_score, news)

                    self.metrics.inc_counter("news_items_processed", value=len(news_items))

                # Sleep for 5 minutes before next poll
                await asyncio.sleep(300)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("poll_error", error=str(e), exc_info=True)
                await asyncio.sleep(60)

        self.logger.info("poll_loop_stopped")

    async def _fetch_all_news(self) -> List[Dict[str, Any]]:
        """Fetch news from all configured sources"""
        news_items = []

        # Fetch from RSS feeds
        for feed_url in self.rss_feeds:
            try:
                items = await self._fetch_rss_feed(feed_url)
                news_items.extend(items)
            except Exception as e:
                self.logger.warning(f"rss_fetch_error", feed=feed_url, error=str(e))

        # Fetch from NewsAPI if key is provided
        if self.newsapi_key:
            try:
                items = await self._fetch_newsapi()
                news_items.extend(items)
            except Exception as e:
                self.logger.warning("newsapi_fetch_error", error=str(e))

        # Remove duplicates and filter by time (last 24 hours)
        news_items = self._deduplicate_news(news_items)

        return news_items

    async def _fetch_rss_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """Fetch news from RSS feed"""
        items = []

        try:
            async with self.session.get(feed_url, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    feed = feedparser.parse(content)

                    for entry in feed.entries[:10]:  # Limit to 10 latest items
                        items.append({
                            'title': entry.get('title', ''),
                            'description': entry.get('summary', ''),
                            'url': entry.get('link', ''),
                            'published': entry.get('published', ''),
                            'source': feed_url
                        })
        except Exception as e:
            self.logger.debug(f"rss_parse_error", feed=feed_url, error=str(e))

        return items

    async def _fetch_newsapi(self) -> List[Dict[str, Any]]:
        """Fetch news from NewsAPI"""
        items = []

        url = "https://newsapi.org/v2/everything"
        params = {
            'apiKey': self.newsapi_key,
            'q': 'cryptocurrency OR bitcoin OR ethereum',
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 20
        }

        try:
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    for article in data.get('articles', []):
                        items.append({
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'url': article.get('url', ''),
                            'published': article.get('publishedAt', ''),
                            'source': 'newsapi'
                        })
        except Exception as e:
            self.logger.debug("newsapi_request_error", error=str(e))

        return items

    def _analyze_sentiment(self, title: str, description: str) -> float:
        """
        Analyze sentiment of news text using keyword matching

        Returns:
            Sentiment score from -1.0 (very negative) to 1.0 (very positive)
        """
        text = (title + " " + description).lower()

        # Count positive and negative keywords
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in text)

        # Calculate sentiment score
        total_count = positive_count + negative_count

        if total_count == 0:
            return 0.0  # Neutral

        sentiment = (positive_count - negative_count) / total_count

        return max(min(sentiment, 1.0), -1.0)  # Clamp to [-1, 1]

    def _detect_coins(self, title: str, description: str) -> List[str]:
        """Detect which coins are mentioned in the news"""
        text = (title + " " + description).lower()
        detected_coins = []

        for coin, keywords in self.coin_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    detected_coins.append(coin)
                    break

        return detected_coins if detected_coins else ['BTC']  # Default to BTC

    def _deduplicate_news(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate news items"""
        seen_titles = set()
        unique_items = []

        for item in news_items:
            title_key = item['title'][:50].lower()  # Use first 50 chars

            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_items.append(item)

        return unique_items

    async def _publish_signal(self, symbol: str, sentiment: float, news: Dict[str, Any]):
        """Publish news sentiment signal"""
        try:
            signal_event = SignalEvent(
                type=SignalType.NEWS,
                symbol=symbol,
                timestamp=datetime.utcnow(),
                value=sentiment,
                metadata={
                    'title': news['title'],
                    'url': news['url'],
                    'source': news['source'],
                    'sentiment': 'positive' if sentiment > 0.3 else 'negative' if sentiment < -0.3 else 'neutral'
                }
            )

            await self.publisher.publish(signal_event)

            self.logger.debug(
                "signal_published",
                symbol=symbol,
                sentiment=sentiment,
                title=news['title'][:50]
            )

        except Exception as e:
            self.logger.error("signal_publish_error", error=str(e))


async def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="SIGMAX News Sentiment Scanner")
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
    logger.info("sigmax_news_sentiment_starting")
    
    scanner = NewsSentimentScanner(config)
    
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
        logger.info("sigmax_news_sentiment_stopped")


if __name__ == "__main__":
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass
    
    asyncio.run(main())
