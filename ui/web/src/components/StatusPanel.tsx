import Panel from '../ui/components/Panel';
import StatRow from '../ui/components/StatRow';
import InlineStatus from '../ui/components/InlineStatus';
import DataBoundary from '../ui/data/DataBoundary';
import { resolveDataState } from '../ui/state';

interface StatusPanelProps {
  status: any;
  health?: {
    cpu_percent?: number;
    memory_percent?: number;
    disk_percent?: number;
    process_count?: number;
  } | null;
}

export default function StatusPanel({ status, health }: StatusPanelProps) {
  const dataState = resolveDataState({
    isLoading: !status,
    isEmpty: !status,
  });

  const clampPercent = (value?: number) => Math.min(100, Math.max(0, value || 0));

  return (
    <Panel title="System Status">
      <DataBoundary
        state={dataState}
        loadingLabel="Loading status..."
        emptyLabel="No status available."
      >
        {(() => {
          const pnlToday = status.trading?.pnl_today ?? 0;
          const pnlLabel = `${pnlToday >= 0 ? '+' : ''}${pnlToday.toFixed(2)}`;

          return (
            <>
              <div className="space-y-2">
                <StatRow label="Mode" value={status.mode || 'Paper'} />
                <StatRow label="PnL Today" value={pnlLabel} />
                <StatRow label="Open Positions" value={`${status.trading?.open_positions || 0}`} />
                <StatRow label="Trades Today" value={`${status.trading?.trades_today || 0}`} />
              </div>

              <div className="mt-4 pt-4 border-t border-[var(--line)]">
                <h4 className="text-xs font-semibold mb-2">Active Agents</h4>
                <div className="grid grid-cols-2 gap-2">
                  {Object.keys(status.agents || {}).length === 0 && (
                    <InlineStatus label="No agents reported" tone="neutral" />
                  )}
                  {Object.entries(status.agents || {}).map(([name]) => (
                    <div key={name} className="flex items-center justify-between">
                      <span className="text-xs capitalize">{name}</span>
                      <InlineStatus label="Active" tone="positive" />
                    </div>
                  ))}
                </div>
              </div>

              {health && (
                <div className="mt-4 pt-4 border-t border-[var(--line)]">
                  <h4 className="text-xs font-semibold mb-2">System Health</h4>
                  <div className="space-y-3">
                    {[
                      { label: 'CPU', value: health.cpu_percent },
                      { label: 'Memory', value: health.memory_percent },
                      { label: 'Disk', value: health.disk_percent },
                    ].map((item) => {
                      const pct = clampPercent(item.value);
                      return (
                        <div key={item.label}>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-[var(--muted)]">{item.label}</span>
                            <span>{pct.toFixed(1)}%</span>
                          </div>
                          <div className="mt-1 h-1.5 rounded-[var(--radius)] bg-[var(--line)] overflow-hidden">
                            <div
                              className="h-full bg-[var(--fg)]"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                    <StatRow label="Processes" value={`${health.process_count ?? 0}`} />
                  </div>
                </div>
              )}
            </>
          );
        })()}
      </DataBoundary>
    </Panel>
  );
}
