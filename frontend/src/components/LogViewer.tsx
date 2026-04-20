'use client';
import { useState } from 'react';

interface LogViewerProps {
  content: string;
}

const LEVELS = ['ALL', 'ERROR', 'WARN', 'INFO', 'DEBUG'] as const;

export default function LogViewer({ content }: LogViewerProps) {
  const [filter, setFilter] = useState<string>('ALL');
  const [search, setSearch] = useState('');

  const lines = content.split('\n').filter((line) => {
    if (filter !== 'ALL' && !line.includes(filter)) return false;
    if (search && !line.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap gap-2">
          {LEVELS.map((level) => (
            <button
              key={level}
              onClick={() => setFilter(level)}
              className={`rounded-full px-3 py-1.5 text-xs transition-all ${
                filter === level ? 'bg-[var(--ink)] text-white' : 'bg-white/52 text-[var(--ink-soft)] hover:bg-white/74'
              }`}
            >
              {level}
            </button>
          ))}
        </div>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search logs"
          className="w-full rounded-full bg-white/55 px-4 py-2 text-sm text-[var(--ink)] outline-none placeholder:text-[var(--ink-soft)] lg:max-w-sm"
        />
      </div>

      <div className="max-h-96 space-y-2 overflow-y-auto rounded-[26px] bg-white/38 p-4 font-mono text-sm">
        {lines.length === 0 && <p className="text-[var(--ink-soft)]">No matching log entries.</p>}
        {lines.map((line, i) => (
          <div key={i} className="rounded-[18px] bg-white/44 px-3 py-2 text-[var(--ink-soft)]">
            {line}
          </div>
        ))}
      </div>
    </div>
  );
}
