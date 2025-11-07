# resume-ats-docx-gen

A batteries-included toolkit for turning structured or free-form resume data into ATS-friendly DOCX files. The repo contains the Python generator, an OpenAI Agents-powered FastAPI backend, a standalone MCP server for AI clients, and a Next.js frontend for collecting inputs.

## What's Inside
- **CLI (`resume-gen`)** – render DOCX files directly from JSON.
- **FastAPI server (`resume-api`)** – orchestrates agent workflows (resume/context extraction, job research, JSON builder) via `app_agents.workflows.ResumeOrchestrator` and streams the result into the DOCX generator.
- **Agent workspace (`app_agents/`)** – reusable OpenAI Agents SDK building blocks plus testing/mocking helpers.
- **Model Context Protocol server (`resume_mcp/`)** – exposes the generator to Claude Desktop, VS Code Copilot, and other MCP clients.
- **Next.js frontend (`frontend/`)** – experiment with the workflow through a modern UI before wiring it into real systems.
- **Examples & tests** – end-to-end scripts and an extensive pytest suite.

## Tech Stack
- **Python** 3.8+, `python-docx`, `click`, `FastAPI`, `uvicorn`, `pydantic`, `mcp`, `docx2pdf`, `openai` + OpenAI Agents SDK helpers.
- **AI workflows** built on the OpenAI Responses API + Agents SDK (see `app_agents/workflows`).
- **Frontend** with Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Radix UI, `react-dropzone`, `next-themes`, and Zod validation.

## Repository Layout
```
resume-ats-docx-gen/
├── resume_gen/          # Core generator + CLI entry point
├── api/                 # FastAPI server (resume-api)
├── app_agents/          # Agents SDK orchestrator, prompts, mocks, scripts
├── resume_mcp/          # FastMCP server + validation models/tools
├── frontend/            # Next.js UI (App Router)
├── tests/               # Pytest suite + fixtures/mocks
├── examples/            # Small helper scripts for demos/tests
├── *.json               # Example resume payloads
└── README.md            # You are here
```

## Architecture Overview
```
                ┌────────────────────────────┐
User Input →    │  FastAPI Server (api/)     │  → JSON suggestions (/api/workflow/json)
(CLI | UI)      │  • combines text + uploads │
                │  • instantiates            │
                │    ResumeOrchestrator      │
                └────────────┬───────────────┘
                             │
                             ▼
         ┌────────────────────────────────────────────┐
         │ app_agents.workflows.ResumeOrchestrator    │
         │  • resume_context_extractor                │
         │  • job_research_agent (job mode only)      │
         │  • resume_json_creator (flow manager,      │
         │    tune/improve, personal summary,         │
         │    JSON builder, judge)                    │
         └────────────┬───────────────────────────────┘
                      │
                      ▼
                Optimized resume JSON + reasoning
                             │
               ┌─────────────▼─────────────┐
               │ resume_gen.ResumeGenerator│  → DOCX saved to outbox/
               └─────────────┬─────────────┘
                             │
                  File download (/api/workflow/docx)

AI assistants that speak the Model Context Protocol (Claude Desktop, VS Code
Copilot, etc.) bypass FastAPI entirely. They connect directly to
`resume_mcp/server.py`, invoke the `generate_resume` tool, and interact with the
same `ResumeGenerator` + validation stack without going through the HTTP API.
FastAPI is therefore optimized for the CLI/UI workflow, while MCP stays focused
on direct agent access.
```
Optional: `resume_mcp/server.py` exposes the same generator/validation stack to MCP clients so Copilot or Claude can call `generate_resume`. The FastAPI server calls `ResumeGenerator` directly for lower latency, while MCP clients continue to use the tool interface.

## Installation
```bash
# Clone and enter the repo
git clone https://github.com/EngineerNV/resume-ats-docx-gen.git
cd resume-ats-docx-gen

# Create & activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install all Python packages
pip install -e .[dev]
```

## Configuration
1. Copy `.env.example` to `.env` and set `OPENAI_API_KEY` (and optionally `OPENAI_BASE_URL`).
2. Frontend settings live in `frontend/.env.local` (see `frontend/README.md`).
3. Generated DOCX files are stored under `outbox/`. Delete individual files when you no longer need them.

## Quick Start
### 1. CLI – JSON → DOCX
```bash
resume-gen render --in example_resume.json --out outbox/my_resume.docx
```

### 2. FastAPI server
```bash
# Inside the virtualenv
resume-api               # or: uvicorn api.server:app --reload
```
Endpoints:
- `GET /` – health check
- `POST /api/workflow/json` – agent-optimized JSON suggestions
- `POST /api/workflow/docx` – same workflow plus DOCX generation

Example DOCX request:
```bash
curl -X POST http://localhost:8000/api/workflow/docx \
  -F 'mode=job' \
  -F 'resumeText=@tests/fixtures/jordan_resume.txt' \
  -F 'jobDescriptionText=Staff engineer role...' \
  -o outbox/jordan_job_tuned.docx
```

### 3. MCP server (optional AI client integration)
```bash
python -m resume_mcp.server
```
Configure Claude Desktop or VS Code Copilot to call the `generate_resume` MCP tool (see `resume_mcp/README.md`).

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
```
Set `USE_MOCK=false` and point `PY_WORKFLOW_JSON_URL` / `PY_WORKFLOW_DOCX_URL` at the FastAPI server to exercise the real workflow.

## JSON Format
Input JSON matches the schema enforced by `resume_mcp/models.py`. Minimal example:
```json
{
  "header": {
    "name": "Your Name",
    "email": "you@example.com",
    "location": "City, State",
    "linkedin": "linkedin.com/in/you",
    "github": "github.com/you"
  },
  "professional_summary": "Optional short summary or list of paragraphs",
  "skills": {
    "Languages": ["Python", "Go"],
    "Frameworks": ["FastAPI", "Next.js"]
  },
  "experience": [
    {
      "role": "Senior Software Engineer",
      "company": "Example Corp",
      "dates": "May 2021 – Present",
      "location": "Remote",
      "bullets": [
        "Owned the resume automation platform and improved conversion by 32%",
        "Led migration to FastAPI + OpenAI Agents"
      ]
    },
    {
      "role": "Software Engineer",
      "company": "Another Co",
      "dates": "2018 – 2021",
      "location": "Austin, TX",
      "subsections": [
        {
          "header": "PLATFORM",
          "bullets": [
            "Scaled ingestion services handling 5B events/day"
          ]
        }
      ]
    }
  ],
  "education": [
    {
      "degree": "B.S. Computer Science",
      "institution": "State University",
      "dates": "2014 – 2018",
      "location": "Seattle, WA",
      "gpa": "3.8/4.0"
    }
  ],
  "awards": ["Dean's List (2017)"]
}
```
See `example_resume.json`, `john_doe_resume.json`, and `example_with_summary.json` for fully-populated payloads.

## Customization
- Edit `resume_gen/config.json` to tweak fonts, spacing, and hyperlink colors.
- `resume_gen/generator.py` exposes helpers for adding new sections (e.g., certifications) if your JSON schema evolves.
- `app_agents/prompts.py` contains the instructions used by each agent. Update prompts/models there before re-exporting orchestrations.

## Testing
The test suite mixes pure Python tests and integration checks. Most FastAPI + agent tests expect a valid `OPENAI_API_KEY`; others rely on `app_agents.testing.FakeOpenAI` fixtures.

```bash
# Run everything (requires API key for the networked tests)
pytest

# Run deterministic/offline tests only
pytest tests/test_direct_generation.py tests/test_mcp.py
```
Key entry points:
- `tests/test_fastapi_agents_docx.py` – full end-to-end smoke test.
- `tests/test_direct_generation.py` – validates generator + optional filename agent without MCP IPC.
- `tests/test_mcp.py` – ensures the MCP server registers the correct tools/resources.
- `tests/test_resume_workflow.py` – covers `ResumeOrchestrator` logic with mock responses.

## Additional Documentation
- `ARCHITECTURE.md` – deeper dive into the data flow and design choices.
- `api/README.md` – detailed API contract, examples, troubleshooting.
- `app_agents/README.md` – how the OpenAI agent workflows are wired together.
- `resume_mcp/README.md` – MCP tooling, templates, and error handling.
- `frontend/README.md` – UI setup, environment flags, feature list.
- `tests/README.md` – overview of the pytest suite.

## License
MIT
