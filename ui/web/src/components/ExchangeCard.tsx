import { useState } from 'react';
import type { ExchangeCredential, ConnectionTestResult } from '../services/api';
import InlineStatus from '../ui/components/InlineStatus';
import SecondaryAction from '../ui/components/SecondaryAction';

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

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const result = await onTest(exchange.id);
      setTestResult(result);

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
    if (!confirm('Remove this connection?')) return;
    await onDelete(exchange.id);
  };

  const statusLabel = !exchange.enabled
    ? 'Disabled'
    : exchange.connection_status === 'connected'
      ? 'Connected'
      : exchange.connection_status === 'failed'
        ? 'Failed'
        : 'Unknown';

  const statusTone = !exchange.enabled
    ? 'neutral'
    : exchange.connection_status === 'connected'
      ? 'positive'
      : exchange.connection_status === 'failed'
        ? 'negative'
        : 'neutral';

  return (
    <div className="border border-[var(--line)] bg-[var(--panel)] rounded-[var(--radius)] p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold">{exchange.name}</h3>
          <p className="text-xs text-[var(--muted)]">{exchange.exchange}</p>
        </div>
        <InlineStatus label={statusLabel} tone={statusTone} />
      </div>

      <div className="mt-3 space-y-1 text-xs">
        <div className="flex justify-between">
          <span className="text-[var(--muted)]">API Key</span>
          <span className="font-mono">{exchange.api_key}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--muted)]">Network</span>
          <span>{exchange.network}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--muted)]">Testnet</span>
          <span>{exchange.testnet ? 'Enabled' : 'Disabled'}</span>
        </div>
        {exchange.last_connected && (
          <div className="flex justify-between">
            <span className="text-[var(--muted)]">Last Connected</span>
            <span>{new Date(exchange.last_connected).toLocaleString()}</span>
          </div>
        )}
      </div>

      {testResult && (
        <div className="mt-3 text-xs text-[var(--muted)]">
          {testResult.success ? testResult.message || 'Connection successful.' : testResult.error}
          {testResult.balance && (
            <details className="mt-2">
              <summary className="cursor-pointer">Balance details</summary>
              <pre className="mt-2 whitespace-pre-wrap text-[var(--muted)]">
                {JSON.stringify(testResult.balance, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        <SecondaryAction onClick={handleTest} disabled={testing}>
          {testing ? 'Testing...' : 'Test'}
        </SecondaryAction>
        <SecondaryAction onClick={handleToggleEnabled}>
          {exchange.enabled ? 'Disable' : 'Enable'}
        </SecondaryAction>
        <SecondaryAction onClick={handleToggleTestnet}>
          {exchange.testnet ? 'Disable Testnet' : 'Enable Testnet'}
        </SecondaryAction>
        <SecondaryAction onClick={handleDelete} className="text-[var(--danger)]">
          Remove
        </SecondaryAction>
      </div>
    </div>
  );
}
