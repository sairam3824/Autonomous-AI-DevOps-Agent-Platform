'use client';
import { clsx } from 'clsx';

interface HealthIndicatorProps {
  label: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unreachable' | 'unavailable' | string;
}

export default function HealthIndicator({ label, status }: HealthIndicatorProps) {
  const colors: Record<string, string> = {
    healthy: 'bg-emerald-500',
    degraded: 'bg-amber-500',
    unhealthy: 'bg-red-500',
    unreachable: 'bg-red-500',
    unavailable: 'bg-slate-500',
  };

  const color = colors[status] || 'bg-slate-500';

  return (
    <div className="flex items-center gap-1.5" title={`${label}: ${status}`}>
      <div className={clsx('w-2 h-2 rounded-full', color, status === 'healthy' && 'animate-pulse-slow')} />
      <span className="text-xs text-slate-500 capitalize">{label}</span>
    </div>
  );
}
