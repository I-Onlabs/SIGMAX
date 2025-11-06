#!/usr/bin/env python3
"""
SIGMAX WebSocket Example
Demonstrates real-time updates via WebSocket connection
"""

import asyncio
import json
from typing import Dict, Any
import websockets


async def connect_to_sigmax(url: str = "ws://localhost:8000/ws"):
    """Connect to SIGMAX WebSocket and receive updates"""
    print("🔌 Connecting to SIGMAX WebSocket...")
    print(f"   URL: {url}\n")

    try:
        async with websockets.connect(url) as websocket:
            print("✅ Connected to SIGMAX!")
            print("📡 Listening for updates...\n")

            message_count = 0

            while True:
                try:
                    # Receive message
                    message = await websocket.recv()
                    data = json.loads(message)
                    message_count += 1

                    # Handle different message types
                    msg_type = data.get("type", "unknown")

                    if msg_type == "connected":
                        print(f"🎉 {data.get('message')}")

                    elif msg_type == "status_update":
                        timestamp = data.get("timestamp", "")
                        update_data = data.get("data", {})
                        print(f"📊 Status Update #{message_count}")
                        print(f"   Time: {timestamp}")
                        print(f"   Price: ${update_data.get('price', 0):,.2f}")
                        print(f"   Sentiment: {update_data.get('sentiment', 0):.2f}")
                        print()

                    elif msg_type == "trade":
                        trade_data = data.get("data", {})
                        print(f"💰 Trade Notification #{message_count}")
                        print(f"   Symbol: {trade_data.get('symbol')}")
                        print(f"   Action: {trade_data.get('action').upper()}")
                        print(f"   Size: {trade_data.get('size')}")
                        print(f"   Price: ${trade_data.get('price', 0):,.2f}")
                        print()

                    elif msg_type == "alert":
                        alert_data = data.get("data", {})
                        severity = alert_data.get("severity", "info").upper()
                        print(f"🚨 Alert: {severity}")
                        print(f"   Message: {alert_data.get('message')}")
                        print()

                    else:
                        print(f"📨 Message #{message_count}: {msg_type}")
                        print(f"   {json.dumps(data, indent=2)}")
                        print()

                    # Send heartbeat every 10 messages
                    if message_count % 10 == 0:
                        await websocket.send(
                            json.dumps({"type": "heartbeat", "count": message_count})
                        )

                except websockets.exceptions.ConnectionClosed:
                    print("❌ Connection closed by server")
                    break
                except json.JSONDecodeError as e:
                    print(f"⚠️  Invalid JSON received: {e}")
                except KeyboardInterrupt:
                    print("\n👋 Disconnecting...")
                    break

    except Exception as e:
        print(f"❌ Error connecting to WebSocket: {e}")
        return


async def main():
    """Main function"""
    print("🤖 SIGMAX WebSocket Client Example\n")

    # Connect to WebSocket
    await connect_to_sigmax()

    print("\n✅ Example completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
