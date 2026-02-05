interface AgentDebateLogProps {
  decisions?: Array<{
    symbol: string;
    decision: string;
    confidence: number;
    bull_score: string;
    bear_score: string;
    reasoning: string;
  }>;
}

export default function AgentDebateLog({ decisions }: AgentDebateLogProps) {
  const items = decisions?.slice(0, 6) || [];

  if (items.length === 0) {
    return <p className="text-sm text-[var(--muted)]">No decisions yet.</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((decision, index) => {
        const confidence =
          typeof decision.confidence === 'number' ? decision.confidence : 0;

        return (
          <div
            key={`${decision.symbol}-${index}`}
            className="border border-[var(--line)] rounded-[var(--radius)] p-3"
          >
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold">{decision.symbol}</div>
              <div className="text-xs text-[var(--muted)]">
                {decision.decision?.toUpperCase() || 'HOLD'} · {Math.round(confidence * 100)}%
              </div>
            </div>
            <div className="mt-3 grid gap-2 text-xs">
              <div>
                <div className="text-[var(--muted)]">Bull</div>
                <div>{decision.bull_score || '—'}</div>
              </div>
              <div>
                <div className="text-[var(--muted)]">Bear</div>
                <div>{decision.bear_score || '—'}</div>
              </div>
              <div>
                <div className="text-[var(--muted)]">Summary</div>
                <div>{decision.reasoning || 'No reasoning available.'}</div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
