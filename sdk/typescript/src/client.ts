/**
 * SIGMAX TypeScript SDK - Main Client
 */

import {
  AnalyzeOptions,
  AnalysisResult,
  ChatRequest,
  ControlResponse,
  ExecutionResult,
  HealthCheck,
  LivenessCheck,
  Metrics,
  Portfolio,
  ProposeOptions,
  ProposalList,
  QuantumCircuit,
  ReadinessCheck,
  SigmaxClientOptions,
  StreamEvent,
  SystemStatus,
  TradeHistory,
  TradeProposal,
  AgentDebate,
} from './types';
import { buildUrl, makeRequest } from './utils/fetch';
// import { streamSSE } from './utils/sse'; // TODO: Implement streaming support

/**
 * SIGMAX SDK Client
 *
 * Main client for interacting with the SIGMAX API
 *
 * @example
 * ```typescript
 * import { SigmaxClient } from '@sigmax/sdk';
 *
 * const client = new SigmaxClient({
 *   apiKey: 'your-api-key',
 *   apiUrl: 'http://localhost:8000'
 * });
 *
 * // Analyze a symbol
 * const analysis = await client.analyze('BTC/USDT');
 *
 * // Stream analysis with real-time updates
 * for await (const event of client.analyzeStream('BTC/USDT')) {
 *   if (event.type === 'step') {
 *     console.log('Step:', event.step, event.update);
 *   } else if (event.type === 'final') {
 *     console.log('Final decision:', event.decision);
 *   }
 * }
 * ```
 */
export class SigmaxClient {
  private apiUrl: string;
  private apiKey: string;
  private timeout: number;
  private headers: Record<string, string>;

  constructor(options: SigmaxClientOptions) {
    this.apiUrl = options.apiUrl || 'http://localhost:8000';
    this.apiKey = options.apiKey;
    this.timeout = options.timeout || 30000;
    this.headers = {
      Authorization: `Bearer ${this.apiKey}`,
      ...options.headers,
    };

    // Remove trailing slash from API URL
    if (this.apiUrl.endsWith('/')) {
      this.apiUrl = this.apiUrl.slice(0, -1);
    }
  }

  // ============================================================================
  // Analysis Methods
  // ============================================================================

  /**
   * Analyze a trading symbol using multi-agent debate system
   *
   * @param symbol - Trading pair (e.g., 'BTC/USDT')
   * @param options - Analysis options
   * @returns Analysis result with decision and artifacts
   *
   * @example
   * ```typescript
   * const result = await client.analyze('BTC/USDT', {
   *   include_debate: true,
   *   risk_profile: 'balanced'
   * });
   * console.log('Decision:', result.decision?.action);
   * console.log('Confidence:', result.decision?.confidence);
   * ```
   */
  async analyze(
    symbol: string,
    options: AnalyzeOptions = {}
  ): Promise<AnalysisResult> {
    return makeRequest<AnalysisResult>(
      buildUrl(this.apiUrl, '/api/analyze'),
      {
        method: 'POST',
        body: {
          symbol: symbol.toUpperCase(),
          include_debate: options.include_debate || false,
        },
        headers: this.headers,
        timeout: this.timeout,
      }
    );
  }

  /**
   * Stream analysis with real-time step-by-step updates
   *
   * @param symbol - Trading pair (e.g., 'BTC/USDT')
   * @param options - Analysis options
   * @returns Async iterator of stream events
   *
   * @example
   * ```typescript
   * for await (const event of client.analyzeStream('ETH/USDT')) {
   *   switch (event.type) {
   *     case 'step':
   *       console.log(`[${event.step}]`, event.update);
   *       break;
   *     case 'final':
   *       console.log('Analysis complete:', event.decision);
   *       break;
   *     case 'error':
   *       console.error('Error:', event.error);
   *       break;
   *   }
   * }
   * ```
   */
  async *analyzeStream(
    symbol: string,
    options: AnalyzeOptions = {}
  ): AsyncIterableIterator<StreamEvent> {
    const chatRequest: ChatRequest = {
      message: `Analyze ${symbol}`,
      symbol: symbol.toUpperCase(),
      risk_profile: options.risk_profile || 'conservative',
      mode: options.mode || 'paper',
      require_manual_approval_live:
        options.require_manual_approval_live !== undefined
          ? options.require_manual_approval_live
          : true,
    };

    const url = buildUrl(this.apiUrl, '/api/chat/stream');

    // Use POST for streaming endpoint
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        ...this.headers,
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify(chatRequest),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    // Stream events
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events
        const lines = buffer.split('\n');
        buffer = '';

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i].trim();

          if (line.startsWith('event:')) {
            const eventType = line.substring(6).trim();
            const nextLine = lines[i + 1];

            if (nextLine && nextLine.startsWith('data:')) {
              const dataStr = nextLine.substring(5).trim();
              try {
                const data = JSON.parse(dataStr);
                yield {
                  type: eventType as any,
                  ...data,
                };
              } catch {
                // Skip invalid JSON
              }
              i++; // Skip data line
            }
          } else if (!line.startsWith('data:') && !line.startsWith('event:') && line) {
            // Incomplete line, add back to buffer
            buffer = line;
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Get full agent debate history for a symbol
   *
   * @param symbol - Trading pair
   * @returns Agent debate with bull/bear arguments
   */
  async getAgentDebate(symbol: string): Promise<AgentDebate> {
    return makeRequest<AgentDebate>(
      buildUrl(this.apiUrl, `/api/agents/debate/${symbol.toUpperCase()}`),
      {
        method: 'GET',
        headers: this.headers,
        timeout: this.timeout,
      }
    );
  }

  // ============================================================================
  // Trade Proposal Methods
  // ============================================================================

  /**
   * Create a trade proposal based on analysis
   *
   * @param options - Proposal options
   * @returns Trade proposal requiring approval
   *
   * @example
   * ```typescript
   * const proposal = await client.proposeTradeProposal({
   *   symbol: 'BTC/USDT',
   *   risk_profile: 'balanced',
   *   mode: 'paper'
   * });
   * console.log('Proposal ID:', proposal.proposal_id);
   * ```
   */
  async proposeTradeProposal(options: ProposeOptions): Promise<TradeProposal> {
    const response = await makeRequest<{ proposal: TradeProposal }>(
      buildUrl(this.apiUrl, '/api/chat/proposals'),
      {
        method: 'POST',
        body: {
          symbol: options.symbol.toUpperCase(),
          risk_profile: options.risk_profile || 'conservative',
          mode: options.mode || 'paper',
        },
        headers: this.headers,
        timeout: this.timeout,
      }
    );

    return response.proposal;
  }

  /**
   * List all pending trade proposals
   *
   * @returns List of all proposals
   */
  async listProposals(): Promise<ProposalList> {
    return makeRequest<ProposalList>(
      buildUrl(this.apiUrl, '/api/chat/proposals'),
      {
        method: 'GET',
        headers: this.headers,
        timeout: this.timeout,
      }
    );
  }

  /**
   * Get a specific trade proposal by ID
   *
   * @param proposalId - Proposal ID
   * @returns Trade proposal details
   */
  async getProposal(proposalId: string): Promise<TradeProposal> {
    return makeRequest<TradeProposal>(
      buildUrl(this.apiUrl, `/api/chat/proposals/${proposalId}`),
      {
        method: 'GET',
        headers: this.headers,
        timeout: this.timeout,
      }
    );
  }

  /**
   * Approve a trade proposal
   *
   * @param proposalId - Proposal ID to approve
   * @returns Updated proposal with approved status
   */
  async approveProposal(proposalId: string): Promise<TradeProposal> {
    return makeRequest<TradeProposal>(
      buildUrl(this.apiUrl, `/api/chat/proposals/${proposalId}/approve`),
      {
        method: 'POST',
        headers: this.headers,
        timeout: this.timeout,
      }
    );
  }

  /**
   * Execute an approved trade proposal
   *
   * @param proposalId - Proposal ID to execute
   * @returns Execution result
   *
   * @example
   * ```typescript
   * // Create, approve, and execute a proposal
   * const proposal = await client.proposeTradeProposal({
   *   symbol: 'BTC/USDT',
   *   mode: 'paper'
   * });
   *
   * await client.approveProposal(proposal.proposal_id);
   * const result = await client.executeProposal(proposal.proposal_id);
   *
   * console.log('Execution:', result.success ? 'Success' : 'Failed');
   * ```
   */
  async executeProposal(proposalId: string): Promise<ExecutionResult> {
    return makeRequest<ExecutionResult>(
      buildUrl(this.apiUrl, `/api/chat/proposals/${proposalId}/execute`),
      {
        method: 'POST',
        headers: this.headers,
        timeout: this.timeout,
      }
    );
  }

  // ============================================================================
  // Portfolio & Trading Methods
  // ============================================================================

  /**
   * Get current portfolio holdings and performance
   *
   * @returns Portfolio with positions and P&L
   */
  async getPortfolio(): Promise<Portfolio> {
    return makeRequest<Portfolio>(buildUrl(this.apiUrl, '/api/portfolio'), {
      method: 'GET',
      headers: this.headers,
      timeout: this.timeout,
    });
  }

  /**
   * Get trade history with pagination
   *
   * @param limit - Maximum number of trades (default: 50, max: 500)
   * @param offset - Number of trades to skip (default: 0)
   * @param symbol - Filter by trading pair (optional)
   * @returns Paginated trade history
   */
  async getTradeHistory(
    limit = 50,
    offset = 0,
    symbol?: string
  ): Promise<TradeHistory> {
    return makeRequest<TradeHistory>(
      buildUrl(this.apiUrl, '/api/history', {
        limit,
        offset,
        symbol: symbol?.toUpperCase(),
      }),
      {
        method: 'GET',
        headers: this.headers,
        timeout: this.timeout,
      }
    );
  }

  // ============================================================================
  // System Status & Control Methods
  // ============================================================================

  /**
   * Get comprehensive system status
   *
   * @returns System status with metrics and agent activity
   */
  async getStatus(): Promise<SystemStatus> {
    return makeRequest<SystemStatus>(buildUrl(this.apiUrl, '/api/status'), {
      method: 'GET',
      headers: this.headers,
      timeout: this.timeout,
    });
  }

  /**
   * Start the trading system
   *
   * @returns Control response
   */
  async startTrading(): Promise<ControlResponse> {
    return makeRequest<ControlResponse>(
      buildUrl(this.apiUrl, '/api/control/start'),
      {
        method: 'POST',
        headers: this.headers,
        timeout: this.timeout,
      }
    );
  }

  /**
   * Pause trading temporarily
   *
   * @returns Control response
   */
  async pauseTrading(): Promise<ControlResponse> {
    return makeRequest<ControlResponse>(
      buildUrl(this.apiUrl, '/api/control/pause'),
      {
        method: 'POST',
        headers: this.headers,
        timeout: this.timeout,
      }
    );
  }

  /**
   * Stop the trading system
   *
   * @returns Control response
   */
  async stopTrading(): Promise<ControlResponse> {
    return makeRequest<ControlResponse>(
      buildUrl(this.apiUrl, '/api/control/stop'),
      {
        method: 'POST',
        headers: this.headers,
        timeout: this.timeout,
      }
    );
  }

  /**
   * Emergency stop - closes all positions immediately
   *
   * WARNING: This will close ALL open positions at market price!
   *
   * @returns Control response with positions closed count
   */
  async emergencyStop(): Promise<ControlResponse> {
    return makeRequest<ControlResponse>(
      buildUrl(this.apiUrl, '/api/control/panic'),
      {
        method: 'POST',
        headers: this.headers,
        timeout: this.timeout,
      }
    );
  }

  // ============================================================================
  // Health & Monitoring Methods
  // ============================================================================

  /**
   * Basic health check
   *
   * @returns Health status
   */
  async healthCheck(): Promise<HealthCheck> {
    return makeRequest<HealthCheck>(buildUrl(this.apiUrl, '/health'), {
      method: 'GET',
      timeout: 5000, // Short timeout for health checks
    });
  }

  /**
   * Readiness probe (Kubernetes-style)
   *
   * @returns Readiness status with dependency checks
   */
  async readinessCheck(): Promise<ReadinessCheck> {
    return makeRequest<ReadinessCheck>(buildUrl(this.apiUrl, '/health/ready'), {
      method: 'GET',
      timeout: 5000,
    });
  }

  /**
   * Liveness probe (Kubernetes-style)
   *
   * @returns Liveness status
   */
  async livenessCheck(): Promise<LivenessCheck> {
    return makeRequest<LivenessCheck>(buildUrl(this.apiUrl, '/health/live'), {
      method: 'GET',
      timeout: 5000,
    });
  }

  /**
   * Get API performance metrics
   *
   * @returns System and API metrics
   */
  async getMetrics(): Promise<Metrics> {
    return makeRequest<Metrics>(buildUrl(this.apiUrl, '/metrics'), {
      method: 'GET',
      headers: this.headers,
      timeout: this.timeout,
    });
  }

  // ============================================================================
  // Quantum Methods
  // ============================================================================

  /**
   * Get quantum circuit visualization
   *
   * @returns Quantum circuit data with SVG representation
   */
  async getQuantumCircuit(): Promise<QuantumCircuit> {
    return makeRequest<QuantumCircuit>(
      buildUrl(this.apiUrl, '/api/quantum/circuit'),
      {
        method: 'GET',
        headers: this.headers,
        timeout: this.timeout,
      }
    );
  }
}
