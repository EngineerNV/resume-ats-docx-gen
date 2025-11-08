'use client';

import clsx from 'clsx';

interface SubmitButtonsProps {
  onBuildResume: () => void;
  loadingAction?: 'docx' | null;
  disabled?: boolean;
}


import LoadingSpinner from './LoadingSpinner';

export function SubmitButtons({ onBuildResume, loadingAction = null, disabled = false }: SubmitButtonsProps) {
  return (
    <div className="flex flex-col items-center justify-center py-8">
      <button
        type="button"
        onClick={onBuildResume}
        disabled={disabled || loadingAction !== null}
        className={clsx(
          'inline-flex items-center justify-center rounded-full bg-brand px-8 py-4 text-lg font-bold text-white shadow-lg transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-slate-950',
          disabled || loadingAction !== null ? 'opacity-70' : 'hover:bg-brand/90'
        )}
        style={{ minWidth: '220px', minHeight: '56px' }}
      >
        {loadingAction === 'docx' ? 'Building resume…' : 'Build Resume'}
      </button>
      {loadingAction === 'docx' && (
        <div className="mt-6">
          <LoadingSpinner message="Generating your DOCX resume..." />
        </div>
      )}
      <p className="mt-2 text-[10px] text-slate-400 text-center max-w-xs mx-auto select-none pointer-events-none">
        By clicking Build Resume, you accept that AI results may be inaccurate and agree to review all outputs before use.
      </p>
    </div>
  );
}
