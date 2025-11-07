"""Sentiment Agent - Advanced Multi-Source Sentiment Analysis"""

from typing import Dict, Any, List
from datetime import datetime
from loguru import logger
from math import tanh, sqrt


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
        classification = self._classify_sentiment(aggregate_score)

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
            "classification": classification,
            "sentiment_label": classification,
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
        """Analyze news sentiment"""
        # TODO: Integrate with CryptoPanic, NewsAPI, etc.

        # Mock news headlines for demonstration
        mock_headlines = [
            f"{symbol} breaks resistance, traders optimistic",
            f"Institutions accumulating {symbol}",
            f"{symbol} faces headwinds from regulation",
        ]

        # Calculate sentiment from headlines
        total_score = 0
        headline_scores = []

        for headline in mock_headlines:
            score = self._score_text(headline)
            headline_scores.append({
                "headline": headline,
                "score": score
            })
            total_score += score

        avg_score = total_score / len(mock_headlines) if mock_headlines else 0

        return {
            "score": avg_score,
            "article_count": len(mock_headlines),
            "top_headlines": headline_scores[:5],
            "source": "news_aggregator"
        }

    async def _analyze_social(
        self,
        symbol: str,
        lookback_hours: int
    ) -> Dict[str, Any]:
        """Analyze social media sentiment"""
        # TODO: Integrate with Twitter API, Reddit API

        # Mock social mentions
        mock_posts = [
            f"{symbol} to the moon! 🚀",
            f"Selling my {symbol}, too risky",
            f"{symbol} looking strong on the charts",
        ]

        total_score = 0
        post_scores = []

        for post in mock_posts:
            score = self._score_text(post)
            post_scores.append({
                "text": post,
                "score": score
            })
            total_score += score

        avg_score = total_score / len(mock_posts) if mock_posts else 0

        # Check if trending
        trending = abs(avg_score) > 0.5

        return {
            "score": avg_score,
            "mention_count": len(mock_posts),
            "trending": trending,
            "top_posts": post_scores[:5],
            "source": "social_media"
        }

    async def _analyze_onchain(self, symbol: str) -> Dict[str, Any]:
        """Analyze on-chain metrics for sentiment"""
        # TODO: Integrate with The Graph, GoldRush, etc.

        # Mock on-chain data
        mock_metrics = {
            "exchange_inflow": 1000,  # BTC flowing INTO exchanges (bearish)
            "exchange_outflow": 1500,  # BTC flowing OUT of exchanges (bullish)
            "whale_transactions": 50,
            "active_addresses": 95000,
            "transaction_volume": 5000000
        }

        # Calculate sentiment from flows
        net_flow = mock_metrics['exchange_outflow'] - mock_metrics['exchange_inflow']
        flow_score = tanh(net_flow / 1000)  # Normalize with tanh

        # Whale activity (neutral to bullish if accumulating)
        whale_score = 0.3 if mock_metrics['whale_transactions'] > 40 else 0

        # Active addresses (more activity = bullish)
        activity_score = 0.2 if mock_metrics['active_addresses'] > 90000 else -0.1

        total_score = (flow_score * 0.5 + whale_score * 0.3 + activity_score * 0.2)

        return {
            "score": total_score,
            "metrics": mock_metrics,
            "exchange_flow": {
                "inflow": mock_metrics["exchange_inflow"],
                "outflow": mock_metrics["exchange_outflow"],
                "net": net_flow
            },
            "interpretation": {
                "flow": "bullish" if net_flow > 0 else "bearish",
                "whale_activity": "active" if whale_score > 0 else "quiet",
                "network_activity": "high" if activity_score > 0 else "low"
            },
            "source": "onchain"
        }

    async def _get_fear_greed_index(self) -> Dict[str, Any]:
        """Get Fear & Greed index"""
        # TODO: Integrate with actual Fear & Greed API

        # Mock index (0-100, where 0=extreme fear, 100=extreme greed)
        mock_index = 55

        # Normalize to -1 to 1 scale
        normalized = (mock_index - 50) / 50

        classification = (
            "extreme_fear" if mock_index < 25 else
            "fear" if mock_index < 45 else
            "neutral" if mock_index < 55 else
            "greed" if mock_index < 75 else
            "extreme_greed"
        )

        return {
            "index": mock_index,
            "normalized_score": normalized,
            "classification": classification,
            "source": "fear_greed_index"
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
        normalized_score = tanh(score / 5)

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
        variance = _variance(scores)
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

        classification = self._classify_sentiment(aggregate_score)

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
        return f"""
{symbol} Sentiment Analysis:

Overall: {classification.upper().replace('_', ' ')} ({aggregate_score:+.2f})

Market mood is {classification.replace('_', ' ')} with Fear & Greed at {fear_greed['index']}/100.
News coverage is {('positive' if news['score'] > 0 else 'negative')},
social media is {('bullish' if social['score'] > 0 else 'bearish')},
and on-chain metrics show {onchain['interpretation']['flow']} flow.
"""

    async def get_sentiment_trend(self, periods: int = 10) -> Dict[str, Any]:
        """Get sentiment trend over recent periods"""
        if len(self.sentiment_history) < 2:
            return {"trend": "unknown", "direction": "unknown", "change": 0}

        recent = self.sentiment_history[-periods:]
        scores = [s['aggregate_score'] for s in recent]

        # Calculate trend
        if len(scores) < 2:
            return {"trend": "unknown", "direction": "unknown", "change": 0}

        change = scores[-1] - scores[0]

        trend = (
            "improving" if change > 0.1 else
            "deteriorating" if change < -0.1 else
            "stable"
        )

        return {
            "trend": trend,
            "direction": trend,
            "change": change,
            "current": scores[-1],
            "previous": scores[0],
            "volatility": _std(scores)
        }


def _variance(values: List[float]) -> float:
    if not values:
        return 0.0

    mean = sum(values) / len(values)
    return sum((value - mean) ** 2 for value in values) / len(values)


def _std(values: List[float]) -> float:
    return sqrt(_variance(values))
