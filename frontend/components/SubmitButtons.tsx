'use client';

import clsx from 'clsx';

interface SubmitButtonsProps {
  onBuildResume: () => void;
  loadingAction?: 'docx' | null;
  disabled?: boolean;
}

export function SubmitButtons({ onBuildResume, loadingAction = null, disabled = false }: SubmitButtonsProps) {
  return (
    <div className="flex items-center justify-end">
      <button
        type="button"
        onClick={onBuildResume}
        disabled={disabled || loadingAction !== null}
        className={clsx(
          'inline-flex items-center justify-center rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-slate-950',
          disabled || loadingAction !== null ? 'opacity-70' : 'hover:bg-brand/90'
        )}
      >
        {loadingAction === 'docx' ? 'Building resume…' : 'Build Resume'}
      </button>
    </div>
  );
}
