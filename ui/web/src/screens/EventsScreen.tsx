import AlertPanel from '../components/AlertPanel';
import Panel from '../ui/components/Panel';

interface EventsScreenProps {
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
}

export default function EventsScreen({ tradeExecutions }: EventsScreenProps) {
  const isEmpty = tradeExecutions.length === 0;

  return (
    <div className="grid gap-6">
      {isEmpty && (
        <Panel title="Event Status">
          <p className="text-sm text-[var(--muted)]">No events received yet.</p>
        </Panel>
      )}
      <AlertPanel trades={tradeExecutions} />
    </div>
  );
}
