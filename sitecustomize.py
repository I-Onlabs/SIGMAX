"""Test harness compatibility helpers for SIGMAX."""

from __future__ import annotations

from pathlib import Path


def _ensure_expected_repo_path() -> None:
    """Create a symlink at /home/user/SIGMAX if the path is missing.

    The validation suite imports modules using an absolute path that resolves to
    ``/home/user/SIGMAX``. When the repository is checked out elsewhere (the
    default in the execution environment is ``/workspace/SIGMAX``), Python
    raises ``FileNotFoundError`` during module loading. Establishing a
    best-effort symlink keeps the tests decoupled from the host layout without
    requiring modifications to the validation code.
    """

    expected_root = Path("/home/user/SIGMAX")
    if expected_root.exists():
        return

    try:
        repo_root = Path(__file__).resolve().parent
        expected_root.parent.mkdir(parents=True, exist_ok=True)
        expected_root.symlink_to(repo_root, target_is_directory=True)
    except Exception:
        # Swallow any filesystem or permission errors so normal imports proceed
        # even if we cannot create the compatibility link.
        pass


_ensure_expected_repo_path()
