import type { ReactNode } from 'react';

export interface EventItem {
  id: string;
  title: string;
  timestamp: string;
  severity?: 'info' | 'warning' | 'critical' | 'emergency';
  description?: string;
  meta?: string[];
}

interface EventListProps {
  items: EventItem[];
  emptyLabel?: string;
  renderAction?: (item: EventItem) => ReactNode;
}

const severityLabel: Record<NonNullable<EventItem['severity']>, string> = {
  info: 'Info',
  warning: 'Warning',
  critical: 'Critical',
  emergency: 'Emergency',
};

export default function EventList({
  items,
  emptyLabel = 'No events available.',
  renderAction,
}: EventListProps) {
  if (items.length === 0) {
    return <p className="text-sm text-[var(--muted)]">{emptyLabel}</p>;
  }

  return (
    <div className="divide-y divide-[var(--line)]">
      {items.map((item) => (
        <div key={item.id} className="py-3">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="text-sm font-semibold truncate">{item.title}</div>
              {item.description && (
                <div className="text-xs text-[var(--muted)] mt-1">
                  {item.description}
                </div>
              )}
              {item.meta && item.meta.length > 0 && (
                <div className="mt-2 text-xs text-[var(--muted)] space-y-1">
                  {item.meta.map((entry, index) => (
                    <div key={`${item.id}-meta-${index}`}>{entry}</div>
                  ))}
                </div>
              )}
            </div>
            <div className="text-right text-xs text-[var(--muted)] whitespace-nowrap">
              <div>{item.timestamp}</div>
              {item.severity && <div>{severityLabel[item.severity]}</div>}
              {renderAction && <div className="mt-2">{renderAction(item)}</div>}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
