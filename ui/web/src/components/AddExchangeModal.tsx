import { useState, useEffect, type FormEvent } from 'react';
import type { AddExchangeRequest, SupportedExchange } from '../services/api';
import api from '../services/api';
import PrimaryAction from '../ui/components/PrimaryAction';
import SecondaryAction from '../ui/components/SecondaryAction';

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

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
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
    <div className="fixed inset-0 z-50 bg-[var(--bg)] overflow-auto">
      <div className="max-w-2xl mx-auto p-6">
        <div className="border border-[var(--line)] bg-[var(--panel)] rounded-[var(--radius)] p-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold">Add Connection</h2>
            <p className="text-sm text-[var(--muted)]">
              Connect an exchange account.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="exchange-select" className="block text-xs font-semibold mb-2">
                Exchange
              </label>
              <select
                id="exchange-select"
                value={formData.exchange}
                onChange={(e) =>
                  setFormData({ ...formData, exchange: e.target.value })
                }
                className="w-full px-3 py-2 border border-[var(--line)] rounded-[var(--radius)] bg-transparent text-sm"
                required
              >
                {supportedExchanges.map((ex) => (
                  <option key={ex.id} value={ex.id}>
                    {ex.name}
                    {ex.testnet_available ? ' (Testnet)' : ''}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="account-name" className="block text-xs font-semibold mb-2">
                Account Name
              </label>
              <input
                id="account-name"
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Account name"
                className="w-full px-3 py-2 border border-[var(--line)] rounded-[var(--radius)] bg-transparent text-sm"
                required
              />
            </div>

            <div>
              <label htmlFor="api-key" className="block text-xs font-semibold mb-2">
                API Key
              </label>
              <input
                id="api-key"
                type="text"
                value={formData.api_key}
                onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                placeholder="API key"
                className="w-full px-3 py-2 border border-[var(--line)] rounded-[var(--radius)] bg-transparent text-sm font-mono"
                required
              />
            </div>

            <div>
              <label htmlFor="api-secret" className="block text-xs font-semibold mb-2">
                API Secret
              </label>
              <input
                id="api-secret"
                type="password"
                value={formData.api_secret}
                onChange={(e) =>
                  setFormData({ ...formData, api_secret: e.target.value })
                }
                placeholder="API secret"
                className="w-full px-3 py-2 border border-[var(--line)] rounded-[var(--radius)] bg-transparent text-sm font-mono"
                required
              />
            </div>

            {selectedExchange?.requires_passphrase && (
              <div>
                <label htmlFor="passphrase" className="block text-xs font-semibold mb-2">
                  Passphrase
                </label>
                <input
                  id="passphrase"
                  type="password"
                  value={formData.passphrase}
                  onChange={(e) =>
                    setFormData({ ...formData, passphrase: e.target.value })
                  }
                  placeholder="Passphrase"
                  className="w-full px-3 py-2 border border-[var(--line)] rounded-[var(--radius)] bg-transparent text-sm font-mono"
                  required
                />
              </div>
            )}

            {selectedExchange?.testnet_available && (
              <div className="flex items-center justify-between border border-[var(--line)] rounded-[var(--radius)] p-3">
                <div>
                  <div className="text-xs font-semibold">Use Testnet</div>
                  <div className="text-xs text-[var(--muted)]">Sandbox environment</div>
                </div>
                <input
                  type="checkbox"
                  checked={formData.testnet}
                  onChange={() =>
                    setFormData({ ...formData, testnet: !formData.testnet })
                  }
                />
              </div>
            )}

            <div className="flex items-center justify-between border border-[var(--line)] rounded-[var(--radius)] p-3">
              <div>
                <div className="text-xs font-semibold">Enable Immediately</div>
                <div className="text-xs text-[var(--muted)]">
                  Allow this connection to be used after saving.
                </div>
              </div>
              <input
                type="checkbox"
                checked={formData.enabled}
                onChange={() =>
                  setFormData({ ...formData, enabled: !formData.enabled })
                }
              />
            </div>

            <div className="border border-[var(--line)] rounded-[var(--radius)] p-3">
              <div className="text-xs font-semibold">Security Notice</div>
              <p className="text-xs text-[var(--muted)] mt-1">
                Credentials are stored securely. Use testnet first and enable IP
                restrictions where supported.
              </p>
            </div>

            {error && <p className="text-xs text-[var(--danger)]">{error}</p>}

            <div className="flex items-center justify-end gap-2 pt-2">
              <SecondaryAction type="button" onClick={handleClose}>
                Cancel
              </SecondaryAction>
              <PrimaryAction type="submit" disabled={loading}>
                {loading ? 'Saving...' : 'Add Connection'}
              </PrimaryAction>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
