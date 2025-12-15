/**
 * AddExchangeModal - Modal for adding/editing exchange credentials
 */

import { useState, useEffect } from 'react';
import type { AddExchangeRequest, SupportedExchange } from '../services/api';
import api from '../services/api';

interface AddExchangeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (exchange: AddExchangeRequest) => Promise<void>;
}

export default function AddExchangeModal({ isOpen, onClose, onAdd }: AddExchangeModalProps) {
  const [supportedExchanges, setSupportedExchanges] = useState<SupportedExchange[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<AddExchangeRequest>({
    exchange: 'binance',
    name: '',
    api_key: '',
    api_secret: '',
    passphrase: '',
    testnet: false,
    enabled: true,
  });

  // Load supported exchanges
  useEffect(() => {
    if (isOpen) {
      loadSupportedExchanges();
    }
  }, [isOpen]);

  const loadSupportedExchanges = async () => {
    try {
      const data = await api.getSupportedExchanges();
      setSupportedExchanges(data.exchanges);
    } catch (err: any) {
      console.error('Failed to load supported exchanges:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await onAdd(formData);
      handleClose();
    } catch (err: any) {
      setError(err.message || 'Failed to add exchange');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      exchange: 'binance',
      name: '',
      api_key: '',
      api_secret: '',
      passphrase: '',
      testnet: false,
      enabled: true,
    });
    setError(null);
    onClose();
  };

  const selectedExchange = supportedExchanges.find((ex) => ex.id === formData.exchange);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" aria-modal="true" role="dialog">
      <div className="bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-gray-700">
        {/* Header */}
        <div className="sticky top-0 bg-gray-800 border-b border-gray-700 p-6">
          <h2 className="text-2xl font-bold text-white">Add Exchange</h2>
          <p className="text-gray-400 mt-1">
            Connect your exchange account for automated trading
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Exchange Selection */}
          <div>
            <label htmlFor="exchange-select" className="block text-sm font-medium text-gray-300 mb-2">
              Exchange *
            </label>
            <select
              id="exchange-select"
              value={formData.exchange}
              onChange={(e) =>
                setFormData({ ...formData, exchange: e.target.value })
              }
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              {supportedExchanges.map((ex) => (
                <option key={ex.id} value={ex.id}>
                  {ex.name}
                  {ex.testnet_available ? ' (Testnet Available)' : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Name */}
          <div>
            <label htmlFor="account-name" className="block text-sm font-medium text-gray-300 mb-2">
              Account Name *
            </label>
            <input
              id="account-name"
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Binance Main Account"
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              A friendly name to identify this account
            </p>
          </div>

          {/* API Key */}
          <div>
            <label htmlFor="api-key" className="block text-sm font-medium text-gray-300 mb-2">
              API Key *
            </label>
            <input
              id="api-key"
              type="text"
              value={formData.api_key}
              onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
              placeholder="Enter your API key"
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              required
            />
          </div>

          {/* API Secret */}
          <div>
            <label htmlFor="api-secret" className="block text-sm font-medium text-gray-300 mb-2">
              API Secret *
            </label>
            <input
              id="api-secret"
              type="password"
              value={formData.api_secret}
              onChange={(e) =>
                setFormData({ ...formData, api_secret: e.target.value })
              }
              placeholder="Enter your API secret"
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              required
            />
          </div>

          {/* Passphrase (if required) */}
          {selectedExchange?.requires_passphrase && (
            <div>
              <label htmlFor="passphrase" className="block text-sm font-medium text-gray-300 mb-2">
                Passphrase *
              </label>
              <input
                id="passphrase"
                type="password"
                value={formData.passphrase}
                onChange={(e) =>
                  setFormData({ ...formData, passphrase: e.target.value })
                }
                placeholder="Enter your passphrase"
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                required
              />
            </div>
          )}

          {/* Testnet Toggle */}
          {selectedExchange?.testnet_available && (
            <div className="flex items-center justify-between p-4 bg-gray-700/50 rounded">
              <div>
                <label id="testnet-label" className="text-sm font-medium text-gray-300">Use Testnet</label>
                <p className="text-xs text-gray-500 mt-1">
                  Test with sandbox environment (no real funds)
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={formData.testnet}
                aria-labelledby="testnet-label"
                onClick={() =>
                  setFormData({ ...formData, testnet: !formData.testnet })
                }
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  formData.testnet ? 'bg-yellow-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    formData.testnet ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          )}

          {/* Enable Toggle */}
          <div className="flex items-center justify-between p-4 bg-gray-700/50 rounded">
            <div>
              <label id="enable-label" className="text-sm font-medium text-gray-300">
                Enable Immediately
              </label>
              <p className="text-xs text-gray-500 mt-1">
                Start using this exchange after adding
              </p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={formData.enabled}
              aria-labelledby="enable-label"
              onClick={() =>
                setFormData({ ...formData, enabled: !formData.enabled })
              }
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                formData.enabled ? 'bg-blue-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  formData.enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Security Warning */}
          <div className="bg-yellow-900/20 border border-yellow-700 rounded p-4">
            <div className="flex items-start gap-3">
              <div className="text-yellow-500 text-xl" aria-hidden="true">⚠️</div>
              <div className="flex-1">
                <h4 className="text-sm font-medium text-yellow-400 mb-1">
                  Security Notice
                </h4>
                <p className="text-xs text-yellow-300">
                  Your API credentials are encrypted and stored securely. Never share your
                  API keys. We recommend using testnet first and enabling IP whitelist on
                  your exchange account.
                </p>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-900/20 border border-red-700 rounded p-4 text-red-400 text-sm" role="alert">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-3 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded font-medium transition-colors"
            >
              {loading ? 'Adding...' : 'Add Exchange'}
            </button>
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="flex-1 px-6 py-3 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 text-white rounded font-medium transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
