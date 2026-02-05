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
import Panel from '../ui/components/Panel';
import MetricGrid from '../ui/components/MetricGrid';
import PrimaryAction from '../ui/components/PrimaryAction';
import InlineStatus from '../ui/components/InlineStatus';
import DataBoundary from '../ui/data/DataBoundary';
import { resolveDataState } from '../ui/state';

export default function ExchangeManager() {
  const [exchanges, setExchanges] = useState<ExchangeCredential[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');

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
      throw err;
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

    if (result.success) {
      await loadExchanges();
    }

    return result;
  };

  const enabledCount = exchanges.filter((ex) => ex.enabled).length;
  const connectedCount = exchanges.filter(
    (ex) => ex.enabled && ex.connection_status === 'connected'
  ).length;

  const dataState = resolveDataState({
    isLoading: loading,
    isEmpty: !loading && exchanges.length === 0,
    error,
  });

  return (
    <div className="space-y-6">
      <Panel
        title="Connections"
        action={
          <div className="flex items-center gap-3">
            {saveStatus === 'saving' && <InlineStatus label="Saving" tone="neutral" />}
            {saveStatus === 'saved' && <InlineStatus label="Saved" tone="positive" />}
            <PrimaryAction onClick={() => setShowAddModal(true)}>
              Add Connection
            </PrimaryAction>
          </div>
        }
      >
        <MetricGrid
          items={[
            { label: 'Total', value: `${exchanges.length}` },
            { label: 'Enabled', value: `${enabledCount}` },
            { label: 'Connected', value: `${connectedCount}` },
          ]}
          columns={3}
        />
      </Panel>

      <Panel title={`Accounts (${exchanges.length})`}>
        {error && (
          <div className="mb-3 flex items-center justify-between gap-3 text-xs">
            <span className="text-[var(--danger)]">{error}</span>
            <button
              onClick={loadExchanges}
              className="px-2 py-1 border border-[var(--line)] rounded-[var(--radius)]"
            >
              Retry
            </button>
          </div>
        )}
        <DataBoundary
          state={dataState}
          loadingLabel="Loading connections..."
          emptyLabel="No connections yet."
          errorLabel={error || 'Unable to load connections.'}
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
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
        </DataBoundary>
      </Panel>

      <Panel title="Notes">
        <ul className="text-xs text-[var(--muted)] list-disc pl-4 space-y-1">
          <li>Generate API keys from your exchange settings.</li>
          <li>Use testnet to verify connectivity before enabling live trading.</li>
          <li>Test connections after saving credentials.</li>
        </ul>
      </Panel>

      <AddExchangeModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={handleAdd}
      />
    </div>
  );
}
