# SIGMAX API Reference

**Version:** 2.0.0
**Base URL:** `http://localhost:8000`
**Documentation:** `/docs` (Swagger UI) or `/redoc` (ReDoc)

## Authentication

All endpoints except health checks require API key authentication (when `SIGMAX_API_KEY` is set).

**Header Format:**
```http
Authorization: Bearer YOUR_API_KEY
```

**Example:**
```bash
curl -H "Authorization: Bearer your-api-key-here" \
     http://localhost:8000/api/status
```

---

## Rate Limits

| Endpoint Category | Limit |
|------------------|-------|
| Default | 60 requests/minute |
| Analysis (`/api/analyze`) | 10 requests/minute |
| Trading (`/api/trade`) | 5 requests/minute |

**Rate Limit Headers:**
- `X-RateLimit-Remaining`: Requests remaining
- `Retry-After`: Seconds until rate limit resets (on 429 error)

---

## Configuration (Environment Variables)

**Execution backend**
- `EXECUTION_BACKEND`: `ccxt` (default) or `lean`
- `LEAN_BRIDGE_URL`: HTTP endpoint for LEAN execution (required if `EXECUTION_BACKEND=lean`)
- `LEAN_BRIDGE_TIMEOUT`: Bridge timeout in seconds (default `5`)
- `LEAN_BRIDGE_CLOSE_URL`: Optional close-all endpoint (default `LEAN_BRIDGE_URL/close_all`)

**Multi-exchange data**
- `EXCHANGE`: Default exchange id (e.g., `binance`)
- `EXCHANGES`: Comma-separated list of exchanges to initialize (e.g., `binance,coinbase`)

**On-chain sampling (optional)**
- `CHAINS`: Comma-separated list of chains to sample (e.g., `evm,solana`)
- `CHAIN_RPC_EVM`: JSON-RPC endpoint for EVM chains
- `CHAIN_RPC_SOLANA`: JSON-RPC endpoint for Solana
- `onchain` field in market data will include `rpc_snapshot` with `base_fee_wei`, `block_age_sec`, and `rpc_latency_ms` when available.

---

## System Endpoints

### GET /

Get API information.

**Response:**
```json
{
  "name": "SIGMAX API",
  "version": "2.0.0",
  "status": "operational",
  "docs": "/docs",
  "health": "/health",
  "metrics": "/metrics"
}
```

---

### GET /health

Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-06T10:30:00Z",
  "uptime": 1730889000.0
}
```

---

### GET /health/ready

Kubernetes-style readiness probe. Checks all dependencies.

**Response:**
```json
{
  "ready": true,
  "checks": {
    "api": true,
    "memory": true,
    "cpu": true,
    "disk": true
  },
  "timestamp": "2025-11-06T10:30:00Z"
}
```

**Status Codes:**
- `200`: System ready
- `503`: System not ready (check `checks` object)

---

### GET /health/live

Kubernetes-style liveness probe.

**Response:**
```json
{
  "alive": true,
  "timestamp": "2025-11-06T10:30:00Z"
}
```

---

### GET /metrics

Get system and API metrics.

**Response:**
```json
{
  "timestamp": "2025-11-06T10:30:00Z",
  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 62.8,
    "disk_percent": 35.1,
    "process_count": 250
  },
  "api": {
    "total_requests": 1523,
    "failed_requests": 12,
    "success_rate": 0.992,
    "avg_response_time": 0.145,
    "endpoints": {
      "/api/analyze": {
        "count": 150,
        "errors": 2,
        "total_time": 45.2
      }
    }
  }
}
```

---

### GET /api/status

Get comprehensive system status.

**Response:**
```json
{
  "running": true,
  "mode": "paper",
  "timestamp": "2025-11-06T10:30:00Z",
  "agents": {
    "orchestrator": "active",
    "researcher": "active",
    "analyzer": "active",
    "optimizer": "active",
    "risk": "active",
    "privacy": "active"
  },
  "trading": {
    "open_positions": 2,
    "pnl_today": 125.50,
    "trades_today": 5,
    "win_rate": 0.65
  },
  "system": {
    "cpu_usage": 45.2,
    "memory_usage": 62.8
  }
}
```

---

## Analysis Endpoints

### POST /api/analyze

Analyze a trading symbol using multi-agent debate system.

**Authentication:** Required
**Rate Limit:** 10 requests/minute

**Request Body:**
```json
{
  "symbol": "BTC/USDT",
  "include_debate": false
}
```

**Parameters:**
- `symbol` (string, required): Trading pair in BASE/QUOTE format
- `include_debate` (boolean, optional): Include full agent debate log

**Response:**
```json
{
  "symbol": "BTC/USDT",
  "decision": "buy",
  "confidence": 0.75,
  "timestamp": "2025-11-06T10:30:00Z",
  "reasoning": {
    "bull": "Strong upward momentum with increasing volume",
    "bear": "Overbought on 4h timeframe, watch for pullback",
    "technical": "RSI at 65, MACD bullish crossover",
    "risk": "Within acceptable risk parameters"
  },
  "technical_indicators": {
    "rsi": 65.0,
    "macd": 250.5,
    "volume": 1500000
  }
}
```

**Decisions:**
- `buy`: Strong bullish signal
- `sell`: Strong bearish signal
- `hold`: Insufficient confidence or mixed signals

**Status Codes:**
- `200`: Analysis complete
- `400`: Invalid symbol format
- `401`: Missing/invalid API key
- `429`: Rate limit exceeded
- `500`: Analysis failed

**Example:**
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT", "include_debate": false}'
```

---

### GET /api/agents/debate/{symbol}

Get multi-agent debate history for a symbol.

**Parameters:**
- `symbol` (path, required): Trading pair (e.g., BTC/USDT)

**Response:**
```json
{
  "symbol": "BTC/USDT",
  "timestamp": "2025-11-06T10:30:00Z",
  "debate": [
    {
      "agent": "researcher",
      "role": "market_intelligence",
      "content": "Gathered 50+ data points from multiple sources...",
      "timestamp": "2025-11-06T10:30:00Z",
      "confidence": 0.7
    },
    {
      "agent": "bull",
      "role": "buy_case",
      "argument": "Strong upward momentum...",
      "timestamp": "2025-11-06T10:30:01Z",
      "score": 0.75
    },
    {
      "agent": "bear",
      "role": "sell_case",
      "argument": "Overbought conditions...",
      "timestamp": "2025-11-06T10:30:02Z",
      "score": 0.45
    }
  ],
  "summary": {
    "bull_score": 0.75,
    "bear_score": 0.45,
    "final_decision": "buy",
    "confidence": 0.75
  }
}
```

---

### GET /api/quantum/circuit

Get latest quantum circuit visualization.

**Response:**
```json
{
  "svg": "",
  "timestamp": "2025-11-06T10:30:00Z",
  "method": "VQE",
  "qubits": 4,
  "shots": 1000,
  "backend": "qasm_simulator",
  "optimization_result": {
    "converged": true,
    "iterations": 50,
    "final_energy": -1.85
  }
}
```

---

## Trading Endpoints

### POST /api/trade

Execute a trade order.

**⚠️ WARNING:** Executes actual trades in live mode!

**Authentication:** Required
**Rate Limit:** 5 requests/minute

**Request Body:**
```json
{
  "symbol": "BTC/USDT",
  "action": "buy",
  "size": 0.001
}
```

**Parameters:**
- `symbol` (string, required): Trading pair
- `action` (string, required): One of: `buy`, `sell`, `hold`
- `size` (number, required): Trade size in base currency (must be > 0)

**Response:**
```json
{
  "success": true,
  "order_id": "ORDER_1730889000123",
  "symbol": "BTC/USDT",
  "action": "buy",
  "size": 0.001,
  "status": "filled",
  "timestamp": "2025-11-06T10:30:00Z",
  "filled_price": 95000.0,
  "fee": 0.001
}
```

**Status Codes:**
- `200`: Trade executed successfully
- `400`: Invalid request (check error message)
- `401`: Missing/invalid API key
- `429`: Rate limit exceeded
- `500`: Trade execution failed

**Example:**
```bash
curl -X POST http://localhost:8000/api/trade \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC/USDT",
    "action": "buy",
    "size": 0.001
  }'
```

---

### GET /api/portfolio

Get current portfolio holdings and performance.

**Response:**
```json
{
  "total_value": 50.0,
  "cash": 2.5,
  "invested": 47.5,
  "positions": [
    {
      "symbol": "BTC/USDT",
      "size": 0.0005,
      "entry_price": 90000.0,
      "current_price": 95000.0,
      "value": 47.5,
      "pnl": 2.5,
      "pnl_pct": 5.56,
      "pnl_usd": 2.5
    }
  ],
  "performance": {
    "total_return": 5.26,
    "daily_return": 0.5,
    "sharpe_ratio": 1.8,
    "max_drawdown": -2.5
  },
  "timestamp": "2025-11-06T10:30:00Z"
}
```

---

### GET /api/history

Get trade history with pagination.

**Query Parameters:**
- `limit` (number, optional): Max trades to return (default: 50, max: 500)
- `offset` (number, optional): Number of trades to skip (default: 0)
- `symbol` (string, optional): Filter by trading pair

**Response:**
```json
{
  "trades": [
    {
      "id": "123",
      "symbol": "BTC/USDT",
      "action": "buy",
      "size": 0.001,
      "price": 95000.0,
      "timestamp": "2025-11-06T10:30:00Z",
      "pnl": 125.50
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0,
  "symbol": null,
  "timestamp": "2025-11-06T10:30:00Z"
}
```

**Example:**
```bash
curl "http://localhost:8000/api/history?limit=10&symbol=BTC/USDT"
```

---

## Control Endpoints

### POST /api/control/start

Start the trading system.

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "Trading started successfully",
  "timestamp": "2025-11-06T10:30:00Z",
  "mode": "paper"
}
```

---

### POST /api/control/pause

Pause trading temporarily. Keeps monitoring active but stops new trades.

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "Trading paused successfully",
  "timestamp": "2025-11-06T10:30:00Z"
}
```

---

### POST /api/control/stop

Stop the trading system completely.

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "Trading stopped successfully",
  "timestamp": "2025-11-06T10:30:00Z"
}
```

---

### POST /api/control/panic

🚨 **EMERGENCY STOP** - Close all positions immediately.

**⚠️ WARNING:** This will:
- Close ALL open positions at market price
- Cancel all pending orders
- Disable all trading
- Require manual restart

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "Emergency stop executed - All positions closed",
  "timestamp": "2025-11-06T10:30:00Z",
  "positions_closed": 2,
  "orders_cancelled": 1
}
```

---

## WebSocket API

### WS /ws

Real-time updates via WebSocket.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to SIGMAX');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

**Message Types:**

**1. Connection Confirmation**
```json
{
  "type": "connected",
  "message": "Connected to SIGMAX"
}
```

**2. Status Updates**
```json
{
  "type": "status_update",
  "timestamp": "2025-11-06T10:30:00Z",
  "data": {
    "price": 95000.0,
    "sentiment": 0.5,
    "positions": 2
  }
}
```

**3. Trade Notifications**
```json
{
  "type": "trade",
  "data": {
    "symbol": "BTC/USDT",
    "action": "buy",
    "size": 0.001,
    "price": 95000.0
  }
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error description",
  "error": "Additional error info (if DEBUG=true)"
}
```

### Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Bad Request | Check request parameters |
| 401 | Unauthorized | Provide valid API key |
| 404 | Not Found | Check endpoint URL |
| 429 | Too Many Requests | Wait and retry |
| 500 | Internal Server Error | Check logs, contact support |
| 503 | Service Unavailable | System not ready, check `/health/ready` |

---

## SDKs & Client Libraries

### Python Client

```python
import requests

class SIGMAXClient:
    def __init__(self, base_url="http://localhost:8000", api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}"
            })

    def analyze(self, symbol, include_debate=False):
        """Analyze a symbol"""
        response = self.session.post(
            f"{self.base_url}/api/analyze",
            json={"symbol": symbol, "include_debate": include_debate}
        )
        response.raise_for_status()
        return response.json()

    def get_portfolio(self):
        """Get portfolio"""
        response = self.session.get(f"{self.base_url}/api/portfolio")
        response.raise_for_status()
        return response.json()

    def execute_trade(self, symbol, action, size):
        """Execute a trade"""
        response = self.session.post(
            f"{self.base_url}/api/trade",
            json={"symbol": symbol, "action": action, "size": size}
        )
        response.raise_for_status()
        return response.json()

# Usage
client = SIGMAXClient(api_key="your-api-key")
result = client.analyze("BTC/USDT")
print(result)
```

### JavaScript/TypeScript Client

```typescript
class SIGMAXClient {
  constructor(private baseUrl = 'http://localhost:8000', private apiKey?: string) {}

  private async request(endpoint: string, options: RequestInit = {}) {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(this.apiKey && { Authorization: `Bearer ${this.apiKey}` }),
    };

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: { ...headers, ...options.headers },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  async analyze(symbol: string, includeDebate = false) {
    return this.request('/api/analyze', {
      method: 'POST',
      body: JSON.stringify({ symbol, include_debate: includeDebate }),
    });
  }

  async getPortfolio() {
    return this.request('/api/portfolio');
  }

  async executeTrade(symbol: string, action: string, size: number) {
    return this.request('/api/trade', {
      method: 'POST',
      body: JSON.stringify({ symbol, action, size }),
    });
  }
}

// Usage
const client = new SIGMAXClient('http://localhost:8000', 'your-api-key');
const result = await client.analyze('BTC/USDT');
console.log(result);
```

---

## Testing

### Health Check

```bash
curl http://localhost:8000/health
```

### Analyze Symbol (with API key)

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT"}'
```

### Get Portfolio

```bash
curl http://localhost:8000/api/portfolio \
  -H "Authorization: Bearer $API_KEY"
```

---

## Support

- 📖 Full Documentation: `/docs` (Swagger UI)
- 📘 Alternative Docs: `/redoc` (ReDoc)
- 🐛 Issues: [GitHub](https://github.com/yourusername/SIGMAX/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/SIGMAX/discussions)

---

**Last Updated:** 2025-11-06
**API Version:** 2.0.0
