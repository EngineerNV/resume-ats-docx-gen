# Architecture & Integration Overview

This document explains how the CLI, FastAPI backend, OpenAI agent workflows, MCP server, and Next.js frontend collaborate to turn unstructured resumes into ATS-friendly DOCX files.

## 1. High-Level System
```
┌────────────────────┐        ┌────────────────────────────────────┐
│ CLI / Frontend /   │  HTTP  │ FastAPI Server (api/server.py)     │
│ API clients        ├───────►│ • combines text + uploads          │
└────────────────────┘        │ • validates inputs                  │
                              │ • instantiates ResumeOrchestrator  │
                              └───────────────┬────────────────────┘
                                              │
                                              ▼
                 ┌────────────────────────────────────────────┐
                 │ app_agents.workflows.ResumeOrchestrator    │
                 │  • resume_context_extractor (parses raw    │
                 │    text)                                   │
                 │  • job_research_agent (job mode only)      │
                 │  • resume_json_creator (flow manager,      │
                 │    tune/improve, personal summary, JSON    │
                 │    builder, judge)                         │
                 └────────────────────────────────────────────┘
                                              │
                                              ▼
                             Optimized resume JSON + reasoning
                                              │
                              ┌───────────────▼────────────────┐
                              │ resume_gen.ResumeGenerator     │
                              │ • python-docx rendering        │
                              │ • config-driven styling        │
                              └───────────────┬────────────────┘
                                              │
                               DOCX saved to outbox/ + download
```
The standalone MCP server (`resume_mcp/server.py`) exposes the same generator/validation stack to AI tooling. MCP clients call `generate_resume` via Model Context Protocol, while the FastAPI server links to `ResumeGenerator` directly for lower latency.

## 2. Component Responsibilities
### FastAPI server (`api/server.py`)
- Exposes `GET /`, `POST /api/workflow/json`, and `POST /api/workflow/docx`.
- Normalizes request payloads by combining free text and uploaded files via `read_file_content` and `combine_text_and_files`.
- Executes the agent workflow (`ResumeOrchestrator.run`) and returns JSON or streams the rendered DOCX file stored in `outbox/`.
- Handles validation (required text, job description for job mode, decoding failures) and responds with structured JSON errors.

### Agent workflow (`app_agents/workflows/`)
- `ResumeOrchestrator` is the only entry point. It:
  1. Detects mode (`job_tuning` vs `resume_improvement`).
  2. Runs `job_research_agent` when job descriptions are supplied, surfacing ATS insights for the downstream prompt.
  3. Invokes `resume_context_extractor` to give the agent chain structured facts.
  4. Calls `resume_json_creator`, which wires the Flow Manager → Tune/Improve → Personal Statement → JSON Builder → Judge agents defined with the OpenAI Agents SDK.
  5. Returns `ResumeWorkflowResult` (optimized JSON, filename, mode, job research notes, reasoning).
- `run_resume_workflow(...)` wraps the async orchestrator so CLI/tests can call it synchronously.
- `app_agents/testing` contains `FakeOpenAI` and mock recordings for deterministic tests.

### DOCX generation (`resume_gen/`)
- `ResumeGenerator` reads either the shipped `config.json` or defaults, sets up a python-docx `Document`, and renders headers, summaries, skills, experience (bullets or subsections), education, and awards.
- `resume_gen/cli.py` exposes the generator via `resume-gen render --in … --out …`.
- Generated documents are placed in `outbox/` by both the CLI and API; adjust or clean that folder as needed.

### MCP server (`resume_mcp/`)
- Implements the `generate_resume` tool plus `template://` and `outbox://` resources with FastMCP.
- Validates input JSON through `resume_mcp.models.Resume` before passing it to the same `ResumeGenerator` used by the API.
- Enables Claude Desktop, VS Code Copilot, or any MCP-aware assistant to call the generator without invoking FastAPI.

### Frontend (`frontend/`)
- Next.js App Router UI for collecting resume text/files, previewing payloads, and calling either mock routes or the Python backend (`PY_WORKFLOW_JSON_URL`, `PY_WORKFLOW_DOCX_URL`).
- Defaults to mock data so the UX can be exercised without an API key; set `USE_MOCK=false` to proxy to FastAPI.

## 3. Data Flows
### `/api/workflow/json`
1. Inputs (`mode`, `resumeText`, `context`, `jobDescriptionText`, optional files) are merged into plain text.
2. `ResumeOrchestrator` runs asynchronously and returns optimized JSON plus metadata.
3. Response payload:
   ```json
   {
     "ok": true,
     "data": {
       "mode": "job_tuning",
       "filename": "JaneSmith_Resume.docx",
       "optimized_resume_json": { … },
       "job_research_output": "…",
       "reasoning": "Generated job_tuning resume for Jane Smith aligned to job requirements"
     }
   }
   ```

### `/api/workflow/docx`
1. Follows the same orchestration as `/api/workflow/json`.
2. Instantiates `ResumeGenerator(result.optimized_resume_json)` and writes to `outbox/` using the filename returned by the File Naming Agent (e.g., `firstname_lastname_resume.docx`).
3. Streams the generated DOCX back to the caller with `FileResponse` and `Cache-Control: no-store` headers.

### CLI
- Reads JSON from disk, feeds it directly into `ResumeGenerator`, and writes to the requested location.

### MCP
- External agents call `generate_resume(resume, filename)`.
- `resume_mcp.tools.generate_resume_tool` performs validation and generation and returns both filesystem and `outbox://` URIs.

## 4. Error Handling Layers
1. **FastAPI form validation** – ensures resume text is present and job descriptions accompany `mode=job`.
2. **File decoding** – gracefully decodes `.txt`, `.md`, `.docx`, or `.pdf` uploads (requires `pymupdf` for PDFs).
3. **Agent workflow exceptions** – surfaced as `WORKFLOW_ERROR` responses with tracebacks for debugging.
4. **DOCX generation** – verifies `outbox/<filename>.docx` exists before streaming and reports `FILE_NOT_FOUND` if not.
5. **MCP tool validation** – `pydantic.ValidationError` messages are converted into actionable bullet lists for LLM clients.

## 5. Testing Strategy
- `tests/test_fastapi_agents_docx.py` spins up the FastAPI server (requires a valid OpenAI key) and exercises JSON + DOCX endpoints.
- `tests/test_resume_workflow.py` and friends mock the Agents SDK via `app_agents.testing.FakeOpenAI` to verify orchestrator plumbing without network calls.
- `tests/test_direct_generation.py` focuses on `ResumeGenerator` + optional filename agent interactions.
- `tests/test_mcp.py` validates that MCP tools/resources are registered and functional.

Run `pytest` for the full suite or execute individual scripts (they are all runnable modules) when debugging a particular slice of the system.

## 6. Frontend Integration
Configure `frontend/.env.local`:
```
USE_MOCK=false
PY_WORKFLOW_JSON_URL=http://localhost:8000/api/workflow/json
PY_WORKFLOW_DOCX_URL=http://localhost:8000/api/workflow/docx
```
The UI enforces the same validation rules as the API, shows payload previews, and reveals reasoning returned by the agents to help users understand the optimizations that were applied.

## 7. Optional Features
- `app_agents/workflows/file_naming_agent.py` (legacy) is currently NOT invoked; filenames are derived locally from `header.name` inside the orchestrator for determinism and speed. The agent remains for tests/backward compatibility.
- `generate_claude_config.py` emits helper JSON for Claude Desktop MCP configuration.

Keeping documentation aligned with the code paths above ensures contributors know exactly which layer to touch when updating prompts, changing the generator, or extending the API contract.
