'use client';

import { useCallback, useMemo, useState } from 'react';
import { useDropzone, FileRejection, Accept } from 'react-dropzone';
import clsx from 'clsx';
import { formatBytes, totalBytes } from '../lib/utils';
import type { UploadedFile } from '../lib/types';

interface FileDropzoneProps {
  label: string;
  description: string;
  accept: Accept;
  maxFiles: number;
  maxTotalBytes: number;
  files: UploadedFile[];
  onFilesChange: (files: UploadedFile[]) => void;
  externalError?: string | null;
}

export function FileDropzone({
  label,
  description,
  accept,
  maxFiles,
  maxTotalBytes,
  files,
  onFilesChange,
  externalError
}: FileDropzoneProps) {
  const [error, setError] = useState<string | null>(null);

  const createId = useCallback(
    () =>
      typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    []
  );

  const onDrop = useCallback(
    (accepted: File[], rejected: FileRejection[]) => {
      let nextFiles = [...files];
      const acceptedFiles: UploadedFile[] = accepted.map((file) => ({
        id: `${file.name}-${file.size}-${file.lastModified}-${createId()}`,
        file
      }));

      if (nextFiles.length + acceptedFiles.length > maxFiles) {
        setError(`Maximum of ${maxFiles} files allowed.`);
        return;
      }

      nextFiles = [...nextFiles, ...acceptedFiles];
      const total = totalBytes(nextFiles);
      if (total > maxTotalBytes) {
        setError(`Combined file size must stay under ${formatBytes(maxTotalBytes)}.`);
        return;
      }

      if (rejected.length > 0) {
        const messages = new Set<string>();
        rejected.forEach(({ errors }) => {
          errors.forEach((err) => messages.add(err.message));
        });
        setError(Array.from(messages).join(' '));
      } else {
        setError(null);
      }

      onFilesChange(nextFiles);
    },
    [createId, files, maxFiles, maxTotalBytes, onFilesChange]
  );

  const onRemove = useCallback(
    (id: string) => {
      setError(null);
      onFilesChange(files.filter((item) => item.id !== id));
    },
    [files, onFilesChange]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept,
    maxFiles,
    multiple: maxFiles > 1,
    onDrop,
    onDropRejected: (rejections) => {
      const messages = new Set<string>();
      rejections.forEach(({ errors }) => {
        errors.forEach((err) => messages.add(err.message));
      });
      setError(Array.from(messages).join(' '));
    }
  });

  const helper = useMemo(
    () => `${description} • ${files.length}/${maxFiles} files • ${formatBytes(totalBytes(files))} / ${formatBytes(maxTotalBytes)}`,
    [description, files, maxFiles, maxTotalBytes]
  );

  const activeError = externalError ?? error;

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">{label}</label>
      <div
        {...getRootProps({
          className: clsx(
            'flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-slate-300 px-6 py-10 text-center transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
            isDragActive
              ? 'border-brand bg-brand/10 text-brand'
              : 'hover:border-brand/60 hover:bg-slate-100 dark:hover:bg-slate-800'
          )
        })}
        aria-label={label}
        aria-describedby={activeError ? `${label}-error` : undefined}
      >
        <input {...getInputProps()} />
        <span className="text-sm font-semibold">Drop files here or click to browse</span>
        <span className="text-xs text-slate-500 dark:text-slate-400">{helper}</span>
      </div>
      {activeError && (
        <p id={`${label}-error`} className="text-sm text-rose-600" role="alert">
          {activeError}
        </p>
      )}
      {files.length > 0 && (
        <ul className="space-y-2" role="list">
          {files.map(({ id, file }) => (
            <li
              key={id}
              role="listitem"
              className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm shadow-sm dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="flex flex-col text-left">
                <span className="font-medium text-slate-800 dark:text-slate-100">{file.name}</span>
                <span className="text-xs text-slate-500 dark:text-slate-400">{formatBytes(file.size)}</span>
              </div>
              <button
                type="button"
                onClick={() => onRemove(id)}
                className="rounded-full px-3 py-1 text-xs font-semibold text-rose-600 transition hover:bg-rose-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
