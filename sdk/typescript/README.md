# SIGMAX TypeScript SDK

[![npm version](https://badge.fury.io/js/%40sigmax%2Fsdk.svg)](https://www.npmjs.com/package/@sigmax/sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Production-ready TypeScript/JavaScript SDK for the **SIGMAX Autonomous AI Crypto Trading System**.

## Features

- **Full TypeScript Support** - Complete type definitions for all API endpoints
- **Dual Package** - Works in Node.js (ESM & CommonJS) and browsers
- **Streaming Support** - Real-time analysis via Server-Sent Events (SSE)
- **Error Handling** - Comprehensive error types with proper HTTP status mapping
- **Zero Dependencies** - Lightweight with no external runtime dependencies
- **Tree-Shakeable** - Modern ESM exports for optimal bundle sizes

## Installation

```bash
# npm
npm install @sigmax/sdk

# yarn
yarn add @sigmax/sdk

# pnpm
pnpm add @sigmax/sdk
```

## Quick Start

### Node.js (TypeScript/ESM)

```typescript
import { SigmaxClient } from '@sigmax/sdk';

const client = new SigmaxClient({
  apiKey: process.env.SIGMAX_API_KEY,
  apiUrl: 'http://localhost:8000' // optional, defaults to localhost:8000
});

// Analyze a trading pair
const analysis = await client.analyze('BTC/USDT', {
  risk_profile: 'balanced',
  include_debate: true
});

console.log('Decision:', analysis.decision?.action);
console.log('Confidence:', analysis.decision?.confidence);
```

### Node.js (CommonJS)

```javascript
const { SigmaxClient } = require('@sigmax/sdk');

const client = new SigmaxClient({
  apiKey: 'your-api-key',
  apiUrl: 'http://localhost:8000'
});

async function main() {
  const result = await client.analyze('ETH/USDT');
  console.log(result);
}

main();
```

### Browser (ESM)

```html
<script type="module">
  import { SigmaxClient } from '@sigmax/sdk';

  const client = new SigmaxClient({
    apiKey: 'your-api-key',
    apiUrl: 'http://localhost:8000'
  });

  const analysis = await client.analyze('BTC/USDT');
  console.log(analysis);
</script>
```

## API Reference

### Client Initialization

```typescript
const client = new SigmaxClient({
  apiKey: string;           // Required: Your SIGMAX API key
  apiUrl?: string;          // Optional: API base URL (default: http://localhost:8000)
  timeout?: number;         // Optional: Request timeout in ms (default: 30000)
  headers?: Record<string, string>; // Optional: Additional headers
});
```

### Analysis Methods

#### `analyze(symbol, options?)`

Analyze a trading symbol using the multi-agent debate system.

```typescript
const result = await client.analyze('BTC/USDT', {
  include_debate: true,      // Include full agent debate log
  risk_profile: 'balanced',  // 'conservative' | 'balanced' | 'aggressive'
  mode: 'paper'              // 'paper' | 'live'
});

// Result includes:
// - decision: { action, confidence, reasoning, risk_assessment }
// - artifacts: Array of analysis artifacts
// - debate?: Full multi-agent debate (if include_debate: true)
```

#### `analyzeStream(symbol, options?)`

Stream analysis with real-time step-by-step updates via SSE.

```typescript
for await (const event of client.analyzeStream('ETH/USDT')) {
  switch (event.type) {
    case 'meta':
      console.log('Connected:', event.session_id);
      break;
    case 'step':
      console.log('Step:', event.step, event.update);
      break;
    case 'final':
      console.log('Decision:', event.decision);
      console.log('Proposal:', event.proposal);
      break;
    case 'error':
      console.error('Error:', event.error);
      break;
  }
}
```

#### `getAgentDebate(symbol)`

Get the full multi-agent debate history for a symbol.

```typescript
const debate = await client.getAgentDebate('BTC/USDT');

// Returns:
// - debate: Array of agent entries (Bull, Bear, Researcher, Analyzer, Risk)
// - summary: { bull_score, bear_score, final_decision, confidence }
```

### Trade Proposal Methods

#### `proposeTradeProposal(options)`

Create a trade proposal based on analysis.

```typescript
const proposal = await client.proposeTradeProposal({
  symbol: 'BTC/USDT',
  risk_profile: 'balanced',
  mode: 'paper'
});

console.log('Proposal ID:', proposal.proposal_id);
console.log('Action:', proposal.action);
console.log('Size:', proposal.size);
console.log('Rationale:', proposal.rationale);
```

#### `listProposals()`

List all pending trade proposals.

```typescript
const proposals = await client.listProposals();

console.log('Total:', proposals.count);
console.log('Proposals:', proposals.proposals);
```

#### `getProposal(proposalId)`

Get a specific trade proposal by ID.

```typescript
const proposal = await client.getProposal('proposal-123');
```

#### `approveProposal(proposalId)`

Approve a trade proposal.

```typescript
const approved = await client.approveProposal('proposal-123');
console.log('Approved:', approved.approved);
```

#### `executeProposal(proposalId)`

Execute an approved trade proposal.

```typescript
const result = await client.executeProposal('proposal-123');
console.log('Success:', result.success);
console.log('Order ID:', result.result.order_id);
```

### Portfolio & Trading Methods

#### `getPortfolio()`

Get current portfolio holdings and performance.

```typescript
const portfolio = await client.getPortfolio();

console.log('Total value:', portfolio.total_value);
console.log('Cash:', portfolio.cash);
console.log('Positions:', portfolio.positions);
console.log('P&L:', portfolio.total_pnl);
```

#### `getTradeHistory(limit?, offset?, symbol?)`

Get trade history with pagination.

```typescript
const history = await client.getTradeHistory(50, 0, 'BTC/USDT');

console.log('Total trades:', history.total);
console.log('Trades:', history.trades);
```

### System Status & Control Methods

#### `getStatus()`

Get comprehensive system status.

```typescript
const status = await client.getStatus();

console.log('Mode:', status.mode);
console.log('Risk Profile:', status.risk_profile);
console.log('Active Positions:', status.active_positions);
```

#### `startTrading()`

Start the trading system.

```typescript
const result = await client.startTrading();
console.log('Started:', result.success);
```

#### `pauseTrading()`

Pause trading temporarily (keeps monitoring active).

```typescript
const result = await client.pauseTrading();
```

#### `stopTrading()`

Stop the trading system.

```typescript
const result = await client.stopTrading();
```

#### `emergencyStop()`

Emergency stop - closes ALL positions immediately.

**WARNING:** This will close all open positions at market price!

```typescript
const result = await client.emergencyStop();
console.log('Positions closed:', result.positions_closed);
console.log('Orders cancelled:', result.orders_cancelled);
```

### Health & Monitoring Methods

#### `healthCheck()`

Basic health check.

```typescript
const health = await client.healthCheck();
console.log('Status:', health.status);
```

#### `readinessCheck()`

Kubernetes-style readiness probe.

```typescript
const ready = await client.readinessCheck();
console.log('Ready:', ready.ready);
console.log('Checks:', ready.checks);
```

#### `livenessCheck()`

Kubernetes-style liveness probe.

```typescript
const alive = await client.livenessCheck();
console.log('Alive:', alive.alive);
```

#### `getMetrics()`

Get API performance metrics.

```typescript
const metrics = await client.getMetrics();

console.log('Total requests:', metrics.api.total_requests);
console.log('Success rate:', metrics.api.success_rate);
console.log('Avg response time:', metrics.api.avg_response_time);
console.log('CPU usage:', metrics.system.cpu_percent);
```

### Quantum Methods

#### `getQuantumCircuit()`

Get quantum circuit visualization for portfolio optimization.

```typescript
const circuit = await client.getQuantumCircuit();

console.log('Qubits:', circuit.qubits);
console.log('Depth:', circuit.depth);
console.log('SVG:', circuit.circuit_svg);
```

## Error Handling

The SDK provides comprehensive error types:

```typescript
import {
  SigmaxClient,
  AuthenticationError,
  RateLimitError,
  ValidationError,
  NotFoundError,
  PermissionError,
  ServiceUnavailableError,
  TimeoutError,
  NetworkError
} from '@sigmax/sdk';

try {
  const result = await client.analyze('BTC/USDT');
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Invalid API key');
  } else if (error instanceof RateLimitError) {
    console.error('Rate limit exceeded. Retry after:', error.retryAfter);
  } else if (error instanceof ValidationError) {
    console.error('Invalid request:', error.message);
  } else if (error instanceof NotFoundError) {
    console.error('Resource not found');
  } else if (error instanceof PermissionError) {
    console.error('Permission denied');
  } else if (error instanceof ServiceUnavailableError) {
    console.error('Service unavailable');
  } else if (error instanceof TimeoutError) {
    console.error('Request timed out');
  } else if (error instanceof NetworkError) {
    console.error('Network error:', error.message);
  }
}
```

## Streaming Examples

### Real-time Analysis with Progress Updates

```typescript
console.log('Starting analysis stream...\n');

for await (const event of client.analyzeStream('BTC/USDT', {
  risk_profile: 'balanced',
  mode: 'paper'
})) {
  const timestamp = new Date(event.timestamp).toLocaleTimeString();

  switch (event.type) {
    case 'meta':
      console.log(`[${timestamp}] Connected - Session: ${event.session_id}`);
      break;

    case 'step':
      console.log(`[${timestamp}] ${event.step}: ${event.update}`);
      break;

    case 'final':
      console.log(`\n[${timestamp}] FINAL DECISION`);
      console.log('Action:', event.decision.action);
      console.log('Confidence:', (event.decision.confidence * 100).toFixed(1) + '%');
      console.log('Reasoning:', event.decision.reasoning);

      if (event.proposal) {
        console.log('\nTrade Proposal Generated:');
        console.log('ID:', event.proposal.proposal_id);
        console.log('Symbol:', event.proposal.symbol);
        console.log('Action:', event.proposal.action);
        console.log('Size:', event.proposal.size);
      }
      break;

    case 'error':
      console.error(`[${timestamp}] Error:`, event.error);
      break;
  }
}

console.log('\nStream completed!');
```

### Cancellable Stream with Timeout

```typescript
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), 60000); // 1 minute timeout

try {
  for await (const event of client.analyzeStream('ETH/USDT')) {
    console.log(event);

    if (event.type === 'final') break;
  }
} catch (error) {
  if (error.name === 'AbortError') {
    console.log('Stream cancelled or timed out');
  }
} finally {
  clearTimeout(timeout);
}
```

## TypeScript Support

The SDK is written in TypeScript and provides complete type definitions:

```typescript
import type {
  AnalysisResult,
  TradeProposal,
  Portfolio,
  StreamEvent,
  RiskProfile,
  Mode,
  Action
} from '@sigmax/sdk';

const analysis: AnalysisResult = await client.analyze('BTC/USDT');
const proposal: TradeProposal = await client.proposeTradeProposal({
  symbol: 'BTC/USDT',
  risk_profile: 'balanced' as RiskProfile,
  mode: 'paper' as Mode
});
```

## Rate Limits

The SIGMAX API enforces rate limits:

- **Default endpoints:** 60 requests/minute
- **Analysis endpoints:** 10 requests/minute
- **Trading endpoints:** 5 requests/minute

When rate limited, a `RateLimitError` is thrown with `retryAfter` property indicating seconds to wait.

## Examples

See the `examples/` directory for complete working examples:

- `basic-usage.ts` - Complete SDK usage walkthrough
- `streaming.ts` - Real-time streaming analysis
- `node-example.js` - CommonJS usage (plain Node.js)
- `browser-example.html` - Browser usage with UI

## Building from Source

```bash
# Install dependencies
npm install

# Build the package
npm run build

# This creates:
# - dist/index.js (CommonJS)
# - dist/index.mjs (ESM)
# - dist/index.d.ts (TypeScript definitions)
```

## License

MIT

## Support

- Documentation: https://github.com/yourusername/sigmax
- Issues: https://github.com/yourusername/sigmax/issues
- API Docs: http://localhost:8000/docs (when running SIGMAX)

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.
