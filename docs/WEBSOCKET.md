# SIGMAX WebSocket API Documentation

Real-time bidirectional communication for SIGMAX trading system.

## Table of Contents

- [Overview](#overview)
- [Connection](#connection)
- [Message Protocol](#message-protocol)
- [Subscription System](#subscription-system)
- [Events](#events)
- [Client Libraries](#client-libraries)
- [Examples](#examples)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

---

## Overview

The SIGMAX WebSocket API provides real-time updates for:

- **Trading Events**: Proposals, approvals, executions
- **Analysis Updates**: Agent decisions and market analysis
- **Portfolio Changes**: Position updates and P&L
- **Market Data**: Price updates for subscribed symbols
- **System Status**: Health metrics and operational state

### Features

- **Subscription-based**: Subscribe only to events you need
- **Symbol-specific**: Get updates for specific trading pairs
- **Bidirectional**: Send commands and receive responses
- **Auto-reconnect**: Client library handles reconnection
- **Multi-instance**: Redis pub/sub for horizontal scaling
- **Heartbeat**: Automatic connection health monitoring

---

## Connection

### Endpoint

```
ws://localhost:8000/api/ws
wss://api.sigmax.io/api/ws  (production)
```

### Authentication (Optional)

Pass API key as query parameter:

```
ws://localhost:8000/api/ws?api_key=your-api-key-here
```

### Connection Flow

1. **Client connects** to WebSocket endpoint
2. **Server accepts** and sends `connected` event with connection_id
3. **Client subscribes** to topics/symbols
4. **Server sends** `subscribed` confirmation
5. **Server broadcasts** events for subscribed topics
6. **Heartbeat** ping/pong maintains connection
7. **Client disconnects** or reconnects on failure

---

## Message Protocol

### Client → Server Messages

All client messages follow this structure:

```json
{
  "type": "message_type",
  "data": { ... },
  "request_id": "optional-request-id"
}
```

#### Message Types

| Type | Description | Data Fields |
|------|-------------|-------------|
| `subscribe` | Subscribe to topics/symbols | `topics`, `symbols` |
| `unsubscribe` | Unsubscribe from topics/symbols | `topics`, `symbols` |
| `ping` | Keep-alive ping | - |
| `pong` | Response to server ping | - |
| `command` | Execute command | `command`, args |
| `get_status` | Request system status | - |
| `get_subscriptions` | List active subscriptions | - |

### Server → Client Events

All server events follow this structure:

```json
{
  "type": "event_type",
  "data": { ... },
  "timestamp": "2025-12-21T10:30:00.000Z",
  "connection_id": "conn-uuid"
}
```

#### Event Types

| Type | Description | Topic |
|------|-------------|-------|
| `connected` | Connection established | - |
| `subscribed` | Subscription confirmed | - |
| `unsubscribed` | Unsubscription confirmed | - |
| `ping` | Server heartbeat | - |
| `pong` | Response to client ping | - |
| `error` | Error occurred | - |
| `analysis_update` | Analysis completed | `analysis`, `symbol:*` |
| `proposal_created` | Trade proposal created | `proposals` |
| `proposal_approved` | Proposal approved | `proposals` |
| `trade_executed` | Trade executed | `executions` |
| `status_change` | System status changed | `status` |
| `market_update` | Market data update | `market`, `symbol:*` |
| `portfolio_update` | Portfolio changed | `portfolio` |
| `health_update` | System health metrics | `health` |
| `system_status` | Full system status | `status` |
| `alert` | Alert or warning | `alerts` |

---

## Subscription System

### Available Topics

| Topic | Description | Update Frequency |
|-------|-------------|------------------|
| `all` | All events | Varies |
| `proposals` | Trade proposals | Immediate |
| `executions` | Trade executions | Immediate |
| `analysis` | Analysis updates | Immediate |
| `status` | System status | 5 seconds |
| `market` | Market data | 2 seconds |
| `portfolio` | Portfolio updates | 3 seconds |
| `health` | System health | 10 seconds |
| `alerts` | Alerts and warnings | Immediate |

### Symbol Subscriptions

Subscribe to specific trading pairs:

- Format: `symbol:BASE/QUOTE`
- Examples: `symbol:BTC/USDT`, `symbol:ETH/USDT`

### Subscribe Example

```json
{
  "type": "subscribe",
  "data": {
    "topics": ["proposals", "executions", "analysis"],
    "symbols": ["BTC/USDT", "ETH/USDT"]
  }
}
```

**Server Response:**

```json
{
  "type": "subscribed",
  "data": {
    "topics": ["proposals", "executions", "analysis"],
    "symbols": ["BTC/USDT", "ETH/USDT"],
    "message": "Subscribed to 3 topics and 2 symbols"
  },
  "timestamp": "2025-12-21T10:30:00.000Z",
  "connection_id": "conn-uuid"
}
```

### Unsubscribe Example

```json
{
  "type": "unsubscribe",
  "data": {
    "topics": ["market"],
    "symbols": ["ETH/USDT"]
  }
}
```

---

## Events

### Analysis Update Event

Sent when analysis completes for a symbol.

```json
{
  "type": "analysis_update",
  "data": {
    "symbol": "BTC/USDT",
    "decision": "buy",
    "confidence": 0.75,
    "bull_score": 0.8,
    "bear_score": 0.4,
    "reasoning": "Strong upward momentum with increasing volume"
  },
  "timestamp": "2025-12-21T10:30:00.000Z"
}
```

### Proposal Created Event

Sent when a new trade proposal is created.

```json
{
  "type": "proposal_created",
  "data": {
    "proposal_id": "prop_123",
    "symbol": "BTC/USDT",
    "action": "buy",
    "size": 0.001,
    "reason": "Agent consensus: strong buy signal",
    "created_at": "2025-12-21T10:30:00.000Z"
  },
  "timestamp": "2025-12-21T10:30:00.000Z"
}
```

### Trade Executed Event

Sent immediately when a trade is executed.

```json
{
  "type": "trade_executed",
  "data": {
    "proposal_id": "prop_123",
    "symbol": "BTC/USDT",
    "action": "buy",
    "size": 0.001,
    "filled_price": 95000.0,
    "order_id": "order_456",
    "status": "filled",
    "fee": 0.095,
    "timestamp": "2025-12-21T10:31:00.000Z"
  },
  "timestamp": "2025-12-21T10:31:00.000Z"
}
```

### Market Update Event

Sent every 2 seconds with latest market data.

```json
{
  "type": "market_update",
  "data": [
    {
      "symbol": "BTC/USDT",
      "price": 95000.0,
      "volume_24h": 1000000,
      "change_24h": 2.5
    },
    {
      "symbol": "ETH/USDT",
      "price": 3500.0,
      "volume_24h": 500000,
      "change_24h": 1.8
    }
  ],
  "timestamp": "2025-12-21T10:30:00.000Z"
}
```

### Portfolio Update Event

Sent every 3 seconds with current portfolio state.

```json
{
  "type": "portfolio_update",
  "data": {
    "total_value": 100000.0,
    "available_cash": 50000.0,
    "positions": [
      {
        "symbol": "BTC/USDT",
        "size": 0.5,
        "entry_price": 90000.0,
        "current_price": 95000.0,
        "value": 47500.0,
        "pnl": 2500.0,
        "pnl_percent": 5.56
      }
    ],
    "total_pnl": 5000.0,
    "total_pnl_percent": 5.0
  },
  "timestamp": "2025-12-21T10:30:00.000Z"
}
```

### Health Update Event

Sent every 10 seconds with system health metrics.

```json
{
  "type": "health_update",
  "data": {
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "disk_percent": 35.0,
    "process_count": 150
  },
  "timestamp": "2025-12-21T10:30:00.000Z"
}
```

---

## Client Libraries

### Python Client

#### Installation

```bash
pip install websockets loguru
```

#### Basic Usage

```python
import asyncio
from ui.api.clients.websocket_client import SigmaxWebSocketClient

async def main():
    # Create client
    client = SigmaxWebSocketClient()

    # Connect
    await client.connect("ws://localhost:8000/api/ws")

    # Subscribe to topics
    await client.subscribe(
        topics=["proposals", "executions"],
        symbols=["BTC/USDT", "ETH/USDT"]
    )

    # Listen for events
    async for event in client.listen():
        print(f"Event: {event.type}")
        print(f"Data: {event.data}")
        print(f"Timestamp: {event.timestamp}")

asyncio.run(main())
```

#### With Event Callbacks

```python
def handle_proposal(event):
    if event.type == "proposal_created":
        print(f"New proposal: {event.data['proposal_id']}")
        print(f"Symbol: {event.data['symbol']}")
        print(f"Action: {event.data['action']}")

client = SigmaxWebSocketClient()
client.on_event(handle_proposal)

await client.connect("ws://localhost:8000/api/ws")
await client.subscribe(topics=["proposals"])
```

#### Quick Connect Helper

```python
from ui.api.clients.websocket_client import connect_sigmax

# One-line connect with subscriptions
client = await connect_sigmax(
    url="ws://localhost:8000/api/ws",
    topics=["proposals", "executions"],
    symbols=["BTC/USDT"]
)

async for event in client.listen():
    print(event.type, event.data)
```

### TypeScript/JavaScript Client

```typescript
class SigmaxWebSocket {
  private ws: WebSocket;
  private subscriptions: Set<string> = new Set();

  async connect(url: string): Promise<void> {
    this.ws = new WebSocket(url);

    return new Promise((resolve, reject) => {
      this.ws.onopen = () => {
        console.log('Connected to SIGMAX');
        resolve();
      };

      this.ws.onerror = (error) => {
        reject(error);
      };

      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      };
    });
  }

  subscribe(topics: string[], symbols: string[]): void {
    const message = {
      type: 'subscribe',
      data: { topics, symbols }
    };
    this.ws.send(JSON.stringify(message));
  }

  private handleMessage(message: any): void {
    console.log('Event:', message.type);
    console.log('Data:', message.data);

    // Handle specific event types
    switch (message.type) {
      case 'proposal_created':
        this.onProposal(message.data);
        break;
      case 'trade_executed':
        this.onTrade(message.data);
        break;
      // ... other handlers
    }
  }

  onProposal(data: any): void {
    // Override in subclass
  }

  onTrade(data: any): void {
    // Override in subclass
  }
}

// Usage
const client = new SigmaxWebSocket();
await client.connect('ws://localhost:8000/api/ws');
client.subscribe(['proposals', 'executions'], ['BTC/USDT']);
```

---

## Examples

### Monitor All Trading Activity

```python
import asyncio
from ui.api.clients.websocket_client import connect_sigmax

async def monitor_trading():
    client = await connect_sigmax(
        topics=["proposals", "executions", "analysis"]
    )

    async for event in client.listen():
        if event.type == "proposal_created":
            print(f"📝 New Proposal: {event.data['symbol']} - {event.data['action']}")

        elif event.type == "trade_executed":
            print(f"✅ Trade Executed: {event.data['symbol']} @ {event.data['filled_price']}")

        elif event.type == "analysis_update":
            print(f"📊 Analysis: {event.data['symbol']} - {event.data['decision']} (conf: {event.data['confidence']})")

asyncio.run(monitor_trading())
```

### Track Specific Symbol

```python
async def track_btc():
    client = await connect_sigmax(
        symbols=["BTC/USDT"],
        topics=["market", "analysis"]
    )

    async for event in client.listen():
        if event.type == "market_update":
            for market in event.data:
                if market['symbol'] == 'BTC/USDT':
                    print(f"BTC Price: ${market['price']:,.2f}")

        elif event.type == "analysis_update":
            print(f"BTC Analysis: {event.data['decision']} - {event.data['reasoning']}")

asyncio.run(track_btc())
```

### Portfolio Monitoring Dashboard

```python
async def portfolio_dashboard():
    client = await connect_sigmax(
        topics=["portfolio", "executions", "health"]
    )

    async for event in client.listen():
        if event.type == "portfolio_update":
            data = event.data
            print(f"\n💼 Portfolio Update")
            print(f"   Total Value: ${data['total_value']:,.2f}")
            print(f"   Cash: ${data['available_cash']:,.2f}")
            print(f"   P&L: ${data['total_pnl']:,.2f} ({data['total_pnl_percent']:.2f}%)")

            for pos in data['positions']:
                print(f"   {pos['symbol']}: {pos['size']} @ ${pos['current_price']:,.2f} (P&L: ${pos['pnl']:,.2f})")

        elif event.type == "trade_executed":
            print(f"\n🔔 Trade: {event.data['action']} {event.data['size']} {event.data['symbol']} @ ${event.data['filled_price']:,.2f}")

        elif event.type == "health_update":
            health = event.data
            print(f"\n❤️ System Health: CPU {health['cpu_percent']:.1f}% | Memory {health['memory_percent']:.1f}%")

asyncio.run(portfolio_dashboard())
```

---

## Configuration

### Environment Variables

```bash
# Redis URL for multi-instance pub/sub (optional)
REDIS_URL=redis://localhost:6379

# WebSocket connection limits
WS_MAX_CONNECTIONS=1000
WS_HEARTBEAT_INTERVAL=30
WS_CONNECTION_TIMEOUT=60

# CORS origins
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Connection Manager Settings

```python
from ui.api.websocket_manager import ConnectionManager

manager = ConnectionManager(
    redis_url="redis://localhost:6379",
    max_connections=1000,
    heartbeat_interval=30.0,
    connection_timeout=60.0
)
```

### Client Settings

```python
client = SigmaxWebSocketClient(
    auto_reconnect=True,
    max_reconnect_delay=60.0,
    ping_interval=30.0,
    ping_timeout=10.0
)
```

---

## Error Handling

### Error Event

When an error occurs, the server sends an `error` event:

```json
{
  "type": "error",
  "data": {
    "error": "Invalid subscription topic",
    "code": "INVALID_TOPIC",
    "details": "Topic 'invalid_topic' does not exist"
  },
  "timestamp": "2025-12-21T10:30:00.000Z"
}
```

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `INVALID_TOPIC` | Unknown topic | Check available topics |
| `INVALID_SYMBOL` | Invalid symbol format | Use BASE/QUOTE format |
| `MESSAGE_PROCESSING_ERROR` | Failed to process message | Check message format |
| `MAX_CONNECTIONS_EXCEEDED` | Connection limit reached | Wait and retry |
| `AUTHENTICATION_FAILED` | Invalid API key | Check API key |

### Client Error Handling

```python
try:
    client = SigmaxWebSocketClient()
    await client.connect("ws://localhost:8000/api/ws")
    await client.subscribe(topics=["proposals"])

except RuntimeError as e:
    print(f"Connection error: {e}")

except ValueError as e:
    print(f"Invalid subscription: {e}")

except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Best Practices

### 1. Subscribe Only to Needed Topics

```python
# ❌ Bad: Subscribe to everything
await client.subscribe(topics=["all"])

# ✅ Good: Subscribe to specific topics
await client.subscribe(topics=["proposals", "executions"])
```

### 2. Use Symbol-Specific Subscriptions

```python
# ✅ Good: Only get updates for trading symbols
await client.subscribe(symbols=["BTC/USDT", "ETH/USDT"])
```

### 3. Handle Reconnection Gracefully

```python
client = SigmaxWebSocketClient(
    auto_reconnect=True,
    max_reconnect_delay=60.0
)

# Client will automatically reconnect and restore subscriptions
```

### 4. Use Event Callbacks for Real-time Actions

```python
def on_proposal(event):
    if event.type == "proposal_created":
        # Take immediate action
        approve_proposal(event.data['proposal_id'])

client.on_event(on_proposal)
```

### 5. Monitor Connection Health

```python
async def main():
    client = SigmaxWebSocketClient()
    await client.connect("ws://localhost:8000/api/ws")

    while True:
        if not client.is_connected():
            logger.warning("Connection lost, waiting for reconnect...")
            await asyncio.sleep(5)

        await asyncio.sleep(1)
```

### 6. Clean Disconnect

```python
try:
    async for event in client.listen():
        # Process events
        pass
finally:
    # Always disconnect cleanly
    await client.disconnect()
```

### 7. Rate Limit Awareness

The WebSocket has no rate limits for receiving events, but sending commands may be rate-limited. Use the REST API for bulk operations.

---

## Performance Tuning

### Redis for Multi-Instance

For horizontal scaling, use Redis pub/sub:

```bash
docker-compose up -d redis
export REDIS_URL=redis://localhost:6379
```

This allows multiple API instances to share WebSocket events.

### Connection Pooling

Reuse connections instead of creating new ones:

```python
# Create once, reuse everywhere
global_client = await connect_sigmax(...)

# In your app
async for event in global_client.listen():
    await process_event(event)
```

### Efficient Broadcasting

Events are only sent to subscribers of that topic/symbol, minimizing bandwidth.

---

## Troubleshooting

### Connection Refused

```
Error: Connection refused
```

**Solution**: Ensure API is running:

```bash
cd ui/api
uvicorn main:app --reload --port 8000
```

### Redis Connection Failed

```
Warning: Redis connection failed, using in-memory only
```

**Solution**: Start Redis:

```bash
docker-compose up -d redis
```

Or disable Redis by not setting `REDIS_URL`.

### No Events Received

**Check**:
1. Are you subscribed to the right topics?
2. Is there activity happening (trades, analysis, etc.)?
3. Check server logs for errors

### Frequent Disconnects

**Causes**:
- Network issues
- Server restarts
- Connection timeout

**Solution**: Client auto-reconnection handles this automatically.

---

## API Reference

### ConnectionManager

```python
class ConnectionManager:
    async def connect(websocket: WebSocket, metadata: dict) -> str
    async def disconnect(connection_id: str)
    async def subscribe(connection_id: str, topic: str)
    async def unsubscribe(connection_id: str, topic: str)
    async def send_to(connection_id: str, message: dict) -> bool
    async def broadcast(message: dict, topic: str = None)
    async def broadcast_to_symbols(symbols: list, message: dict)
    def get_stats() -> dict
    def get_connection_info(connection_id: str) -> dict
```

### SigmaxWebSocketClient

```python
class SigmaxWebSocketClient:
    async def connect(url: str, api_key: str = None)
    async def disconnect()
    async def subscribe(topics: list = None, symbols: list = None)
    async def unsubscribe(topics: list = None, symbols: list = None)
    async def get_status() -> dict
    async def listen() -> AsyncIterator[WSEvent]
    def on_event(callback: Callable)
    def is_connected() -> bool
```

---

## Support

For issues or questions:

- **GitHub Issues**: [github.com/yourusername/sigmax/issues](https://github.com/yourusername/sigmax/issues)
- **Documentation**: [docs.sigmax.io](https://docs.sigmax.io)
- **API Docs**: http://localhost:8000/docs

---

## Changelog

### v2.0.0 (2025-12-21)

- Initial WebSocket implementation
- Subscription-based event system
- Redis pub/sub for multi-instance support
- Python client library
- Auto-reconnection support
- Heartbeat mechanism
- Symbol-specific subscriptions
