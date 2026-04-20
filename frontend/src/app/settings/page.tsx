'use client';
import { useAuth } from '@/hooks/useAuth';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-8">
      <Card className="rounded-[38px] px-7 py-8 md:px-10">
        <div className="space-y-3">
          <p className="premium-label">Profile and platform</p>
          <h2 className="premium-title">A cleaner settings view with the essentials only.</h2>
          <p className="max-w-3xl text-sm leading-7 text-[var(--ink-soft)]">
            Identity, environment details, and platform metadata are presented here without the usual settings clutter.
          </p>
        </div>
      </Card>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Card className="rounded-[38px]">
          <p className="premium-label">Account</p>
          <div className="mt-5 space-y-3">
            <Row label="Name" value={user?.username || '-'} />
            <Row label="Email" value={user?.email || '-'} />
            <Row label="User ID" value={user?.id ? String(user.id) : '-'} mono />
            <div className="flex items-center justify-between rounded-[24px] bg-white/46 px-4 py-4">
              <span className="text-sm text-[var(--ink-soft)]">Role</span>
              <Badge variant="info">{user?.role || 'unknown'}</Badge>
            </div>
            <div className="flex items-center justify-between rounded-[24px] bg-white/46 px-4 py-4">
              <span className="text-sm text-[var(--ink-soft)]">Account status</span>
              <Badge variant={user?.is_active ? 'success' : 'error'}>{user?.is_active ? 'Active' : 'Inactive'}</Badge>
            </div>
          </div>
        </Card>

        <Card className="rounded-[38px]">
          <p className="premium-label">System</p>
          <div className="mt-5 space-y-3">
            <Row label="Platform" value="DevOps AI Platform" />
            <Row label="Version" value="1.0.0" mono />
            <Row label="Backend" value="FastAPI and Python 3.12" />
            <Row label="Frontend" value="Next.js 15 and React 19" />
            <Row label="Inference" value="Ollama with local models" />
            <Row label="Retrieval" value="FAISS and sentence-transformers" />
          </div>
        </Card>
      </section>
    </div>
  );
}

function Row({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-[24px] bg-white/46 px-4 py-4">
      <span className="text-sm text-[var(--ink-soft)]">{label}</span>
      <span className={`${mono ? 'font-mono' : ''} text-sm text-[var(--ink)]`}>{value}</span>
    </div>
  );
}
