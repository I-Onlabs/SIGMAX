interface InlineStatusProps {
  label: string;
  tone?: 'neutral' | 'positive' | 'negative';
}

export default function InlineStatus({ label, tone = 'neutral' }: InlineStatusProps) {
  const toneClass =
    tone === 'positive'
      ? 'text-[var(--fg)]'
      : tone === 'negative'
        ? 'text-[var(--danger)]'
        : 'text-[var(--muted)]';

  return <span className={`text-xs ${toneClass}`}>{label}</span>;
}
