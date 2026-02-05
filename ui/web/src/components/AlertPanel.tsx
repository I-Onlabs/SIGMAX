import { useState } from 'react';
import Panel from '../ui/components/Panel';
import EventList, { type EventItem } from '../ui/components/EventList';
import DataBoundary from '../ui/data/DataBoundary';
import { resolveDataState } from '../ui/state';

interface AlertPanelProps {
  trades?: Array<{
    symbol: string;
    action: string;
    size: number;
    order_id?: string;
    status?: string;
    filled_price?: number;
    fee?: number;
    timestamp?: string;
  }>;
}

type TradeEvent = NonNullable<AlertPanelProps['trades']>[number];

const formatTimestamp = (timestamp?: string) => {
  if (!timestamp) return '—';
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

const resolveSeverity = (status?: string): EventItem['severity'] => {
  const normalized = status?.toLowerCase();
  if (!normalized) return 'info';
  if (['emergency', 'halted', 'panic'].includes(normalized)) return 'emergency';
  if (['failed', 'rejected'].includes(normalized)) return 'critical';
  if (['pending', 'submitted', 'cancelled', 'canceled'].includes(normalized)) return 'warning';
  if (['filled', 'success', 'succeeded', 'completed'].includes(normalized)) return 'info';
  return 'info';
};

export default function AlertPanel({ trades }: AlertPanelProps) {
  const [filter, setFilter] = useState<string>('all');
  const [muted, setMuted] = useState(false);
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());
  const [frozenTrades, setFrozenTrades] = useState<TradeEvent[]>([]);

  const visibleTrades = muted ? frozenTrades : trades || [];
  const alerts = visibleTrades.reduce<EventItem[]>((acc, trade, i) => {
    const id = trade.order_id || `trade-${i}`;
    if (dismissedIds.has(id)) return acc;

    const severity = resolveSeverity(trade.status);
    const description = trade.filled_price
      ? `Filled @ ${trade.filled_price.toFixed(2)}`
      : trade.status
        ? `Status: ${trade.status}`
        : undefined;
    const meta: string[] = [];
    if (trade.order_id) {
      meta.push(`Order ${trade.order_id}`);
    }
    if (typeof trade.fee === 'number') {
      meta.push(`Fee ${trade.fee.toFixed(4)}`);
    }
    if (trade.status) {
      meta.push(`Status ${trade.status}`);
    }

    acc.push({
      id,
      title: `${trade.action.toUpperCase()} ${trade.size} ${trade.symbol}`,
      description,
      timestamp: formatTimestamp(trade.timestamp),
      severity,
      meta,
    });

    return acc;
  }, []);

  const filteredAlerts =
    filter === 'all' ? alerts : alerts.filter((a) => a.severity === filter);

  const dataState = resolveDataState({
    isLoading: trades === undefined,
    isEmpty: filteredAlerts.length === 0,
  });

  const dismissAlert = (id: string) => {
    setDismissedIds((prev) => new Set([...prev, id]));
  };

  const clearAll = () => {
    setDismissedIds(new Set(alerts.map((a) => a.id)));
  };

  const alertCounts = {
    all: alerts.length,
    info: alerts.filter((a) => a.severity === 'info').length,
    warning: alerts.filter((a) => a.severity === 'warning').length,
    critical: alerts.filter((a) => a.severity === 'critical').length,
    emergency: alerts.filter((a) => a.severity === 'emergency').length,
  };

  return (
    <Panel
      title="Events"
      action={
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setMuted((prev) => {
                if (!prev) {
                  setFrozenTrades(trades || []);
                }
                return !prev;
              });
            }}
            className="text-xs px-2 py-1 border border-[var(--line)] rounded-[var(--radius)]"
          >
            {muted ? 'Resume Updates' : 'Freeze List'}
          </button>
          {alerts.length > 0 && (
            <button
              onClick={clearAll}
              className="text-xs px-2 py-1 border border-[var(--line)] rounded-[var(--radius)]"
            >
              Clear
            </button>
          )}
        </div>
      }
    >
      <div className="flex flex-wrap gap-2 mb-4">
        {[
          { key: 'all', label: 'All' },
          { key: 'critical', label: 'Critical' },
          { key: 'emergency', label: 'Emergency' },
          { key: 'warning', label: 'Warning' },
          { key: 'info', label: 'Info' },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`text-xs px-2 py-1 border border-[var(--line)] rounded-[var(--radius)] ${
              filter === key ? 'text-[var(--fg)]' : 'text-[var(--muted)]'
            }`}
          >
            {label} ({alertCounts[key as keyof typeof alertCounts]})
          </button>
        ))}
      </div>
      <p className="text-xs text-[var(--muted)] mb-4">
        Freeze list is UI-only. Live updates continue in the background.
      </p>

      <DataBoundary
        state={dataState}
        loadingLabel="Loading events..."
        emptyLabel="No events available."
      >
        <EventList
          items={filteredAlerts}
          renderAction={(item) => (
            <button
              onClick={() => dismissAlert(item.id)}
              className="text-xs text-[var(--muted)]"
            >
              Dismiss
            </button>
          )}
        />
      </DataBoundary>
    </Panel>
  );
}
