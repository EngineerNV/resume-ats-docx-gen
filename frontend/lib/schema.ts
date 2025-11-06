import { z } from 'zod';

export const MAX_TEXTAREA_LENGTH = 20_000;
export const RESUME_ALLOWED_MIME = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/msword',
  'text/plain',
  'text/markdown'
] as const;
export const JOB_ALLOWED_MIME = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
  'text/html'
] as const;

export const RESUME_MAX_FILES = 5;
export const JOB_MAX_FILES = 3;
export const GROUP_MAX_BYTES = 10 * 1024 * 1024; // 10 MB

type NamedBlob = Blob & { name?: string };

const blobSchema = z
  .instanceof(Blob)
  .refine((file) => {
    const candidate = file as NamedBlob;
    return typeof candidate.name === 'string' && candidate.name.length > 0;
  }, 'File must include a name')
  .refine((file) => typeof file.size === 'number' && file.size >= 0, 'File size missing');

type FileKind = 'resume' | 'job';

function createFileSchema(kind: FileKind) {
  const allowed = (kind === 'resume' ? RESUME_ALLOWED_MIME : JOB_ALLOWED_MIME) as readonly string[];
  return blobSchema.superRefine((file, ctx) => {
    if (file.size > GROUP_MAX_BYTES) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Individual files must be smaller than 10 MB.'
      });
    }
    if (file.type && !allowed.includes(file.type)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Unsupported file type.'
      });
    }
  });
}

export const resumeFileSchema = createFileSchema('resume');
export const jobFileSchema = createFileSchema('job');

export const formDataSchema = z
  .object({
    mode: z.enum(['resume', 'job_tuning']),
    resumeText: z.string().max(MAX_TEXTAREA_LENGTH).optional().default(''),
    context: z.string().max(MAX_TEXTAREA_LENGTH).optional().default(''),
    jobDescriptionText: z.string().max(MAX_TEXTAREA_LENGTH).optional().default(''),
    resumeFiles: z.array(resumeFileSchema).max(RESUME_MAX_FILES).default([]),
    jobDescriptionFiles: z.array(jobFileSchema).max(JOB_MAX_FILES).default([])
  })
  .superRefine((values, ctx) => {
    const hasResumeInput = values.resumeText.trim().length > 0 || values.resumeFiles.length > 0;
    if (!hasResumeInput) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Provide resume text or upload at least one resume file.',
        path: ['resumeText']
      });
    }

    const resumeBytes = values.resumeFiles.reduce((total, file) => total + file.size, 0);
    if (resumeBytes > GROUP_MAX_BYTES) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Resume files exceed the 10 MB combined limit.',
        path: ['resumeFiles']
      });
    }

    const jobBytes = values.jobDescriptionFiles.reduce((total, file) => total + file.size, 0);
    if (jobBytes > GROUP_MAX_BYTES) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Job description files exceed the 10 MB combined limit.',
        path: ['jobDescriptionFiles']
      });
    }

    if (values.mode === 'job_tuning') {
      const hasJobInput =
        values.jobDescriptionText.trim().length > 0 || values.jobDescriptionFiles.length > 0;
      if (!hasJobInput) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Provide a job description or upload related files for job tuning mode.',
          path: ['jobDescriptionText']
        });
      }
    }
  });

export type ValidatedFormData = z.infer<typeof formDataSchema>;
