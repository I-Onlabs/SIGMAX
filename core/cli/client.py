"""
SIGMAX CLI - API client.

Handles communication with the SIGMAX API backend.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, Optional

import httpx
from httpx_sse import aconnect_sse


class SigmaxClient:
    """Client for SIGMAX API."""

    def __init__(self, api_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """Initialize client."""
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.headers = {}

        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    async def analyze(
        self,
        symbol: str,
        risk_profile: str = "conservative",
        mode: str = "paper",
    ) -> Dict[str, Any]:
        """
        Analyze a trading pair (synchronous).

        Returns final analysis result.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/chat/stream",
                headers=self.headers,
                json={
                    "message": f"Analyze {symbol}",
                    "symbol": symbol,
                    "risk_profile": risk_profile,
                    "mode": mode,
                },
                timeout=60.0,
            )
            response.raise_for_status()

            # Parse SSE stream and get final result
            final_result = None
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if "final" in line:
                        final_result = data
                        break

            return final_result or {}

    async def analyze_stream(
        self,
        symbol: str,
        risk_profile: str = "conservative",
        mode: str = "paper",
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Analyze a trading pair (streaming).

        Yields progress events as they arrive.
        """
        async with httpx.AsyncClient() as client:
            async with aconnect_sse(
                client,
                "POST",
                f"{self.api_url}/api/chat/stream",
                headers=self.headers,
                json={
                    "message": f"Analyze {symbol}",
                    "symbol": symbol,
                    "risk_profile": risk_profile,
                    "mode": mode,
                },
                timeout=60.0,
            ) as event_source:
                async for sse in event_source.aiter_sse():
                    data = json.loads(sse.data)
                    yield {"type": sse.event, **data}

    async def get_status(self) -> Dict[str, Any]:
        """Get current SIGMAX status."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/api/status",
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def propose_trade(
        self,
        symbol: str,
        risk_profile: str = "conservative",
        mode: str = "paper",
        size: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Create a trade proposal."""
        payload = {
            "symbol": symbol,
            "risk_profile": risk_profile,
            "mode": mode,
        }

        if size is not None:
            payload["size"] = size

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/chat/proposals",
                headers=self.headers,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("proposal", result)

    async def list_proposals(self) -> Dict[str, Dict[str, Any]]:
        """List all trade proposals."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/api/chat/proposals",
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("proposals", {})

    async def get_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """Get a specific trade proposal."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/api/chat/proposals/{proposal_id}",
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def approve_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """Approve a trade proposal."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/chat/proposals/{proposal_id}/approve",
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def execute_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """Execute an approved trade proposal."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/chat/proposals/{proposal_id}/execute",
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
