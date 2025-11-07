# Agent Workspace

This directory now contains the Python implementation of the agent workflows that support resume planning and generation. The workflows mirror the OpenAI Agent Builder exports provided by the product team and feed JSON output directly into the MCP resume generator.

## Components

- `config.py` – Pydantic settings wrapper used to read `OPENAI_API_KEY` (and optional `OPENAI_BASE_URL`) from environment variables.
- `client.py` – Helper that constructs an `OpenAI` client configured with the project settings.
- `workflows/` – Collection of reusable workflow entry points:
  - `resume_context_extractor.py` – Wraps the **Resume/Context Extractor** agent workflow.
  - `resume_json_creator.py` – Orchestrates the **Resume Flow Manager**, **Tune Resume to JD**, **Improve Current Resume**, **Personal Statement**, **Resume JSON Builder**, and **Judge for Improvement** agents. This module wires the outputs so they can be consumed by the MCP server.

## Usage

1. Copy `.env.example` to `.env` and set `OPENAI_API_KEY` (and `OPENAI_BASE_URL` if you are targeting a non-default endpoint).
2. Instantiate the workflow in Python:

   ```python
   from agents.workflows import ResumeJsonWorkflow

   workflow = ResumeJsonWorkflow()
   result = workflow.run(
       resume_text="""...raw resume text...""",
       job_description="""...job description...""",
       ats_keywords=["python", "aws"],
       mode="job_tuning",  # or "resume_improvement" / "auto"
       additional_context={"linkedin_summary": "..."},
   )

   print(result.optimized_resume_json.parsed)
   ```

3. The returned `ResumeJsonWorkflowResult` bundles the outputs of every agent call. Feed `result.optimized_resume_json.parsed` directly into the MCP server’s `generate_resume` tool to produce DOCX files.

4. For quick manual testing (including the smoke scenarios requested by product), run the helper script which wraps the workflow with sample data:

   ```bash
   python -m agents.scripts.run_resume_workflow --mode job_tuning
   python -m agents.scripts.run_resume_workflow --mode resume_improvement
   ```

   Use `--resume-file`, `--job-description-file`, or `--ats-keywords` to supply custom inputs, and `--output <path>` to persist the aggregated response JSON for inspection.

   When the OpenAI SDK is unavailable or network access is restricted, you can replay recorded agent outputs with `--mock-run`. For example, the `jordan_resume_improvement` recording validates the resume-improvement branch using the fictional Jordan Reynolds resume that product provided:

   ```bash
   python -m agents.scripts.run_resume_workflow \
     --mode resume_improvement \
     --resume-file tests/fixtures/jordan_resume.txt \
     --mock-run jordan_resume_improvement \
     --output jordan_resume_improvement_output.json
   ```

## Notes

- The workflows assume the OpenAI Python SDK ≥ `1.0`. Make sure to install project dependencies (`pip install -e .`) before running.
- `ResumeJsonWorkflow.run` automatically executes the resume/context extraction workflow before orchestrating the remaining agents, ensuring each downstream call receives the structured context it needs.
- Set `mode="job_tuning"` to explicitly force job-alignment behavior (skip the flow manager decision) or `mode="resume_improvement"` to focus on general polishing. Leave the default `mode="auto"` to reuse the flow manager's decision logic.

## FastAPI Integration

The agent workflows are consumed by the FastAPI server (`api/server.py`) to provide REST API endpoints for the frontend application.

### Workflow Integration Pattern

The API server uses **direct function calls** (not MCP protocol) for optimal performance:

```python
from agents.workflows import ResumeJsonWorkflow
from agents.workflows.mcp_resume_agent import prepare_resume_for_mcp
from resume_mcp.tools import generate_resume_tool

# 1. Run agent workflow for optimization
workflow = ResumeJsonWorkflow()
result = workflow.run(
    resume_text=resume_text,
    job_description=job_description,
    mode="job_tuning"
)

# 2. Generate filename using Filename Agent
filename_result = prepare_resume_for_mcp(result.optimized_resume_json.parsed)

# 3. Direct DOCX generation (not via MCP protocol)
generation_result = generate_resume_tool(
    resume_data=filename_result.resume_data,
    filename=filename_result.filename
)

# 4. Return DOCX file to frontend
return FileResponse(generation_result["path"])
```

### Filename Agent

The `prepare_resume_for_mcp()` function in `mcp_resume_agent.py` provides intelligent filename generation:

**Purpose**: Extract candidate name from resume JSON and generate professional, URL-safe filenames

**Input**: Optimized resume JSON (output from `ResumeJsonWorkflow`)

**Output**: `FilenameResult` with:
- `filename` (str): Generated filename, e.g., `"jane_smith_resume.docx"`
- `resume_data` (dict): Complete resume JSON
- `reasoning` (str): Agent's explanation for the filename choice

**Example**:
```python
from agents.workflows.mcp_resume_agent import prepare_resume_for_mcp

resume_json = {
    "header": {"name": "Jane Smith", "email": "jane@example.com"},
    "skills": {...},
    "experience": [...]
}

result = prepare_resume_for_mcp(resume_json)

print(result.filename)      # "jane_smith_resume.docx"
print(result.reasoning)     # "Extracted 'Jane Smith' from header.name..."
```

**Filename Generation Logic**:
1. Extracts name from `header.name` field
2. Converts to lowercase
3. Replaces spaces with underscores
4. Removes special characters
5. Appends `_resume.docx`
6. Falls back to `resume.docx` if name extraction fails

### Job Research (ATS Keyword Derivation)

Temporarily deferred for this PR to keep scope focused on FastAPI integration. In `job_tuning` mode, callers should pass `ats_keywords` explicitly (the CLI provides sensible defaults for demos).

### Direct Generation vs MCP Protocol

**Important Architecture Decision**: The FastAPI workflow uses direct function calls for ~100ms performance improvement:

**✅ Current Approach (Direct)**:
```python
from resume_mcp.tools import generate_resume_tool

result = generate_resume_tool(resume_data, filename)
# Faster, simpler, fewer dependencies
```

**❌ Previous Approach (MCP Protocol)**:
```python
# Spawned MCP server process, used stdio transport
# Added ~100ms overhead from inter-process communication
```

**Benefits of Direct Calls**:
- **Performance**: ~100ms faster (no IPC overhead)
- **Simplicity**: Fewer moving parts
- **Debugging**: Easier to trace and debug
- **Reliability**: No process spawning issues

The standalone MCP server (`resume_mcp/server.py`) still exists for AI client integration (Claude Desktop, VS Code Copilot) but is not used by the FastAPI workflow.

### Testing the Integration

```bash
# Start the FastAPI server
resume-api

# In another terminal, test the endpoints
curl -X POST http://localhost:8000/api/workflow/json \
  -F 'mode=resume' \
  -F 'resumeText=Your resume here...'

curl -X POST http://localhost:8000/api/workflow/docx \
  -F 'mode=job' \
  -F 'resumeText=Your resume here...' \
  -F 'jobDescriptionText=Job description here...' \
  -o test_resume.docx
```

### API Response Structure

**JSON Endpoint** (`/api/workflow/json`):
```json
{
  "ok": true,
  "data": {
    "mode": "job_tuning",
    "should_align_to_job": true,
    "resume_json": { /* original */ },
    "optimized_resume_json": { /* improved */ },
    "personal_summary": "..."
  }
}
```

**DOCX Endpoint** (`/api/workflow/docx`):
- Returns binary DOCX file
- Content-Type: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Filename from Filename Agent (e.g., `jane_smith_resume.docx`)

