"""Pytest configuration and compatibility helpers for SIGMAX."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

EXPECTED_REPO_ROOT = Path("/home/user/SIGMAX")


def _ensure_expected_repo_path() -> None:
    """Create a symlink the validation suite expects."""
    if EXPECTED_REPO_ROOT.exists():
        return

    try:
        repo_root = Path(__file__).resolve().parent
        EXPECTED_REPO_ROOT.parent.mkdir(parents=True, exist_ok=True)
        EXPECTED_REPO_ROOT.symlink_to(repo_root, target_is_directory=True)
    except Exception:
        # The tests can still run from the actual checkout path if the symlink
        # cannot be created (e.g. permission errors in the CI environment).
        pass


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "asyncio: mark a test as requiring asyncio support")
    _ensure_expected_repo_path()


@pytest.fixture
def event_loop() -> asyncio.AbstractEventLoop:
    """Provide a dedicated event loop per test module."""
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool:
    """Execute coroutine tests without requiring external plugins."""
    if pyfuncitem.get_closest_marker("asyncio") is None:
        return False

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(pyfuncitem.obj(**pyfuncitem.funcargs))
    finally:
        asyncio.set_event_loop(None)
        loop.close()

    return True
