"""
SIGMAX SDK Client.

Async-first client for SIGMAX API with full type safety and streaming support.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
from httpx_sse import aconnect_sse

from .exceptions import (
    SigmaxAPIError,
    SigmaxAuthenticationError,
    SigmaxConnectionError,
    SigmaxRateLimitError,
    SigmaxTimeoutError,
    SigmaxValidationError,
)
from .models import (
    ProposalCreateRequest,
    RiskProfile,
    SystemStatus,
    TradeMode,
    TradeProposal,
)
from .types import StreamEvent


class SigmaxClient:
    """
    Async client for SIGMAX API.

    Provides full access to SIGMAX trading system including:
    - Market analysis (sync and streaming)
    - Trade proposal management
    - Proposal approval and execution
    - System status monitoring

    Example:
        ```python
        from sigmax_sdk import SigmaxClient

        async with SigmaxClient(api_key="your-key") as client:
            # Get system status
            status = await client.get_status()

            # Analyze a trading pair
            result = await client.analyze("BTC/USDT")

            # Stream analysis
            async for event in client.analyze_stream("ETH/USDT"):
                print(event)
        ```
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        api_key: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize SIGMAX client.

        Args:
            api_url: Base URL of SIGMAX API (default: http://localhost:8000)
            api_key: API authentication key (optional for local development)
            timeout: Request timeout in seconds (default: 60.0)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

        self.headers: dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "sigmax-sdk/1.0.0",
        }

        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> SigmaxClient:
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.headers,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers,
            )
        return self._client

    def _handle_error(self, response: httpx.Response) -> None:
        """
        Handle HTTP errors and raise appropriate exceptions.

        Args:
            response: HTTP response object

        Raises:
            SigmaxAuthenticationError: For 401/403 status codes
            SigmaxRateLimitError: For 429 status code
            SigmaxValidationError: For 400/422 status codes
            SigmaxAPIError: For other HTTP errors
        """
        if response.status_code == 401 or response.status_code == 403:
            raise SigmaxAuthenticationError(
                "Authentication failed. Check your API key.",
                status_code=response.status_code,
                response_body=response.text,
            )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise SigmaxRateLimitError(
                retry_after=int(retry_after) if retry_after else None
            )

        if response.status_code == 400 or response.status_code == 422:
            raise SigmaxValidationError(
                f"Validation error: {response.text}",
                details={"status_code": response.status_code},
            )

        raise SigmaxAPIError(
            f"API error: {response.text}",
            status_code=response.status_code,
            response_body=response.text,
        )

    async def analyze(
        self,
        symbol: str,
        risk_profile: RiskProfile = RiskProfile.CONSERVATIVE,
        mode: TradeMode = TradeMode.PAPER,
    ) -> dict[str, Any]:
        """
        Analyze a trading pair (synchronous, returns final result).

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")
            risk_profile: Risk profile for analysis
            mode: Trading mode (paper/live)

        Returns:
            Final analysis result as dictionary

        Raises:
            SigmaxAPIError: On API errors
            SigmaxConnectionError: On connection errors
            SigmaxTimeoutError: On timeout

        Example:
            ```python
            result = await client.analyze(
                "BTC/USDT",
                risk_profile=RiskProfile.MODERATE
            )
            ```
        """
        try:
            client = self._get_client()
            response = await client.post(
                f"{self.api_url}/api/chat/stream",
                json={
                    "message": f"Analyze {symbol}",
                    "symbol": symbol,
                    "risk_profile": risk_profile.value,
                    "mode": mode.value,
                },
            )

            if not response.is_success:
                self._handle_error(response)

            # Parse SSE stream and get final result
            final_result: dict[str, Any] = {}
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if "final" in line or data.get("final"):
                        final_result = data
                        break

            return final_result

        except httpx.TimeoutException as e:
            raise SigmaxTimeoutError(f"Request timeout: {e}") from e
        except httpx.ConnectError as e:
            raise SigmaxConnectionError(f"Connection failed: {e}") from e

    async def analyze_stream(
        self,
        symbol: str,
        risk_profile: RiskProfile = RiskProfile.CONSERVATIVE,
        mode: TradeMode = TradeMode.PAPER,
    ) -> AsyncIterator[StreamEvent]:
        """
        Analyze a trading pair with streaming progress updates.

        Yields server-sent events as analysis progresses.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")
            risk_profile: Risk profile for analysis
            mode: Trading mode (paper/live)

        Yields:
            StreamEvent dictionaries with analysis progress

        Raises:
            SigmaxAPIError: On API errors
            SigmaxConnectionError: On connection errors
            SigmaxTimeoutError: On timeout

        Example:
            ```python
            async for event in client.analyze_stream("ETH/USDT"):
                print(f"Status: {event.get('status')}")
                print(f"Message: {event.get('message')}")
            ```
        """
        try:
            client = self._get_client()
            async with aconnect_sse(
                client,
                "POST",
                f"{self.api_url}/api/chat/stream",
                json={
                    "message": f"Analyze {symbol}",
                    "symbol": symbol,
                    "risk_profile": risk_profile.value,
                    "mode": mode.value,
                },
            ) as event_source:
                async for sse in event_source.aiter_sse():
                    data = json.loads(sse.data)
                    yield StreamEvent(type=sse.event, **data)

        except httpx.TimeoutException as e:
            raise SigmaxTimeoutError(f"Request timeout: {e}") from e
        except httpx.ConnectError as e:
            raise SigmaxConnectionError(f"Connection failed: {e}") from e

    async def get_status(self) -> SystemStatus:
        """
        Get current SIGMAX system status.

        Returns:
            SystemStatus object with health and metrics

        Raises:
            SigmaxAPIError: On API errors
            SigmaxConnectionError: On connection errors

        Example:
            ```python
            status = await client.get_status()
            print(f"System: {status.status}")
            print(f"Active trades: {status.active_trades}")
            ```
        """
        try:
            client = self._get_client()
            response = await client.get(f"{self.api_url}/api/status")

            if not response.is_success:
                self._handle_error(response)

            return SystemStatus(**response.json())

        except httpx.ConnectError as e:
            raise SigmaxConnectionError(f"Connection failed: {e}") from e

    async def propose_trade(
        self,
        symbol: str,
        risk_profile: RiskProfile = RiskProfile.CONSERVATIVE,
        mode: TradeMode = TradeMode.PAPER,
        size: float | None = None,
    ) -> TradeProposal:
        """
        Create a trade proposal.

        Args:
            symbol: Trading pair symbol
            risk_profile: Risk profile for trade
            mode: Trading mode (paper/live)
            size: Optional trade size

        Returns:
            TradeProposal object

        Raises:
            SigmaxAPIError: On API errors
            SigmaxValidationError: On validation errors

        Example:
            ```python
            proposal = await client.propose_trade(
                "BTC/USDT",
                risk_profile=RiskProfile.MODERATE,
                size=0.1
            )
            print(f"Proposal ID: {proposal.proposal_id}")
            ```
        """
        try:
            request = ProposalCreateRequest(
                symbol=symbol,
                risk_profile=risk_profile,
                mode=mode,
                size=size,
            )

            client = self._get_client()
            response = await client.post(
                f"{self.api_url}/api/chat/proposals",
                json=request.model_dump(exclude_none=True),
                timeout=30.0,
            )

            if not response.is_success:
                self._handle_error(response)

            result = response.json()
            proposal_data = result.get("proposal", result)
            return TradeProposal(**proposal_data)

        except httpx.ConnectError as e:
            raise SigmaxConnectionError(f"Connection failed: {e}") from e

    async def list_proposals(self) -> dict[str, TradeProposal]:
        """
        List all trade proposals.

        Returns:
            Dictionary mapping proposal IDs to TradeProposal objects

        Example:
            ```python
            proposals = await client.list_proposals()
            for proposal_id, proposal in proposals.items():
                print(f"{proposal_id}: {proposal.status}")
            ```
        """
        try:
            client = self._get_client()
            response = await client.get(f"{self.api_url}/api/chat/proposals")

            if not response.is_success:
                self._handle_error(response)

            result = response.json()
            proposals_data = result.get("proposals", {})

            return {
                pid: TradeProposal(**data)
                for pid, data in proposals_data.items()
            }

        except httpx.ConnectError as e:
            raise SigmaxConnectionError(f"Connection failed: {e}") from e

    async def get_proposal(self, proposal_id: str) -> TradeProposal:
        """
        Get a specific trade proposal.

        Args:
            proposal_id: Unique proposal identifier

        Returns:
            TradeProposal object

        Raises:
            SigmaxAPIError: If proposal not found or on API errors

        Example:
            ```python
            proposal = await client.get_proposal("prop_123")
            print(f"Status: {proposal.status}")
            ```
        """
        try:
            client = self._get_client()
            response = await client.get(
                f"{self.api_url}/api/chat/proposals/{proposal_id}"
            )

            if not response.is_success:
                self._handle_error(response)

            return TradeProposal(**response.json())

        except httpx.ConnectError as e:
            raise SigmaxConnectionError(f"Connection failed: {e}") from e

    async def approve_proposal(self, proposal_id: str) -> dict[str, Any]:
        """
        Approve a trade proposal.

        Args:
            proposal_id: Unique proposal identifier

        Returns:
            Approval response dictionary

        Example:
            ```python
            result = await client.approve_proposal("prop_123")
            print(f"Approved: {result['success']}")
            ```
        """
        try:
            client = self._get_client()
            response = await client.post(
                f"{self.api_url}/api/chat/proposals/{proposal_id}/approve"
            )

            if not response.is_success:
                self._handle_error(response)

            return response.json()

        except httpx.ConnectError as e:
            raise SigmaxConnectionError(f"Connection failed: {e}") from e

    async def execute_proposal(self, proposal_id: str) -> dict[str, Any]:
        """
        Execute an approved trade proposal.

        Args:
            proposal_id: Unique proposal identifier

        Returns:
            Execution result dictionary

        Raises:
            SigmaxAPIError: If proposal not approved or on execution errors

        Example:
            ```python
            result = await client.execute_proposal("prop_123")
            print(f"Executed: {result.get('success')}")
            ```
        """
        try:
            client = self._get_client()
            response = await client.post(
                f"{self.api_url}/api/chat/proposals/{proposal_id}/execute",
                timeout=30.0,
            )

            if not response.is_success:
                self._handle_error(response)

            return response.json()

        except httpx.ConnectError as e:
            raise SigmaxConnectionError(f"Connection failed: {e}") from e

    async def close(self) -> None:
        """Close the HTTP client session."""
        if self._client:
            await self._client.aclose()
            self._client = None
