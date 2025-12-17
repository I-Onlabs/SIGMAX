"""
Authentication helpers for SIGMAX FastAPI.

Separated from `main.py` to avoid circular imports with route modules.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger


security = HTTPBearer(auto_error=False)


def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> bool:
    """Verify API key from environment."""
    api_key = os.getenv("SIGMAX_API_KEY")

    # If no API key configured, allow all requests (development mode)
    if not api_key:
        logger.warning("⚠️ No API key configured - running in open mode")
        return True

    if not credentials or credentials.credentials != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True

