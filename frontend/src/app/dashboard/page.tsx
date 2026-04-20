'use client';
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { AGENT_TYPES } from '@/lib/constants';
import { healthApi } from '@/lib/api';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import type { HealthStatus } from '@/types';

const actionMap = [
  { label: 'Launch diagnostics', description: 'Run remediation and infrastructure reasoning flows.', href: '/agents' },
  { label: 'Review delivery logic', description: 'Inspect pipelines and tighten release readiness.', href: '/pipelines' },
  { label: 'Explore operational memory', description: 'Query logs and indexed DevOps knowledge.', href: '/logs' },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    healthApi.check().then(({ data }) => setHealth(data)).catch(() => {});
  }, []);

  const services = useMemo(() => Object.entries(health?.services || {}), [health]);
  const healthyCount = services.filter(([, svc]) => svc.status === 'healthy').length;

  return (
    <div className="space-y-8">
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.85fr)]">
        <Card className="premium-surface-strong rounded-[38px] px-7 py-8 md:px-10 md:py-10">
          <div className="space-y-6">
            <div className="space-y-2">
              <p className="premium-label">Control Surface</p>
              <h2 className="premium-title max-w-4xl">A calmer way to supervise infrastructure, delivery, and recovery.</h2>
              <p className="max-w-2xl text-sm leading-7 text-[var(--ink-soft)] md:text-base">
                Welcome back, {user?.username || 'operator'}. The workspace is now centered around clarity, readiness,
                and quick decision-making instead of dashboard clutter.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <Stat label="Platform status" value={health?.status || 'checking'} />
              <Stat label="Healthy services" value={`${healthyCount}/${services.length || 4}`} />
              <Stat label="Agent coverage" value={`${AGENT_TYPES.length} domains`} />
            </div>

            <div className="flex flex-wrap gap-3">
              <Button size="lg" onClick={() => router.push('/agents')}>
                Open agents
              </Button>
              <Button size="lg" variant="secondary" onClick={() => router.push('/projects')}>
                Review projects
              </Button>
            </div>
          </div>
        </Card>

        <Card className="rounded-[38px]">
          <div className="space-y-5">
            <div>
              <p className="premium-label">Current posture</p>
              <h3 className="mt-1 text-3xl text-[var(--ink)]">Service readiness</h3>
            </div>

            <div className="space-y-3">
              {services.length > 0 ? (
                services.map(([name, service]) => (
                  <div key={name} className="flex items-center justify-between rounded-[24px] bg-white/48 px-4 py-3">
                    <div>
                      <p className="text-sm font-medium capitalize text-[var(--ink)]">{name}</p>
                      <p className="text-xs text-[var(--ink-soft)]">Platform dependency</p>
                    </div>
                    <span className="rounded-full bg-white/70 px-3 py-1 text-xs capitalize text-[var(--ink-soft)]">
                      {service.status}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-[var(--ink-soft)]">Loading runtime health.</p>
              )}
            </div>
          </div>
        </Card>
      </section>

      <section className="grid gap-5 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.9fr)]">
        <Card className="rounded-[38px]">
          <div className="space-y-5">
            <div>
              <p className="premium-label">Agent suite</p>
              <h3 className="mt-1 text-3xl text-[var(--ink)]">Core capabilities</h3>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {AGENT_TYPES.map((agent) => (
                <button
                  key={agent.id}
                  onClick={() => router.push('/agents')}
                  className="rounded-[28px] bg-white/44 px-5 py-6 text-left transition-all hover:bg-white/66"
                >
                  <p className="text-lg font-semibold text-[var(--ink)]">{agent.label}</p>
                  <p className="mt-3 text-sm leading-7 text-[var(--ink-soft)]">{agent.description}</p>
                  <p className="mt-5 text-sm text-[var(--accent)]">Open workspace</p>
                </button>
              ))}
            </div>
          </div>
        </Card>

        <Card className="rounded-[38px]">
          <div className="space-y-5">
            <div>
              <p className="premium-label">Recommended flow</p>
              <h3 className="mt-1 text-3xl text-[var(--ink)]">Next actions</h3>
            </div>

            <div className="space-y-3">
              {actionMap.map((action) => (
                <button
                  key={action.label}
                  onClick={() => router.push(action.href)}
                  className="w-full rounded-[26px] bg-white/50 px-5 py-5 text-left transition-all hover:bg-white/72"
                >
                  <p className="text-base font-semibold text-[var(--ink)]">{action.label}</p>
                  <p className="mt-2 text-sm leading-7 text-[var(--ink-soft)]">{action.description}</p>
                </button>
              ))}
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[28px] bg-white/46 px-5 py-5">
      <p className="premium-label">{label}</p>
      <p className="mt-3 text-3xl text-[var(--ink)]">{value}</p>
    </div>
  );
}
