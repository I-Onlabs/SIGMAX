"""
SIGMAX WebSocket Client
Python client library for connecting to SIGMAX WebSocket API.
"""

import asyncio
import json
from datetime import datetime
from typing import AsyncIterator, Callable, Dict, List, Optional, Set
from enum import Enum

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketClientProtocol = None

from loguru import logger


class ConnectionState(Enum):
    """WebSocket connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    CLOSED = "closed"


class WSEvent:
    """WebSocket event wrapper"""

    def __init__(self, type: str, data: Dict, timestamp: str):
        self.type = type
        self.data = data
        self.timestamp = timestamp

    def __repr__(self):
        return f"WSEvent(type={self.type}, timestamp={self.timestamp})"


class SigmaxWebSocketClient:
    """
    SIGMAX WebSocket Client with automatic reconnection and subscription management.

    Features:
    - Automatic reconnection with exponential backoff
    - Subscription persistence across reconnections
    - Event callbacks
    - Async iterator for events
    - Heartbeat/ping-pong handling

    Example:
        ```python
        import asyncio
        from sigmax_websocket import SigmaxWebSocketClient

        async def main():
            client = SigmaxWebSocketClient()
            await client.connect("ws://localhost:8000/api/ws")

            # Subscribe to topics
            await client.subscribe(topics=["proposals", "executions"])
            await client.subscribe(symbols=["BTC/USDT", "ETH/USDT"])

            # Listen for events
            async for event in client.listen():
                print(f"Event: {event.type}")
                print(f"Data: {event.data}")

        asyncio.run(main())
        ```
    """

    def __init__(
        self,
        auto_reconnect: bool = True,
        max_reconnect_delay: float = 60.0,
        ping_interval: float = 30.0,
        ping_timeout: float = 10.0
    ):
        """
        Initialize WebSocket client.

        Args:
            auto_reconnect: Enable automatic reconnection
            max_reconnect_delay: Maximum delay between reconnection attempts
            ping_interval: Interval for sending ping messages
            ping_timeout: Timeout for ping/pong responses
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "websockets library not installed. "
                "Install with: pip install websockets"
            )

        self.auto_reconnect = auto_reconnect
        self.max_reconnect_delay = max_reconnect_delay
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout

        # Connection state
        self.ws: Optional[WebSocketClientProtocol] = None
        self.url: Optional[str] = None
        self.state = ConnectionState.DISCONNECTED
        self.connection_id: Optional[str] = None

        # Subscriptions (persisted across reconnections)
        self.subscribed_topics: Set[str] = set()
        self.subscribed_symbols: Set[str] = set()

        # Event handling
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.event_callbacks: List[Callable[[WSEvent], None]] = []

        # Background tasks
        self.receive_task: Optional[asyncio.Task] = None
        self.ping_task: Optional[asyncio.Task] = None
        self.reconnect_delay = 1.0

    async def connect(self, url: str, api_key: Optional[str] = None):
        """
        Connect to SIGMAX WebSocket server.

        Args:
            url: WebSocket URL (e.g., ws://localhost:8000/api/ws)
            api_key: Optional API key for authentication
        """
        self.url = url
        if api_key:
            self.url = f"{url}?api_key={api_key}"

        await self._connect()

    async def _connect(self):
        """Internal connection logic"""
        if not self.url:
            raise ValueError("URL not set. Call connect() first.")

        try:
            self.state = ConnectionState.CONNECTING
            logger.info(f"Connecting to {self.url}...")

            self.ws = await websockets.connect(
                self.url,
                ping_interval=None,  # We handle ping ourselves
                ping_timeout=self.ping_timeout
            )

            self.state = ConnectionState.CONNECTED
            self.reconnect_delay = 1.0  # Reset reconnect delay

            logger.info("✓ Connected to SIGMAX WebSocket")

            # Wait for welcome message
            welcome_msg = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
            welcome_data = json.loads(welcome_msg)
            self.connection_id = welcome_data.get("connection_id")

            logger.info(f"Connection ID: {self.connection_id}")

            # Start background tasks
            self.receive_task = asyncio.create_task(self._receive_loop())
            self.ping_task = asyncio.create_task(self._ping_loop())

            # Restore subscriptions
            await self._restore_subscriptions()

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.state = ConnectionState.DISCONNECTED
            if self.auto_reconnect:
                await self._schedule_reconnect()
            else:
                raise

    async def disconnect(self):
        """Disconnect from server"""
        logger.info("Disconnecting...")

        self.state = ConnectionState.CLOSED
        self.auto_reconnect = False  # Disable auto-reconnect

        # Cancel background tasks
        if self.receive_task:
            self.receive_task.cancel()
        if self.ping_task:
            self.ping_task.cancel()

        # Close WebSocket
        if self.ws:
            await self.ws.close()
            self.ws = None

        logger.info("✓ Disconnected")

    async def subscribe(
        self,
        topics: Optional[List[str]] = None,
        symbols: Optional[List[str]] = None
    ):
        """
        Subscribe to topics and/or symbols.

        Args:
            topics: List of topics (e.g., ["proposals", "executions"])
            symbols: List of symbols (e.g., ["BTC/USDT", "ETH/USDT"])
        """
        if not self.is_connected():
            raise RuntimeError("Not connected. Call connect() first.")

        topics = topics or []
        symbols = symbols or []

        # Store subscriptions for reconnection
        self.subscribed_topics.update(topics)
        self.subscribed_symbols.update(symbols)

        # Send subscription message
        message = {
            "type": "subscribe",
            "data": {
                "topics": topics,
                "symbols": symbols
            }
        }

        await self._send(message)
        logger.info(f"Subscribed to {len(topics)} topics and {len(symbols)} symbols")

    async def unsubscribe(
        self,
        topics: Optional[List[str]] = None,
        symbols: Optional[List[str]] = None
    ):
        """
        Unsubscribe from topics and/or symbols.

        Args:
            topics: List of topics to unsubscribe from
            symbols: List of symbols to unsubscribe from
        """
        if not self.is_connected():
            raise RuntimeError("Not connected")

        topics = topics or []
        symbols = symbols or []

        # Remove from stored subscriptions
        for topic in topics:
            self.subscribed_topics.discard(topic)
        for symbol in symbols:
            self.subscribed_symbols.discard(symbol)

        # Send unsubscribe message
        message = {
            "type": "unsubscribe",
            "data": {
                "topics": topics,
                "symbols": symbols
            }
        }

        await self._send(message)
        logger.info(f"Unsubscribed from {len(topics)} topics and {len(symbols)} symbols")

    async def get_status(self) -> Dict:
        """
        Request current system status.

        Returns:
            Status data
        """
        if not self.is_connected():
            raise RuntimeError("Not connected")

        # Send command
        message = {
            "type": "command",
            "data": {
                "command": "get_status"
            }
        }

        await self._send(message)

        # Wait for response
        # In production, you'd use request_id to match responses
        # For now, just wait for next system_status event
        timeout = 5.0
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                if event.type == "system_status":
                    return event.data
            except asyncio.TimeoutError:
                continue

        raise TimeoutError("Status request timed out")

    async def listen(self) -> AsyncIterator[WSEvent]:
        """
        Async iterator for receiving events.

        Yields:
            WSEvent instances

        Example:
            ```python
            async for event in client.listen():
                print(f"Event: {event.type}, Data: {event.data}")
            ```
        """
        while True:
            event = await self.event_queue.get()
            yield event

    def on_event(self, callback: Callable[[WSEvent], None]):
        """
        Register event callback.

        Args:
            callback: Function to call on each event

        Example:
            ```python
            def handle_event(event: WSEvent):
                print(f"Event: {event.type}")

            client.on_event(handle_event)
            ```
        """
        self.event_callbacks.append(callback)

    def is_connected(self) -> bool:
        """Check if currently connected"""
        return self.state == ConnectionState.CONNECTED and self.ws is not None

    async def _send(self, message: Dict):
        """Send message to server"""
        if not self.ws:
            raise RuntimeError("WebSocket not connected")

        await self.ws.send(json.dumps(message))

    async def _receive_loop(self):
        """Background task to receive messages"""
        try:
            while self.is_connected() and self.ws:
                try:
                    # Receive message
                    raw_message = await self.ws.recv()
                    message = json.loads(raw_message)

                    # Create event
                    event = WSEvent(
                        type=message.get("type"),
                        data=message.get("data", {}),
                        timestamp=message.get("timestamp", datetime.now().isoformat())
                    )

                    # Handle ping/pong
                    if event.type == "ping":
                        await self._send({"type": "pong"})
                        continue
                    elif event.type == "pong":
                        continue

                    # Add to queue
                    await self.event_queue.put(event)

                    # Call callbacks
                    for callback in self.event_callbacks:
                        try:
                            callback(event)
                        except Exception as e:
                            logger.error(f"Error in event callback: {e}")

                except websockets.ConnectionClosed:
                    logger.warning("Connection closed by server")
                    break
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    break

        except asyncio.CancelledError:
            logger.debug("Receive loop cancelled")
        finally:
            # Connection lost - schedule reconnect
            if self.state == ConnectionState.CONNECTED:
                self.state = ConnectionState.DISCONNECTED
                if self.auto_reconnect:
                    await self._schedule_reconnect()

    async def _ping_loop(self):
        """Background task to send periodic pings"""
        try:
            while self.is_connected():
                await asyncio.sleep(self.ping_interval)

                if self.is_connected():
                    try:
                        await self._send({"type": "ping"})
                    except Exception as e:
                        logger.error(f"Error sending ping: {e}")
                        break

        except asyncio.CancelledError:
            logger.debug("Ping loop cancelled")

    async def _schedule_reconnect(self):
        """Schedule reconnection with exponential backoff"""
        if not self.auto_reconnect or self.state == ConnectionState.CLOSED:
            return

        self.state = ConnectionState.RECONNECTING

        logger.info(f"Reconnecting in {self.reconnect_delay:.1f}s...")
        await asyncio.sleep(self.reconnect_delay)

        # Exponential backoff
        self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)

        await self._connect()

    async def _restore_subscriptions(self):
        """Restore subscriptions after reconnection"""
        if self.subscribed_topics or self.subscribed_symbols:
            logger.info("Restoring subscriptions...")
            await self.subscribe(
                topics=list(self.subscribed_topics),
                symbols=list(self.subscribed_symbols)
            )


# Convenience function for quick usage
async def connect_sigmax(
    url: str = "ws://localhost:8000/api/ws",
    api_key: Optional[str] = None,
    topics: Optional[List[str]] = None,
    symbols: Optional[List[str]] = None
) -> SigmaxWebSocketClient:
    """
    Quick connect to SIGMAX WebSocket.

    Args:
        url: WebSocket URL
        api_key: Optional API key
        topics: Topics to subscribe to
        symbols: Symbols to subscribe to

    Returns:
        Connected client instance

    Example:
        ```python
        client = await connect_sigmax(
            topics=["proposals", "executions"],
            symbols=["BTC/USDT"]
        )

        async for event in client.listen():
            print(event.type, event.data)
        ```
    """
    client = SigmaxWebSocketClient()
    await client.connect(url, api_key)

    if topics or symbols:
        await client.subscribe(topics=topics, symbols=symbols)

    return client
