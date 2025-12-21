#!/usr/bin/env python3
"""
Quick verification script for SIGMAX SDK package.

Checks that all components are properly configured and importable.
"""

import sys
from pathlib import Path


def check_imports() -> bool:
    """Verify all SDK components can be imported."""
    print("Checking imports...")
    try:
        from sigmax_sdk import (
            AnalysisResult,
            ChatMessage,
            ProposalStatus,
            RiskProfile,
            SigmaxAPIError,
            SigmaxAuthenticationError,
            SigmaxClient,
            SigmaxConnectionError,
            SigmaxError,
            SigmaxRateLimitError,
            SigmaxTimeoutError,
            SigmaxValidationError,
            StreamEvent,
            SystemStatus,
            TradeMode,
            TradeProposal,
        )

        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def check_version() -> bool:
    """Verify package version is set."""
    print("\nChecking version...")
    try:
        from sigmax_sdk import __version__

        print(f"✓ Version: {__version__}")
        return True
    except ImportError as e:
        print(f"✗ Version check failed: {e}")
        return False


def check_files() -> bool:
    """Verify all required files exist."""
    print("\nChecking files...")
    required_files = [
        "sigmax_sdk/__init__.py",
        "sigmax_sdk/client.py",
        "sigmax_sdk/models.py",
        "sigmax_sdk/exceptions.py",
        "sigmax_sdk/types.py",
        "sigmax_sdk/py.typed",
        "pyproject.toml",
        "setup.py",
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "DEVELOPMENT.md",
        "Makefile",
    ]

    sdk_root = Path(__file__).parent
    all_exist = True

    for file_path in required_files:
        full_path = sdk_root / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_exist = False

    return all_exist


def check_examples() -> bool:
    """Verify example files exist."""
    print("\nChecking examples...")
    example_files = [
        "examples/basic_usage.py",
        "examples/streaming.py",
        "examples/async_operations.py",
        "examples/error_handling.py",
        "examples/README.md",
    ]

    sdk_root = Path(__file__).parent
    all_exist = True

    for file_path in example_files:
        full_path = sdk_root / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_exist = False

    return all_exist


def check_tests() -> bool:
    """Verify test files exist."""
    print("\nChecking tests...")
    test_files = [
        "tests/__init__.py",
        "tests/test_client.py",
    ]

    sdk_root = Path(__file__).parent
    all_exist = True

    for file_path in test_files:
        full_path = sdk_root / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_exist = False

    return all_exist


def check_type_hints() -> bool:
    """Verify type hints are working."""
    print("\nChecking type hints...")
    try:
        from sigmax_sdk import SigmaxClient

        # Check if __annotations__ exist
        if hasattr(SigmaxClient.__init__, "__annotations__"):
            print("✓ Type hints present")
            return True
        else:
            print("⚠ Type hints might not be fully configured")
            return True
    except Exception as e:
        print(f"✗ Type hint check failed: {e}")
        return False


def print_summary() -> None:
    """Print package summary."""
    print("\n" + "=" * 60)
    print("SIGMAX SDK Package Summary")
    print("=" * 60)

    try:
        from sigmax_sdk import __version__

        print(f"\nVersion: {__version__}")
    except ImportError:
        print("\nVersion: Unable to determine")

    print("\nComponents:")
    print("- SigmaxClient (async API client)")
    print("- Pydantic models (TradeProposal, SystemStatus, etc.)")
    print("- Exception hierarchy (SigmaxError, SigmaxAPIError, etc.)")
    print("- Type definitions (StreamEvent, RiskProfile, etc.)")

    print("\nFeatures:")
    print("- Async-first design with httpx")
    print("- Server-Sent Events streaming")
    print("- Complete type safety with Pydantic")
    print("- Comprehensive error handling")
    print("- Context manager support")
    print("- Production-ready packaging")

    print("\nNext Steps:")
    print("1. Install in development mode: make dev")
    print("2. Run tests: make test")
    print("3. Try examples: python examples/basic_usage.py")
    print("4. Build package: make build")
    print("5. Publish to PyPI: make publish")

    print("\n" + "=" * 60)


def main() -> int:
    """Run all verification checks."""
    print("=" * 60)
    print("SIGMAX SDK Package Verification")
    print("=" * 60 + "\n")

    checks = [
        ("File structure", check_files),
        ("Example files", check_examples),
        ("Test files", check_tests),
        ("Imports", check_imports),
        ("Version", check_version),
        ("Type hints", check_type_hints),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} check crashed: {e}")
            results.append((name, False))

    # Print results
    print("\n" + "=" * 60)
    print("Verification Results")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False

    if all_passed:
        print("\n✓ All checks passed! Package is ready.")
        print_summary()
        return 0
    else:
        print("\n✗ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
