/**
 * SIGMAX SDK - Node.js CommonJS Example
 *
 * This example shows how to use the SDK in a plain Node.js environment
 * without TypeScript, using CommonJS imports.
 */

const { SigmaxClient } = require('@sigmax/sdk');

async function main() {
  // Initialize the client
  const client = new SigmaxClient({
    apiKey: process.env.SIGMAX_API_KEY || 'your-api-key-here',
    apiUrl: process.env.SIGMAX_API_URL || 'http://localhost:8000',
  });

  console.log('🚀 SIGMAX SDK - Node.js CommonJS Example\n');

  try {
    // 1. Health check
    console.log('Checking system health...');
    const health = await client.healthCheck();
    console.log('Status:', health.status);
    console.log('');

    // 2. Analyze BTC
    console.log('Analyzing BTC/USDT...');
    const analysis = await client.analyze('BTC/USDT', {
      risk_profile: 'conservative',
    });

    console.log('\nAnalysis Result:');
    console.log('Decision:', analysis.decision?.action);
    console.log('Confidence:', (analysis.decision?.confidence * 100).toFixed(1) + '%');
    console.log('Reasoning:', analysis.decision?.reasoning);
    console.log('');

    // 3. Get portfolio
    console.log('Getting portfolio...');
    const portfolio = await client.getPortfolio();
    console.log('Total value: $' + portfolio.total_value.toFixed(2));
    console.log('Positions:', portfolio.positions.length);
    console.log('P&L: $' + portfolio.total_pnl.toFixed(2));
    console.log('');

    // 4. Get agent debate
    console.log('Getting agent debate for BTC/USDT...');
    const debate = await client.getAgentDebate('BTC/USDT');
    console.log('Debate entries:', debate.debate.length);
    console.log('Bull score:', debate.summary.bull_score);
    console.log('Bear score:', debate.summary.bear_score);
    console.log('Final decision:', debate.summary.final_decision);
    console.log('');

    console.log('✅ Example completed successfully!');

  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

// Run the example
main();
