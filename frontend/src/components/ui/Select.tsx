'use client';
import { clsx } from 'clsx';
import { SelectHTMLAttributes, forwardRef } from 'react';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: { value: string; label: string }[];
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, options, className, ...props }, ref) => (
    <div className="space-y-2">
      {label && <label className="premium-label block">{label}</label>}
      <select
        ref={ref}
        className={clsx(
          'w-full rounded-[24px] bg-white/60 px-4 py-3 text-sm text-[var(--ink)] outline-none transition-all',
          'shadow-[inset_0_1px_0_rgba(255,255,255,0.4),0_10px_30px_rgba(97,74,49,0.05)] focus:bg-white/84',
          className
        )}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  )
);

Select.displayName = 'Select';
export default Select;
