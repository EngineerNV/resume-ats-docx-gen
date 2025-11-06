'use client';

import clsx from 'clsx';

interface SubmitButtonsProps {
  onGetSuggestions: () => void;
  onDownloadDocx: () => void;
  loadingAction?: 'json' | 'docx' | null;
  disabled?: boolean;
}

export function SubmitButtons({ onGetSuggestions, onDownloadDocx, loadingAction = null, disabled = false }: SubmitButtonsProps) {
  return (
    <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:justify-end">
      <button
        type="button"
        onClick={onGetSuggestions}
        disabled={disabled || loadingAction !== null}
        className={clsx(
          'inline-flex items-center justify-center rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-slate-950',
          disabled || loadingAction !== null ? 'opacity-70' : 'hover:bg-brand/90'
        )}
      >
        {loadingAction === 'json' ? 'Fetching suggestions…' : 'Get Suggestions'}
      </button>
      <button
        type="button"
        onClick={onDownloadDocx}
        disabled={disabled || loadingAction !== null}
        className={clsx(
          'inline-flex items-center justify-center rounded-full border border-brand px-6 py-3 text-sm font-semibold text-brand transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:text-brand-dark dark:focus-visible:ring-offset-slate-950',
          disabled || loadingAction !== null ? 'opacity-70' : 'hover:bg-brand/10'
        )}
      >
        {loadingAction === 'docx' ? 'Preparing DOCX…' : 'Download DOCX'}
      </button>
    </div>
  );
}
