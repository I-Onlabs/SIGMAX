/**
 * ExchangeCard - Display individual exchange credential with actions
 */

import { useState } from 'react';
import type { ExchangeCredential, ConnectionTestResult } from '../services/api';

interface ExchangeCardProps {
  exchange: ExchangeCredential;
  onUpdate: (id: string, updates: any) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onTest: (id: string) => Promise<ConnectionTestResult>;
}

export default function ExchangeCard({
  exchange,
  onUpdate,
  onDelete,
  onTest,
}: ExchangeCardProps) {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);
  const [showDelete, setShowDelete] = useState(false);

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const result = await onTest(exchange.id);
      setTestResult(result);

      // Update connection status in parent
      if (result.success) {
        await onUpdate(exchange.id, {}); // Trigger refresh
      }
    } catch (error: any) {
      setTestResult({
        success: false,
        error: error.message || 'Connection test failed',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleToggleEnabled = async () => {
    await onUpdate(exchange.id, { enabled: !exchange.enabled });
  };

  const handleToggleTestnet = async () => {
    await onUpdate(exchange.id, { testnet: !exchange.testnet });
  };

  const handleDelete = async () => {
    await onDelete(exchange.id);
    setShowDelete(false);
  };

  // Get status color
  const getStatusColor = () => {
    if (!exchange.enabled) return 'text-gray-500';
    switch (exchange.connection_status) {
      case 'connected':
        return 'text-green-500';
      case 'failed':
        return 'text-red-500';
      default:
        return 'text-yellow-500';
    }
  };

  const getStatusText = () => {
    if (!exchange.enabled) return 'Disabled';
    switch (exchange.connection_status) {
      case 'connected':
        return 'Connected';
      case 'failed':
        return 'Failed';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold text-white">{exchange.name}</h3>
            <span className="px-2 py-1 text-xs font-medium bg-gray-700 text-gray-300 rounded">
              {exchange.exchange.toUpperCase()}
            </span>
            {exchange.testnet && (
              <span className="px-2 py-1 text-xs font-medium bg-yellow-900/30 text-yellow-500 rounded">
                TESTNET
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-2">
            <div className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
            <span className={`text-sm ${getStatusColor()}`}>{getStatusText()}</span>
            {exchange.last_connected && (
              <span className="text-xs text-gray-500">
                • Last: {new Date(exchange.last_connected).toLocaleString()}
              </span>
            )}
          </div>
        </div>

        {/* Enable/Disable Toggle */}
        <button
          onClick={handleToggleEnabled}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            exchange.enabled ? 'bg-blue-600' : 'bg-gray-700'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              exchange.enabled ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      {/* Credentials */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">API Key:</span>
          <code className="text-gray-300 font-mono text-xs">{exchange.api_key}</code>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Network:</span>
          <span className="text-gray-300">{exchange.network}</span>
        </div>
      </div>

      {/* Test Result */}
      {testResult && (
        <div
          className={`mb-4 p-3 rounded text-sm ${
            testResult.success
              ? 'bg-green-900/20 border border-green-700 text-green-400'
              : 'bg-red-900/20 border border-red-700 text-red-400'
          }`}
        >
          {testResult.success ? (
            <div>
              <div className="font-medium">✓ {testResult.message}</div>
              {testResult.balance && (
                <div className="text-xs mt-1 text-green-300">
                  Balance: {JSON.stringify(testResult.balance, null, 2)}
                </div>
              )}
            </div>
          ) : (
            <div>✗ {testResult.error}</div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleTest}
          disabled={testing || !exchange.enabled}
          className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded text-sm font-medium transition-colors"
        >
          {testing ? 'Testing...' : 'Test Connection'}
        </button>

        <button
          onClick={handleToggleTestnet}
          disabled={!exchange.enabled}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 text-white rounded text-sm font-medium transition-colors"
        >
          {exchange.testnet ? 'Use Mainnet' : 'Use Testnet'}
        </button>

        <button
          onClick={() => setShowDelete(true)}
          className="px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded text-sm font-medium transition-colors"
        >
          Delete
        </button>
      </div>

      {/* Delete Confirmation */}
      {showDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-2">Delete Exchange?</h3>
            <p className="text-gray-400 mb-6">
              Are you sure you want to delete "{exchange.name}"? This action cannot be undone.
            </p>
            <div className="flex items-center gap-3">
              <button
                onClick={handleDelete}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded font-medium transition-colors"
              >
                Delete
              </button>
              <button
                onClick={() => setShowDelete(false)}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded font-medium transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
