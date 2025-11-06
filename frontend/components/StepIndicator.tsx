'use client';

import clsx from 'clsx';

export interface StepDefinition {
  label: string;
  description?: string;
}

export interface StepState extends StepDefinition {
  status: 'complete' | 'current' | 'upcoming';
  disabled?: boolean;
}

interface StepIndicatorProps {
  steps: StepState[];
  onStepSelect?: (index: number) => void;
}

export function StepIndicator({ steps, onStepSelect }: StepIndicatorProps) {
  return (
    <nav aria-label="Workflow steps" className="w-full">
      <ol className="flex flex-wrap items-center justify-center gap-4">
        {steps.map((step, index) => {
          const isClickable = onStepSelect && !step.disabled;
          return (
            <li key={step.label} className="flex items-center gap-3" aria-current={step.status === 'current' ? 'step' : undefined}>
              <button
                type="button"
                className={clsx(
                  'flex min-w-[8rem] flex-col rounded-2xl border px-4 py-3 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
                  step.status === 'current'
                    ? 'border-brand bg-brand/10 text-brand'
                    : step.status === 'complete'
                    ? 'border-emerald-500/70 bg-emerald-50 text-emerald-700 dark:border-emerald-500/50 dark:bg-emerald-500/10 dark:text-emerald-300'
                    : 'border-slate-200 bg-white text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300',
                  isClickable ? 'cursor-pointer hover:shadow-sm' : 'cursor-default'
                )}
                onClick={() => isClickable && onStepSelect(index)}
                disabled={!isClickable}
              >
                <span className="text-xs font-semibold uppercase tracking-wide">{step.label}</span>
                {step.description && <span className="text-xs text-slate-500 dark:text-slate-400">{step.description}</span>}
              </button>
              {index < steps.length - 1 && <div className="h-px w-12 bg-slate-200 dark:bg-slate-700" aria-hidden="true" />}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
