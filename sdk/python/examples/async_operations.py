"""
SIGMAX SDK Async Operations Example.

Demonstrates advanced async patterns:
- Concurrent batch operations
- Task gathering with error handling
- Async context management
- Retry patterns
"""

import asyncio
from typing import Any

from sigmax_sdk import (
    RiskProfile,
    SigmaxAPIError,
    SigmaxClient,
    SigmaxTimeoutError,
    TradeMode,
)


async def batch_analysis(
    client: SigmaxClient,
    symbols: list[str],
    risk_profile: RiskProfile = RiskProfile.MODERATE,
) -> dict[str, Any]:
    """
    Analyze multiple symbols concurrently.

    Args:
        client: SIGMAX client instance
        symbols: List of trading pairs to analyze
        risk_profile: Risk profile for all analyses

    Returns:
        Dictionary mapping symbols to analysis results
    """
    print(f"\nAnalyzing {len(symbols)} symbols concurrently...")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Risk Profile: {risk_profile.value}\n")

    # Create concurrent tasks
    tasks = {
        symbol: client.analyze(symbol, risk_profile, TradeMode.PAPER)
        for symbol in symbols
    }

    # Gather results with error handling
    results = await asyncio.gather(
        *tasks.values(),
        return_exceptions=True,
    )

    # Process results
    analysis_results = {}
    for symbol, result in zip(symbols, results):
        if isinstance(result, Exception):
            print(f"✗ {symbol}: Failed - {result}")
            analysis_results[symbol] = {"error": str(result)}
        else:
            print(f"✓ {symbol}: Success")
            analysis_results[symbol] = result

    return analysis_results


async def retry_with_backoff(
    client: SigmaxClient,
    symbol: str,
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> dict[str, Any]:
    """
    Retry analysis with exponential backoff.

    Args:
        client: SIGMAX client instance
        symbol: Trading pair to analyze
        max_retries: Maximum retry attempts
        base_delay: Base delay for exponential backoff

    Returns:
        Analysis result

    Raises:
        SigmaxAPIError: If all retries fail
    """
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries} for {symbol}...")
            result = await client.analyze(symbol)
            print(f"✓ {symbol} analysis succeeded")
            return result

        except SigmaxTimeoutError:
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                print(f"  Timeout, retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                print(f"✗ {symbol} failed after {max_retries} attempts")
                raise

        except SigmaxAPIError as e:
            print(f"✗ {symbol} API error: {e.message}")
            raise

    raise SigmaxAPIError(f"Failed to analyze {symbol} after {max_retries} attempts")


async def proposal_workflow(client: SigmaxClient, symbol: str) -> None:
    """
    Complete proposal workflow: create, approve, execute.

    Args:
        client: SIGMAX client instance
        symbol: Trading pair for proposal
    """
    print(f"\n{'='*60}")
    print(f"Trade Proposal Workflow: {symbol}")
    print(f"{'='*60}\n")

    try:
        # Step 1: Create proposal
        print("1. Creating trade proposal...")
        proposal = await client.propose_trade(
            symbol=symbol,
            risk_profile=RiskProfile.MODERATE,
            mode=TradeMode.PAPER,
            size=0.1,
        )
        print(f"   ✓ Proposal created: {proposal.proposal_id}")
        print(f"   - Side: {proposal.side}")
        print(f"   - Size: {proposal.size}")
        print(f"   - Status: {proposal.status}")
        print(f"   - Rationale: {proposal.rationale[:100]}...")

        # Step 2: Get proposal details
        print("\n2. Retrieving proposal details...")
        retrieved = await client.get_proposal(proposal.proposal_id)
        print(f"   ✓ Retrieved: {retrieved.proposal_id}")
        print(f"   - Status: {retrieved.status}")

        # Step 3: Approve proposal
        print("\n3. Approving proposal...")
        approval = await client.approve_proposal(proposal.proposal_id)
        print(f"   ✓ Approval result: {approval}")

        # Step 4: Execute proposal
        print("\n4. Executing proposal...")
        execution = await client.execute_proposal(proposal.proposal_id)
        print(f"   ✓ Execution result: {execution}")

        print(f"\n{'='*60}")
        print("Workflow completed successfully!")
        print(f"{'='*60}")

    except SigmaxAPIError as e:
        print(f"\n✗ Workflow failed: {e.message}")
        if e.status_code:
            print(f"   Status code: {e.status_code}")


async def parallel_proposals(
    client: SigmaxClient,
    symbols: list[str],
) -> None:
    """
    Create multiple proposals in parallel.

    Args:
        client: SIGMAX client instance
        symbols: List of symbols to create proposals for
    """
    print(f"\nCreating {len(symbols)} proposals in parallel...")

    # Create proposals concurrently
    tasks = [
        client.propose_trade(
            symbol=symbol,
            risk_profile=RiskProfile.MODERATE,
            mode=TradeMode.PAPER,
        )
        for symbol in symbols
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Display results
    successful = 0
    failed = 0

    for symbol, result in zip(symbols, results):
        if isinstance(result, Exception):
            print(f"✗ {symbol}: {result}")
            failed += 1
        else:
            print(f"✓ {symbol}: {result.proposal_id}")
            successful += 1

    print(f"\nResults: {successful} successful, {failed} failed")


async def monitor_system(client: SigmaxClient, interval: float = 5.0, count: int = 5) -> None:
    """
    Monitor system status periodically.

    Args:
        client: SIGMAX client instance
        interval: Seconds between checks
        count: Number of checks to perform
    """
    print(f"\nMonitoring system status ({count} checks, {interval}s interval)...\n")

    for i in range(count):
        try:
            status = await client.get_status()
            print(f"[Check {i+1}/{count}]")
            print(f"  Status: {status.status}")
            print(f"  Active Trades: {status.active_trades}")
            print(f"  Pending Proposals: {status.pending_proposals}")
            print(f"  API Health: {'✓' if status.api_health else '✗'}")

            if i < count - 1:
                await asyncio.sleep(interval)

        except SigmaxAPIError as e:
            print(f"  ✗ Status check failed: {e.message}")

        print()


async def main() -> None:
    """Run async operation examples."""
    print("=" * 60)
    print("SIGMAX SDK - Async Operations Examples")
    print("=" * 60)

    async with SigmaxClient(api_url="http://localhost:8000") as client:
        # Example 1: Batch analysis
        print("\n\n=== Example 1: Batch Analysis ===")
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT"]
        await batch_analysis(client, symbols, RiskProfile.MODERATE)

        # Example 2: Retry with backoff
        print("\n\n=== Example 2: Retry with Backoff ===")
        try:
            await retry_with_backoff(client, "BTC/USDT", max_retries=3)
        except SigmaxAPIError as e:
            print(f"Final error: {e}")

        # Example 3: Complete proposal workflow
        print("\n\n=== Example 3: Proposal Workflow ===")
        await proposal_workflow(client, "BTC/USDT")

        # Example 4: Parallel proposals
        print("\n\n=== Example 4: Parallel Proposals ===")
        await parallel_proposals(client, ["BTC/USDT", "ETH/USDT"])

        # Example 5: System monitoring
        print("\n\n=== Example 5: System Monitoring ===")
        await monitor_system(client, interval=2.0, count=3)

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        raise
