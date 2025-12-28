"""
Autonomous Research Toolkit - Minimal Information Paradigm
Inspired by AI-Trader's autonomous information discovery

Instead of agents receiving pre-curated data, they use this toolkit
to independently search and synthesize information, testing true AI
reasoning capability.

Key Differences from Traditional Approach:
- Traditional: Agent receives pre-processed price, sentiment, news
- Autonomous: Agent decides WHAT to search for and HOW to interpret

This reduces human bias in data selection and provides better
evaluation of agent quality.
"""

from typing import Dict, Any, List, Optional, Protocol, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from enum import Enum
from loguru import logger
import asyncio


class ToolCategory(Enum):
    """Categories of research tools."""
    PRICE_DATA = "price_data"
    NEWS_SEARCH = "news_search"
    SENTIMENT = "sentiment"
    FUNDAMENTALS = "fundamentals"
    ON_CHAIN = "on_chain"
    SOCIAL = "social"
    TECHNICAL = "technical"


@dataclass
class ToolResult:
    """Result from a tool invocation."""
    tool_name: str
    success: bool
    data: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    latency_ms: float = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchQuery:
    """A search query with parameters."""
    query: str
    symbols: List[str] = field(default_factory=list)
    time_range: Optional[str] = None  # "1h", "1d", "1w", etc.
    sources: List[str] = field(default_factory=list)
    limit: int = 10


class BaseTool(ABC):
    """Base class for autonomous research tools."""

    def __init__(self, name: str, category: ToolCategory):
        self.name = name
        self.category = category
        self._call_count = 0
        self._total_latency = 0

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass

    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return f"{self.name} ({self.category.value})"

    @property
    def avg_latency(self) -> float:
        """Average latency in milliseconds."""
        if self._call_count == 0:
            return 0
        return self._total_latency / self._call_count


class PriceTool(BaseTool):
    """Tool for fetching current and historical prices."""

    def __init__(self, price_service=None):
        super().__init__("get_price", ToolCategory.PRICE_DATA)
        self.price_service = price_service

    async def execute(
        self,
        symbol: str,
        timeframe: str = "current",
        lookback: Optional[int] = None
    ) -> ToolResult:
        """
        Get price data for a symbol.

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            timeframe: "current", "1h", "4h", "1d"
            lookback: Number of candles for historical data
        """
        start = datetime.utcnow()

        try:
            if self.price_service:
                if timeframe == "current":
                    data = await self.price_service.get_current_price(symbol)
                else:
                    data = await self.price_service.get_ohlcv(
                        symbol, timeframe, lookback or 100
                    )
            else:
                # Mock response for testing
                data = {
                    "symbol": symbol,
                    "price": 0.0,
                    "timeframe": timeframe,
                    "timestamp": datetime.utcnow().isoformat()
                }

            latency = (datetime.utcnow() - start).total_seconds() * 1000
            self._call_count += 1
            self._total_latency += latency

            return ToolResult(
                tool_name=self.name,
                success=True,
                data=data,
                latency_ms=latency
            )

        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                error=str(e)
            )


class NewsTool(BaseTool):
    """Tool for searching news and announcements."""

    def __init__(self, news_service=None):
        super().__init__("search_news", ToolCategory.NEWS_SEARCH)
        self.news_service = news_service

    async def execute(
        self,
        query: str,
        symbols: Optional[List[str]] = None,
        time_range: str = "24h",
        limit: int = 10
    ) -> ToolResult:
        """
        Search for news articles.

        Args:
            query: Search query
            symbols: Filter by symbols
            time_range: Time range for news
            limit: Max results
        """
        start = datetime.utcnow()

        try:
            if self.news_service:
                data = await self.news_service.search(
                    query=query,
                    symbols=symbols,
                    time_range=time_range,
                    limit=limit
                )
            else:
                # Mock response
                data = {
                    "query": query,
                    "articles": [],
                    "total": 0
                }

            latency = (datetime.utcnow() - start).total_seconds() * 1000
            self._call_count += 1
            self._total_latency += latency

            return ToolResult(
                tool_name=self.name,
                success=True,
                data=data,
                latency_ms=latency
            )

        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                error=str(e)
            )


class SentimentTool(BaseTool):
    """Tool for analyzing market sentiment."""

    def __init__(self, sentiment_service=None):
        super().__init__("analyze_sentiment", ToolCategory.SENTIMENT)
        self.sentiment_service = sentiment_service

    async def execute(
        self,
        symbol: str,
        sources: Optional[List[str]] = None
    ) -> ToolResult:
        """
        Analyze sentiment for a symbol.

        Args:
            symbol: Symbol to analyze
            sources: Optional list of sources ("twitter", "reddit", "news")
        """
        start = datetime.utcnow()

        try:
            if self.sentiment_service:
                data = await self.sentiment_service.analyze(
                    symbol=symbol,
                    sources=sources or ["twitter", "reddit", "news"]
                )
            else:
                # Mock response
                data = {
                    "symbol": symbol,
                    "sentiment_score": 0.0,
                    "sources_analyzed": 0,
                    "confidence": 0.0
                }

            latency = (datetime.utcnow() - start).total_seconds() * 1000
            self._call_count += 1
            self._total_latency += latency

            return ToolResult(
                tool_name=self.name,
                success=True,
                data=data,
                latency_ms=latency
            )

        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                error=str(e)
            )


class FundamentalsTool(BaseTool):
    """Tool for fetching fundamental data."""

    def __init__(self, fundamentals_service=None):
        super().__init__("get_fundamentals", ToolCategory.FUNDAMENTALS)
        self.fundamentals_service = fundamentals_service

    async def execute(
        self,
        symbol: str,
        metrics: Optional[List[str]] = None
    ) -> ToolResult:
        """
        Get fundamental metrics for a symbol.

        Args:
            symbol: Symbol to analyze
            metrics: Specific metrics to fetch (e.g., ["pe_ratio", "market_cap"])
        """
        start = datetime.utcnow()

        try:
            if self.fundamentals_service:
                data = await self.fundamentals_service.get_metrics(
                    symbol=symbol,
                    metrics=metrics
                )
            else:
                # Mock response
                data = {
                    "symbol": symbol,
                    "metrics": {},
                    "last_updated": datetime.utcnow().isoformat()
                }

            latency = (datetime.utcnow() - start).total_seconds() * 1000
            self._call_count += 1
            self._total_latency += latency

            return ToolResult(
                tool_name=self.name,
                success=True,
                data=data,
                latency_ms=latency
            )

        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                error=str(e)
            )


class OnChainTool(BaseTool):
    """Tool for on-chain analytics (crypto)."""

    def __init__(self, onchain_service=None):
        super().__init__("get_onchain", ToolCategory.ON_CHAIN)
        self.onchain_service = onchain_service

    async def execute(
        self,
        symbol: str,
        metrics: Optional[List[str]] = None
    ) -> ToolResult:
        """
        Get on-chain metrics for a cryptocurrency.

        Args:
            symbol: Crypto symbol
            metrics: Specific metrics (e.g., ["whale_movements", "exchange_flows"])
        """
        start = datetime.utcnow()

        try:
            if self.onchain_service:
                data = await self.onchain_service.get_metrics(
                    symbol=symbol,
                    metrics=metrics
                )
            else:
                data = {
                    "symbol": symbol,
                    "metrics": {},
                    "blockchain": "unknown"
                }

            latency = (datetime.utcnow() - start).total_seconds() * 1000
            self._call_count += 1
            self._total_latency += latency

            return ToolResult(
                tool_name=self.name,
                success=True,
                data=data,
                latency_ms=latency
            )

        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                error=str(e)
            )


class SocialTool(BaseTool):
    """Tool for social media analytics."""

    def __init__(self, social_service=None):
        super().__init__("search_social", ToolCategory.SOCIAL)
        self.social_service = social_service

    async def execute(
        self,
        query: str,
        platforms: Optional[List[str]] = None,
        limit: int = 20
    ) -> ToolResult:
        """
        Search social media for mentions.

        Args:
            query: Search query
            platforms: Platforms to search ("twitter", "reddit", "discord")
            limit: Max results
        """
        start = datetime.utcnow()

        try:
            if self.social_service:
                data = await self.social_service.search(
                    query=query,
                    platforms=platforms or ["twitter", "reddit"],
                    limit=limit
                )
            else:
                data = {
                    "query": query,
                    "posts": [],
                    "total": 0
                }

            latency = (datetime.utcnow() - start).total_seconds() * 1000
            self._call_count += 1
            self._total_latency += latency

            return ToolResult(
                tool_name=self.name,
                success=True,
                data=data,
                latency_ms=latency
            )

        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                error=str(e)
            )


class TechnicalTool(BaseTool):
    """Tool for technical analysis indicators."""

    def __init__(self, technical_service=None):
        super().__init__("get_technicals", ToolCategory.TECHNICAL)
        self.technical_service = technical_service

    async def execute(
        self,
        symbol: str,
        indicators: Optional[List[str]] = None,
        timeframe: str = "1h"
    ) -> ToolResult:
        """
        Calculate technical indicators.

        Args:
            symbol: Symbol to analyze
            indicators: List of indicators (e.g., ["RSI", "MACD", "BB"])
            timeframe: Timeframe for calculations
        """
        start = datetime.utcnow()

        try:
            if self.technical_service:
                data = await self.technical_service.calculate(
                    symbol=symbol,
                    indicators=indicators or ["RSI", "MACD", "EMA"],
                    timeframe=timeframe
                )
            else:
                data = {
                    "symbol": symbol,
                    "indicators": {},
                    "timeframe": timeframe
                }

            latency = (datetime.utcnow() - start).total_seconds() * 1000
            self._call_count += 1
            self._total_latency += latency

            return ToolResult(
                tool_name=self.name,
                success=True,
                data=data,
                latency_ms=latency
            )

        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                error=str(e)
            )


class AutonomousToolkit:
    """
    Toolkit for autonomous agent research.

    Provides agents with tools to independently discover and analyze
    market information, implementing the "minimal information paradigm."

    Usage:
        toolkit = AutonomousToolkit()

        # Agent uses tools to gather information
        price = await toolkit.execute("get_price", symbol="BTC/USDT")
        news = await toolkit.execute("search_news", query="Bitcoin ETF")
        sentiment = await toolkit.execute("analyze_sentiment", symbol="BTC")

        # Agent synthesizes information into decision
        decision = agent.synthesize([price, news, sentiment])
    """

    def __init__(
        self,
        price_service=None,
        news_service=None,
        sentiment_service=None,
        fundamentals_service=None,
        onchain_service=None,
        social_service=None,
        technical_service=None
    ):
        """
        Initialize toolkit with optional service implementations.

        Services can be None for testing - tools will return mock data.
        """
        # Initialize tools
        self.tools: Dict[str, BaseTool] = {
            "get_price": PriceTool(price_service),
            "search_news": NewsTool(news_service),
            "analyze_sentiment": SentimentTool(sentiment_service),
            "get_fundamentals": FundamentalsTool(fundamentals_service),
            "get_onchain": OnChainTool(onchain_service),
            "search_social": SocialTool(social_service),
            "get_technicals": TechnicalTool(technical_service),
        }

        # Usage tracking
        self._tool_usage: Dict[str, int] = {}
        self._total_calls = 0

        logger.info(f"Autonomous Toolkit initialized with {len(self.tools)} tools")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        """List available tools with descriptions."""
        return [
            {"name": tool.name, "category": tool.category.value}
            for tool in self.tools.values()
        ]

    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Arguments to pass to the tool

        Returns:
            ToolResult with the tool's output
        """
        tool = self.tools.get(tool_name)

        if not tool:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                error=f"Unknown tool: {tool_name}"
            )

        # Track usage
        self._tool_usage[tool_name] = self._tool_usage.get(tool_name, 0) + 1
        self._total_calls += 1

        # Execute tool
        result = await tool.execute(**kwargs)

        logger.debug(
            f"Tool {tool_name}: success={result.success}, "
            f"latency={result.latency_ms:.1f}ms"
        )

        return result

    async def execute_parallel(
        self,
        calls: List[Dict[str, Any]]
    ) -> List[ToolResult]:
        """
        Execute multiple tools in parallel.

        Args:
            calls: List of {"tool": "name", **kwargs}

        Returns:
            List of ToolResults in same order as calls
        """
        tasks = [
            self.execute(call.pop("tool"), **call)
            for call in calls
        ]

        return await asyncio.gather(*tasks)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get toolkit usage statistics."""
        return {
            "total_calls": self._total_calls,
            "by_tool": self._tool_usage,
            "tool_latencies": {
                name: tool.avg_latency
                for name, tool in self.tools.items()
            }
        }

    def reset_stats(self):
        """Reset usage statistics."""
        self._tool_usage.clear()
        self._total_calls = 0
        for tool in self.tools.values():
            tool._call_count = 0
            tool._total_latency = 0


@dataclass
class AutonomousAgentConfig:
    """Configuration for an autonomous research agent."""
    allowed_tools: List[str] = field(default_factory=lambda: [
        "get_price", "search_news", "analyze_sentiment",
        "get_technicals"
    ])
    max_tool_calls: int = 10
    timeout_seconds: float = 30.0
    require_price_check: bool = True
    require_news_check: bool = False


class AutonomousResearchMixin:
    """
    Mixin to add autonomous research capabilities to any agent.

    Usage:
        class MyAgent(BaseAgent, AutonomousResearchMixin):
            async def decide(self, symbol: str, toolkit: AutonomousToolkit):
                # Agent autonomously decides what to research
                await self.research_symbol(symbol, toolkit)
                return self.synthesize_decision()
    """

    async def research_symbol(
        self,
        symbol: str,
        toolkit: AutonomousToolkit,
        config: Optional[AutonomousAgentConfig] = None
    ) -> Dict[str, ToolResult]:
        """
        Autonomously research a symbol using the toolkit.

        This is the key difference from traditional approaches:
        The agent decides what information to gather rather than
        receiving pre-curated data.
        """
        config = config or AutonomousAgentConfig()
        results = {}

        # Agent decides research strategy based on its role
        research_plan = self._create_research_plan(symbol, config)

        # Execute research plan
        for step in research_plan:
            if len(results) >= config.max_tool_calls:
                logger.warning(f"Max tool calls ({config.max_tool_calls}) reached")
                break

            tool_name = step["tool"]
            if tool_name not in config.allowed_tools:
                continue

            result = await toolkit.execute(tool_name, **step.get("params", {}))
            results[step.get("key", tool_name)] = result

            # Allow agent to adapt based on results
            research_plan = self._adapt_research_plan(
                symbol, research_plan, results
            )

        return results

    def _create_research_plan(
        self,
        symbol: str,
        config: AutonomousAgentConfig
    ) -> List[Dict[str, Any]]:
        """
        Create initial research plan.

        Override in subclasses for specialized research strategies.
        """
        plan = []

        if config.require_price_check and "get_price" in config.allowed_tools:
            plan.append({
                "key": "current_price",
                "tool": "get_price",
                "params": {"symbol": symbol, "timeframe": "current"}
            })
            plan.append({
                "key": "price_history",
                "tool": "get_price",
                "params": {"symbol": symbol, "timeframe": "1h", "lookback": 24}
            })

        if config.require_news_check and "search_news" in config.allowed_tools:
            plan.append({
                "key": "recent_news",
                "tool": "search_news",
                "params": {"query": symbol, "time_range": "24h", "limit": 5}
            })

        if "get_technicals" in config.allowed_tools:
            plan.append({
                "key": "technicals",
                "tool": "get_technicals",
                "params": {"symbol": symbol, "indicators": ["RSI", "MACD"]}
            })

        if "analyze_sentiment" in config.allowed_tools:
            plan.append({
                "key": "sentiment",
                "tool": "analyze_sentiment",
                "params": {"symbol": symbol}
            })

        return plan

    def _adapt_research_plan(
        self,
        symbol: str,
        current_plan: List[Dict[str, Any]],
        results: Dict[str, ToolResult]
    ) -> List[Dict[str, Any]]:
        """
        Adapt research plan based on intermediate results.

        This is where the agent shows "intelligence" - adapting
        its research strategy based on what it finds.
        """
        # Example: If sentiment is very negative, dig deeper into news
        if "sentiment" in results:
            sentiment_data = results["sentiment"].data
            if sentiment_data and sentiment_data.get("sentiment_score", 0) < -0.5:
                # Add more news research
                current_plan.append({
                    "key": "negative_news",
                    "tool": "search_news",
                    "params": {
                        "query": f"{symbol} crash OR {symbol} drop",
                        "time_range": "12h",
                        "limit": 10
                    }
                })

        # Example: If price moved significantly, check on-chain data
        if "price_history" in results:
            price_data = results["price_history"].data
            if price_data and self._detect_significant_move(price_data):
                current_plan.append({
                    "key": "onchain",
                    "tool": "get_onchain",
                    "params": {"symbol": symbol}
                })

        return current_plan

    def _detect_significant_move(self, price_data: Dict[str, Any]) -> bool:
        """Detect if price moved significantly (>5% in 24h)."""
        # Would analyze price_data for significant moves
        return False


def create_minimal_info_agent(
    base_agent_class,
    toolkit: AutonomousToolkit,
    config: Optional[AutonomousAgentConfig] = None
):
    """
    Factory to create an agent that follows minimal information paradigm.

    Args:
        base_agent_class: The base agent class to enhance
        toolkit: The autonomous toolkit to use
        config: Agent configuration

    Returns:
        Enhanced agent class with autonomous research
    """
    config = config or AutonomousAgentConfig()

    class MinimalInfoAgent(base_agent_class, AutonomousResearchMixin):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.toolkit = toolkit
            self.research_config = config

        async def decide_autonomous(
            self,
            symbol: str,
            **kwargs
        ) -> Dict[str, Any]:
            """
            Make trading decision using autonomous research.

            Instead of receiving pre-curated data, the agent:
            1. Decides what information to gather
            2. Uses tools to gather information
            3. Synthesizes findings
            4. Makes decision
            """
            # Autonomous research phase
            research_results = await self.research_symbol(
                symbol,
                self.toolkit,
                self.research_config
            )

            # Synthesis phase - let base agent process
            # Convert tool results to format expected by base agent
            market_data = self._results_to_market_data(research_results)

            # Call base agent's decision logic
            if hasattr(super(), 'decide'):
                return await super().decide(symbol=symbol, market_data=market_data, **kwargs)

            return {
                "symbol": symbol,
                "decision": "hold",
                "confidence": 0.5,
                "research_summary": self._summarize_research(research_results)
            }

        def _results_to_market_data(
            self,
            results: Dict[str, ToolResult]
        ) -> Dict[str, Any]:
            """Convert tool results to market data format."""
            market_data = {}

            if "current_price" in results and results["current_price"].success:
                market_data["price"] = results["current_price"].data

            if "technicals" in results and results["technicals"].success:
                market_data["indicators"] = results["technicals"].data

            if "sentiment" in results and results["sentiment"].success:
                market_data["sentiment"] = results["sentiment"].data

            if "recent_news" in results and results["recent_news"].success:
                market_data["news"] = results["recent_news"].data

            return market_data

        def _summarize_research(
            self,
            results: Dict[str, ToolResult]
        ) -> str:
            """Summarize research findings."""
            summaries = []
            for key, result in results.items():
                if result.success:
                    summaries.append(f"{key}: {result.data}")
            return "; ".join(summaries) if summaries else "No data gathered"

    return MinimalInfoAgent
