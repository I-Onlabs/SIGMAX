/**
 * SIGMAX TypeScript SDK - Type Definitions
 *
 * Complete type definitions for the SIGMAX API
 */

// ============================================================================
// Enums
// ============================================================================

export enum Channel {
  Telegram = 'telegram',
  Web = 'web',
  API = 'api',
  CLI = 'cli',
}

export enum Intent {
  Analyze = 'analyze',
  ProposeTrade = 'propose_trade',
  ApproveTrade = 'approve_trade',
  ExecuteTrade = 'execute_trade',
  Status = 'status',
  Explain = 'explain',
}

export type RiskProfile = 'conservative' | 'balanced' | 'aggressive';
export type Mode = 'paper' | 'live';
export type Action = 'buy' | 'sell' | 'hold';
export type StreamEventType = 'step' | 'artifact' | 'final' | 'error' | 'meta';

// ============================================================================
// Configuration
// ============================================================================

export interface SigmaxClientOptions {
  /** API base URL (default: http://localhost:8000) */
  apiUrl?: string;
  /** API key for authentication */
  apiKey: string;
  /** Request timeout in milliseconds (default: 30000) */
  timeout?: number;
  /** Additional headers to include in requests */
  headers?: Record<string, string>;
}

// ============================================================================
// Permissions & Preferences
// ============================================================================

export interface ExecutionPermissions {
  allow_paper: boolean;
  allow_live: boolean;
  require_manual_approval_live: boolean;
}

export interface UserPreferences {
  risk_profile: RiskProfile;
  mode: Mode;
  permissions: ExecutionPermissions;
}

// ============================================================================
// Analysis
// ============================================================================

export interface AnalyzeOptions {
  /** Include full agent debate log in response */
  include_debate?: boolean;
  /** Risk profile for analysis */
  risk_profile?: RiskProfile;
  /** Trading mode */
  mode?: Mode;
  /** Require manual approval for live trades */
  require_manual_approval_live?: boolean;
}

export interface Artifact {
  type: string;
  title: string;
  content: any;
  meta: Record<string, any>;
}

export interface AgentDebateEntry {
  agent: string;
  role: string;
  content?: string;
  argument?: string;
  analysis?: string;
  verdict?: string;
  decision?: string;
  confidence?: number;
  score?: number;
  timestamp: string;
  indicators?: Record<string, any>;
  approved?: boolean;
  reasoning?: string;
}

export interface DebateSummary {
  bull_score: number;
  bear_score: number;
  final_decision: Action;
  confidence: number;
}

export interface AgentDebate {
  symbol: string;
  timestamp: string;
  debate: AgentDebateEntry[];
  summary: DebateSummary;
}

export interface AnalysisResult {
  ok: boolean;
  message: string;
  intent: Intent;
  symbol: string;
  artifacts: Artifact[];
  decision?: {
    action: Action;
    confidence: number;
    reasoning: string;
    risk_assessment: string;
  };
  timestamp: string;
  debate?: AgentDebate;
}

// ============================================================================
// Trade Proposals
// ============================================================================

export interface TradeProposal {
  proposal_id: string;
  symbol: string;
  action: Action;
  size: number;
  notional_usd: number;
  mode: Mode;
  requires_manual_approval: boolean;
  approved: boolean;
  created_at: string;
  rationale?: string;
}

export interface ProposeOptions {
  /** Trading symbol */
  symbol: string;
  /** Risk profile */
  risk_profile?: RiskProfile;
  /** Trading mode */
  mode?: Mode;
}

export interface ProposalList {
  timestamp: string;
  count: number;
  proposals: Record<string, TradeProposal>;
}

export interface ExecutionResult {
  success: boolean;
  result: {
    order_id?: string;
    filled_size?: number;
    filled_price?: number;
    status?: string;
    message?: string;
  };
  timestamp: string;
}

// ============================================================================
// Streaming (SSE)
// ============================================================================

export interface StreamEvent {
  type: StreamEventType;
  timestamp: string;
  step?: string;
  data?: any;
  update?: any;
  error?: string;
  session_id?: string;
  state?: any;
  decision?: any;
  proposal?: TradeProposal;
  message?: string;
}

// ============================================================================
// System Status
// ============================================================================

export interface SystemMetrics {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  process_count: number;
}

export interface APIMetrics {
  total_requests: number;
  failed_requests: number;
  success_rate: number;
  avg_response_time: number;
  endpoints: Record<string, {
    count: number;
    errors: number;
    total_time: number;
  }>;
}

export interface SystemStatus {
  status: string;
  timestamp: string;
  mode?: Mode;
  risk_profile?: RiskProfile;
  active_positions?: number;
  agents_active?: boolean;
  system?: SystemMetrics;
  api?: APIMetrics;
}

// ============================================================================
// Portfolio
// ============================================================================

export interface Position {
  symbol: string;
  size: number;
  entry_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
  timestamp: string;
}

export interface Portfolio {
  total_value: number;
  cash: number;
  positions: Position[];
  total_pnl: number;
  total_pnl_percent: number;
  timestamp: string;
}

// ============================================================================
// Trade History
// ============================================================================

export interface TradeHistoryEntry {
  trade_id: string;
  symbol: string;
  action: Action;
  size: number;
  price: number;
  notional_usd: number;
  mode: Mode;
  timestamp: string;
  status: string;
}

export interface TradeHistory {
  timestamp: string;
  total: number;
  limit: number;
  offset: number;
  trades: TradeHistoryEntry[];
}

// ============================================================================
// Control Operations
// ============================================================================

export interface ControlResponse {
  success: boolean;
  message: string;
  timestamp: string;
  mode?: Mode;
  risk_profile?: RiskProfile;
  positions_closed?: number;
  orders_cancelled?: number;
}

// ============================================================================
// Health Checks
// ============================================================================

export interface HealthCheck {
  status: string;
  timestamp: string;
  uptime?: number;
}

export interface ReadinessCheck {
  ready: boolean;
  checks: {
    api: boolean;
    memory: boolean;
    cpu: boolean;
    disk: boolean;
  };
  timestamp: string;
}

export interface LivenessCheck {
  alive: boolean;
  timestamp: string;
}

export interface Metrics {
  timestamp: string;
  system: SystemMetrics;
  api: APIMetrics;
}

// ============================================================================
// Quantum
// ============================================================================

export interface QuantumCircuit {
  circuit_svg?: string;
  qubits?: number;
  depth?: number;
  method?: string;
  timestamp: string;
}

// ============================================================================
// Chat (Streaming Analysis)
// ============================================================================

export interface ChatRequest {
  message: string;
  symbol?: string;
  risk_profile?: RiskProfile;
  mode?: Mode;
  require_manual_approval_live?: boolean;
}
