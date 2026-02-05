import type { ReactNode } from 'react';

interface PanelProps {
  title?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export default function Panel({ title, action, children, className }: PanelProps) {
  return (
    <section
      className={`border border-[var(--line)] bg-[var(--panel)] rounded-[var(--radius)] p-4 ${className || ''}`}
    >
      {(title || action) && (
        <div className="flex items-center justify-between mb-3">
          {title && <h2 className="text-sm font-semibold">{title}</h2>}
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </section>
  );
}
