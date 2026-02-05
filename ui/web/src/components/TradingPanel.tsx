import { useState, useEffect } from 'react';
import Panel from '../ui/components/Panel';
import PrimaryAction from '../ui/components/PrimaryAction';
import StatRow from '../ui/components/StatRow';
import api from '../services/api';

interface TradingPanelProps {
  marketData?: Array<{ symbol: string; price: number; change_24h: number }>;
  agentDecisions?: Array<any>;
}

export default function TradingPanel({ marketData, agentDecisions }: TradingPanelProps) {
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [analyzing, setAnalyzing] = useState(false);
  const [decision, setDecision] = useState<any>(null);

  useEffect(() => {
    if (agentDecisions && agentDecisions.length > 0) {
      const latestForSymbol = agentDecisions.find((d) => d.symbol === symbol);
      if (latestForSymbol) {
        setDecision(latestForSymbol);
      }
    }
  }, [agentDecisions, symbol]);

  const handleAnalyze = async () => {
    setAnalyzing(true);

    try {
      const data = await api.analyzeSymbol({ symbol, include_debate: false });
      setDecision(data);
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Analysis failed: ' + (error as Error).message);
    } finally {
      setAnalyzing(false);
    }
  };

  const currentPrice = marketData?.find((m) => m.symbol === symbol)?.price;
  const priceChange = marketData?.find((m) => m.symbol === symbol)?.change_24h;

  return (
    <Panel title="Analysis">
      <div className="space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <label className="block text-xs font-semibold mb-2">Symbol</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="w-full px-3 py-2 rounded-[var(--radius)] border border-[var(--line)] bg-transparent text-sm"
              placeholder="BTC/USDT"
            />
          </div>
          <div className="min-w-[140px] text-right">
            <div className="text-xs text-[var(--muted)]">Last Price</div>
            <div className="text-lg font-semibold">
              {currentPrice ? `$${currentPrice.toLocaleString()}` : '—'}
            </div>
            <div className="text-xs text-[var(--muted)]">
              {priceChange !== undefined ? `${priceChange.toFixed(2)}%` : '—'}
            </div>
          </div>
        </div>

        <PrimaryAction onClick={handleAnalyze} disabled={analyzing} className="w-full">
          {analyzing ? 'Analyzing...' : 'Analyze'}
        </PrimaryAction>

        {decision && (
          <div className="border border-[var(--line)] rounded-[var(--radius)] p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-[var(--muted)]">Decision</span>
              <span className="text-xs font-semibold">
                {decision.decision?.toUpperCase() || 'HOLD'}
              </span>
            </div>
            <div className="space-y-2">
              <StatRow
                label="Confidence"
                value={`${Math.round((typeof decision.confidence === 'number' ? decision.confidence : 0) * 100)}%`}
              />
            </div>
            {(() => {
              const reasoning = decision.reasoning;
              const bull =
                (typeof reasoning === 'object' && reasoning?.bull) ||
                decision.bull_score ||
                '—';
              const bear =
                (typeof reasoning === 'object' && reasoning?.bear) ||
                decision.bear_score ||
                '—';
              const summary =
                typeof reasoning === 'string' ? reasoning : decision.reasoning?.summary;

              return (
                <div className="mt-3 pt-3 border-t border-[var(--line)] text-xs space-y-2">
                  <div>
                    <div className="text-[var(--muted)]">Bull</div>
                    <div>{bull}</div>
                  </div>
                  <div>
                    <div className="text-[var(--muted)]">Bear</div>
                    <div>{bear}</div>
                  </div>
                  {summary && (
                    <div>
                      <div className="text-[var(--muted)]">Summary</div>
                      <div>{summary}</div>
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        )}
      </div>
    </Panel>
  );
}
