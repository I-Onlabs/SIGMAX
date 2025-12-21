"""
SIGMAX SDK Error Handling Example.

Demonstrates comprehensive error handling patterns:
- Exception hierarchy
- Retry strategies
- Graceful degradation
- Error recovery
"""

import asyncio
from typing import Optional

from sigmax_sdk import (
    RiskProfile,
    SigmaxAPIError,
    SigmaxAuthenticationError,
    SigmaxClient,
    SigmaxConnectionError,
    SigmaxError,
    SigmaxRateLimitError,
    SigmaxTimeoutError,
    SigmaxValidationError,
)


async def handle_all_exceptions() -> None:
    """Demonstrate handling different exception types."""
    print("\n" + "=" * 60)
    print("Exception Handling Examples")
    print("=" * 60 + "\n")

    # Example with invalid API key
    print("1. Testing authentication error...")
    try:
        async with SigmaxClient(
            api_url="http://localhost:8000",
            api_key="invalid-key-123",
        ) as client:
            await client.get_status()
    except SigmaxAuthenticationError as e:
        print(f"   ✓ Caught authentication error: {e.message}")
        print(f"   Status code: {e.status_code}")

    # Example with connection error
    print("\n2. Testing connection error...")
    try:
        async with SigmaxClient(api_url="http://invalid-host:9999") as client:
            await client.get_status()
    except SigmaxConnectionError as e:
        print(f"   ✓ Caught connection error: {e.message}")

    # Example with validation error
    print("\n3. Testing validation error...")
    try:
        async with SigmaxClient(api_url="http://localhost:8000") as client:
            # Invalid symbol format
            await client.analyze(symbol="INVALID_SYMBOL_FORMAT_#@!")
    except SigmaxValidationError as e:
        print(f"   ✓ Caught validation error: {e.message}")
    except SigmaxAPIError as e:
        print(f"   ✓ Caught API error: {e.message}")

    # Example with timeout
    print("\n4. Testing timeout error...")
    try:
        async with SigmaxClient(
            api_url="http://localhost:8000",
            timeout=0.001,  # Very short timeout
        ) as client:
            await client.analyze("BTC/USDT")
    except SigmaxTimeoutError as e:
        print(f"   ✓ Caught timeout error: {e.message}")

    # Example with rate limit
    print("\n5. Testing rate limit handling...")
    try:
        # This would trigger if rate limits are enforced
        async with SigmaxClient(api_url="http://localhost:8000") as client:
            # Make rapid requests
            for _ in range(100):
                await client.get_status()
    except SigmaxRateLimitError as e:
        print(f"   ✓ Caught rate limit error: {e.message}")
        if e.retry_after:
            print(f"   Retry after: {e.retry_after} seconds")
    except SigmaxAPIError:
        print("   Rate limits not enforced or different API error")


async def safe_analysis(
    client: SigmaxClient,
    symbol: str,
    max_retries: int = 3,
) -> Optional[dict]:
    """
    Analyze with comprehensive error handling and retries.

    Args:
        client: SIGMAX client instance
        symbol: Trading pair to analyze
        max_retries: Maximum retry attempts

    Returns:
        Analysis result or None on failure
    """
    for attempt in range(max_retries):
        try:
            print(f"Analyzing {symbol} (attempt {attempt + 1}/{max_retries})...")
            result = await client.analyze(symbol, RiskProfile.MODERATE)
            print(f"✓ Success!")
            return result

        except SigmaxAuthenticationError as e:
            print(f"✗ Authentication failed: {e.message}")
            print("  Cannot retry - invalid credentials")
            return None

        except SigmaxValidationError as e:
            print(f"✗ Validation error: {e.message}")
            print("  Cannot retry - invalid request")
            return None

        except SigmaxRateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = e.retry_after or 5
                print(f"  Rate limited, waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                print("  Max retries reached")
                return None

        except SigmaxTimeoutError as e:
            if attempt < max_retries - 1:
                print(f"  Timeout, retrying...")
                await asyncio.sleep(2**attempt)  # Exponential backoff
            else:
                print(f"  Max retries reached: {e.message}")
                return None

        except SigmaxConnectionError as e:
            if attempt < max_retries - 1:
                print(f"  Connection failed, retrying...")
                await asyncio.sleep(2**attempt)
            else:
                print(f"  Max retries reached: {e.message}")
                return None

        except SigmaxAPIError as e:
            print(f"✗ API error: {e.message}")
            if e.status_code and e.status_code >= 500:
                # Server error, might be transient
                if attempt < max_retries - 1:
                    print("  Server error, retrying...")
                    await asyncio.sleep(2**attempt)
                    continue
            return None

        except SigmaxError as e:
            print(f"✗ Unexpected SIGMAX error: {e.message}")
            return None

    return None


async def graceful_degradation() -> None:
    """Demonstrate graceful degradation when services are unavailable."""
    print("\n" + "=" * 60)
    print("Graceful Degradation Example")
    print("=" * 60 + "\n")

    async with SigmaxClient(api_url="http://localhost:8000") as client:
        # Try to get system status
        print("Checking system health...")
        try:
            status = await client.get_status()
            api_available = status.api_health
            db_available = status.database_health
            exchange_available = status.exchange_health

            print(f"API: {'✓' if api_available else '✗'}")
            print(f"Database: {'✓' if db_available else '✗'}")
            print(f"Exchange: {'✓' if exchange_available else '✗'}")

            if not all([api_available, db_available, exchange_available]):
                print("\n⚠ System partially degraded, limiting operations...")

                # Only attempt read operations
                if api_available:
                    print("  Can perform: Status checks")
                if db_available:
                    print("  Can perform: Proposal listing")
                if not exchange_available:
                    print("  Cannot perform: Live trading, market analysis")

        except SigmaxConnectionError:
            print("✗ API completely unavailable")
            print("  Falling back to cached data or manual operations")

        # Attempt analysis with fallback
        print("\nAttempting analysis with fallback...")
        result = await safe_analysis(client, "BTC/USDT")

        if result:
            print("✓ Analysis succeeded")
        else:
            print("✗ Analysis failed, using fallback strategy")
            print("  Fallback: Manual analysis or cached recommendations")


async def batch_with_error_handling() -> None:
    """Batch operations with individual error handling."""
    print("\n" + "=" * 60)
    print("Batch Operations with Error Handling")
    print("=" * 60 + "\n")

    symbols = ["BTC/USDT", "ETH/USDT", "INVALID/PAIR", "SOL/USDT"]

    async with SigmaxClient(api_url="http://localhost:8000") as client:
        print(f"Analyzing {len(symbols)} symbols...\n")

        results = []
        for symbol in symbols:
            result = await safe_analysis(client, symbol, max_retries=2)
            results.append((symbol, result))
            print()

        # Summary
        successful = sum(1 for _, result in results if result is not None)
        print(f"\nResults: {successful}/{len(symbols)} successful")

        for symbol, result in results:
            status = "✓" if result else "✗"
            print(f"  {status} {symbol}")


async def context_manager_error_handling() -> None:
    """Demonstrate context manager error handling."""
    print("\n" + "=" * 60)
    print("Context Manager Error Handling")
    print("=" * 60 + "\n")

    try:
        async with SigmaxClient(api_url="http://localhost:8000") as client:
            print("Client initialized")
            # Simulate error during operation
            raise ValueError("Simulated error during operation")

    except ValueError as e:
        print(f"Caught error: {e}")
        print("Client was properly closed despite error")


async def main() -> None:
    """Run error handling examples."""
    print("=" * 60)
    print("SIGMAX SDK - Error Handling Examples")
    print("=" * 60)

    try:
        # Example 1: Handle all exception types
        await handle_all_exceptions()

        # Example 2: Graceful degradation
        await graceful_degradation()

        # Example 3: Batch with error handling
        await batch_with_error_handling()

        # Example 4: Context manager cleanup
        await context_manager_error_handling()

    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        raise

    print("\n" + "=" * 60)
    print("Error handling examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
