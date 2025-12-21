"""
SIGMAX SDK Streaming Example.

Demonstrates real-time streaming analysis with Server-Sent Events (SSE).
Shows progress updates as analysis runs.
"""

import asyncio
from datetime import datetime

from sigmax_sdk import RiskProfile, SigmaxAPIError, SigmaxClient, TradeMode


async def stream_analysis_with_progress(
    client: SigmaxClient,
    symbol: str,
    risk_profile: RiskProfile = RiskProfile.MODERATE,
) -> None:
    """
    Stream analysis for a symbol and display real-time progress.

    Args:
        client: SIGMAX client instance
        symbol: Trading pair to analyze
        risk_profile: Risk profile for analysis
    """
    print(f"\n{'='*60}")
    print(f"Streaming Analysis: {symbol}")
    print(f"Risk Profile: {risk_profile.value}")
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}\n")

    event_count = 0
    start_time = datetime.now()

    try:
        async for event in client.analyze_stream(
            symbol=symbol,
            risk_profile=risk_profile,
            mode=TradeMode.PAPER,
        ):
            event_count += 1
            event_type = event.get("type", "unknown")
            status = event.get("status", "")
            message = event.get("message", "")

            # Display event
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] Event #{event_count}")
            print(f"  Type: {event_type}")
            if status:
                print(f"  Status: {status}")
            if message:
                print(f"  Message: {message}")

            # Show additional data if present
            if "data" in event:
                data = event["data"]
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key not in ["type", "status", "message"]:
                            print(f"  {key}: {value}")

            # Check if final event
            if event.get("final") or event_type == "complete":
                print("\n✓ Analysis complete!")
                break

            print()  # Blank line between events

    except SigmaxAPIError as e:
        print(f"\n✗ Stream failed: {e.message}")
        if e.status_code:
            print(f"  Status code: {e.status_code}")

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n{'='*60}")
    print(f"Total events: {event_count}")
    print(f"Duration: {elapsed:.2f} seconds")
    print(f"{'='*60}")


async def compare_multiple_streams() -> None:
    """Stream analysis for multiple symbols concurrently."""
    async with SigmaxClient(api_url="http://localhost:8000") as client:
        print("\n" + "=" * 60)
        print("Concurrent Streaming Analysis")
        print("=" * 60)

        # Define symbols to analyze
        symbols = [
            ("BTC/USDT", RiskProfile.CONSERVATIVE),
            ("ETH/USDT", RiskProfile.MODERATE),
            ("SOL/USDT", RiskProfile.AGGRESSIVE),
        ]

        # Create tasks for concurrent streaming
        tasks = [
            stream_analysis_with_progress(client, symbol, risk)
            for symbol, risk in symbols
        ]

        # Run all streams concurrently
        await asyncio.gather(*tasks, return_exceptions=True)


async def single_stream_example() -> None:
    """Simple single-stream analysis example."""
    async with SigmaxClient(api_url="http://localhost:8000") as client:
        await stream_analysis_with_progress(
            client,
            "BTC/USDT",
            RiskProfile.MODERATE,
        )


async def filtered_stream_example() -> None:
    """Filter and process specific event types."""
    async with SigmaxClient(api_url="http://localhost:8000") as client:
        print("\n" + "=" * 60)
        print("Filtered Streaming (status events only)")
        print("=" * 60 + "\n")

        async for event in client.analyze_stream(
            "BTC/USDT",
            RiskProfile.MODERATE,
        ):
            # Only show status update events
            if event.get("type") == "status":
                timestamp = datetime.now().strftime("%H:%M:%S")
                status = event.get("status", "unknown")
                message = event.get("message", "")
                print(f"[{timestamp}] {status}: {message}")

            # Stop on completion
            if event.get("final") or event.get("type") == "complete":
                print("\nAnalysis finished!")
                break


async def main() -> None:
    """Run streaming examples."""
    print("\n" + "=" * 60)
    print("SIGMAX SDK - Streaming Examples")
    print("=" * 60)

    try:
        # Example 1: Single stream with full details
        print("\n\n=== Example 1: Single Stream ===")
        await single_stream_example()

        # Example 2: Filtered stream (status updates only)
        print("\n\n=== Example 2: Filtered Stream ===")
        await filtered_stream_example()

        # Uncomment to run concurrent streams (may be noisy)
        # print("\n\n=== Example 3: Concurrent Streams ===")
        # await compare_multiple_streams()

    except KeyboardInterrupt:
        print("\n\nStream interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
