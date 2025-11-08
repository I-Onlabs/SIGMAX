/**
 * ExchangeManager - Main component for managing exchange credentials
 */

import { useState, useEffect } from 'react';
import type {
  ExchangeCredential,
  AddExchangeRequest,
  UpdateExchangeRequest,
  ConnectionTestResult,
} from '../services/api';
import api from '../services/api';
import ExchangeCard from './ExchangeCard';
import AddExchangeModal from './AddExchangeModal';

export default function ExchangeManager() {
  const [exchanges, setExchanges] = useState<ExchangeCredential[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');

  // Load exchanges on mount
  useEffect(() => {
    loadExchanges();
  }, []);

  const loadExchanges = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getExchanges();
      setExchanges(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load exchanges');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (request: AddExchangeRequest) => {
    setSaveStatus('saving');

    try {
      const newExchange = await api.addExchange(request);
      setExchanges([...exchanges, newExchange]);
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (err: any) {
      setSaveStatus('idle');
      throw err; // Re-throw to let modal handle error
    }
  };

  const handleUpdate = async (id: string, updates: UpdateExchangeRequest) => {
    setSaveStatus('saving');

    try {
      const updated = await api.updateExchange(id, updates);
      setExchanges(exchanges.map((ex) => (ex.id === id ? updated : ex)));
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (err: any) {
      console.error('Failed to update exchange:', err);
      setSaveStatus('idle');
    }
  };

  const handleDelete = async (id: string) => {
    setSaveStatus('saving');

    try {
      await api.deleteExchange(id);
      setExchanges(exchanges.filter((ex) => ex.id !== id));
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (err: any) {
      console.error('Failed to delete exchange:', err);
      setSaveStatus('idle');
    }
  };

  const handleTest = async (id: string): Promise<ConnectionTestResult> => {
    const result = await api.testExchangeConnection(id);

    // Reload exchanges to get updated connection status
    if (result.success) {
      await loadExchanges();
    }

    return result;
  };

  const enabledCount = exchanges.filter((ex) => ex.enabled).length;
  const connectedCount = exchanges.filter(
    (ex) => ex.enabled && ex.connection_status === 'connected'
  ).length;

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                Exchange Management
              </h1>
              <p className="text-gray-400">
                Manage your exchange API credentials securely
              </p>
            </div>

            {/* Save Status Indicator */}
            {saveStatus !== 'idle' && (
              <div className="flex items-center gap-2 text-sm">
                {saveStatus === 'saving' ? (
                  <>
                    <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full" />
                    <span className="text-gray-400">Saving...</span>
                  </>
                ) : (
                  <>
                    <div className="w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">
                      <svg
                        className="w-3 h-3 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                    </div>
                    <span className="text-green-400">Saved</span>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="text-gray-400 text-sm mb-1">Total Exchanges</div>
              <div className="text-2xl font-bold text-white">{exchanges.length}</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="text-gray-400 text-sm mb-1">Enabled</div>
              <div className="text-2xl font-bold text-blue-400">{enabledCount}</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="text-gray-400 text-sm mb-1">Connected</div>
              <div className="text-2xl font-bold text-green-400">{connectedCount}</div>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-900/20 border border-red-700 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="text-red-500 text-xl">⚠️</div>
              <div>
                <h4 className="text-red-400 font-medium">Error Loading Exchanges</h4>
                <p className="text-red-300 text-sm">{error}</p>
              </div>
              <button
                onClick={loadExchanges}
                className="ml-auto px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm font-medium transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full" />
          </div>
        ) : exchanges.length === 0 ? (
          /* Empty State */
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🏦</div>
            <h3 className="text-xl font-semibold text-white mb-2">
              No Exchanges Connected
            </h3>
            <p className="text-gray-400 mb-6">
              Add your first exchange to start trading
            </p>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors inline-flex items-center gap-2"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              Add Exchange
            </button>
          </div>
        ) : (
          /* Exchange List */
          <>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white">
                Connected Exchanges ({exchanges.length})
              </h2>
              <button
                onClick={() => setShowAddModal(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition-colors inline-flex items-center gap-2"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                Add Exchange
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {exchanges.map((exchange) => (
                <ExchangeCard
                  key={exchange.id}
                  exchange={exchange}
                  onUpdate={handleUpdate}
                  onDelete={handleDelete}
                  onTest={handleTest}
                />
              ))}
            </div>
          </>
        )}

        {/* Add Exchange Modal */}
        <AddExchangeModal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          onAdd={handleAdd}
        />

        {/* Help Section */}
        <div className="mt-8 bg-blue-900/20 border border-blue-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-400 mb-3">
            💡 Getting Started
          </h3>
          <div className="space-y-2 text-sm text-blue-300">
            <p>
              <strong>1.</strong> Generate API keys from your exchange account settings
            </p>
            <p>
              <strong>2.</strong> Enable IP whitelist for additional security
            </p>
            <p>
              <strong>3.</strong> Start with testnet to verify everything works
            </p>
            <p>
              <strong>4.</strong> Test connection before enabling live trading
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
