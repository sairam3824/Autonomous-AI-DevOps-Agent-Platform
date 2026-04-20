'use client';
import { clsx } from 'clsx';

interface Tab {
  id: string;
  label: string;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (id: string) => void;
}

export default function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div className="inline-flex flex-wrap gap-2 rounded-full bg-white/40 p-1.5 shadow-[0_18px_40px_rgba(97,74,49,0.06)]">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={clsx(
            'rounded-full px-4 py-2 text-sm transition-all',
            activeTab === tab.id ? 'bg-[var(--ink)] text-white' : 'text-[var(--ink-soft)] hover:bg-white/65 hover:text-[var(--ink)]'
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
