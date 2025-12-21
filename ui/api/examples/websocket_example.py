"""
SIGMAX WebSocket Client Examples
Demonstrates various usage patterns for real-time trading data.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.websocket_client import SigmaxWebSocketClient, connect_sigmax, WSEvent
from loguru import logger


# Example 1: Basic Connection and Subscription
async def basic_example():
    """Basic connection and event listening"""
    logger.info("=== Basic Example ===")

    client = SigmaxWebSocketClient()
    await client.connect("ws://localhost:8000/api/ws")

    # Subscribe to proposals and executions
    await client.subscribe(topics=["proposals", "executions"])

    # Listen for 10 events
    count = 0
    async for event in client.listen():
        logger.info(f"Event {count + 1}: {event.type}")
        logger.info(f"Data: {event.data}")
        count += 1

        if count >= 10:
            break

    await client.disconnect()


# Example 2: Symbol-Specific Monitoring
async def symbol_monitoring_example():
    """Monitor specific trading symbols"""
    logger.info("=== Symbol Monitoring Example ===")

    client = await connect_sigmax(
        symbols=["BTC/USDT", "ETH/USDT"],
        topics=["market", "analysis"]
    )

    async for event in client.listen():
        if event.type == "market_update":
            for market in event.data:
                logger.info(
                    f"{market['symbol']}: ${market['price']:,.2f} "
                    f"(24h: {market['change_24h']:+.2f}%)"
                )

        elif event.type == "analysis_update":
            logger.info(
                f"Analysis: {event.data['symbol']} - "
                f"{event.data['decision']} (confidence: {event.data['confidence']:.2%})"
            )


# Example 3: Trading Activity Monitor
async def trading_monitor_example():
    """Monitor all trading activity"""
    logger.info("=== Trading Monitor Example ===")

    client = await connect_sigmax(
        topics=["proposals", "executions", "analysis"]
    )

    async for event in client.listen():
        if event.type == "proposal_created":
            data = event.data
            logger.success(
                f"📝 New Proposal [{data['proposal_id']}]: "
                f"{data['action'].upper()} {data['size']} {data['symbol']}"
            )

        elif event.type == "proposal_approved":
            logger.info(f"✅ Proposal Approved: {event.data['proposal_id']}")

        elif event.type == "trade_executed":
            data = event.data
            logger.success(
                f"💰 Trade Executed: {data['action'].upper()} {data['size']} "
                f"{data['symbol']} @ ${data['filled_price']:,.2f}"
            )

        elif event.type == "analysis_update":
            data = event.data
            logger.info(
                f"📊 Analysis: {data['symbol']} - {data['decision'].upper()} "
                f"(confidence: {data['confidence']:.2%})"
            )


# Example 4: Portfolio Dashboard
async def portfolio_dashboard_example():
    """Real-time portfolio monitoring dashboard"""
    logger.info("=== Portfolio Dashboard Example ===")

    client = await connect_sigmax(
        topics=["portfolio", "executions", "health"]
    )

    async for event in client.listen():
        if event.type == "portfolio_update":
            data = event.data
            logger.info("\n" + "=" * 60)
            logger.info("💼 PORTFOLIO UPDATE")
            logger.info("=" * 60)
            logger.info(f"Total Value:     ${data['total_value']:>15,.2f}")
            logger.info(f"Available Cash:  ${data['available_cash']:>15,.2f}")
            logger.info(f"Total P&L:       ${data['total_pnl']:>15,.2f} ({data['total_pnl_percent']:+.2f}%)")
            logger.info("-" * 60)

            if data.get('positions'):
                logger.info("POSITIONS:")
                for pos in data['positions']:
                    logger.info(
                        f"  {pos['symbol']:<12} | "
                        f"Size: {pos['size']:>10} | "
                        f"Price: ${pos['current_price']:>10,.2f} | "
                        f"P&L: ${pos['pnl']:>10,.2f} ({pos['pnl_percent']:+.2f}%)"
                    )
            logger.info("=" * 60 + "\n")

        elif event.type == "trade_executed":
            data = event.data
            logger.success(
                f"🔔 Trade: {data['action'].upper()} {data['size']} {data['symbol']} "
                f"@ ${data['filled_price']:,.2f}"
            )

        elif event.type == "health_update":
            health = event.data
            logger.debug(
                f"❤️ System Health: CPU {health['cpu_percent']:.1f}% | "
                f"Memory {health['memory_percent']:.1f}%"
            )


# Example 5: Event Callbacks
async def event_callback_example():
    """Using event callbacks for custom handling"""
    logger.info("=== Event Callback Example ===")

    # Define handlers
    def handle_proposal(event: WSEvent):
        if event.type == "proposal_created":
            data = event.data
            logger.info(f"🔔 New Proposal: {data['symbol']} - {data['action']}")

            # Could trigger external actions here
            # e.g., send notification, update UI, etc.

    def handle_trade(event: WSEvent):
        if event.type == "trade_executed":
            data = event.data
            logger.success(
                f"✅ Trade Executed: {data['symbol']} @ ${data['filled_price']:,.2f}"
            )

            # Could update database, send alerts, etc.

    def handle_analysis(event: WSEvent):
        if event.type == "analysis_update":
            data = event.data
            logger.info(
                f"📊 Analysis: {data['symbol']} - {data['decision']} "
                f"(conf: {data['confidence']:.2%})"
            )

    # Create client with callbacks
    client = SigmaxWebSocketClient()
    client.on_event(handle_proposal)
    client.on_event(handle_trade)
    client.on_event(handle_analysis)

    await client.connect("ws://localhost:8000/api/ws")
    await client.subscribe(topics=["proposals", "executions", "analysis"])

    # Keep listening
    async for event in client.listen():
        # Callbacks are called automatically
        pass


# Example 6: Multi-Symbol Analysis
async def multi_symbol_analysis_example():
    """Analyze multiple symbols simultaneously"""
    logger.info("=== Multi-Symbol Analysis Example ===")

    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT"]

    client = await connect_sigmax(
        symbols=symbols,
        topics=["analysis", "market"]
    )

    # Track analysis results
    analysis_results = {}

    async for event in client.listen():
        if event.type == "analysis_update":
            data = event.data
            symbol = data['symbol']
            analysis_results[symbol] = data

            logger.info(f"\n📊 Analysis for {symbol}:")
            logger.info(f"  Decision:   {data['decision'].upper()}")
            logger.info(f"  Confidence: {data['confidence']:.2%}")
            logger.info(f"  Bull Score: {data.get('bull_score', 'N/A')}")
            logger.info(f"  Bear Score: {data.get('bear_score', 'N/A')}")
            logger.info(f"  Reasoning:  {data.get('reasoning', 'N/A')}")

            # Show summary
            if len(analysis_results) >= len(symbols):
                logger.info("\n" + "=" * 60)
                logger.info("SUMMARY")
                logger.info("=" * 60)
                for sym, res in analysis_results.items():
                    logger.info(
                        f"{sym:<12} | {res['decision'].upper():<6} | "
                        f"Conf: {res['confidence']:.2%}"
                    )
                logger.info("=" * 60 + "\n")


# Example 7: System Health Monitoring
async def health_monitoring_example():
    """Monitor system health metrics"""
    logger.info("=== Health Monitoring Example ===")

    client = await connect_sigmax(topics=["health", "status"])

    async for event in client.listen():
        if event.type == "health_update":
            data = event.data
            cpu = data['cpu_percent']
            memory = data['memory_percent']
            disk = data['disk_percent']

            # Color-coded health status
            cpu_status = "🟢" if cpu < 70 else "🟡" if cpu < 90 else "🔴"
            mem_status = "🟢" if memory < 70 else "🟡" if memory < 90 else "🔴"
            disk_status = "🟢" if disk < 70 else "🟡" if disk < 90 else "🔴"

            logger.info(
                f"System Health: "
                f"{cpu_status} CPU {cpu:.1f}% | "
                f"{mem_status} Memory {memory:.1f}% | "
                f"{disk_status} Disk {disk:.1f}%"
            )

            # Alert on high usage
            if cpu > 90 or memory > 90:
                logger.warning("⚠️ High system resource usage detected!")

        elif event.type == "system_status":
            data = event.data
            logger.info(
                f"System Status: {'🟢 Running' if data.get('running') else '🔴 Stopped'} | "
                f"Mode: {data.get('mode', 'unknown').upper()} | "
                f"Risk Profile: {data.get('risk_profile', 'unknown')}"
            )


# Example 8: Reconnection Handling
async def reconnection_example():
    """Demonstrate automatic reconnection"""
    logger.info("=== Reconnection Example ===")

    client = SigmaxWebSocketClient(
        auto_reconnect=True,
        max_reconnect_delay=30.0
    )

    await client.connect("ws://localhost:8000/api/ws")
    await client.subscribe(topics=["status", "health"])

    logger.info("Client connected. Try stopping and restarting the server...")
    logger.info("Client will automatically reconnect and restore subscriptions.")

    while True:
        try:
            async for event in client.listen():
                if event.type == "connected":
                    logger.success("✅ Connected to server!")

                elif event.type == "system_status":
                    logger.info(f"Status: {event.data.get('running', 'unknown')}")

        except Exception as e:
            logger.error(f"Error: {e}")
            if client.auto_reconnect:
                logger.info("Waiting for reconnection...")
                await asyncio.sleep(5)
            else:
                break


# Main Menu
async def main():
    """Main menu for selecting examples"""
    examples = {
        "1": ("Basic Connection", basic_example),
        "2": ("Symbol Monitoring", symbol_monitoring_example),
        "3": ("Trading Activity Monitor", trading_monitor_example),
        "4": ("Portfolio Dashboard", portfolio_dashboard_example),
        "5": ("Event Callbacks", event_callback_example),
        "6": ("Multi-Symbol Analysis", multi_symbol_analysis_example),
        "7": ("Health Monitoring", health_monitoring_example),
        "8": ("Reconnection Handling", reconnection_example),
    }

    print("\n" + "=" * 60)
    print("SIGMAX WebSocket Client Examples")
    print("=" * 60)
    print("\nSelect an example to run:\n")

    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")

    print("\n  q. Quit\n")
    print("=" * 60)

    choice = input("\nEnter choice: ").strip()

    if choice.lower() == 'q':
        print("Goodbye!")
        return

    if choice in examples:
        name, func = examples[choice]
        print(f"\nRunning: {name}\n")
        try:
            await func()
        except KeyboardInterrupt:
            print("\n\nStopped by user")
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    asyncio.run(main())
