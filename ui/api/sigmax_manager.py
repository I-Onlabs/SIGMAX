"""
SIGMAX Instance Manager for FastAPI
Provides singleton access to SIGMAX trading system
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger
from collections import deque

# Add core to path
core_path = Path(__file__).parent.parent.parent / "core"
sys.path.insert(0, str(core_path))

from main import SIGMAX

# Shared channel/service contracts (core-level, used by all interfaces)
from interfaces.channel_service import ChannelService


class SIGMAXManager:
    """
    Singleton manager for SIGMAX instance
    Allows FastAPI to communicate with running trading system
    """

    _instance: Optional['SIGMAXManager'] = None
    _sigmax: Optional[SIGMAX] = None
    _initialized: bool = False
    _lock: asyncio.Lock = asyncio.Lock()
    _event_queue: deque = deque(maxlen=100)  # Store last 100 events
    _channel_service: Optional[ChannelService] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(
        self,
        mode: str = "paper",
        risk_profile: str = "conservative"
    ) -> bool:
        """
        Initialize SIGMAX instance

        Args:
            mode: Trading mode ('paper', 'live')
            risk_profile: Risk profile ('conservative', 'balanced', 'aggressive')

        Returns:
            True if initialization successful
        """
        async with self._lock:
            if self._initialized:
                logger.info("SIGMAX already initialized")
                return True

            try:
                logger.info(f"Initializing SIGMAX in {mode} mode...")

                # Create SIGMAX instance
                self._sigmax = SIGMAX(
                    mode=mode,
                    risk_profile=risk_profile
                )

                # Initialize modules
                success = await self._sigmax.initialize()

                if success:
                    self._initialized = True
                    # Channel service lives with the SIGMAX instance so
                    # Telegram + web chat + API share the same orchestrator.
                    self._channel_service = ChannelService(
                        orchestrator=self._sigmax.orchestrator,
                        execution_module=self._sigmax.execution_module,
                        compliance_module=self._sigmax.compliance_module,
                    )
                    logger.info("✓ SIGMAX initialized successfully")
                    return True
                else:
                    logger.error("Failed to initialize SIGMAX")
                    return False

            except Exception as e:
                logger.error(f"Error initializing SIGMAX: {e}")
                return False

    async def start(self) -> bool:
        """Start SIGMAX trading system"""
        if not self._initialized or not self._sigmax:
            logger.error("SIGMAX not initialized")
            return False

        try:
            if self._sigmax.running:
                logger.warning("SIGMAX already running")
                return True

            # Start in background task
            asyncio.create_task(self._sigmax.start())
            await asyncio.sleep(1)  # Give it a moment to start

            logger.info("✓ SIGMAX started")
            return True

        except Exception as e:
            logger.error(f"Error starting SIGMAX: {e}")
            return False

    async def pause(self) -> bool:
        """Pause SIGMAX trading"""
        if not self._initialized or not self._sigmax:
            logger.error("SIGMAX not initialized")
            return False

        try:
            await self._sigmax.pause()
            logger.info("✓ SIGMAX paused")
            return True

        except Exception as e:
            logger.error(f"Error pausing SIGMAX: {e}")
            return False

    async def stop(self) -> bool:
        """Stop SIGMAX trading"""
        if not self._initialized or not self._sigmax:
            logger.error("SIGMAX not initialized")
            return False

        try:
            await self._sigmax.stop()
            logger.info("✓ SIGMAX stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping SIGMAX: {e}")
            return False

    async def emergency_stop(self) -> Dict[str, Any]:
        """
        Execute emergency stop - close all positions immediately

        Returns:
            Dict with closed positions and cancelled orders
        """
        if not self._initialized or not self._sigmax:
            raise RuntimeError("SIGMAX not initialized")

        try:
            logger.critical("🚨 EMERGENCY STOP INITIATED")

            # Close all positions via execution module
            result = await self._sigmax.execution_module.emergency_stop()

            # Stop trading
            await self._sigmax.stop()

            logger.critical("🚨 Emergency stop completed")
            return result

        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")
            raise

    async def get_status(self) -> Dict[str, Any]:
        """Get current SIGMAX status"""
        if not self._initialized or not self._sigmax:
            return {
                "initialized": False,
                "running": False,
                "mode": "unknown"
            }

        try:
            # Get orchestrator status
            orchestrator_status = self._sigmax.orchestrator.get_status() if self._sigmax.orchestrator else {}

            # Get execution module status
            execution_status = await self._sigmax.execution_module.get_status() if self._sigmax.execution_module else {}

            return {
                "initialized": self._initialized,
                "running": self._sigmax.running,
                "paused": self._sigmax.paused if hasattr(self._sigmax, 'paused') else False,
                "mode": self._sigmax.mode,
                "risk_profile": self._sigmax.risk_profile,
                "uptime": (datetime.now() - self._sigmax.start_time).total_seconds() if self._sigmax.start_time else 0,
                "agents": orchestrator_status.get("agents", {}),
                "trading": execution_status.get("trading", {}),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {
                "initialized": self._initialized,
                "running": self._sigmax.running if self._sigmax else False,
                "mode": self._sigmax.mode if self._sigmax else "unknown",
                "error": str(e)
            }

    async def analyze_symbol(
        self,
        symbol: str,
        include_debate: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze a trading symbol using multi-agent debate

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            include_debate: Include full debate log

        Returns:
            Analysis result with decision, confidence, reasoning
        """
        if not self._initialized or not self._sigmax:
            raise RuntimeError("SIGMAX not initialized")

        if not self._sigmax.orchestrator:
            raise RuntimeError("Orchestrator not available")

        try:
            # Prefer detailed state for artifacts + correct event payloads
            result = await self._sigmax.orchestrator.analyze_symbol_detailed(symbol)
            decision = result.get("final_decision", {}) if isinstance(result, dict) else {}

            # Add agent decision event to queue for WebSocket broadcast
            self.add_event("agent_decision", {
                "symbol": symbol,
                "decision": decision.get("action", "hold"),
                "confidence": decision.get("confidence", 0),
                "bull_score": result.get("bull_argument", ""),
                "bear_score": result.get("bear_argument", ""),
                "reasoning": decision.get("reasoning", "")
            })

            if not include_debate:
                # Remove detailed messages to keep response concise
                result.pop("messages", None)

            return result

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            raise

    async def execute_trade(
        self,
        symbol: str,
        action: str,
        size: float
    ) -> Dict[str, Any]:
        """
        Execute a trade order

        Args:
            symbol: Trading symbol
            action: 'buy' or 'sell'
            size: Trade size

        Returns:
            Trade execution result
        """
        if not self._initialized or not self._sigmax:
            raise RuntimeError("SIGMAX not initialized")

        if not self._sigmax.execution_module:
            raise RuntimeError("Execution module not available")

        # Hard gate: direct trade API is disabled by default.
        # Use the proposal/approval flow (via chat or dedicated endpoints) instead.
        allow_direct = os.getenv("ALLOW_DIRECT_TRADE_API", "false").lower() == "true"
        if not allow_direct:
            raise PermissionError(
                "Direct trade execution is disabled. Create a proposal and approve/execute it."
            )

        try:
            # Execute trade through unified execution path
            result = await self._sigmax.execution_module.execute_trade(symbol, action, size)

            # Add trade execution event to queue for WebSocket broadcast
            self.add_event("trade_execution", {
                "symbol": symbol,
                "action": action,
                "size": size,
                "order_id": result.get("order_id"),
                "status": result.get("status"),
                "filled_price": result.get("filled_price"),
                "fee": result.get("fee")
            })

            return result

        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            raise

    async def get_portfolio(self) -> Dict[str, Any]:
        """Get current portfolio"""
        if not self._initialized or not self._sigmax:
            raise RuntimeError("SIGMAX not initialized")

        if not self._sigmax.execution_module:
            raise RuntimeError("Execution module not available")

        try:
            portfolio = await self._sigmax.execution_module.get_portfolio()
            return portfolio

        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            raise

    async def get_trade_history(
        self,
        limit: int = 50,
        offset: int = 0,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get trade history"""
        if not self._initialized or not self._sigmax:
            raise RuntimeError("SIGMAX not initialized")

        if not self._sigmax.execution_module:
            raise RuntimeError("Execution module not available")

        try:
            history = await self._sigmax.execution_module.get_trade_history(
                limit=limit,
                offset=offset,
                symbol=symbol
            )
            return history

        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            raise

    async def get_quantum_circuit(self) -> Dict[str, Any]:
        """Get latest quantum circuit visualization"""
        if not self._initialized or not self._sigmax:
            raise RuntimeError("SIGMAX not initialized")

        if not self._sigmax.quantum_module:
            return {
                "enabled": False,
                "message": "Quantum module not enabled"
            }

        try:
            circuit_data = await self._sigmax.quantum_module.get_circuit_visualization()
            return circuit_data

        except Exception as e:
            logger.error(f"Error getting quantum circuit: {e}")
            raise

    def get_channel_service(self) -> ChannelService:
        if not self._initialized or not self._sigmax or not self._channel_service:
            raise RuntimeError("SIGMAX not initialized")
        return self._channel_service

    def is_initialized(self) -> bool:
        """Check if SIGMAX is initialized"""
        return self._initialized

    def is_running(self) -> bool:
        """Check if SIGMAX is running"""
        return self._sigmax.running if self._sigmax else False

    def add_event(self, event_type: str, data: Dict[str, Any]):
        """
        Add an event to the broadcast queue

        Events are automatically broadcast to all WebSocket clients

        Args:
            event_type: Type of event (trade_execution, agent_decision, alert, etc.)
            data: Event data
        """
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        self._event_queue.append(event)
        logger.debug(f"Event added to queue: {event_type}")

    def get_pending_events(self) -> List[Dict[str, Any]]:
        """
        Get all pending events and clear the queue

        Returns:
            List of events to broadcast
        """
        events = list(self._event_queue)
        self._event_queue.clear()
        return events

    def peek_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Peek at recent events without removing them

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent events (most recent first)
        """
        events = list(self._event_queue)
        events.reverse()  # Most recent first
        return events[:limit]


# Global instance
_manager = SIGMAXManager()


async def get_sigmax_manager() -> SIGMAXManager:
    """
    Get SIGMAX manager instance (singleton)

    Auto-initializes on first call if not already initialized
    """
    if not _manager.is_initialized():
        # Auto-initialize in paper mode
        await _manager.initialize(mode="paper", risk_profile="conservative")

    return _manager
