'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useTheme } from 'next-themes';
import type { Accept } from 'react-dropzone';
import { ModeSlider } from '../components/ModeSlider';
import { TextSection } from '../components/TextSection';
import { FileDropzone } from '../components/FileDropzone';
import { StepIndicator, type StepState } from '../components/StepIndicator';
import { PayloadPreview } from '../components/PayloadPreview';
import { SubmitButtons } from '../components/SubmitButtons';
import { GROUP_MAX_BYTES, JOB_MAX_FILES, MAX_TEXTAREA_LENGTH, RESUME_MAX_FILES } from '../lib/schema';
import { buildFormData, computeKeywordPreview, downloadBlobAsFile, openBlobInNewTab, validateState } from
  '../lib/utils';
import type { FormState, KeywordPreviewItem, UploadedFile } from '../lib/types';

const RESUME_ACCEPT: Accept = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
  'text/markdown': ['.md']
};

const JOB_ACCEPT: Accept = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
  'text/html': ['.html']
};

const KEYWORD_FLAG = process.env.NEXT_PUBLIC_ENABLE_KEYWORDS === 'true';

// Ordered descriptors for the wizard UI. The combination of label + description
// drives the StepIndicator component as well as the validation gate that limits
// forward navigation until inputs are considered valid.
const STEP_DEFINITIONS = [
  { label: 'Inputs', description: 'Resume & optional job description' },
  { label: 'Review', description: 'Confirm text and files' },
  { label: 'Submit', description: 'Build a DOCX resume' }
];

// Represents the default client-side form payload. Having a single reference
// helps when we need to reset back to pristine data after a submission.
const INITIAL_STATE: FormState = {
  mode: 'resume',
  resumeText: '',
  resumeFiles: [],
  context: '',
  jobDescriptionText: '',
  jobDescriptionFiles: []
};

interface StatusMessage {
  type: 'success' | 'error' | 'info';
  message: string;
}

export default function HomePage() {
  // -- State orchestration --------------------------------------------------
  // We store individual slices of form data instead of a reducer so that
  // React DevTools remains easy to inspect and the code reads linearly.
  const [state, setState] = useState<FormState>(INITIAL_STATE);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [status, setStatus] = useState<StatusMessage | null>(null);
  const [loadingAction, setLoadingAction] = useState<'docx' | null>(null);
  // suggestions UI removed: we keep backend endpoint but no longer surface suggestions in the UI
  const [docxPreviewUrl, setDocxPreviewUrl] = useState<string | null>(null);
  const [docxFilename, setDocxFilename] = useState<string>('');
  const abortRef = useRef<AbortController | null>(null);
  const docxBlobRef = useRef<Blob | null>(null);
  const createIdempotencyKey = () =>
    typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [themeMounted, setThemeMounted] = useState(false);

  // Revoke any object URLs we create to avoid leaking resources when the user
  // leaves the page or when a new preview replaces the old one.
  useEffect(() => {
    return () => {
      if (docxPreviewUrl) {
        URL.revokeObjectURL(docxPreviewUrl);
      }
    };
  }, [docxPreviewUrl]);

  useEffect(() => {
    setThemeMounted(true);
  }, []);

  // Derive UI metadata for the stepper. We memoize so the StepIndicator only
  // re-renders when the current index changes rather than on every keystroke.
  const steps: StepState[] = useMemo(
    () =>
      STEP_DEFINITIONS.map((step, index) => ({
        ...step,
        status: index < currentStep ? 'complete' : index === currentStep ? 'current' : 'upcoming',
        disabled: index > currentStep
      })),
    [currentStep]
  );

  // Compute lightweight keyword summaries when the optional feature flag is
  // enabled. The helper deduplicates words and normalizes casing.
  const keywordPreview: KeywordPreviewItem[] = useMemo(() => {
    if (!KEYWORD_FLAG) return [];
    const combined = `${state.resumeText}\n${state.context}\n${state.jobDescriptionText}`;
    return computeKeywordPreview(combined);
  }, [state.resumeText, state.context, state.jobDescriptionText]);

  // When an individual field changes we clear the corresponding validation
  // message. This keeps the UI honest without needing a dedicated reducer.
  const updateState = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setState((prev) => ({ ...prev, [key]: value }));
    setFieldErrors((prev) => {
      if (!prev[key as string]) return prev;
      const { [key as string]: _removed, ...rest } = prev;
      return rest;
    });
  };

  const handleFilesChange = (key: 'resumeFiles' | 'jobDescriptionFiles') => (files: UploadedFile[]) => {
    setState((prev) => ({ ...prev, [key]: files }));
    setFieldErrors((prev) => {
      if (!prev[key]) return prev;
      const { [key]: _removed, ...rest } = prev;
      return rest;
    });
  };

  // Executes the shared zod validation. When invalid we set inline error
  // messages and return null so callers can branch early.
  const runValidation = () => {
    const result = validateState(state);
    if (!result.success) {
      const nextErrors: Record<string, string> = {};
      result.error.issues.forEach((issue) => {
        const path = issue.path[0] as string | undefined;
        const key = path ?? 'form';
        if (!nextErrors[key]) {
          nextErrors[key] = issue.message;
        }
      });
      setFieldErrors(nextErrors);
      setStatus({ type: 'error', message: 'Please resolve the highlighted issues before continuing.' });
      return null;
    }

    setFieldErrors({});
    return result.data;
  };

  const goToStep = (index: number) => {
    if (index < currentStep) {
      setCurrentStep(index);
    }
  };

  // Move forward only when validation succeeds. Validation errors push the user
  // back to the input step so they can resolve issues immediately.
  const handleNext = () => {
    const valid = runValidation();
    if (!valid) {
      return;
    }
    setCurrentStep((prev) => Math.min(prev + 1, STEP_DEFINITIONS.length - 1));
    setStatus(null);
  };

  const handleBack = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  };

  const handleModeChange = (mode: FormState['mode']) => {
    updateState('mode', mode);
    if (mode === 'resume') {
      // Clear job-specific validation errors when leaving job mode.
      setFieldErrors((prev) => {
        const { jobDescriptionText, jobDescriptionFiles, ...rest } = prev;
        return rest;
      });
    }
  };

  const resetDocxPreview = () => {
    if (docxPreviewUrl) {
      URL.revokeObjectURL(docxPreviewUrl);
      setDocxPreviewUrl(null);
    }
    docxBlobRef.current = null;
  };

  const resetAbort = () => {
    abortRef.current?.abort();
    abortRef.current = null;
  };

  const resetForm = () => {
    resetAbort();
    resetDocxPreview();
    setState(INITIAL_STATE);
    setCurrentStep(0);
    setFieldErrors({});
    setStatus(null);
    setLoadingAction(null);
    setDocxFilename('');
  };

  // suggestion flow removed from UI.

  // DOCX download mirrors the JSON path but additionally captures the Blob so
  // the user can preview in another tab if desired.
  const submitDocx = async () => {
    const valid = runValidation();
    if (!valid) {
      setCurrentStep(0);
      return;
    }
    setCurrentStep(2);
    resetAbort();
    resetDocxPreview();
    setLoadingAction('docx');
    setStatus({ type: 'info', message: 'Running AI optimization and generating DOCX…' });
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const response = await fetch('http://localhost:8000/api/workflow/docx', {
        method: 'POST',
        body: buildFormData(state),
        cache: 'no-store',
        signal: controller.signal,
        headers: {
          'X-Idempotency-Key': createIdempotencyKey()
        }
      });

      if (!response.ok) {
        let message = 'Unable to generate DOCX.';
        try {
          const payload = await response.json();
          message = payload?.message ?? message;
          if (payload?.fieldErrors) {
            const normalized = Object.fromEntries(
              Object.entries(payload.fieldErrors as Record<string, unknown>).map(([key, val]) => [
                key,
                Array.isArray(val) && typeof val[0] === 'string' ? val[0] : 'Please review this field.'
              ])
            );
            setFieldErrors(normalized);
          }
        } catch (jsonError) {
          // response not JSON; ignore
        }
        setStatus({ type: 'error', message });
        return;
      }

      const blob = await response.blob();
      docxBlobRef.current = blob;
      
      // Get filename from content-disposition header (lowercase for compatibility)
      const contentDisposition = response.headers.get('content-disposition');
      if (process.env.NODE_ENV !== 'production') {
        // Log header value for debugging in Next.js (client-side)
        console.log('[DOCX] content-disposition header:', contentDisposition);
      }
      const match = contentDisposition?.match(/filename="(.+)"/);
      const filename = match ? match[1] : 'resume.docx';
      setDocxFilename(filename);
      
      // Get PDF filename from custom header
      // We no longer generate PDFs; ignore any PDF headers and only handle DOCX.
      
      const objectUrl = URL.createObjectURL(blob);
      setDocxPreviewUrl(objectUrl);
      downloadBlobAsFile(blob, filename);
  setStatus({ type: 'success', message: `✅ DOCX downloaded: ${filename}.` });
    } catch (error) {
      if ((error as DOMException).name === 'AbortError') {
        setStatus({ type: 'info', message: 'Request cancelled.' });
      } else {
        setStatus({ type: 'error', message: 'A network error occurred. Please try again.' });
      }
    } finally {
      setLoadingAction(null);
      abortRef.current = null;
    }
  };

  // Give users an escape hatch when the upstream request stalls.
  const cancelInFlight = () => {
    if (abortRef.current) {
      abortRef.current.abort();
    }
  };

  const currentTheme = themeMounted ? (theme === 'system' ? resolvedTheme : theme) : 'light';
  const toggleTheme = () => {
    if (!themeMounted) return;
    setTheme(currentTheme === 'dark' ? 'light' : 'dark');
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-10 px-4 py-10 sm:px-6 lg:px-8">
      <div className="flex justify-end">
        <button
          type="button"
          onClick={toggleTheme}
          className="flex items-center gap-2 rounded-full border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          <span role="img" aria-hidden="true">
            {currentTheme === 'dark' ? '🌙' : '☀️'}
          </span>
          {currentTheme === 'dark' ? 'Dark mode' : 'Light mode'}
        </button>
      </div>

      <header className="space-y-4 text-center">
        <div className="mx-auto flex items-center justify-center">
          <img 
        src="/baileyproject.png" 
        alt="Bailey Project Logo" 
        className="h-52 w-64 object-cover"
          />
        </div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Ask Bailey</h1>
        <p className="mx-auto max-w-2xl text-balance text-sm text-slate-600 dark:text-slate-300">
          Tech Resume's built from the inspiration of UOP's Best Career Resource.
          <br />
          Created with Multi-Agent Architecture - to help college students and professionals for free.
          
        </p>
      </header>

      <StepIndicator steps={steps} onStepSelect={goToStep} />

      <section className="space-y-8">
        {currentStep === 0 && (
          <div className="space-y-6">
            <ModeSlider value={state.mode} onChange={handleModeChange} />

            <TextSection
              id="resumeText"
              label="Resume text"
              value={state.resumeText}
              onChange={(value) => updateState('resumeText', value)}
              description="Paste your current resume or key bullet points."
              placeholder="Paste resume content or leave blank if uploading files."
              maxLength={MAX_TEXTAREA_LENGTH}
              error={fieldErrors.resumeText}
            />

            <FileDropzone
              label="Resume files"
              description="Upload up to 5 files (.pdf, .docx, .doc, .txt, .md)."
              accept={RESUME_ACCEPT}
              maxFiles={RESUME_MAX_FILES}
              maxTotalBytes={GROUP_MAX_BYTES}
              files={state.resumeFiles}
              onFilesChange={handleFilesChange('resumeFiles')}
              externalError={fieldErrors.resumeFiles}
            />

            <TextSection
              id="context"
              label="Optional context"
              value={state.context}
              onChange={(value) => updateState('context', value)}
              description="Share goals, accomplishments, or constraints for more tailored outputs."
              placeholder="e.g. Focus on data leadership, highlight cloud migrations, mention remote readiness."
              maxLength={MAX_TEXTAREA_LENGTH}
              error={fieldErrors.context}
              rows={6}
            />

            {state.mode === 'job_tuning' && (
              <div className="space-y-6">
                <TextSection
                  id="jobDescriptionText"
                  label="Job description"
                  value={state.jobDescriptionText}
                  onChange={(value) => updateState('jobDescriptionText', value)}
                  description="Paste the job post or recruiter notes to align the resume."
                  placeholder="Paste job description text or upload files below."
                  maxLength={MAX_TEXTAREA_LENGTH}
                  error={fieldErrors.jobDescriptionText}
                />

                <FileDropzone
                  label="Job description files"
                  description="Upload up to 3 files (.pdf, .docx, .txt, .html)."
                  accept={JOB_ACCEPT}
                  maxFiles={JOB_MAX_FILES}
                  maxTotalBytes={GROUP_MAX_BYTES}
                  files={state.jobDescriptionFiles}
                  onFilesChange={handleFilesChange('jobDescriptionFiles')}
                  externalError={fieldErrors.jobDescriptionFiles}
                />
              </div>
            )}

            <div className="flex items-center justify-between">
              {fieldErrors.form && <p className="text-sm text-rose-600">{fieldErrors.form}</p>}
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={handleNext}
                  className="rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-brand/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-slate-950"
                >
                  Continue to review
                </button>
              </div>
            </div>
          </div>
        )}

        {currentStep === 1 && (
          <div className="space-y-6">
            <PayloadPreview
              state={state}
              onRemoveResumeFile={(id) => handleFilesChange('resumeFiles')(state.resumeFiles.filter((file) => file.id !== id))}
              onRemoveJobFile={(id) =>
                handleFilesChange('jobDescriptionFiles')(state.jobDescriptionFiles.filter((file) => file.id !== id))
              }
              showKeywordPreview={KEYWORD_FLAG}
              keywords={keywordPreview}
            />

            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={handleBack}
                className="rounded-full border border-slate-200 px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand dark:border-slate-700 dark:text-slate-200"
              >
                Back to inputs
              </button>
              <button
                type="button"
                onClick={handleNext}
                className="rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-brand/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-slate-950"
              >
                Continue to submit
              </button>
            </div>
          </div>
        )}

        {currentStep === 2 && (
          <div className="space-y-6">
            <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Submit</h2>
              <p className="text-sm text-slate-600 dark:text-slate-300">
                Send your inputs to build a DOCX resume. Requests run locally first and proxy to the backend service when available.
              </p>
              <SubmitButtons onBuildResume={submitDocx} loadingAction={loadingAction} disabled={loadingAction !== null} />
              {loadingAction && (
                <button
                  type="button"
                  onClick={cancelInFlight}
                  className="text-xs font-semibold text-rose-600 underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500"
                >
                  Cancel current request
                </button>
              )}
            </div>

            {status && (
              <div
                role="status"
                className={`rounded-2xl border px-4 py-3 text-sm shadow-sm ${
                  status.type === 'success'
                    ? 'border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/50 dark:bg-emerald-500/10 dark:text-emerald-200'
                    : status.type === 'error'
                    ? 'border-rose-300 bg-rose-50 text-rose-700 dark:border-rose-500/50 dark:bg-rose-500/10 dark:text-rose-200'
                    : 'border-slate-200 bg-slate-100 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200'
                }`}
              >
                {status.message}
              </div>
            )}

            {/* Suggestions UI removed */}

            {docxPreviewUrl && (
              <section className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">✅ Resume Generated!</h3>
                <p className="text-sm text-slate-600 dark:text-slate-300">
                  DOCX: <span className="font-mono text-xs">{docxFilename}</span>
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Your DOCX is ready. Use the buttons below to download or open it.
                </p>
                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => docxBlobRef.current && downloadBlobAsFile(docxBlobRef.current, docxFilename)}
                    className="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-slate-950"
                  >
                    📥 Download DOCX again
                  </button>
                  {/* PDF previews disabled: we return DOCX only. */}
                </div>
              </section>
            )}

            <div className="flex justify-start">
              <button
                type="button"
                onClick={() => setCurrentStep(1)}
                className="rounded-full border border-slate-200 px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand dark:border-slate-700 dark:text-slate-200"
              >
                Back to review
              </button>
            </div>
          </div>
        )}
      </section>
      
      <div className="mt-10">
        <button
          type="button"
          onClick={resetForm}
          className="w-full rounded-full border border-slate-200 px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand dark:border-slate-700 dark:text-slate-200"
        >
          Restart
        </button>
      </div>

      {/* PDF preview disabled - DOCX only response */}
    </main>
  );
}
