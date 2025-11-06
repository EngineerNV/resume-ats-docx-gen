export type Mode = 'resume' | 'job_tuning';

export interface UploadedFile {
  id: string;
  file: File;
}

export interface FormState {
  mode: Mode;
  resumeText: string;
  resumeFiles: UploadedFile[];
  context: string;
  jobDescriptionText: string;
  jobDescriptionFiles: UploadedFile[];
}

export interface FieldError {
  field: string;
  message: string;
}

export interface WorkflowResponse<T> {
  ok: boolean;
  data?: T;
  code?: string;
  fieldErrors?: Record<string, string[]>;
  message?: string;
}

export interface SuggestionPayload {
  summary: string;
  highlights: string[];
  recommendations: string[];
}

export interface KeywordPreviewItem {
  value: string;
  count: number;
}
