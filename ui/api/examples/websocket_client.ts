/**
 * SIGMAX WebSocket Client (TypeScript/JavaScript)
 *
 * Example client implementation for web applications.
 */

// Event types
export enum WSEventType {
  CONNECTED = 'connected',
  SUBSCRIBED = 'subscribed',
  UNSUBSCRIBED = 'unsubscribed',
  PING = 'ping',
  PONG = 'pong',
  ERROR = 'error',
  ANALYSIS_UPDATE = 'analysis_update',
  PROPOSAL_CREATED = 'proposal_created',
  PROPOSAL_APPROVED = 'proposal_approved',
  TRADE_EXECUTED = 'trade_executed',
  STATUS_CHANGE = 'status_change',
  MARKET_UPDATE = 'market_update',
  PORTFOLIO_UPDATE = 'portfolio_update',
  HEALTH_UPDATE = 'health_update',
  SYSTEM_STATUS = 'system_status',
  ALERT = 'alert',
  WARNING = 'warning',
}

// Message interface
export interface WSMessage {
  type: string;
  data: any;
  timestamp: string;
  connection_id?: string;
}

// Event handler type
export type EventHandler = (event: WSMessage) => void;

/**
 * SIGMAX WebSocket Client
 */
export class SigmaxWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string = '';
  private reconnectDelay: number = 1000;
  private maxReconnectDelay: number = 60000;
  private reconnectAttempts: number = 0;
  private autoReconnect: boolean = true;
  private pingInterval: number = 30000;
  private pingTimer: NodeJS.Timeout | null = null;

  private subscriptions: {
    topics: Set<string>;
    symbols: Set<string>;
  } = {
    topics: new Set(),
    symbols: new Set(),
  };

  private eventHandlers: Map<string, Set<EventHandler>> = new Map();

  constructor(options?: {
    autoReconnect?: boolean;
    pingInterval?: number;
    maxReconnectDelay?: number;
  }) {
    if (options?.autoReconnect !== undefined) {
      this.autoReconnect = options.autoReconnect;
    }
    if (options?.pingInterval) {
      this.pingInterval = options.pingInterval;
    }
    if (options?.maxReconnectDelay) {
      this.maxReconnectDelay = options.maxReconnectDelay;
    }
  }

  /**
   * Connect to WebSocket server
   */
  async connect(url: string, apiKey?: string): Promise<void> {
    this.url = apiKey ? `${url}?api_key=${apiKey}` : url;

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('✅ Connected to SIGMAX WebSocket');
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;
          this.startPingTimer();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('🔌 WebSocket disconnected');
          this.stopPingTimer();

          if (this.autoReconnect) {
            this.scheduleReconnect();
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Disconnect from server
   */
  disconnect(): void {
    this.autoReconnect = false;
    this.stopPingTimer();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Subscribe to topics and/or symbols
   */
  async subscribe(options: {
    topics?: string[];
    symbols?: string[];
  }): Promise<void> {
    const { topics = [], symbols = [] } = options;

    // Store subscriptions for reconnection
    topics.forEach(topic => this.subscriptions.topics.add(topic));
    symbols.forEach(symbol => this.subscriptions.symbols.add(symbol));

    // Send subscription message
    this.send({
      type: 'subscribe',
      data: { topics, symbols }
    });
  }

  /**
   * Unsubscribe from topics and/or symbols
   */
  async unsubscribe(options: {
    topics?: string[];
    symbols?: string[];
  }): Promise<void> {
    const { topics = [], symbols = [] } = options;

    // Remove from stored subscriptions
    topics.forEach(topic => this.subscriptions.topics.delete(topic));
    symbols.forEach(symbol => this.subscriptions.symbols.delete(symbol));

    // Send unsubscribe message
    this.send({
      type: 'unsubscribe',
      data: { topics, symbols }
    });
  }

  /**
   * Register event handler
   */
  on(eventType: string | WSEventType, handler: EventHandler): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }
    this.eventHandlers.get(eventType)!.add(handler);
  }

  /**
   * Remove event handler
   */
  off(eventType: string | WSEventType, handler: EventHandler): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  /**
   * Send message to server
   */
  private send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket not connected');
    }
  }

  /**
   * Handle incoming message
   */
  private handleMessage(data: string): void {
    try {
      const message: WSMessage = JSON.parse(data);

      // Handle ping/pong
      if (message.type === 'ping') {
        this.send({ type: 'pong' });
        return;
      }

      // Emit to specific event handlers
      const handlers = this.eventHandlers.get(message.type);
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message);
          } catch (error) {
            console.error('Error in event handler:', error);
          }
        });
      }

      // Emit to wildcard handlers
      const wildcardHandlers = this.eventHandlers.get('*');
      if (wildcardHandlers) {
        wildcardHandlers.forEach(handler => {
          try {
            handler(message);
          } catch (error) {
            console.error('Error in wildcard handler:', error);
          }
        });
      }
    } catch (error) {
      console.error('Error parsing message:', error);
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(): void {
    this.reconnectAttempts++;

    console.log(
      `Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts})...`
    );

    setTimeout(async () => {
      try {
        await this.connect(this.url);
        await this.restoreSubscriptions();
      } catch (error) {
        console.error('Reconnection failed:', error);

        // Exponential backoff
        this.reconnectDelay = Math.min(
          this.reconnectDelay * 2,
          this.maxReconnectDelay
        );
      }
    }, this.reconnectDelay);
  }

  /**
   * Restore subscriptions after reconnection
   */
  private async restoreSubscriptions(): Promise<void> {
    if (this.subscriptions.topics.size > 0 || this.subscriptions.symbols.size > 0) {
      console.log('Restoring subscriptions...');
      await this.subscribe({
        topics: Array.from(this.subscriptions.topics),
        symbols: Array.from(this.subscriptions.symbols)
      });
    }
  }

  /**
   * Start ping timer
   */
  private startPingTimer(): void {
    this.pingTimer = setInterval(() => {
      this.send({ type: 'ping' });
    }, this.pingInterval);
  }

  /**
   * Stop ping timer
   */
  private stopPingTimer(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// ============================================================================
// React Hook Example
// ============================================================================

/**
 * React hook for SIGMAX WebSocket
 *
 * Usage:
 * ```tsx
 * const { events, subscribe, isConnected } = useSigmaxWebSocket({
 *   url: 'ws://localhost:8000/api/ws',
 *   topics: ['proposals', 'executions']
 * });
 *
 * useEffect(() => {
 *   console.log('Latest event:', events[events.length - 1]);
 * }, [events]);
 * ```
 */
export function useSigmaxWebSocket(options: {
  url: string;
  apiKey?: string;
  topics?: string[];
  symbols?: string[];
  autoConnect?: boolean;
}) {
  // This would be implemented in a React context
  // Simplified version for demonstration

  const [client] = useState(() => new SigmaxWebSocketClient());
  const [events, setEvents] = useState<WSMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (options.autoConnect !== false) {
      connect();
    }

    return () => {
      client.disconnect();
    };
  }, []);

  const connect = async () => {
    try {
      await client.connect(options.url, options.apiKey);
      setIsConnected(true);

      if (options.topics || options.symbols) {
        await client.subscribe({
          topics: options.topics,
          symbols: options.symbols
        });
      }

      // Store all events
      client.on('*', (event) => {
        setEvents(prev => [...prev, event]);
      });
    } catch (error) {
      console.error('Connection failed:', error);
      setIsConnected(false);
    }
  };

  return {
    client,
    events,
    isConnected,
    subscribe: (opts: any) => client.subscribe(opts),
    unsubscribe: (opts: any) => client.unsubscribe(opts),
  };
}

// ============================================================================
// Usage Examples
// ============================================================================

/**
 * Example 1: Basic Usage
 */
export async function basicExample() {
  const client = new SigmaxWebSocketClient();

  await client.connect('ws://localhost:8000/api/ws');

  await client.subscribe({
    topics: ['proposals', 'executions'],
    symbols: ['BTC/USDT']
  });

  client.on(WSEventType.PROPOSAL_CREATED, (event) => {
    console.log('New proposal:', event.data);
  });

  client.on(WSEventType.TRADE_EXECUTED, (event) => {
    console.log('Trade executed:', event.data);
  });
}

/**
 * Example 2: Portfolio Monitoring
 */
export async function portfolioMonitor() {
  const client = new SigmaxWebSocketClient();

  await client.connect('ws://localhost:8000/api/ws');
  await client.subscribe({ topics: ['portfolio', 'executions'] });

  client.on(WSEventType.PORTFOLIO_UPDATE, (event) => {
    const portfolio = event.data;
    console.log('Portfolio:', {
      totalValue: portfolio.total_value,
      pnl: portfolio.total_pnl,
      positions: portfolio.positions
    });
  });

  client.on(WSEventType.TRADE_EXECUTED, (event) => {
    console.log(`Trade: ${event.data.action} ${event.data.symbol}`);
  });
}

/**
 * Example 3: React Component
 */
export function TradingDashboard() {
  const { events, isConnected } = useSigmaxWebSocket({
    url: 'ws://localhost:8000/api/ws',
    topics: ['proposals', 'executions', 'portfolio']
  });

  const latestProposal = events
    .filter(e => e.type === WSEventType.PROPOSAL_CREATED)
    .slice(-1)[0];

  const latestTrade = events
    .filter(e => e.type === WSEventType.TRADE_EXECUTED)
    .slice(-1)[0];

  return (
    <div>
      <h1>Trading Dashboard</h1>
      <div>Status: {isConnected ? '🟢 Connected' : '🔴 Disconnected'}</div>

      {latestProposal && (
        <div>
          <h2>Latest Proposal</h2>
          <p>{latestProposal.data.symbol} - {latestProposal.data.action}</p>
        </div>
      )}

      {latestTrade && (
        <div>
          <h2>Latest Trade</h2>
          <p>
            {latestTrade.data.symbol}: {latestTrade.data.action} @ $
            {latestTrade.data.filled_price}
          </p>
        </div>
      )}
    </div>
  );
}
