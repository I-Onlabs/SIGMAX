import type { ReactNode } from 'react';

export type TabId = 'overview' | 'analysis' | 'events' | 'health' | 'connections';

export interface AppShellProps {
  title: string;
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  connectionLabel: string;
  themeLabel: string;
  onToggleTheme: () => void;
  children: ReactNode;
}

const tabs: Array<{ id: TabId; label: string }> = [
  { id: 'overview', label: 'Overview' },
  { id: 'analysis', label: 'Analysis' },
  { id: 'events', label: 'Events' },
  { id: 'health', label: 'System Health' },
  { id: 'connections', label: 'Connections' },
];

export default function AppShell({
  title,
  activeTab,
  onTabChange,
  connectionLabel,
  themeLabel,
  onToggleTheme,
  children,
}: AppShellProps) {
  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--fg)]">
      <header className="border-b border-[var(--line)]">
        <div className="max-w-6xl mx-auto px-6 py-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-base font-semibold">{title}</h1>
            <span className="text-xs text-[var(--muted)]">{connectionLabel}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onToggleTheme}
              className="text-xs px-3 py-1 border border-[var(--line)] rounded-[var(--radius)]"
            >
              {themeLabel}
            </button>
          </div>
        </div>
        <nav className="border-t border-[var(--line)]">
          <div className="max-w-6xl mx-auto px-6">
            <div className="flex items-center gap-4 overflow-x-auto py-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => onTabChange(tab.id)}
                  className={`text-sm px-1 py-2 border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-[var(--fg)] text-[var(--fg)]'
                      : 'border-transparent text-[var(--muted)]'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </nav>
      </header>
      <main className="max-w-6xl mx-auto px-6 py-6">
        {children}
      </main>
    </div>
  );
}
