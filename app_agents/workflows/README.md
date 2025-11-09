# Resume Agent Workflows

This directory contains the OpenAI Agent SDK workflows for resume generation.

## Architecture

### Main Components

1. **`resume_orchestrator.py`** - Main orchestrator that coordinates the entire workflow
   - Runs job research (optional)
   - Extracts structured context
   - Runs resume optimization
   - Derives filename directly from the optimized resume JSON header (no agent call)
   - Returns optimized JSON ready for DOCX generation

2. **`resume_json_creator.py`** - Resume optimization workflow
   - Determines if job tuning or resume improvement mode
   - Runs appropriate agent chain
   - Returns optimized resume JSON

3. **`job_research_agent.py`** - Job research workflow
   - Analyzes job descriptions
   - Extracts ATS keywords
   - Provides leadership values insights

4. **`file_naming_agent.py`** - Legacy / optional agent-driven filename generation (currently NOT invoked by the orchestrator)
   - Retained only for backward compatibility, tests, and potential future interactive use cases
   - Not part of the live FastAPI or orchestration path; filename is computed locally for performance & determinism

## Workflow Flow

```
┌─────────────────────────────────────────────┐
│  FastAPI Endpoint (/api/workflow/docx)     │
│  - Receives resume text, job description    │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  ResumeOrchestrator                         │
│  - Coordinates all workflows                │
└────┬────────────────────────────────────┬───┘
     │                                    │
     ▼                                    ▼
┌──────────────────┐           ┌──────────────────┐
│ Job Research     │           │ Resume JSON      │
│ Workflow         │           │ Creator Workflow │
│ (if job mode)    │           │ (always)         │
└──────┬───────────┘           └────────┬─────────┘
       │                                │
       └────────────┬───────────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ Optimized     │
            │ Resume JSON + │
            │ Local Filename│
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │ generator.py  │
            │ (DOCX)        │
            └───────────────┘
```

## Usage

### From FastAPI

```python
from app_agents.workflows import ResumeOrchestrator

orchestrator = ResumeOrchestrator()
result = await orchestrator.run(
    resume_text="...",
    job_description="...",  # optional
    additional_context="..."  # optional
)

# result.optimized_resume_json - ready for DOCX generation
# result.filename - filename derived locally from resume header (not from file_naming_agent)
# result.mode - "job_tuning" or "resume_improvement"
```

### Direct Usage

```python
from app_agents.workflows import run_resume_workflow
from resume_gen.generator import ResumeGenerator

result = run_resume_workflow(
    resume_text="...",
    job_description="...",
)

ResumeGenerator(result.optimized_resume_json).generate(Path("output") / result.filename)
```

## Agent Details & Filename Generation

### Filename Generation (Current Behavior)
- The orchestrator derives `firstname_lastname_resume.docx` (lowercased, non-alphanumeric stripped) from `optimized_resume_json.header.name`.
- Falls back to `resume.docx` if no usable name tokens are found.
- No uniqueness or collision handling is performed; downstream writers (FastAPI endpoint / CLI) will overwrite existing files with the same name.
- The separate `file_naming_agent.py` is unused in the active workflow; see its README comments if re-activation is desired.

### Resume Flow Manager
- Determines workflow mode (job tuning vs. improvement)
- Returns boolean decision

### Tune Resume to JD Agent
- Analyzes job description and resume
- Provides structured guidance for optimization
- Uses web search for ATS insights

### Improve Current Resume Agent
- Analyzes resume structure
- Provides improvement suggestions
- No job description required

### Judge for Improvement
- Final optimization pass
- Ensures ATS compliance
- Maintains resume structure

### Personal Statement Agent
- Generates professional summary
- Based on resume content and context

### Resume JSON Builder Agent
- Normalizes all data into standard JSON schema
- Ensures schema compliance
- Handles field mapping

## Configuration

Agents use environment variables from `.env`:
- `OPENAI_API_KEY` - Required for OpenAI API access
- `OPENAI_BASE_URL` - Optional custom base URL

## Error Handling

All workflows include error handling:
- Input validation
- Schema validation
- Graceful fallbacks
- Detailed error messages
