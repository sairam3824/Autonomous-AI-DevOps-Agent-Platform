'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { NAV_ITEMS } from '@/lib/constants';
import { useAuthStore } from '@/stores/authStore';

export default function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();

  return (
    <header className="sticky top-0 z-40 border-b border-[var(--line)] bg-[rgba(245,240,232,0.78)] backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-[1500px] flex-col gap-4 px-5 py-5 md:px-8 lg:px-10">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <Link href="/dashboard" className="block">
              <p className="font-sans text-[11px] uppercase tracking-[0.34em] text-[var(--ink-soft)]">DevOps AI Platform</p>
              <h1 className="text-3xl text-[var(--ink)] md:text-4xl">Operational Studio</h1>
            </Link>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="rounded-full bg-white/55 px-4 py-2 text-sm text-[var(--ink-soft)] shadow-[0_10px_40px_rgba(97,74,49,0.08)]">
              {user?.username || 'Guest'}
              <span className="ml-2 text-[var(--accent)]">{user?.role || 'engineer'}</span>
            </div>
            <button
              onClick={() => {
                logout();
                router.push('/auth/login');
              }}
              className="rounded-full bg-[var(--accent-soft)] px-4 py-2 text-sm font-medium text-[var(--accent)] transition-colors hover:bg-[rgba(138,106,61,0.18)]"
            >
              Sign Out
            </button>
          </div>
        </div>

        <nav className="flex flex-wrap gap-2">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-full px-4 py-2 text-sm transition-all ${
                  isActive
                    ? 'bg-[var(--ink)] text-white shadow-[0_14px_32px_rgba(31,26,23,0.18)]'
                    : 'bg-white/45 text-[var(--ink-soft)] hover:bg-white/72 hover:text-[var(--ink)]'
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
