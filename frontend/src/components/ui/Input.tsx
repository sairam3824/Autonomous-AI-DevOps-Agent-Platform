'use client';
import { clsx } from 'clsx';
import { InputHTMLAttributes, TextareaHTMLAttributes, forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, ...props }, ref) => (
    <div className="space-y-2">
      {label && <label className="premium-label block">{label}</label>}
      <input
        ref={ref}
        className={clsx(
          'w-full rounded-[24px] bg-white/60 px-4 py-3 text-sm text-[var(--ink)] outline-none transition-all placeholder:text-[var(--ink-soft)]/70',
          'shadow-[inset_0_1px_0_rgba(255,255,255,0.4),0_10px_30px_rgba(97,74,49,0.05)] focus:bg-white/84',
          error && 'bg-[#f8e9e7]',
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-[#8a4a43]">{error}</p>}
    </div>
  )
);
Input.displayName = 'Input';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, className, ...props }, ref) => (
    <div className="space-y-2">
      {label && <label className="premium-label block">{label}</label>}
      <textarea
        ref={ref}
        className={clsx(
          'w-full rounded-[28px] bg-white/60 px-4 py-3 text-sm text-[var(--ink)] outline-none transition-all placeholder:text-[var(--ink-soft)]/70',
          'shadow-[inset_0_1px_0_rgba(255,255,255,0.4),0_10px_30px_rgba(97,74,49,0.05)] focus:bg-white/84',
          'min-h-[120px] resize-y',
          error && 'bg-[#f8e9e7]',
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-[#8a4a43]">{error}</p>}
    </div>
  )
);
Textarea.displayName = 'Textarea';
