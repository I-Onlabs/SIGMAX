"""
Researcher Agent - Gathers market intelligence
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger


class ResearcherAgent:
    """
    Researcher Agent - Gathers and synthesizes market intelligence

    Sources:
    - News sentiment
    - Social media trends
    - On-chain metrics
    - Economic indicators
    """

    def __init__(self, llm):
        self.llm = llm
        logger.info("✓ Researcher agent initialized")

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
        # TODO: Integrate with news APIs (CryptoPanic, NewsAPI, etc.)
        return {
            "score": 0.0,
            "articles": [],
            "keywords": []
        }

    async def _get_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get social media sentiment"""
        # TODO: Integrate with Twitter API, Reddit API, etc.
        return {
            "score": 0.0,
            "trending": False,
            "volume": 0
        }

    async def _get_onchain_metrics(self, symbol: str) -> Dict[str, Any]:
        """Get on-chain metrics"""
        # TODO: Integrate with The Graph, GoldRush, etc.
        base_symbol = symbol.split("/")[0]

        return {
            "active_addresses": 0,
            "transaction_volume": 0.0,
            "whale_activity": "neutral",
            "exchange_flows": {"inflow": 0.0, "outflow": 0.0}
        }

    async def _get_macro_factors(self) -> Dict[str, Any]:
        """Get macroeconomic factors"""
        # TODO: Integrate with economic data APIs
        return {
            "fed_policy": "neutral",
            "dxy": 0.0,
            "vix": 0.0,
            "risk_on": True
        }

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
