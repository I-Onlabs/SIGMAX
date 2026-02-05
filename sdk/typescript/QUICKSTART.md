# SIGMAX SDK - Quick Start Guide

Get up and running with the SIGMAX TypeScript SDK in minutes.

## Prerequisites

- Node.js 18+ (for Node.js usage)
- Modern browser with ES6+ support (for browser usage)
- SIGMAX API server running (default: http://localhost:8000)
- SIGMAX API key

## Installation

If published:

```bash
npm install @sigmax/sdk
```

If not published, install from source:

```bash
git clone https://github.com/I-Onlabs/SIGMAX.git
cd SIGMAX/sdk/typescript
npm install && npm run build
npm link
```

Then in your project:

```bash
npm link @sigmax/sdk
```

## 5-Minute Walkthrough

### 1. Initialize the Client

```typescript
import { SigmaxClient } from '@sigmax/sdk';

const client = new SigmaxClient({
  apiKey: process.env.SIGMAX_API_KEY || 'your-api-key',
  apiUrl: 'http://localhost:8000'
});
```

### 2. Check System Health

```typescript
const health = await client.healthCheck();
console.log('System status:', health.status);
```

### 3. Analyze a Trading Pair

```typescript
const analysis = await client.analyze('BTC/USDT', {
  risk_profile: 'balanced'
});

console.log('Decision:', analysis.decision?.action);
console.log('Confidence:', analysis.decision?.confidence);
console.log('Reasoning:', analysis.decision?.reasoning);
```

### 4. Stream Real-Time Analysis

```typescript
for await (const event of client.analyzeStream('ETH/USDT')) {
  if (event.type === 'step') {
    console.log('Progress:', event.step);
  } else if (event.type === 'final') {
    console.log('Final decision:', event.decision);
    break;
  }
}
```

### 5. Create and Execute a Trade (Paper Mode)

```typescript
// Create proposal
const proposal = await client.proposeTradeProposal({
  symbol: 'BTC/USDT',
  risk_profile: 'balanced',
  mode: 'paper'
});

console.log('Proposal ID:', proposal.proposal_id);
console.log('Recommended action:', proposal.action);

// Approve proposal
await client.approveProposal(proposal.proposal_id);

// Execute (paper trading)
const result = await client.executeProposal(proposal.proposal_id);
console.log('Execution result:', result.success);
```

## Common Use Cases

### Use Case 1: Automated Analysis Loop

```typescript
const symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'];

for (const symbol of symbols) {
  try {
    const analysis = await client.analyze(symbol, {
      risk_profile: 'conservative'
    });

    if (analysis.decision?.confidence > 0.75) {
      console.log(`Strong signal for ${symbol}:`, analysis.decision.action);
    }
  } catch (error) {
    console.error(`Error analyzing ${symbol}:`, error.message);
  }

  // Respect rate limits
  await new Promise(resolve => setTimeout(resolve, 6000));
}
```

### Use Case 2: Real-Time Trading Dashboard

```typescript
async function startDashboard() {
  // Get initial status
  const status = await client.getStatus();
  console.log('Trading mode:', status.mode);

  // Get portfolio
  const portfolio = await client.getPortfolio();
  console.log('Total value:', portfolio.total_value);
  console.log('P&L:', portfolio.total_pnl);

  // List active proposals
  const proposals = await client.listProposals();
  console.log('Pending proposals:', proposals.count);

  // Get metrics
  const metrics = await client.getMetrics();
  console.log('API success rate:', metrics.api.success_rate);
}
```

### Use Case 3: Multi-Agent Debate Analysis

```typescript
const symbol = 'BTC/USDT';

// Get full agent debate
const debate = await client.getAgentDebate(symbol);

console.log('\nAgent Debate Summary:');
console.log('Bull score:', debate.summary.bull_score);
console.log('Bear score:', debate.summary.bear_score);
console.log('Final decision:', debate.summary.final_decision);

console.log('\nDebate Details:');
for (const entry of debate.debate) {
  console.log(`\n[${entry.agent}]`);
  console.log(entry.argument || entry.analysis || entry.verdict);
}
```

### Use Case 4: Error Handling

```typescript
import {
  SigmaxClient,
  RateLimitError,
  AuthenticationError,
  ValidationError
} from '@sigmax/sdk';

try {
  const result = await client.analyze('INVALID/PAIR');
} catch (error) {
  if (error instanceof RateLimitError) {
    console.log('Rate limited. Retry after:', error.retryAfter, 'seconds');
    // Implement exponential backoff
  } else if (error instanceof AuthenticationError) {
    console.error('Invalid API key');
    // Refresh credentials
  } else if (error instanceof ValidationError) {
    console.error('Invalid request:', error.message);
    // Fix input parameters
  } else {
    console.error('Unexpected error:', error);
  }
}
```

## Environment Variables

Create a `.env` file in your project:

```bash
SIGMAX_API_KEY=your-api-key-here
SIGMAX_API_URL=http://localhost:8000
```

Then use in your code:

```typescript
import dotenv from 'dotenv';
dotenv.config();

const client = new SigmaxClient({
  apiKey: process.env.SIGMAX_API_KEY!,
  apiUrl: process.env.SIGMAX_API_URL
});
```

## Running Examples

The SDK includes ready-to-run examples:

```bash
# Node.js example (CommonJS)
npm run example:basic

# TypeScript streaming example (requires tsx)
npm run example:streaming

# Or run directly
node examples/node-example.js
npx tsx examples/basic-usage.ts
npx tsx examples/streaming.ts
```

## Browser Usage

For browser usage, see `examples/browser-example.html`:

```bash
# Build the SDK first
npm run build

# Then open browser-example.html in a browser
# Or serve it with a local server:
npx serve .
```

## Next Steps

- Read the full [README.md](./README.md) for complete API reference
- Explore the [examples/](./examples) directory
- Check the [CHANGELOG.md](./CHANGELOG.md) for version history
- Visit http://localhost:8000/docs for SIGMAX API documentation

## Tips

1. **Always use paper mode for testing** - Set `mode: 'paper'` to avoid real trades
2. **Respect rate limits** - Add delays between requests to avoid rate limiting
3. **Handle errors properly** - Use try/catch and check for specific error types
4. **Monitor your portfolio** - Regularly call `getPortfolio()` to track performance
5. **Use streaming for real-time updates** - `analyzeStream()` provides step-by-step progress

## Support

- Issues: https://github.com/yourusername/sigmax/issues
- Documentation: https://github.com/yourusername/sigmax
- API Docs: http://localhost:8000/docs
