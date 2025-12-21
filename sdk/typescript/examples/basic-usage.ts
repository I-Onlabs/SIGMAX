/**
 * SIGMAX SDK - Basic Usage Example
 *
 * This example demonstrates basic SDK usage including:
 * - Client initialization
 * - Symbol analysis
 * - Trade proposals
 * - Error handling
 */

import { SigmaxClient, SigmaxError } from '@sigmax/sdk';

async function main() {
  // Initialize the client
  const client = new SigmaxClient({
    apiKey: process.env.SIGMAX_API_KEY || 'your-api-key-here',
    apiUrl: process.env.SIGMAX_API_URL || 'http://localhost:8000',
  });

  try {
    console.log('🚀 SIGMAX SDK - Basic Usage Example\n');

    // 1. Check system health
    console.log('📊 Checking system health...');
    const health = await client.healthCheck();
    console.log('Status:', health.status);
    console.log('');

    // 2. Get system status
    console.log('🔍 Getting system status...');
    const status = await client.getStatus();
    console.log('Mode:', status.mode);
    console.log('Risk Profile:', status.risk_profile);
    console.log('');

    // 3. Analyze a trading symbol
    const symbol = 'BTC/USDT';
    console.log(`📈 Analyzing ${symbol}...`);

    const analysis = await client.analyze(symbol, {
      risk_profile: 'balanced',
      include_debate: false,
    });

    console.log('\nAnalysis Result:');
    console.log('Symbol:', analysis.symbol);
    console.log('Decision:', analysis.decision?.action);
    console.log('Confidence:', analysis.decision?.confidence);
    console.log('Reasoning:', analysis.decision?.reasoning);
    console.log('');

    // 4. Create a trade proposal
    console.log('💡 Creating trade proposal...');

    const proposal = await client.proposeTradeProposal({
      symbol,
      risk_profile: 'balanced',
      mode: 'paper', // Safe to use paper mode for testing
    });

    console.log('\nTrade Proposal:');
    console.log('Proposal ID:', proposal.proposal_id);
    console.log('Symbol:', proposal.symbol);
    console.log('Action:', proposal.action);
    console.log('Size:', proposal.size);
    console.log('Notional USD:', proposal.notional_usd);
    console.log('Mode:', proposal.mode);
    console.log('Rationale:', proposal.rationale);
    console.log('');

    // 5. List all proposals
    console.log('📋 Listing all proposals...');
    const proposalList = await client.listProposals();
    console.log('Total proposals:', proposalList.count);
    console.log('');

    // 6. Approve and execute (paper mode only for safety)
    if (proposal.mode === 'paper') {
      console.log('✅ Approving proposal...');
      const approved = await client.approveProposal(proposal.proposal_id);
      console.log('Approved:', approved.approved);
      console.log('');

      console.log('⚡ Executing proposal...');
      const execution = await client.executeProposal(proposal.proposal_id);
      console.log('Execution success:', execution.success);
      console.log('Result:', execution.result);
      console.log('');
    }

    // 7. Get portfolio
    console.log('💼 Getting portfolio...');
    const portfolio = await client.getPortfolio();
    console.log('Total value:', portfolio.total_value);
    console.log('Cash:', portfolio.cash);
    console.log('Positions:', portfolio.positions.length);
    console.log('Total P&L:', portfolio.total_pnl);
    console.log('');

    // 8. Get trade history
    console.log('📜 Getting trade history...');
    const history = await client.getTradeHistory(10, 0);
    console.log('Total trades:', history.total);
    console.log('Recent trades:', history.trades.length);
    console.log('');

    // 9. Get metrics
    console.log('📊 Getting API metrics...');
    const metrics = await client.getMetrics();
    console.log('Total requests:', metrics.api.total_requests);
    console.log('Success rate:', (metrics.api.success_rate * 100).toFixed(2) + '%');
    console.log('Avg response time:', metrics.api.avg_response_time + 'ms');
    console.log('');

    console.log('✅ Example completed successfully!');

  } catch (error) {
    if (error instanceof SigmaxError) {
      console.error('❌ SIGMAX Error:', error.name);
      console.error('Message:', error.message);
    } else {
      console.error('❌ Unexpected error:', error);
    }
    process.exit(1);
  }
}

// Run the example
main();
