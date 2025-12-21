"""
WebSocket Connection Manager for SIGMAX
Handles WebSocket connections, subscriptions, and broadcasting with Redis pub/sub support.
"""

import asyncio
import json
import time
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Dict, Set, Optional, Any, List
from fastapi import WebSocket
from loguru import logger

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - using in-memory pub/sub only")


class WebSocketConnection:
    """Represents a single WebSocket connection with metadata"""

    def __init__(self, websocket: WebSocket, connection_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.connected_at = datetime.now()
        self.last_ping = time.time()
        self.subscriptions: Set[str] = set()
        self.metadata: Dict[str, Any] = {}

    def is_alive(self, timeout: float = 60.0) -> bool:
        """Check if connection is still alive based on last ping"""
        return (time.time() - self.last_ping) < timeout

    def update_ping(self):
        """Update last ping timestamp"""
        self.last_ping = time.time()


class ConnectionManager:
    """
    Advanced WebSocket connection manager with subscription support and Redis pub/sub.

    Features:
    - Per-connection subscriptions (symbol-specific, topic-specific)
    - Redis pub/sub for multi-instance broadcasting
    - Heartbeat/ping-pong mechanism
    - Connection limits and cleanup
    - Graceful reconnection support
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        max_connections: int = 1000,
        heartbeat_interval: float = 30.0,
        connection_timeout: float = 60.0
    ):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)  # topic -> {connection_ids}
        self.max_connections = max_connections
        self.heartbeat_interval = heartbeat_interval
        self.connection_timeout = connection_timeout

        # Redis pub/sub
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.redis_pubsub: Optional[redis.client.PubSub] = None
        self.redis_listener_task: Optional[asyncio.Task] = None

        # Stats
        self.total_connections = 0
        self.total_disconnections = 0
        self.total_messages_sent = 0

        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize Redis connection and background tasks"""
        if self.redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test connection
                await self.redis_client.ping()

                # Setup pub/sub
                self.redis_pubsub = self.redis_client.pubsub()
                await self.redis_pubsub.subscribe("sigmax:broadcast")

                # Start Redis listener
                self.redis_listener_task = asyncio.create_task(self._redis_listener())

                logger.info(f"✓ Redis pub/sub initialized: {self.redis_url}")
            except Exception as e:
                logger.warning(f"Redis connection failed, using in-memory only: {e}")
                self.redis_client = None

        # Start background tasks
        self.cleanup_task = asyncio.create_task(self._cleanup_stale_connections())
        self.heartbeat_task = asyncio.create_task(self._send_heartbeats())

        logger.info("✓ WebSocket ConnectionManager initialized")

    async def shutdown(self):
        """Cleanup resources"""
        logger.info("Shutting down ConnectionManager...")

        # Cancel background tasks
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.redis_listener_task:
            self.redis_listener_task.cancel()

        # Close all connections
        for conn_id in list(self.connections.keys()):
            await self.disconnect(conn_id)

        # Close Redis
        if self.redis_pubsub:
            await self.redis_pubsub.unsubscribe("sigmax:broadcast")
            await self.redis_pubsub.close()
        if self.redis_client:
            await self.redis_client.close()

        logger.info("✓ ConnectionManager shutdown complete")

    async def connect(self, websocket: WebSocket, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            metadata: Optional metadata (user_id, api_key, etc.)

        Returns:
            connection_id: Unique connection identifier

        Raises:
            RuntimeError: If max connections exceeded
        """
        # Check connection limit
        if len(self.connections) >= self.max_connections:
            raise RuntimeError(f"Maximum connections ({self.max_connections}) exceeded")

        # Accept connection
        await websocket.accept()

        # Generate unique connection ID
        connection_id = str(uuid.uuid4())

        # Create connection object
        conn = WebSocketConnection(websocket, connection_id)
        if metadata:
            conn.metadata = metadata

        # Store connection
        self.connections[connection_id] = conn
        self.total_connections += 1

        logger.info(
            f"WebSocket connected: {connection_id} "
            f"(total: {len(self.connections)}, lifetime: {self.total_connections})"
        )

        return connection_id

    async def disconnect(self, connection_id: str):
        """
        Disconnect and cleanup a WebSocket connection.

        Args:
            connection_id: Connection identifier
        """
        if connection_id not in self.connections:
            return

        conn = self.connections[connection_id]

        # Unsubscribe from all topics
        for topic in list(conn.subscriptions):
            await self.unsubscribe(connection_id, topic)

        # Remove connection
        del self.connections[connection_id]
        self.total_disconnections += 1

        logger.info(
            f"WebSocket disconnected: {connection_id} "
            f"(total: {len(self.connections)}, lifetime disconnects: {self.total_disconnections})"
        )

    async def subscribe(self, connection_id: str, topic: str):
        """
        Subscribe a connection to a topic.

        Topics:
        - symbol:{SYMBOL} - e.g., symbol:BTC/USDT
        - proposals - Trade proposals
        - executions - Trade executions
        - analysis - Analysis updates
        - status - System status
        - all - All events

        Args:
            connection_id: Connection identifier
            topic: Topic to subscribe to
        """
        if connection_id not in self.connections:
            logger.warning(f"Cannot subscribe - connection not found: {connection_id}")
            return

        conn = self.connections[connection_id]
        conn.subscriptions.add(topic)
        self.subscriptions[topic].add(connection_id)

        logger.debug(f"Connection {connection_id} subscribed to: {topic}")

    async def unsubscribe(self, connection_id: str, topic: str):
        """
        Unsubscribe a connection from a topic.

        Args:
            connection_id: Connection identifier
            topic: Topic to unsubscribe from
        """
        if connection_id not in self.connections:
            return

        conn = self.connections[connection_id]
        conn.subscriptions.discard(topic)
        self.subscriptions[topic].discard(connection_id)

        # Cleanup empty subscription sets
        if not self.subscriptions[topic]:
            del self.subscriptions[topic]

        logger.debug(f"Connection {connection_id} unsubscribed from: {topic}")

    async def send_to(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """
        Send message to a specific connection.

        Args:
            connection_id: Target connection
            message: Message to send

        Returns:
            True if sent successfully, False otherwise
        """
        if connection_id not in self.connections:
            return False

        conn = self.connections[connection_id]

        try:
            await conn.websocket.send_json(message)
            self.total_messages_sent += 1
            return True
        except Exception as e:
            logger.error(f"Error sending to {connection_id}: {e}")
            # Connection broken, disconnect
            await self.disconnect(connection_id)
            return False

    async def broadcast(self, message: Dict[str, Any], topic: Optional[str] = None):
        """
        Broadcast message to all connections or specific topic subscribers.

        Args:
            message: Message to broadcast
            topic: Optional topic filter (only send to subscribers of this topic)
        """
        # Determine target connections
        if topic:
            target_connections = list(self.subscriptions.get(topic, set()))
        else:
            target_connections = list(self.connections.keys())

        # Send to all targets
        failed_connections = []
        for connection_id in target_connections:
            success = await self.send_to(connection_id, message)
            if not success:
                failed_connections.append(connection_id)

        logger.debug(
            f"Broadcast to {len(target_connections)} connections "
            f"(topic: {topic or 'all'}, failed: {len(failed_connections)})"
        )

        # Publish to Redis for multi-instance support
        if self.redis_client and topic:
            try:
                await self.redis_client.publish(
                    "sigmax:broadcast",
                    json.dumps({"topic": topic, "message": message})
                )
            except Exception as e:
                logger.error(f"Redis publish failed: {e}")

    async def broadcast_to_symbols(self, symbols: List[str], message: Dict[str, Any]):
        """
        Broadcast to all subscribers of specific symbols.

        Args:
            symbols: List of symbols (e.g., ["BTC/USDT", "ETH/USDT"])
            message: Message to broadcast
        """
        for symbol in symbols:
            topic = f"symbol:{symbol}"
            await self.broadcast(message, topic=topic)

    async def _redis_listener(self):
        """Background task to listen to Redis pub/sub and relay to local connections"""
        if not self.redis_pubsub:
            return

        logger.info("Starting Redis pub/sub listener...")

        try:
            async for message in self.redis_pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        topic = data.get("topic")
                        msg = data.get("message")

                        # Relay to local connections
                        if topic and msg:
                            target_connections = list(self.subscriptions.get(topic, set()))
                            for connection_id in target_connections:
                                await self.send_to(connection_id, msg)
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
        except asyncio.CancelledError:
            logger.info("Redis listener cancelled")
        except Exception as e:
            logger.error(f"Redis listener error: {e}")

    async def _cleanup_stale_connections(self):
        """Background task to cleanup stale connections"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                stale_connections = []
                for connection_id, conn in self.connections.items():
                    if not conn.is_alive(self.connection_timeout):
                        stale_connections.append(connection_id)

                for connection_id in stale_connections:
                    logger.warning(f"Cleaning up stale connection: {connection_id}")
                    await self.disconnect(connection_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    async def _send_heartbeats(self):
        """Background task to send heartbeat pings"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                }

                # Send to all connections
                for connection_id in list(self.connections.keys()):
                    await self.send_to(connection_id, ping_message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat task: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "active_connections": len(self.connections),
            "total_connections_lifetime": self.total_connections,
            "total_disconnections_lifetime": self.total_disconnections,
            "total_messages_sent": self.total_messages_sent,
            "subscriptions_count": len(self.subscriptions),
            "topics": list(self.subscriptions.keys()),
            "redis_enabled": self.redis_client is not None,
            "max_connections": self.max_connections
        }

    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific connection"""
        if connection_id not in self.connections:
            return None

        conn = self.connections[connection_id]
        return {
            "connection_id": connection_id,
            "connected_at": conn.connected_at.isoformat(),
            "last_ping": conn.last_ping,
            "subscriptions": list(conn.subscriptions),
            "metadata": conn.metadata
        }
