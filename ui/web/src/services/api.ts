/**
 * SIGMAX API Client
 * Provides typed interface to FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Types
export interface SystemStatus {
  initialized: boolean;
  running: boolean;
  paused?: boolean;
  mode: string;
  risk_profile?: string;
  uptime?: number;
  agents?: Record<string, string>;
  trading?: {
    open_positions?: number;
    pnl_today?: number;
    trades_today?: number;
    win_rate?: number;
  };
  system?: {
    cpu_usage?: number;
    memory_usage?: number;
    disk_usage?: number;
  };
  timestamp: string;
}

export interface AnalysisRequest {
  symbol: string;
  include_debate?: boolean;
}

export interface AnalysisResult {
  symbol: string;
  decision?: string;
  confidence?: number;
  reasoning?: {
    bull?: string;
    bear?: string;
    technical?: string;
    risk?: string;
  };
  technical_indicators?: Record<string, number>;
  timestamp: string;
}

export interface TradeRequest {
  symbol: string;
  action: 'buy' | 'sell' | 'hold';
  size: number;
}

export interface TradeResult {
  success: boolean;
  order_id?: string;
  symbol: string;
  action: string;
  size: number;
  status?: string;
  filled_price?: number;
  fee?: number;
  timestamp: string;
}

export interface Portfolio {
  total_value: number;
  cash: number;
  invested: number;
  positions: Array<{
    symbol: string;
    size: number;
    entry_price: number;
    current_price: number;
    value: number;
    pnl: number;
    pnl_pct: number;
    pnl_usd: number;
  }>;
  performance: {
    total_return: number;
    daily_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
  };
  timestamp: string;
}

export interface TradeHistory {
  trades: Array<{
    id: string;
    symbol: string;
    action: string;
    size: number;
    price: number;
    fee: number;
    timestamp: string;
  }>;
  total: number;
  limit: number;
  offset: number;
  symbol?: string;
  timestamp: string;
}

export interface QuantumCircuit {
  svg?: string;
  timestamp: string;
  method?: string;
  qubits?: number;
  shots?: number;
  backend?: string;
  optimization_result?: {
    converged: boolean;
    iterations: number;
    final_energy: number;
  };
}

// Exchange Management Types
export interface ExchangeCredential {
  id: string;
  exchange: string;
  name: string;
  api_key: string; // Masked
  api_secret: string; // Masked
  passphrase?: string | null; // Masked
  network: string;
  enabled: boolean;
  testnet: boolean;
  created_at?: string;
  updated_at?: string;
  last_connected?: string | null;
  connection_status: string; // 'unknown' | 'connected' | 'failed'
}

export interface AddExchangeRequest {
  exchange: string;
  name: string;
  api_key: string;
  api_secret: string;
  passphrase?: string;
  testnet: boolean;
  enabled: boolean;
}

export interface UpdateExchangeRequest {
  name?: string;
  api_key?: string;
  api_secret?: string;
  passphrase?: string;
  testnet?: boolean;
  enabled?: boolean;
}

export interface ConnectionTestResult {
  success: boolean;
  message?: string;
  error?: string;
  balance?: Record<string, any>;
  network?: string;
}

export interface SupportedExchange {
  id: string;
  name: string;
  testnet_available: boolean;
  requires_passphrase: boolean;
}

/**
 * API Client Class
 */
class SIGMAXApiClient {
  private apiKey?: string;

  constructor(apiKey?: string) {
    this.apiKey = apiKey;
  }

  /**
   * Set API key for authenticated requests
   */
  setApiKey(key: string) {
    this.apiKey = key;
  }

  /**
   * Make authenticated request
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers = new Headers(options.headers || {});
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    // Add API key if available
    if (this.apiKey) {
      headers.set('Authorization', `Bearer ${this.apiKey}`);
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // === System Endpoints ===

  /**
   * Get system status
   */
  async getStatus(): Promise<SystemStatus> {
    return this.request<SystemStatus>('/api/status');
  }

  /**
   * Get system metrics
   */
  async getMetrics(): Promise<any> {
    return this.request('/metrics');
  }

  /**
   * Get health status
   */
  async getHealth(): Promise<any> {
    return this.request('/health');
  }

  // === Analysis Endpoints ===

  /**
   * Analyze a trading symbol
   */
  async analyzeSymbol(request: AnalysisRequest): Promise<AnalysisResult> {
    return this.request<AnalysisResult>('/api/analyze', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get agent debate log for a symbol
   */
  async getAgentDebate(symbol: string): Promise<any> {
    return this.request(`/api/agents/debate/${symbol}`);
  }

  // === Trading Endpoints ===

  /**
   * Execute a trade
   */
  async executeTrade(request: TradeRequest): Promise<TradeResult> {
    return this.request<TradeResult>('/api/trade', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get portfolio
   */
  async getPortfolio(): Promise<Portfolio> {
    return this.request<Portfolio>('/api/portfolio');
  }

  /**
   * Get trade history
   */
  async getTradeHistory(
    limit: number = 50,
    offset: number = 0,
    symbol?: string
  ): Promise<TradeHistory> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    if (symbol) {
      params.append('symbol', symbol);
    }

    return this.request<TradeHistory>(`/api/history?${params}`);
  }

  // === Quantum Endpoint ===

  /**
   * Get quantum circuit visualization
   */
  async getQuantumCircuit(): Promise<QuantumCircuit> {
    return this.request<QuantumCircuit>('/api/quantum/circuit');
  }

  // === Control Endpoints ===

  /**
   * Start trading system
   */
  async startTrading(): Promise<any> {
    return this.request('/api/control/start', { method: 'POST' });
  }

  /**
   * Pause trading system
   */
  async pauseTrading(): Promise<any> {
    return this.request('/api/control/pause', { method: 'POST' });
  }

  /**
   * Stop trading system
   */
  async stopTrading(): Promise<any> {
    return this.request('/api/control/stop', { method: 'POST' });
  }

  /**
   * Emergency stop - closes all positions
   */
  async emergencyStop(): Promise<any> {
    return this.request('/api/control/panic', { method: 'POST' });
  }

  // === Exchange Management Endpoints ===

  /**
   * Get all exchange credentials
   */
  async getExchanges(): Promise<ExchangeCredential[]> {
    return this.request<ExchangeCredential[]>('/api/exchanges');
  }

  /**
   * Get supported exchanges list
   */
  async getSupportedExchanges(): Promise<{ exchanges: SupportedExchange[] }> {
    return this.request('/api/exchanges/supported/list');
  }

  /**
   * Add new exchange credentials
   */
  async addExchange(request: AddExchangeRequest): Promise<ExchangeCredential> {
    return this.request<ExchangeCredential>('/api/exchanges', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Update exchange credentials
   */
  async updateExchange(
    id: string,
    request: UpdateExchangeRequest
  ): Promise<ExchangeCredential> {
    return this.request<ExchangeCredential>(`/api/exchanges/${id}`, {
      method: 'PUT',
      body: JSON.stringify(request),
    });
  }

  /**
   * Delete exchange credentials
   */
  async deleteExchange(id: string): Promise<void> {
    await this.request(`/api/exchanges/${id}`, {
      method: 'DELETE',
    });
  }

  /**
   * Test exchange connection
   */
  async testExchangeConnection(id: string): Promise<ConnectionTestResult> {
    return this.request<ConnectionTestResult>(`/api/exchanges/${id}/test`, {
      method: 'POST',
    });
  }
}

// Export singleton instance
export const api = new SIGMAXApiClient();

export default api;
