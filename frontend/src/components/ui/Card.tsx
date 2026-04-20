'use client';
import { clsx } from 'clsx';
import { HTMLAttributes, ReactNode } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  header?: ReactNode;
  glow?: boolean;
}

export default function Card({ header, glow, className, children, ...props }: CardProps) {
  return (
    <section
      className={clsx(
        'premium-surface rounded-[32px] p-6',
        glow && 'shadow-[0_24px_80px_rgba(138,106,61,0.12),inset_0_1px_0_rgba(255,255,255,0.42)]',
        className
      )}
      {...props}
    >
      {header && (
        <div className="mb-5 space-y-1">
          {typeof header === 'string' ? <h3 className="text-2xl text-[var(--ink)]">{header}</h3> : header}
        </div>
      )}
      {children}
    </section>
  );
}
