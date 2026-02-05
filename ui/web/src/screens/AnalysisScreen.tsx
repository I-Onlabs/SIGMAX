import TradingPanel from '../components/TradingPanel';
import Panel from '../ui/components/Panel';

interface AnalysisScreenProps {
  marketData: Array<{ symbol: string; price: number; change_24h: number }>;
  agentDecisions: Array<any>;
}

export default function AnalysisScreen({ marketData, agentDecisions }: AnalysisScreenProps) {
  const hasData = marketData.length > 0 || agentDecisions.length > 0;

  return (
    <div className="grid gap-6">
      {!hasData && (
        <Panel title="Data Status">
          <p className="text-sm text-[var(--muted)]">
            No live data yet. Start an analysis to populate results.
          </p>
        </Panel>
      )}
      <TradingPanel marketData={marketData} agentDecisions={agentDecisions} />
    </div>
  );
}
