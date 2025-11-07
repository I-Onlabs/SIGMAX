/**
 * SIGMAX WebSocket Hook
 * Manages real-time connection to backend
 */

import { useState, useEffect, useCallback, useRef } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

// WebSocket Message Types
export type WSMessageType =
  | 'connected'
  | 'initial_status'
  | 'market_update'
  | 'portfolio_update'
  | 'system_status'
  | 'health_update'
  | 'trade_execution'
  | 'agent_decision'
  | 'pong'
  | 'error';

export interface WSMessage {
  type: WSMessageType;
  data?: any;
  message?: string;
  timestamp: string;
}

export interface MarketData {
  symbol: string;
  price: number;
  volume_24h: number;
  change_24h: number;
  timestamp: string;
}

export interface PortfolioUpdate {
  total_value: number;
  cash: number;
  invested: number;
  positions: Array<any>;
  performance: {
    total_return: number;
    daily_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
  };
  timestamp: string;
}

export interface TradeExecution {
  symbol: string;
  action: string;
  size: number;
  order_id: string;
  status: string;
  filled_price: number;
  fee: number;
}

export interface AgentDecision {
  symbol: string;
  decision: string;
  confidence: number;
  bull_score: string;
  bear_score: string;
  reasoning: string;
}

export interface SystemHealth {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  process_count: number;
}

interface UseWebSocketReturn {
  connected: boolean;
  lastMessage: WSMessage | null;
  marketData: MarketData[];
  portfolio: PortfolioUpdate | null;
  systemStatus: any;
  systemHealth: SystemHealth | null;
  tradeExecutions: TradeExecution[];
  agentDecisions: AgentDecision[];
  sendMessage: (message: any) => void;
  ping: () => void;
}

/**
 * Custom hook for WebSocket connection
 */
export function useWebSocket(): UseWebSocketReturn {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [portfolio, setPortfolio] = useState<PortfolioUpdate | null>(null);
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [tradeExecutions, setTradeExecutions] = useState<TradeExecution[]>([]);
  const [agentDecisions, setAgentDecisions] = useState<AgentDecision[]>([]);

  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<number | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 10;

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    // Clear existing reconnect timeout
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    try {
      const websocket = new WebSocket(WS_URL);

      websocket.onopen = () => {
        console.log('✓ WebSocket connected');
        setConnected(true);
        reconnectAttempts.current = 0;
      };

      websocket.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Handle different message types
          switch (message.type) {
            case 'connected':
              console.log('✓ Server connected:', message.message);
              break;

            case 'initial_status':
              setSystemStatus(message.data);
              break;

            case 'market_update':
              if (Array.isArray(message.data)) {
                setMarketData(message.data);
              }
              break;

            case 'portfolio_update':
              setPortfolio(message.data);
              break;

            case 'system_status':
              setSystemStatus(message.data);
              break;

            case 'health_update':
              setSystemHealth(message.data);
              break;

            case 'trade_execution':
              setTradeExecutions(prev => [message.data, ...prev].slice(0, 50));
              break;

            case 'agent_decision':
              setAgentDecisions(prev => [message.data, ...prev].slice(0, 20));
              break;

            case 'pong':
              // Heartbeat response
              break;

            case 'error':
              console.error('WebSocket error:', message.message);
              break;

            default:
              console.log('Unknown message type:', message.type);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnected(false);
      };

      websocket.onclose = () => {
        console.log('WebSocket disconnected');
        setConnected(false);
        ws.current = null;

        // Attempt to reconnect with exponential backoff
        reconnectAttempts.current += 1;

        if (reconnectAttempts.current <= maxReconnectAttempts) {
          const delay = Math.min(
            1000 * Math.pow(2, reconnectAttempts.current - 1),
            30000
          );

          console.log(
            `Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current}/${maxReconnectAttempts})`
          );

          reconnectTimeout.current = window.setTimeout(() => {
            connect();
          }, delay);
        } else {
          console.error('Max reconnection attempts reached');
        }
      };

      ws.current = websocket;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnected(false);
    }
  }, []);

  /**
   * Send message to server
   */
  const sendMessage = useCallback((message: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }, []);

  /**
   * Send ping to server
   */
  const ping = useCallback(() => {
    sendMessage({ type: 'ping' });
  }, [sendMessage]);

  /**
   * Connect on mount, cleanup on unmount
   */
  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  return {
    connected,
    lastMessage,
    marketData,
    portfolio,
    systemStatus,
    systemHealth,
    tradeExecutions,
    agentDecisions,
    sendMessage,
    ping,
  };
}

export default useWebSocket;
