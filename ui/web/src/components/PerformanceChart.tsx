import { useEffect, useState } from 'react';
import Panel from '../ui/components/Panel';
import MetricGrid from '../ui/components/MetricGrid';

interface PortfolioUpdate {
  total_value?: number;
  cash?: number;
  invested?: number;
  positions?: Array<any>;
  performance?: {
    total_return?: number;
    daily_return?: number;
    sharpe_ratio?: number;
    max_drawdown?: number;
  };
  timestamp?: string;
}

interface PerformanceChartProps {
  portfolio: PortfolioUpdate | null;
}

export default function PerformanceChart({ portfolio }: PerformanceChartProps) {
  const [timeframe, setTimeframe] = useState<'1h' | '24h' | '7d' | '30d'>('24h');
  const [performanceHistory, setPerformanceHistory] = useState<
    Array<{ timestamp: string; value: number }>
  >([]);

  useEffect(() => {
    if (portfolio && portfolio.total_value !== undefined) {
      setPerformanceHistory((prev) => {
        const newHistory = [
          ...prev,
          {
            timestamp: portfolio.timestamp || new Date().toISOString(),
            value: portfolio.total_value || 0,
          },
        ];
        return newHistory.slice(-100);
      });
    }
  }, [portfolio]);

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);

  const formatPercent = (value: number) => `${(value * 100).toFixed(2)}%`;

  const totalPnl = portfolio ? (portfolio.total_value || 50) - 50 : 0;
  const sharpeRatio = portfolio?.performance?.sharpe_ratio || 0;
  const maxDrawdown = portfolio?.performance?.max_drawdown || 0;

  const timeframeMs: Record<typeof timeframe, number> = {
    '1h': 60 * 60 * 1000,
    '24h': 24 * 60 * 60 * 1000,
    '7d': 7 * 24 * 60 * 60 * 1000,
    '30d': 30 * 24 * 60 * 60 * 1000,
  };
  const cutoff = Date.now() - timeframeMs[timeframe];
  const filteredHistory = performanceHistory.filter((entry) => {
    const ts = Date.parse(entry.timestamp);
    return Number.isNaN(ts) ? true : ts >= cutoff;
  });

  const maxVal = filteredHistory.length > 0
    ? Math.max(...filteredHistory.map((d) => d.value))
    : 50;
  const minVal = filteredHistory.length > 0
    ? Math.min(...filteredHistory.map((d) => d.value))
    : 50;
  const range = maxVal - minVal || 1;

  const metrics = [
    { label: 'Total PnL', value: formatCurrency(totalPnl) },
    {
      label: 'Total Value',
      value: formatCurrency(portfolio?.total_value || 50),
      helper: `Cash ${formatCurrency(portfolio?.cash || 0)}`,
    },
    { label: 'Sharpe Ratio', value: sharpeRatio.toFixed(2) },
    {
      label: 'Daily Return',
      value: formatPercent(portfolio?.performance?.daily_return || 0),
      helper: `Max Drawdown ${maxDrawdown.toFixed(2)}%`,
    },
  ];

  return (
    <Panel
      title="Performance"
      action={
        <div className="flex items-center gap-2">
          {(['1h', '24h', '7d', '30d'] as const).map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`text-xs px-2 py-1 border border-[var(--line)] rounded-[var(--radius)] ${
                timeframe === tf ? 'text-[var(--fg)]' : 'text-[var(--muted)]'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      }
    >
      {portfolio ? (
        <MetricGrid items={metrics} columns={2} />
      ) : (
        <p className="text-sm text-[var(--muted)]">No portfolio data yet.</p>
      )}
      <p className="mt-2 text-xs text-[var(--muted)]">
        Timeframe reflects in-session samples only.
      </p>

      <div className="mt-4">
        {filteredHistory.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">No performance data yet.</p>
        ) : (
          <div className="relative h-48">
            <svg className="w-full h-full" viewBox="0 0 800 200" preserveAspectRatio="none">
              {[0, 25, 50, 75, 100].map((y) => (
                <line
                  key={y}
                  x1="0"
                  y1={y * 2}
                  x2="800"
                  y2={y * 2}
                  stroke="var(--line)"
                  strokeWidth="1"
                />
              ))}
              <line
                x1="0"
                y1={200 - ((50 - minVal) / range) * 200}
                x2="800"
                y2={200 - ((50 - minVal) / range) * 200}
                stroke="var(--line)"
                strokeWidth="1"
                strokeDasharray="4,4"
              />
              <polyline
                points={filteredHistory
                  .map((d, i) => {
                    const denom = Math.max(filteredHistory.length - 1, 1);
                    const x = (i / denom) * 800;
                    const y = 200 - ((d.value - minVal) / range) * 200;
                    return `${x},${y}`;
                  })
                  .join(' ')}
                fill="none"
                stroke="var(--fg)"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <div className="absolute top-0 left-0 h-full flex flex-col justify-between text-xs text-[var(--muted)]">
              <span>{formatCurrency(maxVal)}</span>
              <span>{formatCurrency((maxVal + minVal) / 2)}</span>
              <span>{formatCurrency(minVal)}</span>
            </div>
          </div>
        )}
      </div>
    </Panel>
  );
}
