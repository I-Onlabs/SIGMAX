"""
LEAN Execution Module - Optional bridge for QuantConnect LEAN integrations.

This module is intentionally minimal and only used when EXECUTION_BACKEND=lean.
It does not change default behavior and fails safely if not configured.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
import json
import os
import urllib.request
import urllib.error


class LeanExecutionModule:
    """
    Execution module that forwards trade intents to a LEAN bridge endpoint.

    Configuration:
    - LEAN_BRIDGE_URL: HTTP endpoint that accepts trade intents (required)
    - LEAN_BRIDGE_TIMEOUT: seconds (optional, default 5)
    """

    def __init__(self, mode: str = "paper"):
        self.mode = mode
        self.bridge_url = os.getenv("LEAN_BRIDGE_URL")
        self.timeout = float(os.getenv("LEAN_BRIDGE_TIMEOUT", "5"))
        self.trade_history = []
        self.available = False

        logger.info("✓ Lean execution module created")

    async def initialize(self) -> None:
        """Initialize LEAN bridge settings."""
        if self.bridge_url:
            self.available = True
            logger.info(f"✓ LEAN bridge configured: {self.bridge_url}")
        else:
            logger.warning("LEAN bridge not configured (LEAN_BRIDGE_URL missing)")

    async def execute_trade(
        self,
        symbol: str,
        action: str,
        size: float,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Forward trade intent to LEAN bridge.
        Returns a structured error if bridge is not configured.
        """
        if not self.available:
            return {
                "success": False,
                "error": "LEAN bridge not configured",
                "reason": "set LEAN_BRIDGE_URL to enable LEAN execution"
            }

        payload = {
            "symbol": symbol,
            "action": action,
            "size": size,
            "price": price,
            "mode": self.mode
        }

        try:
            request = urllib.request.Request(
                self.bridge_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                result = json.loads(body) if body else {"success": True}

            self.trade_history.append({
                "symbol": symbol,
                "action": action,
                "size": size,
                "price": price,
                "timestamp": datetime.now().isoformat(),
                "mode": self.mode
            })

            return result
        except urllib.error.HTTPError as e:
            return {
                "success": False,
                "error": f"LEAN bridge HTTP error {e.code}",
                "detail": e.reason
            }
        except Exception as e:
            logger.error(f"LEAN bridge error: {e}")
            return {
                "success": False,
                "error": "LEAN bridge request failed",
                "detail": str(e)
            }

    async def close_all_positions(self) -> Dict[str, Any]:
        """Best-effort close request to LEAN bridge (optional endpoint)."""
        if not self.available:
            return {
                "success": False,
                "error": "LEAN bridge not configured"
            }

        close_url = os.getenv("LEAN_BRIDGE_CLOSE_URL", f"{self.bridge_url}/close_all")
        try:
            request = urllib.request.Request(
                close_url,
                data=json.dumps({}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {"success": True}
        except Exception as e:
            logger.error(f"LEAN bridge close_all error: {e}")
            return {
                "success": False,
                "error": "LEAN bridge close_all failed",
                "detail": str(e)
            }

    async def get_status(self) -> Dict[str, Any]:
        """Return bridge status without network calls."""
        return {
            "mode": self.mode,
            "backend": "lean",
            "available": self.available,
            "bridge_url": self.bridge_url
        }
