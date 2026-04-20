'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/stores/authStore';
import Button from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading } = useAuthStore();
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (password !== confirm) {
      setError('Passwords do not match');
      return;
    }
    try {
      await register(email, username, password);
      router.push('/dashboard');
    } catch (err: unknown) {
      setError((err as Error).message || 'Registration failed');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-5 py-10">
      <div className="grid w-full max-w-6xl gap-8 xl:grid-cols-[minmax(0,1fr)_minmax(440px,0.78fr)]">
        <section className="premium-surface-strong rounded-[40px] px-8 py-10 md:px-12 md:py-14">
          <p className="premium-label">Create account</p>
          <h1 className="mt-4 text-5xl leading-none text-[var(--ink)] md:text-7xl">Set up your premium operations workspace.</h1>
          <p className="mt-6 max-w-2xl text-base leading-8 text-[var(--ink-soft)]">
            Build a self-hosted environment for delivery intelligence, infrastructure reasoning, and incident response with a calmer visual experience.
          </p>
        </section>

        <section className="premium-surface rounded-[40px] px-7 py-8 md:px-9 md:py-10">
          <p className="premium-label">Registration</p>
          <h2 className="mt-2 text-4xl text-[var(--ink)]">Join the platform</h2>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            {error && <div className="rounded-[24px] bg-[#f7e8e5] px-4 py-3 text-sm text-[#874d47]">{error}</div>}
            <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required />
            <Input label="Username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="your name" required />
            <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Minimum 6 characters" required />
            <Input label="Confirm password" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="Re-enter password" required />
            <Button type="submit" isLoading={isLoading} className="w-full" size="lg">
              Create account
            </Button>
          </form>

          <p className="mt-6 text-sm text-[var(--ink-soft)]">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-[var(--accent)]">
              Sign in
            </Link>
          </p>
        </section>
      </div>
    </div>
  );
}
