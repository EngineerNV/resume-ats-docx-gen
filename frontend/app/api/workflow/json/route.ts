import { NextResponse } from 'next/server';
import suggestionsMock from '../../../../mocks/suggestions.json';
import { formDataSchema, ValidatedFormData } from '../../../../lib/schema';
import { ZodError } from 'zod';
import type { SafeParseReturnType } from 'zod';

const USE_MOCK = process.env.USE_MOCK !== 'false';
const PY_WORKFLOW_JSON_URL = process.env.PY_WORKFLOW_JSON_URL;

type SuggestionsResponse = typeof suggestionsMock;

function isFile(value: unknown): value is File {
  return typeof File !== 'undefined' && value instanceof File;
}

function mapErrors(error: unknown) {
  if (error && typeof error === 'object' && 'issues' in error) {
    const issues = (error as any).issues as { path: (string | number)[]; message: string }[];
    const fieldErrors: Record<string, string[]> = {};
    issues.forEach((issue) => {
      const key = issue.path[0] ? String(issue.path[0]) : 'form';
      if (!fieldErrors[key]) {
        fieldErrors[key] = [];
      }
      fieldErrors[key].push(issue.message);
    });
    return fieldErrors;
  }
  return undefined;
}

function toProxyFormData(data: ValidatedFormData) {
  const formData = new FormData();
  formData.set('mode', data.mode);
  formData.set('resumeText', data.resumeText ?? '');
  formData.set('context', data.context ?? '');
  formData.set('jobDescriptionText', data.jobDescriptionText ?? '');
  data.resumeFiles.forEach((file) => formData.append('resumeFiles', file, isFile(file) ? file.name : 'resume'));
  data.jobDescriptionFiles.forEach((file) => formData.append('jobDescriptionFiles', file, isFile(file) ? file.name : 'job'));
  return formData;
}

type FormValidationResult = SafeParseReturnType<unknown, ValidatedFormData>;

// Accept either multipart form-data or JSON payloads, mirroring the flexibility
// of the real Python backend. Every path funnels into the shared Zod schema so
// downstream logic can rely on a consistent shape.
async function parseRequest(request: Request): Promise<FormValidationResult> {
  const contentType = request.headers.get('content-type') ?? '';
  if (contentType.includes('multipart/form-data')) {
    const formData = await request.formData();
    const payload = {
      mode: String(formData.get('mode') ?? 'resume'),
      resumeText: String(formData.get('resumeText') ?? ''),
      context: String(formData.get('context') ?? ''),
      jobDescriptionText: String(formData.get('jobDescriptionText') ?? ''),
      resumeFiles: formData.getAll('resumeFiles').filter(isFile),
      jobDescriptionFiles: formData.getAll('jobDescriptionFiles').filter(isFile)
    };
    return formDataSchema.safeParse(payload);
  }

  try {
    const body = await request.json();
    return formDataSchema.safeParse({
      mode: body.mode,
      resumeText: body.resumeText ?? '',
      context: body.context ?? '',
      jobDescriptionText: body.jobDescriptionText ?? '',
      resumeFiles: Array.isArray(body.resumeFiles) ? body.resumeFiles : [],
      jobDescriptionFiles: Array.isArray(body.jobDescriptionFiles) ? body.jobDescriptionFiles : []
    });
  } catch (error) {
    return {
      success: false,
      error: new ZodError([
        {
          code: 'custom',
          path: ['form'],
          message: 'Invalid JSON payload.'
        }
      ])
    };
  }
}

export async function POST(request: Request) {
  const validation = await parseRequest(request);
  if (!validation.success) {
    return NextResponse.json(
      { ok: false, code: 'VALIDATION_ERROR', fieldErrors: mapErrors(validation.error) },
      { status: 400 }
    );
  }

  const data = validation.data;

  if (USE_MOCK || !PY_WORKFLOW_JSON_URL) {
    return NextResponse.json({ ok: true, data: suggestionsMock as SuggestionsResponse }, { status: 200 });
  }

  const proxyFormData = toProxyFormData(data);
  const headers = new Headers();
  const idempotencyKey = request.headers.get('x-idempotency-key');
  if (idempotencyKey) {
    headers.set('x-idempotency-key', idempotencyKey);
  }

  try {
    const response = await fetch(PY_WORKFLOW_JSON_URL, {
      method: 'POST',
      body: proxyFormData,
      headers,
      cache: 'no-store'
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      return NextResponse.json(
        {
          ok: false,
          code: 'UPSTREAM_ERROR',
          message: payload?.message ?? 'Backend service error.',
          fieldErrors: payload?.fieldErrors
        },
        { status: response.status }
      );
    }

    const payload = await response.json();
    return NextResponse.json({ ok: true, data: payload }, { status: 200 });
  } catch (error) {
    return NextResponse.json(
      { ok: false, code: 'NETWORK_ERROR', message: 'Failed to reach workflow service.' },
      { status: 502 }
    );
  }
}
