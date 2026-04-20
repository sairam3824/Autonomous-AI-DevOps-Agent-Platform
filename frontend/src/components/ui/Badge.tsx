'use client';
import { clsx } from 'clsx';

interface BadgeProps {
  variant?: 'success' | 'warning' | 'error' | 'info' | 'neutral';
  children: React.ReactNode;
  className?: string;
}

const variants = {
  success: 'bg-[rgba(74,119,93,0.12)] text-[#3e6d54]',
  warning: 'bg-[rgba(165,129,63,0.12)] text-[#8b6a2f]',
  error: 'bg-[rgba(145,78,71,0.12)] text-[#874d47]',
  info: 'bg-[rgba(92,119,138,0.12)] text-[#4c6b81]',
  neutral: 'bg-white/52 text-[var(--ink-soft)]',
};

export default function Badge({ variant = 'neutral', children, className }: BadgeProps) {
  return (
    <span className={clsx('inline-flex rounded-full px-3 py-1 text-xs font-medium', variants[variant], className)}>
      {children}
    </span>
  );
}
