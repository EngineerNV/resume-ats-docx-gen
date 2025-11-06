'use client';

import { remainingCharacters } from '../lib/utils';

interface TextSectionProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  description?: string;
  placeholder?: string;
  maxLength: number;
  rows?: number;
  error?: string;
  required?: boolean;
}

export function TextSection({
  id,
  label,
  value,
  onChange,
  description,
  placeholder,
  maxLength,
  rows = 8,
  error,
  required
}: TextSectionProps) {
  const remaining = remainingCharacters(value);
  const nearingLimit = remaining <= 2000;
  const helperText = error ?? `${value.length.toLocaleString()} / ${maxLength.toLocaleString()} characters`;
  const describedBy = [description ? `${id}-description` : null, `${id}-help`]
    .filter(Boolean)
    .join(' ')
    .trim();

  return (
    <div className="space-y-2">
      <label htmlFor={id} className="block text-sm font-medium text-slate-700 dark:text-slate-200">
        {label}
      </label>
      {description && (
        <p className="text-sm text-slate-500 dark:text-slate-400" id={`${id}-description`}>
          {description}
        </p>
      )}
      <textarea
        id={id}
        name={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        maxLength={maxLength}
        rows={rows}
        required={required}
        aria-describedby={describedBy.length > 0 ? describedBy : undefined}
        aria-invalid={Boolean(error)}
        placeholder={placeholder}
        className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100"
      />
      <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400" id={`${id}-help`}>
        <span className={error ? 'font-semibold text-rose-600' : undefined}>{helperText}</span>
        <span className={nearingLimit ? 'font-semibold text-amber-600' : undefined}>
          {remaining.toLocaleString()} characters left
        </span>
      </div>
    </div>
  );
}
