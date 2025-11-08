# Resume Agent Workflows

This directory contains the OpenAI Agent SDK workflows for resume generation.

## Architecture

### Main Components

1. **`resume_orchestrator.py`** - Main orchestrator that coordinates the entire workflow
   - Runs job research (optional)
   - Extracts structured context
   - Runs resume optimization
   - Delegates filename creation to the File Naming Agent
   - Returns optimized JSON ready for DOCX generation

2. **`resume_json_creator.py`** - Resume optimization workflow
   - Determines if job tuning or resume improvement mode
   - Runs appropriate agent chain
   - Returns optimized resume JSON

3. **`job_research_agent.py`** - Job research workflow
   - Analyzes job descriptions
   - Extracts ATS keywords
   - Provides leadership values insights

4. **`file_naming_agent.py`** - Optional agent-driven filename generation
   - Reviews resume content
   - Generates professional filenames and reasoning for MCP/LLM integrations

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
            │ Filename      │
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
# result.filename - filename from the File Naming Agent
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

## Agent Details

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
