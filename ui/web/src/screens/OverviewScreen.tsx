import Panel from '../ui/components/Panel';
import MetricGrid from '../ui/components/MetricGrid';
import StatRow from '../ui/components/StatRow';
import EventList, { type EventItem } from '../ui/components/EventList';
import PerformanceChart from '../components/PerformanceChart';
import AgentDebateLog from '../components/AgentDebateLog';

interface OverviewScreenProps {
  systemStatus: any;
  portfolio: any;
  agentDecisions: Array<any>;
  tradeExecutions: Array<{
    symbol: string;
    action: string;
    size: number;
    order_id?: string;
    status?: string;
    filled_price?: number;
    fee?: number;
    timestamp?: string;
  }>;
  controlLoading: string | null;
  onStartTrading: () => void;
  onPauseTrading: () => void;
  onEmergencyStop: () => void;
}

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);

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

export default function OverviewScreen({
  systemStatus,
  portfolio,
  agentDecisions,
  tradeExecutions,
  controlLoading,
  onStartTrading,
  onPauseTrading,
  onEmergencyStop,
}: OverviewScreenProps) {
  const pnlToday = systemStatus?.trading?.pnl_today ?? 0;

  const summaryMetrics = [
    { label: 'Mode', value: systemStatus?.mode || '—' },
    {
      label: 'Total Value',
      value: portfolio?.total_value ? formatCurrency(portfolio.total_value) : '—',
      helper: portfolio?.cash ? `Cash ${formatCurrency(portfolio.cash)}` : undefined,
    },
    {
      label: 'Open Positions',
      value: `${systemStatus?.trading?.open_positions ?? 0}`,
    },
    {
      label: 'PnL Today',
      value: pnlToday ? formatCurrency(pnlToday) : formatCurrency(0),
    },
  ];

  const recentEvents: EventItem[] = tradeExecutions.slice(0, 5).map((trade, index) => {
    const id = trade.order_id || `${trade.symbol}-${index}`;
    const title = `${trade.action.toUpperCase()} ${trade.size} ${trade.symbol}`;
    const description = trade.filled_price
      ? `Filled @ ${formatCurrency(trade.filled_price)}`
      : trade.status
        ? `Status: ${trade.status}`
        : undefined;
    const severity = resolveSeverity(trade.status);
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
    return {
      id,
      title,
      description,
      timestamp: formatTimestamp(trade.timestamp),
      severity,
      meta,
    };
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <Panel title="Summary">
          <MetricGrid items={summaryMetrics} columns={2} />
        </Panel>

        <PerformanceChart portfolio={portfolio} />

        <Panel title="Latest Decisions">
          <AgentDebateLog decisions={agentDecisions} />
        </Panel>
      </div>

      <div className="space-y-6">
        <Panel title="System State">
          <div className="space-y-2">
            <StatRow label="Mode" value={systemStatus?.mode || '—'} />
            <StatRow label="Risk Profile" value={systemStatus?.risk_profile || '—'} />
            <StatRow label="Uptime" value={systemStatus?.uptime ? `${systemStatus.uptime}s` : '—'} />
          </div>
        </Panel>

        <Panel title="Recent Events">
          <EventList items={recentEvents} emptyLabel="No events yet." />
        </Panel>

        <Panel title="Quick Actions">
          <div className="space-y-2">
            <button
              onClick={onStartTrading}
              disabled={controlLoading !== null || systemStatus?.running}
              className="w-full px-4 py-2 rounded-[var(--radius)] border border-[var(--line)] text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {controlLoading === 'start'
                ? 'Starting...'
                : systemStatus?.running
                  ? 'Trading Active'
                  : 'Start Trading'}
            </button>
            <button
              onClick={onPauseTrading}
              disabled={controlLoading !== null || !systemStatus?.running}
              className="w-full px-4 py-2 rounded-[var(--radius)] border border-[var(--line)] text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {controlLoading === 'pause' ? 'Pausing...' : 'Pause'}
            </button>
            <button
              onClick={onEmergencyStop}
              disabled={controlLoading !== null}
              className="w-full px-4 py-2 rounded-[var(--radius)] border border-[var(--line)] text-sm text-[var(--danger)] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {controlLoading === 'stop' ? 'Stopping...' : 'Emergency Stop'}
            </button>
          </div>
        </Panel>
      </div>
    </div>
  );
}
