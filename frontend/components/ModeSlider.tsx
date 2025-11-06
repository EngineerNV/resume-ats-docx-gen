'use client';

import * as ToggleGroup from '@radix-ui/react-toggle-group';
import clsx from 'clsx';
import type { Mode } from '../lib/types';

interface ModeSliderProps {
  value: Mode;
  onChange: (value: Mode) => void;
}

const modes: { value: Mode; label: string; description: string }[] = [
  { value: 'resume', label: 'Resume', description: 'Polish a resume without targeting a role.' },
  {
    value: 'job_tuning',
    label: 'Job Tuning',
    description: 'Tailor the resume with a job description or posting.'
  }
];

export function ModeSlider({ value, onChange }: ModeSliderProps) {
  return (
    <ToggleGroup.Root
      type="single"
      value={value}
      onValueChange={(next) => {
        if (next) onChange(next as Mode);
      }}
      className="grid grid-cols-1 gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm ring-1 ring-black/5 dark:border-slate-800 dark:bg-slate-900"
      aria-label="Workflow mode"
    >
      {modes.map((mode) => (
        <ToggleGroup.Item
          key={mode.value}
          value={mode.value}
          className={clsx(
            'flex flex-col rounded-xl border border-transparent px-4 py-3 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
            value === mode.value
              ? 'bg-brand/10 text-brand ring-1 ring-brand dark:bg-brand/20 dark:text-brand-dark'
              : 'hover:border-brand/40 hover:bg-slate-100 dark:hover:bg-slate-800'
          )}
        >
          <span className="text-sm font-semibold uppercase tracking-wide text-slate-700 dark:text-slate-200">
            {mode.label}
          </span>
          <span className="text-sm text-slate-600 dark:text-slate-300">{mode.description}</span>
        </ToggleGroup.Item>
      ))}
    </ToggleGroup.Root>
  );
}
