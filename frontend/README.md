# Resume Workflow Frontend

A Next.js 14 App Router UI for collecting resume inputs, reviewing payloads, and proxying to backend workflow services for JSON suggestions and DOCX generation.

## Getting Started

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser. The application defaults to mocked responses so you can exercise the full workflow locally.

## Environment Flags

| Variable | Description | Default |
| --- | --- | --- |
| `USE_MOCK` | When truthy, API routes return canned responses and generate an in-memory DOCX instead of proxying to Python services. | `true` |
| `PY_WORKFLOW_JSON_URL` | URL for the upstream JSON suggestion service. Ignored when `USE_MOCK` is truthy. | _unset_ |
| `PY_WORKFLOW_DOCX_URL` | URL for the upstream DOCX generation service. Ignored when `USE_MOCK` is truthy. | _unset_ |
| `NEXT_PUBLIC_ENABLE_KEYWORDS` | Enables the keyword preview chip list on the review step when set to `true`. | `false` |

Create a `.env.local` file in `frontend/` to override defaults as needed.

## Features

- Three-step guided experience (inputs → review → submit) with validation and accessible navigation.
- Drag-and-drop file uploads with inline feedback and combined size limits.
- Review summary with optional keyword preview and file removal prior to submission.
- Dual submission paths: JSON suggestions render inline, DOCX downloads with preview link.
- Cancel in-flight requests via `AbortController` backed controls.
- Dark mode support via `next-themes` and Tailwind CSS.

## Mock Data

- JSON suggestions: `mocks/suggestions.json`

The DOCX route produces a lightweight document at request-time so that no binary assets need to live in the repository. Point the API routes at real services when integrating with the Python workflow backend.
