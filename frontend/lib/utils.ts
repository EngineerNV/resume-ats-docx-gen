import { formDataSchema, GROUP_MAX_BYTES, MAX_TEXTAREA_LENGTH } from './schema';
import type { FormState, KeywordPreviewItem, UploadedFile } from './types';

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const index = Math.floor(Math.log(bytes) / Math.log(1024));
  const value = bytes / Math.pow(1024, index);
  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
}

export function totalBytes(files: UploadedFile[]): number {
  return files.reduce((sum, item) => sum + item.file.size, 0);
}

export function buildFormData(state: FormState): FormData {
  const fd = new FormData();
  fd.set('mode', state.mode);
  fd.set('resumeText', state.resumeText);
  fd.set('context', state.context);
  fd.set('jobDescriptionText', state.jobDescriptionText);

  state.resumeFiles.forEach(({ file }) => {
    fd.append('resumeFiles', file, file.name);
  });

  state.jobDescriptionFiles.forEach(({ file }) => {
    fd.append('jobDescriptionFiles', file, file.name);
  });

  return fd;
}

export function downloadBlobAsFile(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function openBlobInNewTab(blob: Blob) {
  const url = URL.createObjectURL(blob);
  window.open(url, '_blank', 'noopener');
  setTimeout(() => URL.revokeObjectURL(url), 1000 * 30);
}

export function validateState(state: FormState) {
  const payload = {
    mode: state.mode,
    resumeText: state.resumeText,
    context: state.context,
    jobDescriptionText: state.jobDescriptionText,
    resumeFiles: state.resumeFiles.map((item) => item.file),
    jobDescriptionFiles: state.jobDescriptionFiles.map((item) => item.file)
  };

  return formDataSchema.safeParse(payload);
}

export function remainingCharacters(value: string): number {
  return Math.max(0, MAX_TEXTAREA_LENGTH - value.length);
}

export function totalLimitForLabel(files: UploadedFile[]): string {
  return `${formatBytes(totalBytes(files))} / ${formatBytes(GROUP_MAX_BYTES)}`;
}

export function computeKeywordPreview(text: string): KeywordPreviewItem[] {
  const tokens = text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter((token) => token.length > 3);

  const counts = new Map<string, number>();
  for (const token of tokens) {
    counts.set(token, (counts.get(token) ?? 0) + 1);
  }

  return Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 25)
    .map(([value, count]) => ({ value, count }));
}
