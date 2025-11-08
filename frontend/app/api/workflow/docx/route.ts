import { NextResponse } from 'next/server';
import { Document, Packer, Paragraph, TextRun } from 'docx';
import { formDataSchema, ValidatedFormData, NamedBlob } from '../../../../lib/schema';

export const runtime = 'nodejs';

const USE_MOCK = process.env.USE_MOCK !== 'false';
const PY_WORKFLOW_DOCX_URL = process.env.PY_WORKFLOW_DOCX_URL;

function isFile(value: unknown): value is File {
  return typeof File !== 'undefined' && value instanceof File;
}

function toProxyFormData(data: ValidatedFormData) {
  const formData = new FormData();
  formData.set('mode', data.mode);
  formData.set('resumeText', data.resumeText ?? '');
  formData.set('context', data.context ?? '');
  formData.set('jobDescriptionText', data.jobDescriptionText ?? '');
  (data.resumeFiles as File[]).forEach((file) => formData.append('resumeFiles', file, file.name ?? 'resume'));
  (data.jobDescriptionFiles as File[]).forEach((file) => formData.append('jobDescriptionFiles', file, file.name ?? 'job'));
  return formData;
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

async function parseForm(request: Request) {
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

export async function POST(request: Request) {
  const contentType = request.headers.get('content-type') ?? '';
  if (!contentType.includes('multipart/form-data')) {
    return NextResponse.json(
      { ok: false, code: 'UNSUPPORTED_MEDIA_TYPE', message: 'Use multipart/form-data for DOCX generation.' },
      { status: 415 }
    );
  }

  const validation = await parseForm(request);
  if (!validation.success) {
    return NextResponse.json(
      { ok: false, code: 'VALIDATION_ERROR', fieldErrors: mapErrors(validation.error) },
      { status: 400 }
    );
  }

  const data = validation.data;
  // Log runtime mode to help debug whether we're using the mock branch or proxy
  console.log('[workflow/docx] USE_MOCK=', USE_MOCK, 'PY_WORKFLOW_DOCX_URL=', PY_WORKFLOW_DOCX_URL);

  // Basic payload summary for debugging (don't log full resume text in prod)
  console.log('[workflow/docx] payload summary:', {
    mode: data.mode,
    resumeTextLength: data.resumeText ? data.resumeText.length : 0,
    contextLength: data.context ? data.context.length : 0,
    jobDescriptionTextLength: data.jobDescriptionText ? data.jobDescriptionText.length : 0,
    resumeFiles: (data.resumeFiles as File[]).map((f) => (f as NamedBlob).name ?? 'unnamed'),
    jobDescriptionFiles: (data.jobDescriptionFiles as File[]).map((f) => (f as NamedBlob).name ?? 'unnamed')
  });

  if (USE_MOCK || !PY_WORKFLOW_DOCX_URL) {
    // Generate a lightweight DOCX on the fly so the mock flow remains binary-compatible
    // without needing to ship a static artifact in the repository.
    const buffer = await createMockDocx(data);
    console.log('[workflow/docx] returning mock DOCX (filename=resume.docx, size=', buffer.byteLength, ')');
    // Next/Edge runtime expects BodyInit-compatible types; convert Node Buffer -> ArrayBuffer
    const arrayBuffer = buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
    const uint8 = new Uint8Array(arrayBuffer);
    // Cast to any to satisfy NextResponse typing in the Node.js runtime environment
    return new NextResponse(uint8 as any, {
      status: 200,
      headers: {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'Content-Disposition': 'attachment; filename="resume.docx"',
        'Cache-Control': 'no-store'
      }
    });
  }

  const proxyFormData = toProxyFormData(data);
  const headers = new Headers();
  const idempotencyKey = request.headers.get('x-idempotency-key');
  if (idempotencyKey) {
    headers.set('x-idempotency-key', idempotencyKey);
  }

  try {
    const response = await fetch(PY_WORKFLOW_DOCX_URL, {
      method: 'POST',
      body: proxyFormData,
      headers,
      cache: 'no-store'
    });

    if (!response.ok || !response.body) {
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
    // Log upstream response info to help debugging filename/header issues
    console.log('[workflow/docx] upstream response status=', response.status);
    try {
      console.log('[workflow/docx] upstream Content-Disposition=', response.headers.get('Content-Disposition'));
      console.log('[workflow/docx] upstream Content-Type=', response.headers.get('Content-Type'));
    } catch (err) {
      console.warn('[workflow/docx] failed reading upstream headers', err);
    }

    const headersOut = new Headers(response.headers);
    // Ensure we always have a Content-Disposition; prefer upstream if present
    const upstreamCD = headersOut.get('Content-Disposition');
    if (upstreamCD) {
      headersOut.set('Content-Disposition', upstreamCD);
    } else {
      headersOut.set('Content-Disposition', 'attachment; filename="resume.docx"');
    }

    headersOut.set('Cache-Control', 'no-store');
    headersOut.set('Content-Type',
      headersOut.get('Content-Type') ?? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    );

    console.log('[workflow/docx] returning proxied response with headers:', {
      'Content-Disposition': headersOut.get('Content-Disposition'),
      'Content-Type': headersOut.get('Content-Type'),
      'Status': response.status
    });

    return new NextResponse(response.body, {
      status: response.status,
      headers: headersOut
    });
  } catch (error) {
    console.error('[workflow/docx] network error when proxying to PY_WORKFLOW_DOCX_URL=', PY_WORKFLOW_DOCX_URL, error);
    return NextResponse.json(
      { ok: false, code: 'NETWORK_ERROR', message: 'Failed to reach workflow service.' },
      { status: 502 }
    );
  }
}

/**
 * Builds a minimal DOCX document that reflects the incoming payload.
 * The goal is to mimic the real download surface area (binary stream, headers)
 * while keeping the mock fully deterministic and source-controlled.
 */
async function createMockDocx(data: ValidatedFormData) {
  const resumePreview = data.resumeText?.slice(0, 200) || 'No resume text provided.';
  const jobPreview = data.jobDescriptionText?.slice(0, 200) || 'No job description provided.';
  const contextPreview = data.context?.slice(0, 200) || 'No additional context provided.';

  const resumeFileParagraphs =
    data.resumeFiles.length === 0
      ? [new Paragraph({ text: 'None provided', bullet: { level: 0 } })]
      : data.resumeFiles.map(
          (file) => new Paragraph({ text: (file as NamedBlob).name ?? 'unnamed file', bullet: { level: 0 } })
        );

  const jobFileParagraphs =
    data.jobDescriptionFiles.length === 0
      ? [new Paragraph({ text: 'None provided', bullet: { level: 0 } })]
      : data.jobDescriptionFiles.map(
          (file) => new Paragraph({ text: (file as NamedBlob).name ?? 'unnamed file', bullet: { level: 0 } })
        );

  const doc = new Document({
    sections: [
      {
        children: [
          new Paragraph({
            children: [
              new TextRun({
                text: 'Resume Workflow Mock Output',
                bold: true,
                size: 32
              })
            ]
          }),
          new Paragraph({
            children: [
              new TextRun({
                text: 'This document is generated locally to exercise the download pipeline while mocks are enabled.'
              })
            ]
          }),
          new Paragraph({ text: `Mode: ${data.mode}` }),
          new Paragraph({ text: 'Resume text preview:' }),
          new Paragraph({
            children: [new TextRun({ text: resumePreview, italics: true })]
          }),
          new Paragraph({ text: 'Context preview:' }),
          new Paragraph({
            children: [new TextRun({ text: contextPreview, italics: true })]
          }),
          new Paragraph({ text: 'Job description preview:' }),
          new Paragraph({
            children: [new TextRun({ text: jobPreview, italics: true })]
          }),
          new Paragraph({ text: 'Attached resume files:' }),
          ...resumeFileParagraphs,
          new Paragraph({ text: 'Attached job description files:' }),
          ...jobFileParagraphs
        ]
      }
    ]
  });

  return Packer.toBuffer(doc);
}
