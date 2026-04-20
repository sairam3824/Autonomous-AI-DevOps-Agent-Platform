'use client';
import { clsx } from 'clsx';
import { ButtonHTMLAttributes, forwardRef } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    const base =
      'inline-flex items-center justify-center rounded-full transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-60';
    const variants = {
      primary: 'bg-[var(--ink)] text-white shadow-[0_16px_40px_rgba(31,26,23,0.16)] hover:translate-y-[-1px]',
      secondary: 'bg-white/62 text-[var(--ink)] hover:bg-white/82',
      ghost: 'bg-transparent text-[var(--ink-soft)] hover:bg-white/42 hover:text-[var(--ink)]',
      danger: 'bg-[#6a3a31] text-white hover:bg-[#5a3028]',
    };
    const sizes = {
      sm: 'px-4 py-2 text-sm',
      md: 'px-5 py-2.5 text-sm',
      lg: 'px-6 py-3 text-base',
    };

    return (
      <button
        ref={ref}
        className={clsx(base, variants[variant], sizes[size], className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? 'Working...' : children}
      </button>
    );
  }
);

Button.displayName = 'Button';
export default Button;
