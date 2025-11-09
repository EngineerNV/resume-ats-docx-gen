# Agent Workspace (`app_agents/`)

Python source of the OpenAI Agents SDK workflows that power the resume optimization pipeline. Everything funnels through `ResumeOrchestrator`, which stitches together the context extractor, job research agent, and the exported agent chain from Agent Builder.

## Modules
- `config.py` – Pydantic settings helper that reads `OPENAI_API_KEY` and optional `OPENAI_BASE_URL`.
- `client.py` – constructs an OpenAI client or returns the fake client used in tests.
- `prompts.py` – instructions for every agent (flow manager, job tuner, resume improver, personal summary, JSON builder, judge, job research, filename agent).
- `workflows/` – building blocks:
  - `resume_orchestrator.py` – single entry point; exposes `ResumeOrchestrator` (async) and `run_resume_workflow` (sync wrapper). Derives filenames locally from the optimized resume header (no agent invocation for naming in the active path).
  - `resume_context_extractor.py` – extracts structured bullets/sections from raw text so downstream prompts get normalized data.
  - `job_research_agent.py` – optional branch that derives ATS keywords/leadership values in job mode.
  - `resume_json_creator.py` – wires the exported agent chain from OpenAI (flow manager → tune/improve → personal summary → JSON builder → judge).
  - `file_naming_agent.py` – legacy/optional helper retained for tests & potential future interactive use; NOT called by `ResumeOrchestrator` at runtime.
  - `base.py` – shared helper classes for defining Agents SDK requests/responses.
- `testing/` – `FakeOpenAI`, mock response specs, and canned runs for deterministic tests.
- `scripts/run_resume_workflow.py` – CLI helper that exercises the workflow with sample data or recorded mock runs.

## Setup
1. Create `.env` in the project root and set `OPENAI_API_KEY`.
2. Install dependencies via `pip install -e .[dev]`.
3. (Optional) export `OPENAI_BASE_URL` if you are targeting a self-hosted OpenAI-compatible endpoint.

## ResumeOrchestrator Lifecycle
```python
from app_agents.workflows import ResumeOrchestrator, run_resume_workflow

orchestrator = ResumeOrchestrator()
result = await orchestrator.run(
    resume_text="...",
    job_description="...",      # optional
    additional_context="..."     # optional
)
```
Returns `ResumeWorkflowResult` with:
- `optimized_resume_json` – dict ready for `ResumeGenerator`.
- `filename` – locally derived filename (e.g., `firstname_lastname_resume.docx`) based on `header.name`; falls back to `resume.docx`.
- `mode` – `job_tuning` or `resume_improvement`.
- `job_research_output` – ATS/leadership summary when job mode is active.
- `reasoning` – short explanation of what was generated.

Use `run_resume_workflow(...)` when synchronous code needs the same result (wrapper around `asyncio.run`).

### What Happens Under the Hood
1. **Mode detection** – job descriptions trigger the `job_tuning` branch.
2. **Job research** – `job_research_agent` summarizes ATS keywords/leadership themes for downstream prompts.
3. **Context extraction** – `resume_context_extractor` produces structured JSON describing the existing resume.
4. **Resume JSON workflow** – `resume_json_creator` runs the Flow Manager plus the full suite of agents exported from Agent Builder, culminating in a judged/optimized resume JSON document.
5. **Filename + reasoning** – orchestrator constructs a deterministic filename from the candidate name (no agent call) and logs a one-line explanation. (The File Naming Agent remains available but unused.)

## File Naming Agent (Legacy / Optional)
`app_agents/workflows/file_naming_agent.py` is currently NOT invoked by the orchestrator or FastAPI server. It is retained for backward compatibility, tests, and potential future enhancement where LLM reasoning about filenames (e.g., multi-variant outputs) might be desirable. You can still call it directly:
```python
from app_agents.workflows.file_naming_agent import prepare_resume_for_mcp

result = prepare_resume_for_mcp(optimized_resume_dict)
print(result.filename)
print(result.reasoning)
```
The FastAPI server does NOT use this agent; filenames are derived locally for performance and determinism. Collisions (same derived name) will overwrite existing files in `outbox/` (see below).

### Filename Collision Behavior
- No uniqueness check or incrementing strategy is implemented today.
- If `outbox/john_doe_resume.docx` exists and a new request derives the same name, the previous file is overwritten.
- If you need stable retention without overwrites, implement a wrapper that appends a timestamp or UUID before calling `ResumeGenerator.generate`.

## Scripts & Mocking
Run the helper script with real inputs or recorded runs (no API calls):
```bash
python -m app_agents.scripts.run_resume_workflow --mode job_tuning \
  --resume-file tests/fixtures/jordan_resume.txt \
  --mock-run jordan_resume_improvement \
  --output jordan_output.json
```
See `app_agents/testing/mock_runs.py` for available recordings. `FakeOpenAI` can also be instantiated directly inside tests to avoid network calls.

## Contributing Tips
- When updating prompts or agent definitions, keep `prompts.py` as the single source of truth and reference those constants inside the workflow modules.
- `resume_json_creator.py` mirrors the exported JSON from Agent Builder. Update it when the upstream workflow changes so we do not fork prompts in multiple places.
- Add or adjust deterministic tests under `tests/` (many of them already import pieces from this package) whenever the workflow contract changes.
