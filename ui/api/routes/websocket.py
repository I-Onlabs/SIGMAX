"""
WebSocket API Routes for SIGMAX
Real-time bidirectional communication endpoint.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger
import psutil

from websocket_manager import ConnectionManager
from websocket_protocol import (
    WSEventType,
    WSMessageType,
    create_event,
    parse_client_message,
    validate_subscription_topics,
    validate_symbols,
)
from sigmax_manager import get_sigmax_manager


router = APIRouter()

# Global connection manager (initialized in startup)
connection_manager: Optional[ConnectionManager] = None


async def init_websocket_manager(redis_url: Optional[str] = None):
    """Initialize the global WebSocket connection manager"""
    global connection_manager

    if connection_manager is None:
        connection_manager = ConnectionManager(
            redis_url=redis_url,
            max_connections=1000,
            heartbeat_interval=30.0,
            connection_timeout=60.0
        )
        await connection_manager.initialize()
        logger.info("✓ WebSocket manager initialized")


async def shutdown_websocket_manager():
    """Shutdown the WebSocket connection manager"""
    global connection_manager

    if connection_manager:
        await connection_manager.shutdown()
        connection_manager = None
        logger.info("✓ WebSocket manager shutdown complete")


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager"""
    if connection_manager is None:
        raise RuntimeError("WebSocket manager not initialized")
    return connection_manager


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    api_key: Optional[str] = Query(None, description="Optional API key for authentication")
):
    """
    WebSocket endpoint for real-time bidirectional communication.

    ## Connection Flow:
    1. Client connects to ws://host/api/ws
    2. Server accepts connection and sends 'connected' event
    3. Client can subscribe to topics/symbols
    4. Server sends updates for subscribed topics
    5. Client can send commands (analyze, get_status, etc.)
    6. Server maintains heartbeat (ping/pong)

    ## Client -> Server Messages:

    ### Subscribe to topics:
    ```json
    {
        "type": "subscribe",
        "data": {
            "topics": ["proposals", "executions", "analysis"],
            "symbols": ["BTC/USDT", "ETH/USDT"]
        }
    }
    ```

    ### Unsubscribe:
    ```json
    {
        "type": "unsubscribe",
        "data": {
            "topics": ["proposals"],
            "symbols": ["BTC/USDT"]
        }
    }
    ```

    ### Ping (keep-alive):
    ```json
    {
        "type": "ping"
    }
    ```

    ### Execute command:
    ```json
    {
        "type": "command",
        "data": {
            "command": "get_status"
        }
    }
    ```

    ## Server -> Client Events:

    - **connected**: Connection established
    - **subscribed**: Subscription confirmed
    - **ping/pong**: Heartbeat
    - **analysis_update**: Analysis completed
    - **proposal_created**: New trade proposal
    - **proposal_approved**: Proposal approved
    - **trade_executed**: Trade executed
    - **status_change**: System status changed
    - **market_update**: Market data update
    - **portfolio_update**: Portfolio changed
    - **health_update**: System health metrics
    - **error**: Error occurred

    ## Topics:

    - **all**: All events
    - **proposals**: Trade proposals
    - **executions**: Trade executions
    - **analysis**: Analysis updates
    - **status**: System status
    - **market**: Market data
    - **portfolio**: Portfolio updates
    - **health**: System health
    - **alerts**: Alerts and warnings

    ## Symbol Subscriptions:

    Subscribe to specific symbols:
    - symbol:BTC/USDT
    - symbol:ETH/USDT
    """
    manager = get_connection_manager()
    sigmax_manager = await get_sigmax_manager()

    connection_id = None

    try:
        # Connect and register
        metadata = {"api_key": api_key} if api_key else {}
        connection_id = await manager.connect(websocket, metadata)

        # Send welcome message
        welcome_event = create_event(
            WSEventType.CONNECTED,
            {
                "message": "Connected to SIGMAX WebSocket",
                "server_version": "2.0.0",
                "connection_id": connection_id,
                "available_topics": [
                    "all", "proposals", "executions", "analysis",
                    "status", "market", "portfolio", "health", "alerts"
                ],
                "instructions": "Send 'subscribe' message to start receiving updates"
            },
            connection_id=connection_id
        )
        await websocket.send_json(welcome_event.model_dump())

        # Send initial status
        try:
            status = await sigmax_manager.get_status()
            status_event = create_event(
                WSEventType.SYSTEM_STATUS,
                status,
                connection_id=connection_id
            )
            await websocket.send_json(status_event.model_dump())
        except Exception as e:
            logger.warning(f"Could not fetch initial status: {e}")

        # Main message loop
        while True:
            try:
                # Receive message from client
                raw_message = await websocket.receive_json()
                logger.debug(f"Received message from {connection_id}: {raw_message}")

                # Parse and handle message
                await handle_client_message(
                    connection_id,
                    raw_message,
                    websocket,
                    manager,
                    sigmax_manager
                )

            except WebSocketDisconnect:
                logger.info(f"Client {connection_id} disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing message from {connection_id}: {e}")
                # Send error event
                error_event = create_event(
                    WSEventType.ERROR,
                    {
                        "error": str(e),
                        "code": "MESSAGE_PROCESSING_ERROR"
                    },
                    connection_id=connection_id
                )
                await websocket.send_json(error_event.model_dump())

    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
    finally:
        # Cleanup
        if connection_id:
            await manager.disconnect(connection_id)


async def handle_client_message(
    connection_id: str,
    raw_message: Dict[str, Any],
    websocket: WebSocket,
    manager: ConnectionManager,
    sigmax_manager
):
    """
    Handle incoming client messages.

    Args:
        connection_id: Connection identifier
        raw_message: Raw message dict
        websocket: WebSocket instance
        manager: Connection manager
        sigmax_manager: SIGMAX manager
    """
    try:
        # Parse message
        message = parse_client_message(raw_message)
        msg_type = message.type

        # Handle different message types
        if msg_type == WSMessageType.SUBSCRIBE:
            await handle_subscribe(connection_id, message, websocket, manager)

        elif msg_type == WSMessageType.UNSUBSCRIBE:
            await handle_unsubscribe(connection_id, message, websocket, manager)

        elif msg_type == WSMessageType.PING:
            await handle_ping(connection_id, websocket, manager)

        elif msg_type == WSMessageType.PONG:
            # Client responding to our ping - update last_ping
            conn = manager.connections.get(connection_id)
            if conn:
                conn.update_ping()

        elif msg_type == WSMessageType.GET_STATUS:
            await handle_get_status(connection_id, websocket, sigmax_manager)

        elif msg_type == WSMessageType.GET_SUBSCRIPTIONS:
            await handle_get_subscriptions(connection_id, websocket, manager)

        elif msg_type == WSMessageType.COMMAND:
            await handle_command(connection_id, message, websocket, sigmax_manager)

        else:
            raise ValueError(f"Unknown message type: {msg_type}")

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        error_event = create_event(
            WSEventType.ERROR,
            {
                "error": str(e),
                "code": "INVALID_MESSAGE"
            },
            connection_id=connection_id
        )
        await websocket.send_json(error_event.model_dump())


async def handle_subscribe(
    connection_id: str,
    message,
    websocket: WebSocket,
    manager: ConnectionManager
):
    """Handle subscription request"""
    data = message.data or {}

    # Extract topics and symbols
    topics = data.get("topics", [])
    symbols = data.get("symbols", [])

    # Validate and normalize
    try:
        if topics:
            topics = validate_subscription_topics(topics)
        if symbols:
            symbols = validate_symbols(symbols)
    except ValueError as e:
        raise ValueError(f"Invalid subscription: {e}")

    # Subscribe to topics
    for topic in topics:
        await manager.subscribe(connection_id, topic)

    # Subscribe to symbols
    for symbol in symbols:
        topic = f"symbol:{symbol}"
        await manager.subscribe(connection_id, topic)

    # Send confirmation
    subscribed_event = create_event(
        WSEventType.SUBSCRIBED,
        {
            "topics": topics,
            "symbols": symbols,
            "message": f"Subscribed to {len(topics)} topics and {len(symbols)} symbols"
        },
        connection_id=connection_id
    )
    await websocket.send_json(subscribed_event.model_dump())


async def handle_unsubscribe(
    connection_id: str,
    message,
    websocket: WebSocket,
    manager: ConnectionManager
):
    """Handle unsubscribe request"""
    data = message.data or {}

    topics = data.get("topics", [])
    symbols = data.get("symbols", [])

    # Unsubscribe from topics
    for topic in topics:
        await manager.unsubscribe(connection_id, topic)

    # Unsubscribe from symbols
    for symbol in symbols:
        topic = f"symbol:{symbol}"
        await manager.unsubscribe(connection_id, topic)

    # Send confirmation
    unsubscribed_event = create_event(
        WSEventType.UNSUBSCRIBED,
        {
            "topics": topics,
            "symbols": symbols,
            "message": f"Unsubscribed from {len(topics)} topics and {len(symbols)} symbols"
        },
        connection_id=connection_id
    )
    await websocket.send_json(unsubscribed_event.model_dump())


async def handle_ping(
    connection_id: str,
    websocket: WebSocket,
    manager: ConnectionManager
):
    """Handle ping request"""
    # Update last ping time
    conn = manager.connections.get(connection_id)
    if conn:
        conn.update_ping()

    # Respond with pong
    pong_event = create_event(
        WSEventType.PONG,
        {"message": "pong"},
        connection_id=connection_id
    )
    await websocket.send_json(pong_event.model_dump())


async def handle_get_status(
    connection_id: str,
    websocket: WebSocket,
    sigmax_manager
):
    """Handle status request"""
    status = await sigmax_manager.get_status()

    status_event = create_event(
        WSEventType.SYSTEM_STATUS,
        status,
        connection_id=connection_id
    )
    await websocket.send_json(status_event.model_dump())


async def handle_get_subscriptions(
    connection_id: str,
    websocket: WebSocket,
    manager: ConnectionManager
):
    """Handle get subscriptions request"""
    conn_info = manager.get_connection_info(connection_id)

    if conn_info:
        subscriptions = conn_info.get("subscriptions", [])
    else:
        subscriptions = []

    event = create_event(
        WSEventType.SYSTEM_STATUS,
        {
            "subscriptions": subscriptions,
            "count": len(subscriptions)
        },
        connection_id=connection_id
    )
    await websocket.send_json(event.model_dump())


async def handle_command(
    connection_id: str,
    message,
    websocket: WebSocket,
    sigmax_manager
):
    """Handle command request"""
    data = message.data or {}
    command = data.get("command")

    if command == "get_status":
        await handle_get_status(connection_id, websocket, sigmax_manager)

    elif command == "get_portfolio":
        portfolio = await sigmax_manager.get_portfolio()
        event = create_event(
            WSEventType.PORTFOLIO_UPDATE,
            portfolio,
            connection_id=connection_id
        )
        await websocket.send_json(event.model_dump())

    elif command == "get_health":
        health_data = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "process_count": len(psutil.pids()),
        }
        event = create_event(
            WSEventType.HEALTH_UPDATE,
            health_data,
            connection_id=connection_id
        )
        await websocket.send_json(event.model_dump())

    else:
        raise ValueError(f"Unknown command: {command}")


# Background task for broadcasting system updates
async def broadcast_system_updates():
    """
    Background task to broadcast periodic system updates.

    Broadcasts:
    - Market data every 2 seconds (to 'market' subscribers)
    - Portfolio updates every 3 seconds (to 'portfolio' subscribers)
    - System status every 5 seconds (to 'status' subscribers)
    - Health metrics every 10 seconds (to 'health' subscribers)
    """
    manager = get_connection_manager()
    sigmax_manager = await get_sigmax_manager()

    tick = 0

    while True:
        try:
            await asyncio.sleep(1)
            tick += 1

            # Market data every 2 seconds
            if tick % 2 == 0:
                await broadcast_market_data(manager, sigmax_manager)

            # Portfolio every 3 seconds
            if tick % 3 == 0:
                await broadcast_portfolio(manager, sigmax_manager)

            # Status every 5 seconds
            if tick % 5 == 0:
                await broadcast_status(manager, sigmax_manager)

            # Health every 10 seconds
            if tick % 10 == 0:
                await broadcast_health(manager)

            # Pending events immediately
            await broadcast_pending_events(manager, sigmax_manager)

            # Reset tick counter
            if tick >= 30:
                tick = 0

        except asyncio.CancelledError:
            logger.info("Broadcast task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in broadcast task: {e}")
            await asyncio.sleep(1)


async def broadcast_market_data(manager: ConnectionManager, sigmax_manager):
    """Broadcast market data to 'market' topic subscribers"""
    try:
        # Get market data for common symbols
        symbols = ["BTC/USDT", "ETH/USDT"]
        market_data = []

        for symbol in symbols:
            try:
                # Mock data for now - integrate with data module later
                data = {
                    "symbol": symbol,
                    "price": 95000.0 if "BTC" in symbol else 3500.0,
                    "volume_24h": 1000000,
                    "change_24h": 2.5
                }
                market_data.append(data)
            except Exception:
                pass

        if market_data:
            event = create_event(WSEventType.MARKET_UPDATE, market_data)
            await manager.broadcast(event.model_dump(), topic="market")

    except Exception as e:
        logger.debug(f"Error broadcasting market data: {e}")


async def broadcast_portfolio(manager: ConnectionManager, sigmax_manager):
    """Broadcast portfolio updates to 'portfolio' topic subscribers"""
    try:
        portfolio = await sigmax_manager.get_portfolio()
        event = create_event(WSEventType.PORTFOLIO_UPDATE, portfolio)
        await manager.broadcast(event.model_dump(), topic="portfolio")
    except Exception as e:
        logger.debug(f"Error broadcasting portfolio: {e}")


async def broadcast_status(manager: ConnectionManager, sigmax_manager):
    """Broadcast system status to 'status' topic subscribers"""
    try:
        status = await sigmax_manager.get_status()
        event = create_event(WSEventType.SYSTEM_STATUS, status)
        await manager.broadcast(event.model_dump(), topic="status")
    except Exception as e:
        logger.debug(f"Error broadcasting status: {e}")


async def broadcast_health(manager: ConnectionManager):
    """Broadcast health metrics to 'health' topic subscribers"""
    try:
        health_data = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "process_count": len(psutil.pids()),
        }
        event = create_event(WSEventType.HEALTH_UPDATE, health_data)
        await manager.broadcast(event.model_dump(), topic="health")
    except Exception as e:
        logger.debug(f"Error broadcasting health: {e}")


async def broadcast_pending_events(manager: ConnectionManager, sigmax_manager):
    """Broadcast pending events from SIGMAX event queue"""
    try:
        events = sigmax_manager.get_pending_events()

        for event_data in events:
            event_type = event_data.get("type")
            data = event_data.get("data", {})

            # Map event type to WebSocket event type and topic
            if event_type == "trade_execution":
                ws_event = create_event(WSEventType.TRADE_EXECUTED, data)
                await manager.broadcast(ws_event.model_dump(), topic="executions")

            elif event_type == "trade_proposal":
                ws_event = create_event(WSEventType.PROPOSAL_CREATED, data)
                await manager.broadcast(ws_event.model_dump(), topic="proposals")

            elif event_type == "trade_proposal_approved":
                ws_event = create_event(WSEventType.PROPOSAL_APPROVED, data)
                await manager.broadcast(ws_event.model_dump(), topic="proposals")

            elif event_type == "agent_decision":
                ws_event = create_event(WSEventType.ANALYSIS_UPDATE, data)
                await manager.broadcast(ws_event.model_dump(), topic="analysis")

                # Also broadcast to symbol-specific subscribers
                symbol = data.get("symbol")
                if symbol:
                    await manager.broadcast(ws_event.model_dump(), topic=f"symbol:{symbol}")

    except Exception as e:
        logger.debug(f"Error broadcasting pending events: {e}")
