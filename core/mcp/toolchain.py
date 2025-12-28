"""
MCP Toolchain - Model Context Protocol Integration
Inspired by AI-Trader's standardized tool access layer

Provides MCP-compliant tool definitions for:
- Market data analysis
- Trading execution
- Research and search
- Portfolio management

This enables standardized tool access across all agents
and easy integration with LangChain/LangGraph.
"""

from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
from loguru import logger
import json
import asyncio


class MCPTransport(Enum):
    """MCP transport types."""
    STDIO = "stdio"
    HTTP = "streamable_http"
    WEBSOCKET = "websocket"


@dataclass
class MCPTool:
    """MCP-compliant tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[..., Awaitable[Any]]
    category: str = "general"
    requires_auth: bool = False

    def to_mcp_schema(self) -> Dict[str, Any]:
        """Convert to MCP tool schema format."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": self.input_schema,
                "required": [
                    k for k, v in self.input_schema.items()
                    if v.get("required", False)
                ]
            }
        }


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    transport: MCPTransport
    url: Optional[str] = None
    tools: List[str] = field(default_factory=list)
    auth_token: Optional[str] = None


class MCPToolRegistry:
    """
    Registry for MCP tools.

    Provides centralized tool management for:
    - Tool registration
    - Discovery
    - Execution
    - Access control
    """

    def __init__(self):
        self._tools: Dict[str, MCPTool] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(self, tool: MCPTool):
        """Register a tool."""
        self._tools[tool.name] = tool

        if tool.category not in self._categories:
            self._categories[tool.category] = []
        self._categories[tool.category].append(tool.name)

        logger.debug(f"Registered MCP tool: {tool.name}")

    def get(self, name: str) -> Optional[MCPTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available tools."""
        tools = self._tools.values()

        if category:
            tools = [t for t in tools if t.category == category]

        return [t.to_mcp_schema() for t in tools]

    def list_categories(self) -> List[str]:
        """List tool categories."""
        return list(self._categories.keys())

    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool."""
        tool = self._tools.get(tool_name)

        if not tool:
            return {
                "error": f"Unknown tool: {tool_name}",
                "success": False
            }

        try:
            result = await tool.handler(**arguments)
            return {
                "result": result,
                "success": True
            }
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "error": str(e),
                "success": False
            }


# Global registry
_registry = MCPToolRegistry()


def get_registry() -> MCPToolRegistry:
    """Get the global MCP tool registry."""
    return _registry


def mcp_tool(
    name: str,
    description: str,
    category: str = "general"
):
    """
    Decorator to register a function as an MCP tool.

    Usage:
        @mcp_tool("get_price", "Get current price for a symbol", category="data")
        async def get_price(symbol: str) -> dict:
            ...
    """
    def decorator(func):
        # Extract schema from function annotations
        import inspect
        sig = inspect.signature(func)

        input_schema = {}
        for param_name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                schema = _annotation_to_schema(param.annotation)
                schema["required"] = param.default == inspect.Parameter.empty
                input_schema[param_name] = schema
            else:
                input_schema[param_name] = {"type": "string"}

        tool = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=func,
            category=category
        )

        _registry.register(tool)

        return func

    return decorator


def _annotation_to_schema(annotation) -> Dict[str, Any]:
    """Convert Python type annotation to JSON schema."""
    if annotation == str:
        return {"type": "string"}
    elif annotation == int:
        return {"type": "integer"}
    elif annotation == float:
        return {"type": "number"}
    elif annotation == bool:
        return {"type": "boolean"}
    elif annotation == list or annotation == List:
        return {"type": "array"}
    elif annotation == dict or annotation == Dict:
        return {"type": "object"}
    else:
        return {"type": "string"}


# ============================================================================
# SIGMAX MCP Tool Definitions
# ============================================================================

# Analysis Tools
@mcp_tool(
    name="analyze_symbol",
    description="Analyze a trading symbol with technical and sentiment analysis",
    category="analysis"
)
async def analyze_symbol(
    symbol: str,
    include_technicals: bool = True,
    include_sentiment: bool = True,
    timeframe: str = "1h"
) -> Dict[str, Any]:
    """Analyze a trading symbol."""
    # Would integrate with analyzer agents
    return {
        "symbol": symbol,
        "analysis": {
            "technicals": {"rsi": 50, "macd": 0} if include_technicals else None,
            "sentiment": {"score": 0, "volume": 0} if include_sentiment else None
        },
        "timeframe": timeframe,
        "timestamp": datetime.utcnow().isoformat()
    }


@mcp_tool(
    name="get_sentiment",
    description="Get market sentiment for a symbol from multiple sources",
    category="analysis"
)
async def get_sentiment(
    symbol: str,
    sources: List[str] = None
) -> Dict[str, Any]:
    """Get sentiment analysis."""
    sources = sources or ["twitter", "reddit", "news"]
    return {
        "symbol": symbol,
        "sentiment_score": 0.0,
        "sources": sources,
        "timestamp": datetime.utcnow().isoformat()
    }


@mcp_tool(
    name="quantum_optimize",
    description="Optimize portfolio allocation using quantum algorithms",
    category="analysis"
)
async def quantum_optimize(
    symbols: List[str],
    risk_tolerance: float = 0.5,
    method: str = "vqe"
) -> Dict[str, Any]:
    """Quantum portfolio optimization."""
    return {
        "symbols": symbols,
        "method": method,
        "allocations": {s: 1.0 / len(symbols) for s in symbols},
        "expected_return": 0.0,
        "risk": 0.0
    }


# Trading Tools
@mcp_tool(
    name="create_proposal",
    description="Create a trade proposal for review",
    category="trading"
)
async def create_proposal(
    symbol: str,
    action: str,
    amount: float,
    reasoning: str,
    confidence: float = 0.5
) -> Dict[str, Any]:
    """Create a trade proposal."""
    return {
        "proposal_id": f"prop_{datetime.utcnow().timestamp()}",
        "symbol": symbol,
        "action": action,
        "amount": amount,
        "reasoning": reasoning,
        "confidence": confidence,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }


@mcp_tool(
    name="execute_trade",
    description="Execute a trade (requires approval)",
    category="trading"
)
async def execute_trade(
    proposal_id: str,
    override_checks: bool = False
) -> Dict[str, Any]:
    """Execute a trade from proposal."""
    return {
        "proposal_id": proposal_id,
        "status": "executed",
        "executed_at": datetime.utcnow().isoformat()
    }


@mcp_tool(
    name="close_position",
    description="Close an open position",
    category="trading"
)
async def close_position(
    symbol: str,
    percentage: float = 100.0,
    reason: str = ""
) -> Dict[str, Any]:
    """Close a position."""
    return {
        "symbol": symbol,
        "closed_percentage": percentage,
        "reason": reason,
        "closed_at": datetime.utcnow().isoformat()
    }


# Data Tools
@mcp_tool(
    name="get_price",
    description="Get current or historical price data",
    category="data"
)
async def get_price(
    symbol: str,
    timeframe: str = "current"
) -> Dict[str, Any]:
    """Get price data."""
    return {
        "symbol": symbol,
        "price": 0.0,
        "timeframe": timeframe,
        "timestamp": datetime.utcnow().isoformat()
    }


@mcp_tool(
    name="get_orderbook",
    description="Get order book depth for a symbol",
    category="data"
)
async def get_orderbook(
    symbol: str,
    depth: int = 20
) -> Dict[str, Any]:
    """Get order book."""
    return {
        "symbol": symbol,
        "bids": [],
        "asks": [],
        "depth": depth,
        "timestamp": datetime.utcnow().isoformat()
    }


@mcp_tool(
    name="get_history",
    description="Get historical OHLCV data",
    category="data"
)
async def get_history(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 100
) -> Dict[str, Any]:
    """Get historical data."""
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": [],
        "limit": limit
    }


# Search Tools
@mcp_tool(
    name="search_news",
    description="Search for news articles",
    category="search"
)
async def search_news(
    query: str,
    time_range: str = "24h",
    limit: int = 10
) -> Dict[str, Any]:
    """Search news."""
    return {
        "query": query,
        "articles": [],
        "time_range": time_range,
        "total": 0
    }


@mcp_tool(
    name="get_financials",
    description="Get financial statements and ratios",
    category="search"
)
async def get_financials(
    symbol: str,
    report_type: str = "latest"
) -> Dict[str, Any]:
    """Get financial data."""
    return {
        "symbol": symbol,
        "report_type": report_type,
        "metrics": {}
    }


@mcp_tool(
    name="search_social",
    description="Search social media for mentions",
    category="search"
)
async def search_social(
    query: str,
    platforms: List[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """Search social media."""
    platforms = platforms or ["twitter", "reddit"]
    return {
        "query": query,
        "platforms": platforms,
        "posts": [],
        "total": 0
    }


# ============================================================================
# MCP Server Configuration
# ============================================================================

MCP_CONFIG = {
    "analysis": MCPServerConfig(
        name="analysis",
        transport=MCPTransport.HTTP,
        url="http://localhost:8001/mcp",
        tools=["analyze_symbol", "get_sentiment", "quantum_optimize"]
    ),
    "trading": MCPServerConfig(
        name="trading",
        transport=MCPTransport.HTTP,
        url="http://localhost:8002/mcp",
        tools=["create_proposal", "execute_trade", "close_position"]
    ),
    "data": MCPServerConfig(
        name="data",
        transport=MCPTransport.HTTP,
        url="http://localhost:8003/mcp",
        tools=["get_price", "get_orderbook", "get_history"]
    ),
    "search": MCPServerConfig(
        name="search",
        transport=MCPTransport.HTTP,
        url="http://localhost:8004/mcp",
        tools=["search_news", "get_financials", "search_social"]
    )
}


class MCPToolchainClient:
    """
    Client for interacting with MCP toolchain.

    Provides a unified interface for agents to access tools
    across multiple MCP servers.
    """

    def __init__(self, config: Dict[str, MCPServerConfig] = None):
        """
        Initialize MCP toolchain client.

        Args:
            config: Server configuration dict
        """
        self.config = config or MCP_CONFIG
        self.registry = get_registry()

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a tool by name.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Tool result
        """
        return await self.registry.execute(tool_name, arguments)

    def list_available_tools(
        self,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List available tools."""
        return self.registry.list_tools(category=category)

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific tool."""
        tool = self.registry.get(tool_name)
        return tool.to_mcp_schema() if tool else None

    async def batch_call(
        self,
        calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tool calls in parallel.

        Args:
            calls: List of {"tool": "name", "arguments": {...}}

        Returns:
            List of results in same order
        """
        tasks = [
            self.call_tool(call["tool"], call.get("arguments", {}))
            for call in calls
        ]

        return await asyncio.gather(*tasks)


# LangChain/LangGraph Integration
def get_langchain_tools():
    """
    Get tools in LangChain-compatible format.

    Returns:
        List of LangChain Tool objects
    """
    try:
        from langchain_core.tools import Tool

        tools = []
        for mcp_tool in _registry._tools.values():
            tool = Tool(
                name=mcp_tool.name,
                description=mcp_tool.description,
                func=lambda **kwargs: asyncio.run(mcp_tool.handler(**kwargs)),
                coroutine=mcp_tool.handler
            )
            tools.append(tool)

        return tools
    except ImportError:
        logger.warning("LangChain not installed")
        return []
