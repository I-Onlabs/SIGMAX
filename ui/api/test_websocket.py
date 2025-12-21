"""
Quick test script for SIGMAX WebSocket implementation
Run this to verify WebSocket functionality.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from clients.websocket_client import SigmaxWebSocketClient
from loguru import logger


async def test_basic_connection():
    """Test 1: Basic connection and disconnection"""
    logger.info("Test 1: Basic Connection")

    client = SigmaxWebSocketClient()

    try:
        await client.connect("ws://localhost:8000/api/ws")
        assert client.is_connected(), "Client should be connected"
        logger.success("✓ Connection successful")

        await client.disconnect()
        assert not client.is_connected(), "Client should be disconnected"
        logger.success("✓ Disconnection successful")

    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        raise


async def test_subscriptions():
    """Test 2: Subscribe and unsubscribe"""
    logger.info("Test 2: Subscriptions")

    client = SigmaxWebSocketClient()

    try:
        await client.connect("ws://localhost:8000/api/ws")

        # Subscribe to topics
        await client.subscribe(topics=["proposals", "executions"])
        logger.success("✓ Subscribed to topics")

        # Subscribe to symbols
        await client.subscribe(symbols=["BTC/USDT", "ETH/USDT"])
        logger.success("✓ Subscribed to symbols")

        # Wait for confirmation events
        await asyncio.sleep(2)

        # Unsubscribe
        await client.unsubscribe(topics=["proposals"])
        logger.success("✓ Unsubscribed from topic")

        await client.disconnect()

    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        raise


async def test_event_reception():
    """Test 3: Receive events"""
    logger.info("Test 3: Event Reception")

    client = SigmaxWebSocketClient()
    events_received = []

    def on_event(event):
        events_received.append(event)
        logger.debug(f"Received event: {event.type}")

    client.on_event(on_event)

    try:
        await client.connect("ws://localhost:8000/api/ws")
        await client.subscribe(topics=["status", "health"])

        # Wait for some events
        logger.info("Waiting for events (10 seconds)...")
        await asyncio.sleep(10)

        assert len(events_received) > 0, "Should have received at least one event"
        logger.success(f"✓ Received {len(events_received)} events")

        # Show event types
        event_types = set(e.type for e in events_received)
        logger.info(f"Event types received: {event_types}")

        await client.disconnect()

    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        raise


async def test_ping_pong():
    """Test 4: Ping/pong mechanism"""
    logger.info("Test 4: Ping/Pong")

    client = SigmaxWebSocketClient()
    pong_received = False

    def on_pong(event):
        nonlocal pong_received
        if event.type == "pong":
            pong_received = True
            logger.success("✓ Received pong")

    client.on_event(on_pong)

    try:
        await client.connect("ws://localhost:8000/api/ws")

        # Send ping
        await client._send({"type": "ping"})

        # Wait for pong
        await asyncio.sleep(2)

        assert pong_received, "Should have received pong"
        logger.success("✓ Ping/pong working")

        await client.disconnect()

    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        raise


async def test_reconnection():
    """Test 5: Auto-reconnection (manual)"""
    logger.info("Test 5: Auto-Reconnection (Manual Test)")

    client = SigmaxWebSocketClient(auto_reconnect=True)

    logger.info("This test requires manual intervention:")
    logger.info("1. Client will connect")
    logger.info("2. Stop the server (Ctrl+C in server terminal)")
    logger.info("3. Restart the server")
    logger.info("4. Client should automatically reconnect")
    logger.info("")
    logger.info("Starting in 5 seconds...")
    await asyncio.sleep(5)

    try:
        await client.connect("ws://localhost:8000/api/ws")
        await client.subscribe(topics=["status"])

        logger.info("Connected. Now stop and restart the server...")

        # Keep listening
        event_count = 0
        async for event in client.listen():
            event_count += 1
            if event.type == "connected":
                logger.success("✓ Reconnected successfully!")

            logger.debug(f"Event {event_count}: {event.type}")

            if event_count >= 20:
                break

        await client.disconnect()

    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        await client.disconnect()


async def run_all_tests():
    """Run all automated tests"""
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Subscriptions", test_subscriptions),
        ("Event Reception", test_event_reception),
        ("Ping/Pong", test_ping_pong),
    ]

    logger.info("=" * 60)
    logger.info("SIGMAX WebSocket Test Suite")
    logger.info("=" * 60)
    logger.info("")

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running: {name}")
            logger.info(f"{'='*60}")

            await test_func()
            passed += 1

            logger.info("")

        except Exception as e:
            failed += 1
            logger.error(f"Test '{name}' failed: {e}")
            logger.info("")

    logger.info("=" * 60)
    logger.info("Test Results")
    logger.info("=" * 60)
    logger.info(f"Passed: {passed}/{len(tests)}")
    logger.info(f"Failed: {failed}/{len(tests)}")
    logger.info("=" * 60)

    if failed == 0:
        logger.success("\n✓ All tests passed!")
    else:
        logger.error(f"\n✗ {failed} test(s) failed")

    return failed == 0


async def main():
    """Main test menu"""
    print("\n" + "=" * 60)
    print("SIGMAX WebSocket Test Suite")
    print("=" * 60)
    print("\nSelect test to run:\n")
    print("  1. Basic Connection")
    print("  2. Subscriptions")
    print("  3. Event Reception")
    print("  4. Ping/Pong")
    print("  5. Auto-Reconnection (Manual)")
    print("  a. Run All Automated Tests")
    print("  q. Quit")
    print("\n" + "=" * 60)

    choice = input("\nEnter choice: ").strip().lower()

    if choice == 'q':
        print("Goodbye!")
        return

    tests = {
        '1': test_basic_connection,
        '2': test_subscriptions,
        '3': test_event_reception,
        '4': test_ping_pong,
        '5': test_reconnection,
    }

    if choice == 'a':
        await run_all_tests()
    elif choice in tests:
        try:
            await tests[choice]()
            logger.success("\n✓ Test completed successfully")
        except Exception as e:
            logger.error(f"\n✗ Test failed: {e}")
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
