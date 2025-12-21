"""
SIGMAX SDK Exceptions.

Custom exception hierarchy for the SIGMAX SDK.
"""

from __future__ import annotations

from typing import Any, Optional


class SigmaxError(Exception):
    """Base exception for all SIGMAX SDK errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """
        Initialize exception.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SigmaxAPIError(SigmaxError):
    """API-level error from SIGMAX server."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ) -> None:
        """
        Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
            response_body: Raw response body
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class SigmaxAuthenticationError(SigmaxAPIError):
    """Authentication failed (401/403)."""

    pass


class SigmaxRateLimitError(SigmaxAPIError):
    """Rate limit exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ) -> None:
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retry
        """
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class SigmaxValidationError(SigmaxError):
    """Request validation failed."""

    pass


class SigmaxConnectionError(SigmaxError):
    """Network connection error."""

    pass


class SigmaxTimeoutError(SigmaxError):
    """Request timeout."""

    pass
