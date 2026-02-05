interface MetricItem {
  label: string;
  value: string;
  helper?: string;
}

interface MetricGridProps {
  items: MetricItem[];
  columns?: 2 | 3;
}

export default function MetricGrid({ items, columns = 3 }: MetricGridProps) {
  const gridClass = columns === 2 ? 'grid-cols-2' : 'grid-cols-3';

  return (
    <div className={`grid ${gridClass} gap-3`}>
      {items.map((item) => (
        <div
          key={`${item.label}-${item.value}`}
          className="border border-[var(--line)] rounded-[var(--radius)] p-3"
        >
          <div className="text-xs text-[var(--muted)]">{item.label}</div>
          <div className="text-base font-semibold">{item.value}</div>
          {item.helper && <div className="text-xs text-[var(--muted)] mt-1">{item.helper}</div>}
        </div>
      ))}
    </div>
  );
}
