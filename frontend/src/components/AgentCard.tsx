'use client';
import { clsx } from 'clsx';
import Badge from './ui/Badge';
import Button from './ui/Button';

interface AgentCardProps {
  name: string;
  description: string;
  icon: string;
  color: string;
  bgColor: string;
  status?: 'idle' | 'running' | 'completed' | 'failed';
  lastRun?: string;
  onRun: () => void;
}

export default function AgentCard({ name, description, icon, color, bgColor, status = 'idle', lastRun, onRun }: AgentCardProps) {
  const statusVariant = { idle: 'neutral' as const, running: 'warning' as const, completed: 'success' as const, failed: 'error' as const };

  return (
    <div
      className={clsx(
        'relative rounded-xl border border-slate-700/50 bg-slate-800/50 p-5 transition-all duration-300',
        'hover:border-slate-600 hover:shadow-lg',
        status === 'running' && 'border-emerald-500/30 animate-glow'
      )}
    >
      <div className="flex items-start justify-between mb-4">
        <div className={clsx('w-10 h-10 rounded-lg flex items-center justify-center', bgColor)}>
          <svg className={clsx('w-5 h-5', color)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={icon} />
          </svg>
        </div>
        <Badge variant={statusVariant[status]}>{status}</Badge>
      </div>
      <h3 className="text-base font-semibold text-white mb-1">{name}</h3>
      <p className="text-sm text-slate-400 mb-4 line-clamp-2">{description}</p>
      {lastRun && <p className="text-xs text-slate-500 mb-3">Last run: {lastRun}</p>}
      <Button onClick={onRun} size="sm" variant="primary" isLoading={status === 'running'} className="w-full">
        {status === 'running' ? 'Running...' : 'Run Agent'}
      </Button>
    </div>
  );
}
