"""
Basic SIGMAX SDK Usage Example.

Demonstrates core functionality including:
- System status checks
- Market analysis
- Error handling
"""

import asyncio
from decimal import Decimal

from sigmax_sdk import (
    RiskProfile,
    SigmaxAPIError,
    SigmaxClient,
    SigmaxConnectionError,
    TradeMode,
)


async def main() -> None:
    """Run basic SDK operations."""
    # Initialize client (adjust URL for your deployment)
    async with SigmaxClient(
        api_url="http://localhost:8000",
        api_key=None,  # Set to your API key if required
        timeout=60.0,
    ) as client:
        print("=" * 60)
        print("SIGMAX SDK - Basic Usage Example")
        print("=" * 60)

        # 1. Check system status
        print("\n1. Checking system status...")
        try:
            status = await client.get_status()
            print(f"   System Status: {status.status}")
            print(f"   Version: {status.version}")
            print(f"   Uptime: {status.uptime_seconds:.2f} seconds")
            print(f"   Active Trades: {status.active_trades}")
            print(f"   Pending Proposals: {status.pending_proposals}")
            print(f"   Mode: {status.mode}")
            print(f"   API Health: {'✓' if status.api_health else '✗'}")
            print(f"   Database Health: {'✓' if status.database_health else '✗'}")
            print(f"   Exchange Health: {'✓' if status.exchange_health else '✗'}")
        except SigmaxConnectionError as e:
            print(f"   ✗ Connection failed: {e}")
            return
        except SigmaxAPIError as e:
            print(f"   ✗ API error: {e.message}")
            return

        # 2. Analyze a trading pair (synchronous)
        print("\n2. Analyzing BTC/USDT (conservative)...")
        try:
            result = await client.analyze(
                symbol="BTC/USDT",
                risk_profile=RiskProfile.CONSERVATIVE,
                mode=TradeMode.PAPER,
            )
            print(f"   Analysis complete:")
            if result:
                print(f"   - Symbol: {result.get('symbol', 'N/A')}")
                print(f"   - Recommendation: {result.get('recommendation', 'N/A')}")
                print(f"   - Confidence: {result.get('confidence', 'N/A')}")
                print(f"   - Analysis: {result.get('analysis', 'N/A')[:100]}...")
            else:
                print("   No result returned")
        except SigmaxAPIError as e:
            print(f"   ✗ Analysis failed: {e.message}")

        # 3. Analyze another pair with different risk profile
        print("\n3. Analyzing ETH/USDT (moderate)...")
        try:
            result = await client.analyze(
                symbol="ETH/USDT",
                risk_profile=RiskProfile.MODERATE,
                mode=TradeMode.PAPER,
            )
            print(f"   Analysis complete:")
            if result:
                print(f"   - Symbol: {result.get('symbol', 'N/A')}")
                print(f"   - Recommendation: {result.get('recommendation', 'N/A')}")
                print(f"   - Risk Level: {result.get('risk_level', 'N/A')}")
        except SigmaxAPIError as e:
            print(f"   ✗ Analysis failed: {e.message}")

        # 4. List all proposals
        print("\n4. Listing trade proposals...")
        try:
            proposals = await client.list_proposals()
            print(f"   Found {len(proposals)} proposal(s)")
            for proposal_id, proposal in list(proposals.items())[:5]:  # Show first 5
                print(f"   - {proposal_id}:")
                print(f"     Status: {proposal.status}")
                print(f"     Symbol: {proposal.symbol}")
                print(f"     Side: {proposal.side}")
                print(f"     Size: {proposal.size}")
        except SigmaxAPIError as e:
            print(f"   ✗ Failed to list proposals: {e.message}")

        print("\n" + "=" * 60)
        print("Example completed successfully!")
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        raise
