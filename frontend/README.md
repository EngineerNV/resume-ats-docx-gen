# Resume Workflow Frontend

A Next.js 14 App Router UI for collecting resume inputs, reviewing payloads, and proxying to backend workflow services for JSON suggestions and DOCX generation.

## Getting Started

### Local Development (Mock Mode)

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser. The application defaults to mocked responses so you can exercise the full workflow locally without a backend.

### With Backend Integration

1. Start the FastAPI backend server:
```bash
# From project root
python -m backend.main
```

2. Configure the frontend to use the backend:
```bash
cd frontend
cat > .env.local << EOF
USE_MOCK=false
PY_WORKFLOW_DOCX_URL=http://localhost:8000/api/workflow/docx
PY_WORKFLOW_JSON_URL=http://localhost:8000/api/workflow/json
EOF
```

3. Start the frontend:
```bash
npm run dev
```

The frontend will now proxy requests to the FastAPI backend at `http://localhost:8000`.

## Environment Flags

| Variable | Description | Default |
| --- | --- | --- |
| `USE_MOCK` | When truthy, API routes return canned responses and generate an in-memory DOCX instead of proxying to Python services. | `true` |
| `PY_WORKFLOW_JSON_URL` | URL for the upstream JSON suggestion service. Ignored when `USE_MOCK` is truthy. | _unset_ |
| `PY_WORKFLOW_DOCX_URL` | URL for the upstream DOCX generation service. Ignored when `USE_MOCK` is truthy. | _unset_ |
| `NEXT_PUBLIC_ENABLE_KEYWORDS` | Enables the keyword preview chip list on the review step when set to `true`. | `false` |

Create a `.env.local` file in `frontend/` to override defaults as needed.

## Features

### User Experience
- **Three-step guided workflow**: Inputs → Review → Submit with clear visual progress
- **Drag-and-drop file uploads**: Intuitive file handling with inline feedback and size limits
- **Review summary**: Preview all inputs before submission with option to edit
- **Dual submission paths**: 
  - Get AI suggestions (JSON response displayed inline)
  - Download DOCX resume (with file path display)
- **File path visibility**: Shows where generated resumes are saved locally
- **Cancel in-flight requests**: Abort controls for long-running operations
- **Dark mode support**: Automatic theme switching via `next-themes`

### Technical Features
- Built with Next.js 14 App Router
- TypeScript for type safety
- Tailwind CSS for styling
- Zod for schema validation
- React Dropzone for file uploads
- Accessible navigation with ARIA labels

## DOCX Preview Considerations

**Important Note**: Browsers cannot natively display DOCX files. When users download a resume:

1. The file is automatically downloaded to their default downloads folder
2. The frontend displays the **local file path** where the resume is saved (when using the backend)
3. Users can:
   - Re-download the file
   - Copy the file path to clipboard
   - Open the file with Word, Google Docs, or any compatible word processor

**Why not PDF preview?** 
- The current implementation focuses on DOCX format for maximum ATS compatibility
- Future enhancement: Add server-side DOCX-to-PDF conversion for browser preview
- For local development, showing the file path is more useful than attempting a preview

## Mock Data

- JSON suggestions: `mocks/suggestions.json`

The DOCX route produces a lightweight document at request-time so that no binary assets need to live in the repository. Point the API routes at real services when integrating with the Python workflow backend.

## Component Architecture

```
app/
├── page.tsx              # Main workflow orchestration
├── layout.tsx            # Root layout with theme provider
└── api/
    └── workflow/
        ├── docx/route.ts  # DOCX generation endpoint
        └── json/route.ts  # Suggestions endpoint

components/
├── FileDropzone.tsx      # File upload with drag & drop
├── ModeSlider.tsx        # Workflow mode selection
├── PayloadPreview.tsx    # Review step content
├── StepIndicator.tsx     # Progress visualization
├── SubmitButtons.tsx     # Action buttons
├── TextSection.tsx       # Text input fields
└── theme-provider.tsx    # Dark mode provider

lib/
├── schema.ts             # Zod validation schemas
├── types.ts              # TypeScript type definitions
└── utils.ts              # Helper functions
```

## Building for Production

```bash
npm run build
npm run start
```
