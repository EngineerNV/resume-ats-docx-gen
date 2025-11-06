'use client';

import { useState } from 'react';
import { formatBytes } from '../lib/utils';
import type { FormState, KeywordPreviewItem } from '../lib/types';

interface PayloadPreviewProps {
  state: FormState;
  onRemoveResumeFile?: (id: string) => void;
  onRemoveJobFile?: (id: string) => void;
  showKeywordPreview?: boolean;
  keywords?: KeywordPreviewItem[];
}

function CollapsibleText({ label, value, previewChars = 500 }: { label: string; value: string; previewChars?: number }) {
  const [expanded, setExpanded] = useState(false);
  const shouldTruncate = value.length > previewChars;
  const displayValue = shouldTruncate && !expanded ? `${value.slice(0, previewChars)}…` : value;

  if (!value) return null;

  return (
    <section className="space-y-2 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <header className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-100">{label}</h3>
        {shouldTruncate && (
          <button
            type="button"
            onClick={() => setExpanded((prev) => !prev)}
            className="text-xs font-semibold text-brand hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
          >
            {expanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </header>
      <p className="whitespace-pre-wrap text-sm text-slate-600 dark:text-slate-300">{displayValue}</p>
    </section>
  );
}

function FileList({
  title,
  files,
  onRemove
}: {
  title: string;
  files: FormState['resumeFiles'];
  onRemove?: (id: string) => void;
}) {
  if (files.length === 0) return null;

  return (
    <section className="space-y-2 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <header className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-100">{title}</h3>
      </header>
      <ul className="space-y-2" role="list">
        {files.map(({ id, file }) => (
          <li
            key={id}
            className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950/50"
            role="listitem"
          >
            <div className="flex flex-col">
              <span className="font-medium text-slate-800 dark:text-slate-100">{file.name}</span>
              <span className="text-xs text-slate-500 dark:text-slate-400">{formatBytes(file.size)}</span>
            </div>
            {onRemove && (
              <button
                type="button"
                onClick={() => onRemove(id)}
                className="rounded-full px-3 py-1 text-xs font-semibold text-rose-600 transition hover:bg-rose-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500"
              >
                Remove
              </button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

export function PayloadPreview({ state, onRemoveResumeFile, onRemoveJobFile, showKeywordPreview, keywords }: PayloadPreviewProps) {
  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <dl className="grid gap-2 sm:grid-cols-2">
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Mode</dt>
            <dd className="font-medium capitalize text-slate-800 dark:text-slate-100">{state.mode.replace('_', ' ')}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Context provided</dt>
            <dd className="font-medium text-slate-800 dark:text-slate-100">{state.context ? 'Yes' : 'No'}</dd>
          </div>
        </dl>
      </div>

      <CollapsibleText label="Resume text" value={state.resumeText} />
      <FileList title="Resume files" files={state.resumeFiles} onRemove={onRemoveResumeFile} />

      {state.context && <CollapsibleText label="Additional context" value={state.context} />}

      {state.mode === 'job_tuning' && (
        <>
          <CollapsibleText label="Job description" value={state.jobDescriptionText} />
          <FileList title="Job description files" files={state.jobDescriptionFiles} onRemove={onRemoveJobFile} />
        </>
      )}

      {showKeywordPreview && keywords && keywords.length > 0 && (
        <section className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <header className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-100">Keyword preview</h3>
            <span className="text-xs text-slate-500 dark:text-slate-400">Top {keywords.length} terms</span>
          </header>
          <div className="flex flex-wrap gap-2">
            {keywords.map((keyword) => (
              <span
                key={keyword.value}
                className="rounded-full bg-brand/10 px-3 py-1 text-xs font-semibold text-brand dark:bg-brand/20 dark:text-brand-dark"
              >
                {keyword.value} · {keyword.count}
              </span>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
