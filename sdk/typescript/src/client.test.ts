/**
 * SIGMAX Client Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SigmaxClient } from './client';
import { AuthenticationError, NetworkError } from './errors';
import { makeRequest } from './utils/fetch';

// Mock only makeRequest, not buildUrl
vi.mock('./utils/fetch', async () => {
  const actual = await vi.importActual<typeof import('./utils/fetch')>('./utils/fetch');
  return {
    ...actual,
    makeRequest: vi.fn(),
  };
});

describe('SigmaxClient', () => {
  let client: SigmaxClient;

  beforeEach(() => {
    vi.clearAllMocks();
    client = new SigmaxClient({
      apiKey: 'test-api-key',
      apiUrl: 'http://test.sigmax.local',
    });
  });

  // ============================================================================
  // Constructor Tests
  // ============================================================================

  describe('constructor', () => {
    it('should create client with provided options', () => {
      expect(client).toBeInstanceOf(SigmaxClient);
    });

    it('should use default values when options not provided', () => {
      const defaultClient = new SigmaxClient({ apiKey: 'test' });
      expect(defaultClient).toBeInstanceOf(SigmaxClient);
    });

    it('should remove trailing slash from API URL', () => {
      const clientWithSlash = new SigmaxClient({
        apiKey: 'test',
        apiUrl: 'http://test.com/',
      });
      expect(clientWithSlash).toBeInstanceOf(SigmaxClient);
    });

    it('should accept custom timeout', () => {
      const customClient = new SigmaxClient({
        apiKey: 'test',
        timeout: 60000,
      });
      expect(customClient).toBeInstanceOf(SigmaxClient);
    });

    it('should accept custom headers', () => {
      const customClient = new SigmaxClient({
        apiKey: 'test',
        headers: { 'X-Custom': 'value' },
      });
      expect(customClient).toBeInstanceOf(SigmaxClient);
    });
  });

  // ============================================================================
  // Analysis Methods
  // ============================================================================

  describe('analyze', () => {
    it('should successfully analyze a symbol', async () => {
      const mockResponse = {
        symbol: 'BTC/USDT',
        decision: {
          action: 'buy',
          confidence: 0.85,
          rationale: 'Strong bullish signals',
        },
        timestamp: new Date().toISOString(),
      };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.analyze('BTC/USDT');

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/api/analyze',
        {
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: 'Bearer test-api-key',
          }),
          timeout: 30000,
          body: {
            symbol: 'BTC/USDT',
            include_debate: false,
          },
        }
      );
    });

    it('should pass analysis options correctly', async () => {
      const mockResponse = { symbol: 'ETH/USDT' };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      await client.analyze('ETH/USDT', {
        include_debate: true,
      });

      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/api/analyze',
        expect.objectContaining({
          body: {
            symbol: 'ETH/USDT',
            include_debate: true,
          },
        })
      );
    });
  });

  describe('getAgentDebate', () => {
    it('should retrieve agent debate for a symbol', async () => {
      const mockResponse = {
        symbol: 'BTC/USDT',
        debate_id: 'debate-123',
        bull_arguments: ['Strong momentum'],
        bear_arguments: ['Overbought'],
      };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.getAgentDebate('BTC/USDT');

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/api/agents/debate/BTC/USDT',
        {
          method: 'GET',
          headers: expect.objectContaining({
            Authorization: 'Bearer test-api-key',
          }),
          timeout: 30000,
        }
      );
    });
  });

  // ============================================================================
  // Proposal Methods
  // ============================================================================

  describe('proposeTradeProposal', () => {
    it('should create a trade proposal', async () => {
      const mockResponse = {
        proposal: {
          proposal_id: 'prop-123',
          symbol: 'BTC/USDT',
          action: 'buy',
          status: 'pending',
        },
      };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.proposeTradeProposal({
        symbol: 'BTC/USDT',
        risk_profile: 'balanced',
        mode: 'paper',
      });

      expect(result).toEqual(mockResponse.proposal);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/api/chat/proposals',
        {
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: 'Bearer test-api-key',
          }),
          timeout: 30000,
          body: {
            symbol: 'BTC/USDT',
            risk_profile: 'balanced',
            mode: 'paper',
          },
        }
      );
    });
  });

  describe('listProposals', () => {
    it('should retrieve list of proposals', async () => {
      const mockResponse = {
        proposals: [{ proposal_id: 'prop-1' }, { proposal_id: 'prop-2' }],
        total: 2,
      };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.listProposals();

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/api/chat/proposals',
        expect.objectContaining({ method: 'GET' })
      );
    });
  });

  describe('getProposal', () => {
    it('should retrieve a specific proposal', async () => {
      const mockResponse = {
        proposal_id: 'prop-123',
        symbol: 'BTC/USDT',
        status: 'pending',
      };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.getProposal('prop-123');

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/api/chat/proposals/prop-123',
        expect.objectContaining({ method: 'GET' })
      );
    });
  });

  describe('approveProposal', () => {
    it('should approve a proposal', async () => {
      const mockResponse = {
        proposal_id: 'prop-123',
        status: 'approved',
      };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.approveProposal('prop-123');

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/api/chat/proposals/prop-123/approve',
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  describe('executeProposal', () => {
    it('should execute an approved proposal', async () => {
      const mockResponse = {
        success: true,
        execution_id: 'exec-123',
      };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.executeProposal('prop-123');

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/api/chat/proposals/prop-123/execute',
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  // ============================================================================
  // Portfolio & Trading Methods
  // ============================================================================

  describe('getPortfolio', () => {
    it('should retrieve current portfolio', async () => {
      const mockResponse = {
        positions: [],
        total_value: 10000,
        pnl: 500,
      };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.getPortfolio();

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/api/portfolio',
        expect.objectContaining({ method: 'GET' })
      );
    });
  });

  describe('getTradeHistory', () => {
    it('should retrieve trade history', async () => {
      const mockResponse = {
        trades: [],
        total: 0,
      };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.getTradeHistory();

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        expect.stringContaining('/api/history'),
        expect.objectContaining({ method: 'GET' })
      );
    });

    it('should pass query parameters for trade history', async () => {
      const mockResponse = { trades: [], total: 0 };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      await client.getTradeHistory(10, 5, 'BTC/USDT');

      expect(makeRequest).toHaveBeenCalledWith(
        expect.stringContaining('limit=10'),
        expect.anything()
      );
      expect(makeRequest).toHaveBeenCalledWith(
        expect.stringContaining('offset=5'),
        expect.anything()
      );
      expect(makeRequest).toHaveBeenCalledWith(
        expect.stringContaining('symbol=BTC%2FUSDT'),
        expect.anything()
      );
    });
  });

  // ============================================================================
  // System Control Methods
  // ============================================================================

  describe('getStatus', () => {
    it('should retrieve system status', async () => {
      const mockResponse = {
        status: 'running',
        uptime: 3600,
      };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.getStatus();

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/api/status',
        expect.objectContaining({ method: 'GET' })
      );
    });
  });

  describe('startTrading', () => {
    it('should start trading system', async () => {
      const mockResponse = { success: true, message: 'Trading started' };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.startTrading();

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/api/control/start',
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  describe('pauseTrading', () => {
    it('should pause trading system', async () => {
      const mockResponse = { success: true, message: 'Trading paused' };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.pauseTrading();

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/api/control/pause',
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  describe('stopTrading', () => {
    it('should stop trading system', async () => {
      const mockResponse = { success: true, message: 'Trading stopped' };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.stopTrading();

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/api/control/stop',
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  describe('emergencyStop', () => {
    it('should trigger emergency stop', async () => {
      const mockResponse = { success: true, positions_closed: 3 };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.emergencyStop();

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/api/control/panic',
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  // ============================================================================
  // Health Check Methods
  // ============================================================================

  describe('healthCheck', () => {
    it('should perform health check', async () => {
      const mockResponse = { status: 'healthy' };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.healthCheck();

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/health',
        expect.objectContaining({ method: 'GET', timeout: 5000 })
      );
    });
  });

  describe('readinessCheck', () => {
    it('should perform readiness check', async () => {
      const mockResponse = { ready: true, checks: {} };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.readinessCheck();

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/health/ready',
        expect.objectContaining({ method: 'GET', timeout: 5000 })
      );
    });
  });

  describe('livenessCheck', () => {
    it('should perform liveness check', async () => {
      const mockResponse = { alive: true };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.livenessCheck();

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/health/live',
        expect.objectContaining({ method: 'GET', timeout: 5000 })
      );
    });
  });

  // ============================================================================
  // Metrics Methods
  // ============================================================================

  describe('getMetrics', () => {
    it('should retrieve system metrics', async () => {
      const mockResponse = {
        requests_total: 1000,
        errors_total: 5,
      };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.getMetrics();

      expect(result).toEqual(mockResponse);
      expect(makeRequest).toHaveBeenCalledWith(
        'http://test.sigmax.local/metrics',
        expect.objectContaining({ method: 'GET' })
      );
    });
  });

  describe('getQuantumCircuit', () => {
    it('should retrieve quantum circuit', async () => {
      const mockResponse = {
        circuit_id: 'qc-123',
        qubits: 5,
      };

      vi.mocked(makeRequest).mockResolvedValueOnce(mockResponse);

      const result = await client.getQuantumCircuit('BTC/USDT');

      expect(result).toEqual(mockResponse);
    });
  });

  // ============================================================================
  // Error Handling
  // ============================================================================

  describe('error handling', () => {
    it('should handle authentication errors', async () => {
      vi.mocked(makeRequest).mockRejectedValueOnce(
        new AuthenticationError('Invalid API key')
      );

      await expect(client.analyze('BTC/USDT')).rejects.toThrow(
        AuthenticationError
      );
    });

    it('should handle network errors', async () => {
      vi.mocked(makeRequest).mockRejectedValueOnce(
        new NetworkError('Connection failed')
      );

      await expect(client.analyze('BTC/USDT')).rejects.toThrow(NetworkError);
    });
  });
});
