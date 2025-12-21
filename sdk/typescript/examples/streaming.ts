/**
 * SIGMAX SDK - Streaming Analysis Example
 *
 * This example demonstrates real-time streaming analysis with:
 * - Server-Sent Events (SSE)
 * - Step-by-step agent updates
 * - Real-time decision making
 * - Async iteration pattern
 */

import { SigmaxClient, StreamEvent } from '@sigmax/sdk';

async function main() {
  // Initialize the client
  const client = new SigmaxClient({
    apiKey: process.env.SIGMAX_API_KEY || 'your-api-key-here',
    apiUrl: process.env.SIGMAX_API_URL || 'http://localhost:8000',
  });

  const symbol = 'ETH/USDT';

  console.log('🚀 SIGMAX SDK - Streaming Analysis Example\n');
  console.log(`📡 Starting live analysis stream for ${symbol}...\n`);
  console.log('━'.repeat(60));

  try {
    let sessionId: string | undefined;
    let stepCount = 0;

    // Stream analysis with real-time updates
    for await (const event of client.analyzeStream(symbol, {
      risk_profile: 'balanced',
      mode: 'paper',
    })) {
      handleStreamEvent(event);

      // Track session
      if (event.type === 'meta' && event.session_id) {
        sessionId = event.session_id;
      }

      // Count steps
      if (event.type === 'step') {
        stepCount++;
      }

      // Exit on final or error
      if (event.type === 'final' || event.type === 'error') {
        break;
      }
    }

    console.log('\n' + '━'.repeat(60));
    console.log(`\n✅ Analysis completed!`);
    console.log(`Session ID: ${sessionId}`);
    console.log(`Total steps: ${stepCount}\n`);

  } catch (error) {
    console.error('\n❌ Stream error:', error);
    process.exit(1);
  }
}

/**
 * Handle different stream event types
 */
function handleStreamEvent(event: StreamEvent): void {
  const timestamp = new Date(event.timestamp).toLocaleTimeString();

  switch (event.type) {
    case 'meta':
      console.log(`\n[${timestamp}] 🔗 Connected to stream`);
      console.log(`Session: ${event.session_id}`);
      break;

    case 'step':
      console.log(`\n[${timestamp}] 🔄 ${formatStepName(event.step || 'Unknown')}`);
      if (event.update) {
        console.log(`  ${formatUpdate(event.update)}`);
      }
      break;

    case 'final':
      console.log(`\n[${timestamp}] ✨ FINAL DECISION`);
      console.log('━'.repeat(60));

      if (event.decision) {
        console.log(`\nAction: ${formatAction(event.decision.action)}`);
        console.log(`Confidence: ${formatConfidence(event.decision.confidence)}`);
        console.log(`Reasoning: ${event.decision.reasoning || 'N/A'}`);
      }

      if (event.proposal) {
        console.log(`\n💡 TRADE PROPOSAL`);
        console.log(`Proposal ID: ${event.proposal.proposal_id}`);
        console.log(`Symbol: ${event.proposal.symbol}`);
        console.log(`Action: ${formatAction(event.proposal.action)}`);
        console.log(`Size: ${event.proposal.size}`);
        console.log(`Notional: $${event.proposal.notional_usd.toFixed(2)}`);
        console.log(`Rationale: ${event.proposal.rationale || 'N/A'}`);
      }

      if (event.state) {
        console.log(`\n📊 STATE`);
        console.log(JSON.stringify(event.state, null, 2));
      }
      break;

    case 'error':
      console.error(`\n[${timestamp}] ❌ ERROR: ${event.error}`);
      break;

    default:
      console.log(`\n[${timestamp}] 📦 ${event.type}:`, event.data);
  }
}

/**
 * Format step name for display
 */
function formatStepName(step: string): string {
  const stepMap: Record<string, string> = {
    research: '🔍 RESEARCH',
    bull_debate: '🐂 BULL CASE',
    bear_debate: '🐻 BEAR CASE',
    analyzer: '📊 TECHNICAL ANALYSIS',
    risk: '🛡️ RISK VALIDATION',
    decision: '⚖️ FINAL DECISION',
  };

  return stepMap[step] || step.toUpperCase();
}

/**
 * Format update message
 */
function formatUpdate(update: any): string {
  if (typeof update === 'string') {
    return update;
  }

  if (typeof update === 'object') {
    // Extract key information
    const parts: string[] = [];

    if (update.message) parts.push(update.message);
    if (update.status) parts.push(`Status: ${update.status}`);
    if (update.progress !== undefined) parts.push(`Progress: ${update.progress}%`);

    return parts.length > 0 ? parts.join(' | ') : JSON.stringify(update);
  }

  return String(update);
}

/**
 * Format action with emoji
 */
function formatAction(action: string): string {
  const actionMap: Record<string, string> = {
    buy: '🟢 BUY',
    sell: '🔴 SELL',
    hold: '🟡 HOLD',
  };

  return actionMap[action.toLowerCase()] || action.toUpperCase();
}

/**
 * Format confidence as percentage with bar
 */
function formatConfidence(confidence: number): string {
  const percent = (confidence * 100).toFixed(1);
  const barLength = 20;
  const filled = Math.round(confidence * barLength);
  const bar = '█'.repeat(filled) + '░'.repeat(barLength - filled);

  return `${percent}% ${bar}`;
}

// Run the example
main();
