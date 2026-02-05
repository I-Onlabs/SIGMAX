import Panel from '../ui/components/Panel';
import MetricGrid from '../ui/components/MetricGrid';
import StatRow from '../ui/components/StatRow';

interface RiskDashboardProps {
  portfolio: any;
  status: any;
}

export default function RiskDashboard({ portfolio, status }: RiskDashboardProps) {
  const totalExposure = portfolio?.positions?.reduce(
    (sum: number, pos: any) => sum + (pos.value || 0),
    0
  ) || 0;
  const dailyPnL = portfolio?.performance?.daily_return
    ? portfolio.performance.daily_return * (portfolio.total_value || 0)
    : 0;
  const openPositions = portfolio?.positions?.length || 0;
  const sharpeRatio = portfolio?.performance?.sharpe_ratio || 0;
  const currentDrawdown = Math.abs(portfolio?.performance?.max_drawdown || 0);

  const maxExposure = 1000;
  const dailyLossLimit = 10;
  const maxDrawdown = 10;

  const metrics = [
    {
      label: 'Total Exposure',
      value: `$${totalExposure.toFixed(2)}`,
      helper: `Limit $${maxExposure}`,
    },
    {
      label: 'Daily PnL',
      value: `${dailyPnL >= 0 ? '+' : ''}${dailyPnL.toFixed(2)}`,
      helper: `Limit -$${dailyLossLimit}`,
    },
    {
      label: 'Drawdown',
      value: `${currentDrawdown.toFixed(1)}%`,
      helper: `Max ${maxDrawdown}%`,
    },
    {
      label: 'Open Positions',
      value: `${openPositions}`,
      helper: `Mode ${status?.mode || '—'}`,
    },
  ];

  return (
    <Panel title="Risk Overview">
      <MetricGrid items={metrics} columns={2} />

      <div className="mt-4 pt-4 border-t border-[var(--line)]">
        <h4 className="text-xs font-semibold mb-2">Risk Adjusted</h4>
        <div className="space-y-2">
          <StatRow label="Sharpe Ratio" value={sharpeRatio.toFixed(2)} />
          <StatRow label="Max Drawdown" value={`${currentDrawdown.toFixed(2)}%`} />
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-[var(--line)]">
        <h4 className="text-xs font-semibold mb-2">Auto-Pause Triggers</h4>
        <div className="space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-[var(--muted)]">Max exposure exceeded</span>
            <span className={totalExposure > maxExposure ? 'text-[var(--danger)]' : 'text-[var(--muted)]'}>
              {totalExposure > maxExposure ? 'Triggered' : 'OK'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[var(--muted)]">Daily loss limit</span>
            <span className={dailyPnL < -dailyLossLimit ? 'text-[var(--danger)]' : 'text-[var(--muted)]'}>
              {dailyPnL < -dailyLossLimit ? 'Triggered' : 'OK'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[var(--muted)]">Max drawdown</span>
            <span className={currentDrawdown > maxDrawdown ? 'text-[var(--danger)]' : 'text-[var(--muted)]'}>
              {currentDrawdown > maxDrawdown ? 'Triggered' : 'OK'}
            </span>
          </div>
        </div>
      </div>
    </Panel>
  );
}
