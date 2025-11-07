'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import type { Accept } from 'react-dropzone';
import { ModeSlider } from '../components/ModeSlider';
import { TextSection } from '../components/TextSection';
import { FileDropzone } from '../components/FileDropzone';
import { StepIndicator, type StepState } from '../components/StepIndicator';
import { PayloadPreview } from '../components/PayloadPreview';
import { SubmitButtons } from '../components/SubmitButtons';
import LoadingSpinner from '../components/LoadingSpinner';
import PdfPreview from '../components/PdfPreview';
import { GROUP_MAX_BYTES, JOB_MAX_FILES, MAX_TEXTAREA_LENGTH, RESUME_MAX_FILES } from '../lib/schema';
import {
  buildFormData,
  computeKeywordPreview,
  downloadBlobAsFile,
  openBlobInNewTab,
  validateState
} from '../lib/utils';
import type { FormState, KeywordPreviewItem, SuggestionPayload, UploadedFile } from '../lib/types';

const RESUME_ACCEPT: Accept = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/msword': ['.doc'],
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
  { label: 'Submit', description: 'Generate suggestions or DOCX' }
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
  const [loadingAction, setLoadingAction] = useState<'json' | 'docx' | null>(null);
  const [jsonResult, setJsonResult] = useState<SuggestionPayload | null>(null);
  const [docxPreviewUrl, setDocxPreviewUrl] = useState<string | null>(null);
  const [docxFilename, setDocxFilename] = useState<string>('');
  const [pdfFilename, setPdfFilename] = useState<string>('');
  const [showPdfPreview, setShowPdfPreview] = useState<boolean>(false);
  const abortRef = useRef<AbortController | null>(null);
  const docxBlobRef = useRef<Blob | null>(null);
  const createIdempotencyKey = () =>
    typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

  // Revoke any object URLs we create to avoid leaking resources when the user
  // leaves the page or when a new preview replaces the old one.
  useEffect(() => {
    return () => {
      if (docxPreviewUrl) {
        URL.revokeObjectURL(docxPreviewUrl);
      }
    };
  }, [docxPreviewUrl]);

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

  // Full JSON suggestion flow: validate, POST to API, surface success/errors,
  // and persist the response so the UI can render the panel below.
  const submitJson = async () => {
    const valid = runValidation();
    if (!valid) {
      setCurrentStep(0);
      return;
    }
    setCurrentStep(2);
    resetAbort();
    setLoadingAction('json');
    setStatus({ type: 'info', message: 'Sending data for suggestions…' });
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const response = await fetch('/api/workflow/json', {
        method: 'POST',
        body: buildFormData(state),
        cache: 'no-store',
        signal: controller.signal,
        headers: {
          'X-Idempotency-Key': createIdempotencyKey()
        }
      });

      const payload = await response.json();
      if (!response.ok || !payload.ok) {
        const message = payload?.message ?? 'Unable to fetch suggestions.';
        if (payload?.fieldErrors) {
          const normalized = Object.fromEntries(
            Object.entries(payload.fieldErrors as Record<string, unknown>).map(([key, val]) => [
              key,
              Array.isArray(val) && typeof val[0] === 'string' ? val[0] : 'Please review this field.'
            ])
          );
          setFieldErrors(normalized);
        }
        setStatus({ type: 'error', message });
        setJsonResult(null);
        return;
      }

      setJsonResult(payload.data as SuggestionPayload);
      setStatus({ type: 'success', message: 'Suggestions ready below.' });
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
      
      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      const filename = contentDisposition?.match(/filename="(.+)"/)?.[1] || 'resume.docx';
      setDocxFilename(filename);
      
      // Get PDF filename from custom header
      const pdfName = response.headers.get('X-PDF-Filename');
      if (pdfName) {
        setPdfFilename(pdfName);
      }
      
      const objectUrl = URL.createObjectURL(blob);
      setDocxPreviewUrl(objectUrl);
      downloadBlobAsFile(blob, filename);
      setStatus({ type: 'success', message: `✅ DOCX downloaded: ${filename}. PDF conversion started in background.` });
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

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-10 px-4 py-10 sm:px-6 lg:px-8">
      <header className="space-y-4 text-center">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Resume Workflow</h1>
        <p className="mx-auto max-w-2xl text-balance text-sm text-slate-600 dark:text-slate-300">
          Collect resume details, optionally include a job description, review the payload, then request AI-powered suggestions or
          download a DOCX you can submit immediately.
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
                Send your inputs to receive structured AI suggestions or to download a refreshed DOCX resume. Requests run locally first
                and proxy to the backend service when available.
              </p>
              <SubmitButtons
                onGetSuggestions={submitJson}
                onDownloadDocx={submitDocx}
                loadingAction={loadingAction}
                disabled={loadingAction !== null}
              />
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

            {jsonResult && (
              <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <header>
                  <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Suggestion summary</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Quick insights tailored to your inputs.</p>
                </header>
                <article className="space-y-4">
                  <div>
                    <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Summary</h4>
                    <p className="whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-200">{jsonResult.summary}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Highlights</h4>
                    <ul className="space-y-2 text-sm text-slate-700 dark:text-slate-200" role="list">
                      {jsonResult.highlights.map((item) => (
                        <li key={item} className="rounded-xl bg-slate-100 px-3 py-2 dark:bg-slate-800/70">
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Recommendations</h4>
                    <ul className="space-y-2 text-sm text-slate-700 dark:text-slate-200" role="list">
                      {jsonResult.recommendations.map((item) => (
                        <li key={item} className="rounded-xl bg-brand/10 px-3 py-2 text-brand dark:bg-brand/20 dark:text-brand-dark">
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                </article>
              </section>
            )}

            {docxPreviewUrl && (
              <section className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">✅ Resume Generated!</h3>
                <p className="text-sm text-slate-600 dark:text-slate-300">
                  DOCX: <span className="font-mono text-xs">{docxFilename}</span>
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  PDF conversion started in background. Click preview to check status.
                </p>
                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => docxBlobRef.current && downloadBlobAsFile(docxBlobRef.current, docxFilename)}
                    className="rounded-full bg-brand px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-slate-950"
                  >
                    📥 Download DOCX again
                  </button>
                  <button
                    type="button"
                    onClick={() => docxBlobRef.current && openBlobInNewTab(docxBlobRef.current)}
                    className="rounded-full border border-brand px-5 py-2 text-sm font-semibold text-brand hover:bg-brand/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:text-brand-dark dark:focus-visible:ring-offset-slate-950"
                  >
                    🔗 Open DOCX in Tab
                  </button>
                  {pdfFilename && (
                    <button
                      type="button"
                      onClick={() => setShowPdfPreview(true)}
                      className="rounded-full bg-blue-600 px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-slate-950"
                    >
                      👁️ Preview PDF
                    </button>
                  )}
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
      
      {/* PDF Preview Modal */}
      {showPdfPreview && pdfFilename && (
        <PdfPreview
          pdfFilename={pdfFilename}
          onClose={() => setShowPdfPreview(false)}
        />
      )}
    </main>
  );
}
