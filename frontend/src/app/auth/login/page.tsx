'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/stores/authStore';
import Button from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
      router.push('/dashboard');
    } catch (err: unknown) {
      setError((err as Error).message || 'Login failed');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-5 py-10">
      <div className="grid w-full max-w-6xl gap-8 xl:grid-cols-[minmax(0,1.1fr)_minmax(420px,0.72fr)]">
        <section className="premium-surface-strong rounded-[40px] px-8 py-10 md:px-12 md:py-14">
          <p className="premium-label">DevOps AI Platform</p>
          <h1 className="mt-4 text-5xl leading-none text-[var(--ink)] md:text-7xl">A more refined operations workspace.</h1>
          <p className="mt-6 max-w-2xl text-base leading-8 text-[var(--ink-soft)]">
            Monitor infrastructure, diagnose failures, analyze delivery systems, and keep operational context in one premium environment.
          </p>
          <div className="mt-10 grid gap-4 md:grid-cols-3">
            <Intro label="Local inference" value="Private by default" />
            <Intro label="Agent systems" value="Infra, delivery, remediation" />
            <Intro label="Knowledge memory" value="Logs plus retrieval" />
          </div>
        </section>

        <section className="premium-surface rounded-[40px] px-7 py-8 md:px-9 md:py-10">
          <p className="premium-label">Sign in</p>
          <h2 className="mt-2 text-4xl text-[var(--ink)]">Welcome back</h2>
          <p className="mt-3 text-sm leading-7 text-[var(--ink-soft)]">Use the demo credentials or continue with your account.</p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            {error && <div className="rounded-[24px] bg-[#f7e8e5] px-4 py-3 text-sm text-[#874d47]">{error}</div>}
            <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="demo@devops.ai" required />
            <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="demo1234" required />
            <Button type="submit" isLoading={isLoading} className="w-full" size="lg">
              Enter workspace
            </Button>
          </form>

          <div className="mt-6 space-y-3 text-sm text-[var(--ink-soft)]">
            <p>Demo access: `demo@devops.ai` / `demo1234`</p>
            <p>
              No account yet?{' '}
              <Link href="/auth/register" className="text-[var(--accent)]">
                Create one
              </Link>
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}

function Intro({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[28px] bg-white/46 px-5 py-5">
      <p className="premium-label">{label}</p>
      <p className="mt-3 text-lg text-[var(--ink)]">{value}</p>
    </div>
  );
}
