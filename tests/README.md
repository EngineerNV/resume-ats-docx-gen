# Test Suite

`pytest`-based coverage of the generator, agent workflows, FastAPI server, and MCP tooling.

## Running Tests
```bash
# Full suite (requires OPENAI_API_KEY for the networked cases)
pytest

# Fast deterministic subset (no OpenAI calls)
pytest tests/test_direct_generation.py tests/test_mcp.py tests/test_resume_workflow.py -v
```
Many tests double as runnable scripts (`python tests/test_fastapi_agents_docx.py`). Those scripts print additional context/logs that help debug failing scenarios.

## Groups & Entry Points
| File | Focus |
| --- | --- |
| `test_fastapi_agents_docx.py` | End-to-end FastAPI smoke test. Starts a uvicorn server, hits JSON & DOCX endpoints, validates generated files. Requires `.env` with `OPENAI_API_KEY` and a working `.venv`. |
| `test_api_integration.py`, `test_api_smoke.py` | Lightweight checks around API request plumbing without spinning up the server. |
| `test_resume_workflow.py`, `test_agent_workflow.py`, `test_agents_only.py` | Exercise `ResumeOrchestrator` and the underlying Agents SDK definitions (often via `FakeOpenAI`). |
| `test_direct_generation.py` | Ensures `ResumeGenerator` + optional filename agent work without launching MCP or FastAPI. |
| `test_job_mode.py` | Validates job-tuning specific behaviors (ATS keyword handling, reasoning strings, etc.). |
| `test_mcp.py`, `test_mcp_resume_agent.py` | Cover the Model Context Protocol server, templates, outbox resources, and the filename agent integration path. |
| `test_simple.py` | Minimal workflow sanity check using sample data. |

Fixtures live in `tests/fixtures/` and include sample resumes (`jordan_resume.txt`, `test_user_resume.json`, etc.).

## Environment Expectations
- Create `.env` in the project root and set `OPENAI_API_KEY` before running tests that touch OpenAI.
- Install optional dependencies (`pymupdf`, `httpx`) if you plan to run the PDF ingestion or FastAPI HTTP tests.
- Some suites spawn `uvicorn` from `.venv/bin/python`; ensure the virtual environment exists.

## Debugging Tips
- Most scripts print detailed progress (e.g., server startup logs, reasoning strings). Run them individually when narrowing down failures.
- The fake client (`app_agents.testing.FakeOpenAI`) makes it easy to add new deterministic cases—capture a mocked response via `MockResponseSpec` and wire it into the relevant test.
- Generated DOCX files are saved to `outbox/` during many tests; inspect those artifacts if a formatting assertion fails.
