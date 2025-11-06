#!/usr/bin/env python3
"""
SIGMAX Basic Usage Example
Demonstrates how to use the SIGMAX API client
"""

import asyncio
import os
from typing import Dict, Any
import httpx


class SIGMAXClient:
    """Simple SIGMAX API client"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key or os.getenv("SIGMAX_API_KEY")
        self.headers = {}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    async def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()

    async def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/status", headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def analyze_symbol(
        self, symbol: str, include_debate: bool = False
    ) -> Dict[str, Any]:
        """Analyze a trading symbol"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/analyze",
                headers=self.headers,
                json={"symbol": symbol, "include_debate": include_debate},
            )
            response.raise_for_status()
            return response.json()

    async def get_portfolio(self) -> Dict[str, Any]:
        """Get portfolio"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/portfolio", headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_debate(self, symbol: str) -> Dict[str, Any]:
        """Get agent debate for a symbol"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/agents/debate/{symbol}", headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def execute_trade(
        self, symbol: str, action: str, size: float
    ) -> Dict[str, Any]:
        """Execute a trade"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/trade",
                headers=self.headers,
                json={"symbol": symbol, "action": action, "size": size},
            )
            response.raise_for_status()
            return response.json()


async def main():
    """Main example function"""
    print("🤖 SIGMAX API Client Example\n")

    # Initialize client
    client = SIGMAXClient()

    # 1. Check health
    print("1. Checking API health...")
    health = await client.health_check()
    print(f"   Status: {health['status']}")
    print()

    # 2. Get system status
    print("2. Getting system status...")
    status = await client.get_status()
    print(f"   Running: {status['running']}")
    print(f"   Mode: {status['mode']}")
    print(f"   Active Agents: {len(status['agents'])}")
    print()

    # 3. Analyze a symbol
    print("3. Analyzing BTC/USDT...")
    analysis = await client.analyze_symbol("BTC/USDT")
    print(f"   Decision: {analysis['decision']}")
    print(f"   Confidence: {analysis['confidence']:.2%}")
    print(f"   Bull: {analysis['reasoning']['bull'][:60]}...")
    print(f"   Bear: {analysis['reasoning']['bear'][:60]}...")
    print()

    # 4. Get agent debate
    print("4. Getting agent debate...")
    debate = await client.get_debate("BTC/USDT")
    print(f"   Debate messages: {len(debate['debate'])}")
    print(f"   Bull score: {debate['summary']['bull_score']}")
    print(f"   Bear score: {debate['summary']['bear_score']}")
    print()

    # 5. Get portfolio
    print("5. Getting portfolio...")
    portfolio = await client.get_portfolio()
    print(f"   Total value: ${portfolio['total_value']:.2f}")
    print(f"   Positions: {len(portfolio['positions'])}")
    print(f"   Cash: ${portfolio['cash']:.2f}")
    print()

    # 6. Execute paper trade (only in paper mode!)
    print("6. Executing paper trade...")
    print("   ⚠️  This is for demonstration only!")
    # Uncomment to execute:
    # trade = await client.execute_trade("BTC/USDT", "buy", 0.0001)
    # print(f"   Order ID: {trade['order_id']}")
    # print(f"   Status: {trade['status']}")
    print("   (Skipped for safety)")
    print()

    print("✅ Example completed successfully!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code}")
        print(f"   {e.response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Error: {e}")
