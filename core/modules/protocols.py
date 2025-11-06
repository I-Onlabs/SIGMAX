"""Protocol definitions for SIGMAX modules

These protocols define the interfaces that modules must implement,
enabling dependency injection, easier testing, and loose coupling.
"""

from typing import Protocol, Dict, Any, Optional, List
from datetime import datetime


class DataModuleProtocol(Protocol):
    """Protocol for data modules that fetch and manage market data"""

    async def initialize(self) -> None:
        """Initialize the data module and establish connections"""
        ...

    async def get_market_data(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get comprehensive market data for a symbol

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe
            limit: Number of candles

        Returns:
            Market data dictionary containing price, volume, OHLCV, etc.
        """
        ...

    async def get_historical_data(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: str = "1h"
    ) -> List[List[float]]:
        """
        Get historical OHLCV data

        Args:
            symbol: Trading pair
            start: Start datetime
            end: End datetime
            timeframe: Candle timeframe

        Returns:
            List of OHLCV candles
        """
        ...

    async def close(self) -> None:
        """Close all connections"""
        ...


class ExecutionModuleProtocol(Protocol):
    """Protocol for execution modules that handle trade execution"""

    async def initialize(self) -> None:
        """Initialize the execution engine"""
        ...

    async def execute_trade(
        self,
        symbol: str,
        action: str,
        size: float,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute a trade

        Args:
            symbol: Trading pair
            action: 'buy' or 'sell'
            size: Position size (in base currency)
            price: Limit price (None for market order)

        Returns:
            Trade result dictionary
        """
        ...

    async def close_all_positions(self) -> Dict[str, Any]:
        """
        Emergency close all open positions

        Returns:
            Result dictionary with closed positions and errors
        """
        ...

    async def get_status(self) -> Dict[str, Any]:
        """
        Get execution module status

        Returns:
            Status dictionary with mode, balance, open orders, etc.
        """
        ...


class QuantumModuleProtocol(Protocol):
    """Protocol for quantum optimization modules"""

    async def initialize(self) -> None:
        """Initialize quantum backend"""
        ...

    async def optimize_portfolio(
        self,
        symbol: str,
        signal: float,
        current_portfolio: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Optimize portfolio using quantum algorithm

        Args:
            symbol: Symbol to optimize
            signal: Signal strength (-1 to 1)
            current_portfolio: Current holdings

        Returns:
            Optimization result with action, size, confidence
        """
        ...

    async def get_status(self) -> Dict[str, Any]:
        """
        Get quantum module status

        Returns:
            Status dictionary
        """
        ...


class ComplianceModuleProtocol(Protocol):
    """Protocol for compliance modules that validate trades"""

    async def initialize(self) -> None:
        """Initialize compliance module"""
        ...

    async def check_trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if trade complies with policies

        Args:
            trade: Trade dictionary

        Returns:
            Compliance result with approved flag and reason
        """
        ...


class RLModuleProtocol(Protocol):
    """Protocol for reinforcement learning modules"""

    async def initialize(self) -> None:
        """Initialize RL module"""
        ...

    async def get_action(
        self,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get RL agent's recommended action

        Args:
            state: Current market state

        Returns:
            Recommended action
        """
        ...


class ArbitrageModuleProtocol(Protocol):
    """Protocol for arbitrage detection modules"""

    async def initialize(self) -> None:
        """Initialize arbitrage module"""
        ...

    async def scan_opportunities(
        self,
        symbols: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Scan for arbitrage opportunities

        Args:
            symbols: Symbols to scan

        Returns:
            List of arbitrage opportunities
        """
        ...


class OrchestratorProtocol(Protocol):
    """Protocol for agent orchestrators"""

    async def initialize(self) -> None:
        """Initialize the orchestrator workflow"""
        ...

    async def analyze_symbol(
        self,
        symbol: str,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a symbol using multi-agent debate

        Args:
            symbol: Trading symbol
            market_data: Optional market data override

        Returns:
            Decision dict with action, confidence, reasoning
        """
        ...

    async def start(self) -> None:
        """Start the orchestrator"""
        ...

    async def pause(self) -> None:
        """Pause the orchestrator"""
        ...

    async def resume(self) -> None:
        """Resume the orchestrator"""
        ...

    async def stop(self) -> None:
        """Stop the orchestrator"""
        ...

    async def get_status(self) -> Dict[str, Any]:
        """
        Get orchestrator status

        Returns:
            Status dictionary
        """
        ...


class AgentProtocol(Protocol):
    """Protocol for individual agents"""

    async def process(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process market data and generate output

        Args:
            symbol: Trading symbol
            market_data: Market data dictionary
            context: Optional context from previous agents

        Returns:
            Agent output dictionary
        """
        ...


class HealthCheckerProtocol(Protocol):
    """Protocol for health checking modules"""

    async def start(self) -> None:
        """Start health checking"""
        ...

    async def stop(self) -> None:
        """Stop health checking"""
        ...

    async def check(self) -> Dict[str, Any]:
        """
        Perform health check

        Returns:
            Health status dictionary
        """
        ...


class TelegramBotProtocol(Protocol):
    """Protocol for Telegram bot modules"""

    async def initialize(self) -> None:
        """Initialize Telegram bot"""
        ...

    async def start(self) -> None:
        """Start Telegram bot"""
        ...

    async def stop(self) -> None:
        """Stop Telegram bot"""
        ...

    async def send_message(
        self,
        message: str,
        parse_mode: Optional[str] = None
    ) -> None:
        """
        Send message to user

        Args:
            message: Message text
            parse_mode: Parse mode (Markdown, HTML, etc.)
        """
        ...


# Type aliases for common structures
MarketData = Dict[str, Any]
TradeSignal = Dict[str, Any]
Decision = Dict[str, Any]
Status = Dict[str, Any]
