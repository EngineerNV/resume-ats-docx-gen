# FastAPI Server (api/)

REST surface area for the resume workflow. The server accepts raw resume text, optional job descriptions, and uploaded files, then drives the OpenAI agent chain before streaming JSON suggestions or a generated DOCX file.

## Requirements
- Python 3.8+
- Dependencies from `pip install -e .[dev]`
- `.env` with `OPENAI_API_KEY` (and optional `OPENAI_BASE_URL`)

## Running the Server
```bash
# Activate the virtual environment first
source .venv/bin/activate

# Simplest option
resume-api

# or run with uvicorn directly
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000

# or via python -m
python -m api.server
```
The server listens on `http://localhost:8000` by default and enables CORS for the local Next.js frontend (`http://localhost:3000` and `3001`).

## Endpoints
### `GET /`
Health check returning build metadata.

### `POST /api/workflow/json`
Runs the full agent workflow and returns the optimized resume JSON plus reasoning.

Form fields (text or files can be mixed):
- `mode` – `resume` (general improvements) or `job` (align to job description).
- `resumeText` – raw resume text (required unless a resume file is uploaded).
- `context` – optional additional info about the candidate (free text).
- `jobDescriptionText` – job description text (required when `mode=job` unless provided via file upload).
- `resumeFiles` – optional list of uploads (`.txt`, `.md`, `.docx`, `.pdf`).
- `jobDescriptionFiles` – optional list of uploads (`.txt`, `.md`, `.docx`, `.pdf`).

Sample response:
```json
{
  "ok": true,
  "data": {
    "mode": "job_tuning",
    "filename": "JaneSmith_Resume.docx",
    "optimized_resume_json": { "header": {"name": "Jane Smith"}, "experience": [...] },
    "job_research_output": "Top ATS keywords: Python, Kubernetes, ...",
    "reasoning": "Generated job_tuning resume for Jane Smith aligned to job requirements"
  }
}
```

### `POST /api/workflow/docx`
Same contract as the JSON endpoint, but after the agent workflow completes the server invokes `resume_gen.ResumeGenerator` to build a DOCX inside `outbox/<filename>.docx` and streams the binary file back to the client.

Example request:
```bash
curl -X POST http://localhost:8000/api/workflow/docx \
  -F 'mode=resume' \
  -F 'resumeText=Jane Smith ...' \
  -o outbox/jane_resume.docx
```

## How It Works
1. Uploaded documents are decoded through `read_file_content`, which understands UTF-8 text, `.docx` (via `python-docx`), and `.pdf` (when `pymupdf` is installed). All sources are concatenated with the plain-text fields.
2. `ResumeOrchestrator.run(...)` executes asynchronously. In job mode it automatically feeds job-research insights into the prompt stack so downstream agents can reason about ATS alignment.
3. The orchestrator returns `ResumeWorkflowResult` with optimized JSON, a deterministic filename (`FirstLast_Resume.docx`), and reasoning metadata.
4. The DOCX endpoint instantiates `ResumeGenerator(result.optimized_resume_json)` and writes to `outbox/`. The JSON endpoint simply forwards the structured payload.

## File Handling Notes
- DOCX outputs are stored under `<project>/outbox/` even when the API streams the result immediately. Clean up files as needed.
- If you upload `.pdf` files, install `pymupdf` (`pip install pymupdf`) to enable extraction; otherwise the API returns a 400 telling you to install it.
- `.doc` files are intentionally unsupported to keep the parsing logic simple.

## Error Responses
All failures share the shape:
```json
{
  "ok": false,
  "code": "VALIDATION_ERROR",
  "message": "Optional description",
  "fieldErrors": { "resumeText": ["Resume text is required"] }
}
```
`code` can be:
- `VALIDATION_ERROR` – missing fields or invalid combinations (e.g., job mode without job description).
- `WORKFLOW_ERROR` – unhandled exception inside the agent orchestration; includes a traceback to aid debugging.
- `FILE_NOT_FOUND` – generator failed to create the expected DOCX file.
- `DOCX_GENERATION_ERROR` – python-docx threw an exception while writing the file.

## Testing & Debugging
- `examples/test_api.sh` pings the health check and includes commented curl commands you can uncomment for manual testing.
- `tests/test_fastapi_agents_docx.py` starts a uvicorn server inside the test run and exercises every endpoint. Requires `OPENAI_API_KEY` and network access to OpenAI.
- `tests/test_api_integration.py` verifies import paths and helper utilities without launching a server.

If a request fails:
1. Check the server logs (uvicorn will print the stack trace).
2. Ensure `.env` exists and `OPENAI_API_KEY` is set in the environment where the server runs.
3. Inspect the payload returned to the client; validation errors include field-level hints, and workflow errors attach the Python traceback so you can pinpoint the failing agent call.

## Frontend Integration
Set the following in `frontend/.env.local` when pointing the UI at this server:
```
USE_MOCK=false
PY_WORKFLOW_JSON_URL=http://localhost:8000/api/workflow/json
PY_WORKFLOW_DOCX_URL=http://localhost:8000/api/workflow/docx
```
The frontend expects the same response payloads described above and will display `reasoning` fields inline so users can understand what changed.
