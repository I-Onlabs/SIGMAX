interface StatRowProps {
  label: string;
  value: string;
  muted?: boolean;
}

export default function StatRow({ label, value, muted = false }: StatRowProps) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-[var(--line)] last:border-b-0">
      <span className="text-xs text-[var(--muted)]">{label}</span>
      <span className={`text-xs font-semibold ${muted ? 'text-[var(--muted)]' : ''}`}>
        {value}
      </span>
    </div>
  );
}
