# SIGMAX SDK Overview

Complete guide to all SIGMAX SDKs and client libraries.

## Available SDKs

| SDK | Language | Status | Use Case |
|-----|----------|--------|----------|
| **Python SDK** | Python 3.11+ | ✅ Available | Server-side, data analysis, automation |
| **TypeScript SDK** | TypeScript/JavaScript | ✅ Available | Web apps, Node.js, full-stack |
| **CLI** | Command Line | ✅ Available | DevOps, scripting, terminal |
| **WebSocket** | Protocol | ✅ Available | Real-time updates, live trading |

## Quick Comparison

### When to Use Each

**Python SDK** - Best for:
- Server-side applications
- Data analysis pipelines
- Machine learning integration
- Async Python applications
- Jupyter notebooks

**TypeScript SDK** - Best for:
- Web applications (React, Vue, Angular)
- Node.js backends
- Electron desktop apps
- Full TypeScript type safety
- Browser-based trading tools

**CLI** - Best for:
- DevOps automation
- Shell scripting
- Cron jobs
- CI/CD pipelines
- Quick manual operations

**WebSocket** - Best for:
- Real-time dashboards
- Live price updates
- Instant notifications
- Bidirectional communication
- Multi-user trading rooms

---

## Python SDK

### Installation

```bash
pip install sigmax-sdk
```

### Quick Start

```python
from sigmax_sdk import SigmaxClient
import asyncio

async def main():
    # Initialize client
    client = SigmaxClient(
        api_url="http://localhost:8000",
        api_key="your_api_key"
    )

    # Analyze a trading pair
    result = await client.analyze("BTC/USDT", risk_profile="balanced")
    print(f"Action: {result.decision.action}")
    print(f"Confidence: {result.decision.confidence}")

    # Create proposal
    proposal = await client.propose_trade(
        symbol="ETH/USDT",
        risk_profile="conservative"
    )
    print(f"Proposal ID: {proposal.proposal_id}")

    # Approve and execute
    await client.approve_proposal(proposal.proposal_id)
    result = await client.execute_proposal(proposal.proposal_id)

asyncio.run(main())
```

### Streaming Analysis

```python
async def stream_analysis():
    client = SigmaxClient(api_key="your_key")

    async for event in client.analyze_stream("BTC/USDT"):
        if event.type == "step":
            print(f"Step: {event.step}")
        elif event.type == "final":
            print(f"Final result: {event.data}")

asyncio.run(stream_analysis())
```

### Documentation

- [Full Python SDK Docs](SDK_PYTHON.md)
- [Python Examples](../sdk/python/examples/)
- [API Reference](API_REFERENCE.md)

---

## TypeScript SDK

### Installation

If published:

```bash
npm install @sigmax/sdk
# or
yarn add @sigmax/sdk
# or
pnpm add @sigmax/sdk
```

If not published, install from source (see `sdk/typescript/INSTALL.md`).

### Quick Start (Node.js)

```typescript
import { SigmaxClient } from '@sigmax/sdk';

const client = new SigmaxClient({
  apiUrl: 'http://localhost:8000',
  apiKey: 'your_api_key'
});

// Analyze
const result = await client.analyze('BTC/USDT', {
  riskProfile: 'balanced'
});

console.log(`Action: ${result.decision.action}`);
console.log(`Confidence: ${result.decision.confidence}`);

// Create and execute proposal
const proposal = await client.proposeTrade('ETH/USDT', {
  riskProfile: 'conservative'
});

await client.approveProposal(proposal.proposalId);
const executionResult = await client.executeProposal(proposal.proposalId);
```

### Streaming Analysis

```typescript
// Async iteration
for await (const event of client.analyzeStream('BTC/USDT')) {
  if (event.type === 'step') {
    console.log(`Step: ${event.step}`);
  } else if (event.type === 'final') {
    console.log('Analysis complete:', event.data);
  }
}
```

### React Integration

```typescript
import { SigmaxClient } from '@sigmax/sdk';
import { useState, useEffect } from 'react';

function TradingDashboard() {
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => {
    const client = new SigmaxClient({ apiKey: process.env.SIGMAX_API_KEY });

    client.analyze('BTC/USDT')
      .then(result => setAnalysis(result))
      .catch(console.error);
  }, []);

  return <div>{analysis?.decision.action}</div>;
}
```

### Documentation

- [Full TypeScript SDK Docs](SDK_TYPESCRIPT.md)
- [TypeScript Examples](../sdk/typescript/examples/)
- [React Integration Guide](REACT_INTEGRATION.md)

---

## WebSocket API

### Connection

```python
# Python
import asyncio
import websockets
import json

async def connect():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # Authenticate
        await websocket.send(json.dumps({
            "type": "auth",
            "data": {"api_key": "your_key"}
        }))

        # Subscribe to symbols
        await websocket.send(json.dumps({
            "type": "subscribe",
            "data": {"symbols": ["BTC/USDT", "ETH/USDT"]}
        }))

        # Listen for events
        async for message in websocket:
            event = json.loads(message)
            print(f"Event: {event['type']}, Data: {event['data']}")

asyncio.run(connect())
```

```typescript
// TypeScript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.on('open', () => {
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    data: { api_key: 'your_key' }
  }));

  // Subscribe
  ws.send(JSON.stringify({
    type: 'subscribe',
    data: { symbols: ['BTC/USDT', 'ETH/USDT'] }
  }));
});

ws.on('message', (data) => {
  const event = JSON.parse(data);
  console.log(`Event: ${event.type}`, event.data);
});
```

### Message Protocol

**Client → Server:**
```json
{
  "type": "subscribe" | "unsubscribe" | "command",
  "data": {
    "symbols": ["BTC/USDT"],
    "events": ["analysis_complete", "proposal_created"]
  }
}
```

**Server → Client:**
```json
{
  "type": "analysis_update" | "proposal_created" | "trade_executed",
  "data": { ... },
  "timestamp": "2024-12-21T15:30:00Z"
}
```

### Event Types

- `analysis_update` - Real-time analysis progress
- `proposal_created` - New trade proposal
- `proposal_approved` - Proposal approved
- `trade_executed` - Trade execution result
- `status_change` - System status update
- `error` - Error notification

### Documentation

- [WebSocket Protocol Spec](WEBSOCKET.md)
- [WebSocket Examples](../examples/websocket/)

---

## CLI

### Installation

```bash
pip install -e ".[cli]"
```

### Usage

```bash
# Analyze
sigmax analyze BTC/USDT --risk balanced

# Create proposal
sigmax propose ETH/USDT --size 1000

# List proposals
sigmax proposals

# Approve and execute
sigmax approve PROP-abc123
sigmax execute PROP-abc123

# Interactive shell
sigmax shell
```

### Documentation

- [CLI Documentation](CLI.md)
- [CLI Quick Start](../QUICKSTART_CLI.md)

---

## Common Patterns

### Error Handling

**Python:**
```python
from sigmax_sdk import SigmaxClient, SigmaxError, AuthenticationError

try:
    client = SigmaxClient(api_key="invalid")
    result = await client.analyze("BTC/USDT")
except AuthenticationError as e:
    print(f"Auth failed: {e}")
except SigmaxError as e:
    print(f"API error: {e}")
```

**TypeScript:**
```typescript
import { SigmaxClient, SigmaxError } from '@sigmax/sdk';

try {
  const client = new SigmaxClient({ apiKey: 'invalid' });
  const result = await client.analyze('BTC/USDT');
} catch (error) {
  if (error instanceof SigmaxError) {
    console.error('API error:', error.message);
  }
}
```

### Batch Operations

**Python:**
```python
async def analyze_multiple(symbols: list[str]):
    client = SigmaxClient(api_key="your_key")

    # Parallel analysis
    tasks = [client.analyze(symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks)

    return results

symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
results = await analyze_multiple(symbols)
```

**TypeScript:**
```typescript
async function analyzeMultiple(symbols: string[]) {
  const client = new SigmaxClient({ apiKey: 'your_key' });

  // Parallel analysis
  const results = await Promise.all(
    symbols.map(symbol => client.analyze(symbol))
  );

  return results;
}

const results = await analyzeMultiple(['BTC/USDT', 'ETH/USDT', 'SOL/USDT']);
```

### Real-Time Dashboard

**Combining WebSocket + SDK:**
```typescript
import { SigmaxClient } from '@sigmax/sdk';

class TradingDashboard {
  private client: SigmaxClient;
  private ws: WebSocket;

  constructor(apiKey: string) {
    this.client = new SigmaxClient({ apiKey });
    this.ws = new WebSocket('ws://localhost:8000/ws');

    this.setupWebSocket();
  }

  private setupWebSocket() {
    this.ws.on('message', async (data) => {
      const event = JSON.parse(data);

      if (event.type === 'proposal_created') {
        // Get full proposal details via REST API
        const proposal = await this.client.getProposal(event.data.proposalId);
        this.displayProposal(proposal);
      }
    });
  }

  async analyzeAndSubscribe(symbol: string) {
    // Initial analysis via REST
    const result = await this.client.analyze(symbol);

    // Subscribe to real-time updates via WebSocket
    this.ws.send(JSON.stringify({
      type: 'subscribe',
      data: { symbols: [symbol] }
    }));

    return result;
  }
}
```

---

## Configuration

### Environment Variables

All SDKs support environment variables:

```bash
export SIGMAX_API_URL=http://localhost:8000
export SIGMAX_API_KEY=your_api_key
export SIGMAX_WS_URL=ws://localhost:8000/ws
```

**Python:**
```python
# Automatically uses SIGMAX_API_KEY if not provided
client = SigmaxClient()  # Uses env vars
```

**TypeScript:**
```typescript
// Automatically uses SIGMAX_API_KEY if not provided
const client = new SigmaxClient();  // Uses env vars
```

### Configuration Files

**Python SDK:**
```python
# ~/.sigmax/config.json
{
  "api_url": "http://localhost:8000",
  "api_key": "your_key",
  "default_risk_profile": "balanced",
  "timeout": 30
}

client = SigmaxClient.from_config()
```

**TypeScript SDK:**
```typescript
// sigmax.config.json
{
  "apiUrl": "http://localhost:8000",
  "apiKey": "your_key",
  "defaultRiskProfile": "balanced",
  "timeout": 30000
}

const client = SigmaxClient.fromConfig('./sigmax.config.json');
```

---

## Advanced Usage

### Custom HTTP Headers

**Python:**
```python
client = SigmaxClient(
    api_key="your_key",
    headers={
        "X-Custom-Header": "value",
        "X-Request-ID": str(uuid.uuid4())
    }
)
```

**TypeScript:**
```typescript
const client = new SigmaxClient({
  apiKey: 'your_key',
  headers: {
    'X-Custom-Header': 'value',
    'X-Request-ID': crypto.randomUUID()
  }
});
```

### Retry Logic

**Python:**
```python
from sigmax_sdk import SigmaxClient, RetryConfig

client = SigmaxClient(
    api_key="your_key",
    retry_config=RetryConfig(
        max_retries=3,
        backoff_factor=2.0,
        retry_on=[500, 502, 503, 504]
    )
)
```

**TypeScript:**
```typescript
const client = new SigmaxClient({
  apiKey: 'your_key',
  retry: {
    maxRetries: 3,
    backoffFactor: 2.0,
    retryOn: [500, 502, 503, 504]
  }
});
```

### Timeouts

**Python:**
```python
# Per-request timeout
result = await client.analyze("BTC/USDT", timeout=60)

# Global timeout
client = SigmaxClient(api_key="your_key", timeout=30)
```

**TypeScript:**
```typescript
// Per-request timeout
const result = await client.analyze('BTC/USDT', { timeout: 60000 });

// Global timeout
const client = new SigmaxClient({
  apiKey: 'your_key',
  timeout: 30000
});
```

---

## Migration Guides

### From CLI to Python SDK

```bash
# CLI
sigmax analyze BTC/USDT --risk balanced
```

```python
# Python SDK equivalent
result = await client.analyze("BTC/USDT", risk_profile="balanced")
```

### From REST API to SDK

```python
# Before (raw httpx)
async with httpx.AsyncClient() as http_client:
    response = await http_client.post(
        "http://localhost:8000/api/analyze",
        json={"symbol": "BTC/USDT", "risk_profile": "balanced"},
        headers={"Authorization": f"Bearer {api_key}"}
    )
    result = response.json()

# After (SDK)
client = SigmaxClient(api_key=api_key)
result = await client.analyze("BTC/USDT", risk_profile="balanced")
```

---

## Support

- **Documentation:** https://github.com/I-Onlabs/SIGMAX/tree/main/docs
- **Issues:** https://github.com/I-Onlabs/SIGMAX/issues
- **Discussions:** https://github.com/I-Onlabs/SIGMAX/discussions

## License

MIT - See [LICENSE](../LICENSE) file
