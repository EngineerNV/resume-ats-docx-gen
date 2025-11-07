# Architecture & Integration Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│                                                                   │
│  - Collects resume text and job description                     │
│  - Sends POST requests to FastAPI server                        │
│  - Receives JSON suggestions or DOCX files                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTP POST
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    FastAPI Server (Python)                       │
│                                                                   │
│  Endpoints:                                                      │
│  - POST /api/workflow/json  → Returns JSON suggestions          │
│  - POST /api/workflow/docx  → Returns DOCX file                 │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         Agent Workflow Orchestration                     │   │
│  │                                                           │   │
│  │  1. Input Validation                                     │   │
│  │  2. Resume Context Extraction (OpenAI Agent)            │   │
│  │  3. Workflow Decision (job tuning vs improvement)       │   │
│  │  4. Resume Optimization (OpenAI Agents)                 │   │
│  │  5. JSON Generation                                      │   │
│  │                                                           │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│                          │                                       │
│                          │ Pass JSON to Filename Agent           │
│                          │                                       │
│  ┌───────────────────────▼─────────────────────────────────┐   │
│  │           Filename Agent (prepare_resume_for_mcp)        │   │
│  │                                                           │   │
│  │  - Reviews optimized resume JSON                         │   │
│  │  - Extracts candidate name                               │   │
│  │  - Generates intelligent filename                        │   │
│  │  - Returns: jane_smith_resume.docx                       │   │
│  │                                                           │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│                          │                                       │
│                          │ Direct function call                  │
│                          │                                       │
│  ┌───────────────────────▼─────────────────────────────────┐   │
│  │      Direct Generation (generate_resume_tool)            │   │
│  │                                                           │   │
│  │  - Validates resume JSON with Pydantic                   │   │
│  │  - Generates DOCX using python-docx                      │   │
│  │  - Saves to outbox/ directory                            │   │
│  │  - Returns file path                                     │   │
│  │                                                           │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

## Component Integration

### 1. FastAPI Server → OpenAI Agent Workflow

**File**: `api/server.py`

```python
from app_agents.workflows import ResumeJsonWorkflow

workflow = ResumeJsonWorkflow()
result = workflow.run(
    mode=workflow_mode,
    resume_text=combined_resume_text,
    job_description=combined_job_description,
    additional_context=additional_context,
)
```

The workflow orchestrates multiple OpenAI agents:
- **Resume Context Extractor**: Parses raw resume text into structured context
- **Flow Manager**: Decides between job tuning vs general improvement
- **Tune Resume to JD Agent**: Aligns resume with job description
- **Improve Current Resume Agent**: General resume enhancement
- **Personal Statement Agent**: Generates professional summary
- **Resume JSON Builder**: Creates structured resume JSON
- **Judge for Improvement**: Final optimization pass

### 2. FastAPI Server → Filename Agent → Direct Generation

**File**: `api/server.py` and `app_agents/workflows/file_naming_agent.py`

```python
from app_agents.workflows import prepare_resume_for_mcp
from resume_mcp.tools import generate_resume_tool

# Filename Agent determines intelligent filename
filename_result = prepare_resume_for_mcp(optimized_resume)

# Direct generation call
generation_result = generate_resume_tool(
    resume_data=filename_result.resume_data,
    filename=filename_result.filename
)
```

**Filename Agent** (`app_agents/workflows/file_naming_agent.py`):
- Reviews optimized resume JSON
- Extracts candidate name from resume data
- Generates professional, URL-safe filename
- Returns filename, resume data, and reasoning

**Direct Generation Tool** (`resume_mcp/tools.py`):
- Validates resume JSON with Pydantic
- Generates DOCX using python-docx library
- Saves file to outbox/ directory
- Returns file path and success status

**Benefits**:
- Simple, direct function calls
- No protocol overhead (~100ms faster)
- Fewer moving parts, more reliable
- Easier to debug and maintain
- Agent still provides intelligent naming

### 3. Standalone MCP Server Usage (Optional)

**File**: `resume_mcp/server.py`

For AI client integration (Claude Desktop, VS Code Copilot):

```bash
python -m resume_mcp.server
```

The standalone MCP server exposes the same generation tools via the MCP protocol for external AI agents. This is separate from the FastAPI workflow which uses direct generation.

## Data Flow

### JSON Workflow Endpoint

```
User Input (Frontend)
  │
  ├─→ mode: "job" | "resume"
  ├─→ resumeText: string
  ├─→ jobDescriptionText: string (optional)
  ├─→ context: string (optional)
  │
  ▼
FastAPI Server
  │
  ├─→ Validate inputs
  ├─→ Combine text and file uploads
  ├─→ Determine workflow mode
  │
  ▼
Agent Workflow (ResumeJsonWorkflow)
  │
  ├─→ Extract resume context
  ├─→ Flow manager decision
  ├─→ Job alignment OR resume improvement
  ├─→ Generate personal summary
  ├─→ Build resume JSON
  ├─→ Optimize with judge agent
  │
  ▼
Response to Frontend
  │
  └─→ {
        "ok": true,
        "data": {
          "mode": "job_tuning",
          "resume_json": {...},
          "optimized_resume_json": {...}
        }
      }
```

### DOCX Workflow Endpoint

```
User Input (Frontend)
  │
  [Same as JSON workflow]
  │
  ▼
FastAPI Server
  │
  [Same validation and workflow]
  │
  ▼
Agent Workflow
  │
  └─→ optimized_resume_json
      │
      ▼
Filename Agent (prepare_resume_for_mcp)
  │
  ├─→ Extract candidate name
  ├─→ Generate intelligent filename
  └─→ Prepare resume data
  │
  ▼
Direct Generation (generate_resume_tool)
  │
  ├─→ Validate with Pydantic
  ├─→ Generate DOCX with python-docx
  ├─→ Save to outbox/jane_smith_resume.docx
  │
  ▼
Response to Frontend
  │
  └─→ Binary DOCX file download
```

## Key Integration Points

### 1. Environment Configuration

Both the agent workflow and API server require:

```bash
# .env file
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional
```

### 2. Shared Dependencies

- **app_agents/workflows**: Workflow orchestration and Filename Agent
- **resume_mcp/tools**: DOCX generation functions
- **resume_gen/generator**: Core resume rendering
- **OpenAI SDK**: Agent execution
- **Pydantic**: Data validation

### 3. Error Handling

The integration provides layered error handling:

1. **FastAPI validation**: Input validation before workflow
2. **Agent workflow**: OpenAI API errors and workflow logic
3. **Filename Agent**: Filename generation with fallback logic
4. **Direct generation**: Resume JSON validation and DOCX generation
5. **Structured responses**: Consistent error format for frontend

## Testing the Integration

### 1. Unit Testing

```bash
# Test API integration
python test_api_integration.py

# Test direct generation
python test_direct_generation.py
```

### 2. Manual Testing

```bash
# Start the server
resume-api

# Test health check
curl http://localhost:8000/

# Test JSON workflow
curl -X POST http://localhost:8000/api/workflow/json \
  -F 'mode=resume' \
  -F 'resumeText=Your resume...'

# Test DOCX generation
curl -X POST http://localhost:8000/api/workflow/docx \
  -F 'mode=job' \
  -F 'resumeText=Your resume...' \
  -F 'jobDescriptionText=Job description...' \
  -o resume.docx
```

### 3. Interactive Testing

Visit `http://localhost:8000/docs` for the Swagger UI with interactive API testing.

## Frontend Integration

Configure the frontend to use the FastAPI server:

```bash
# frontend/.env.local
USE_MOCK=false
PY_WORKFLOW_JSON_URL=http://localhost:8000/api/workflow/json
PY_WORKFLOW_DOCX_URL=http://localhost:8000/api/workflow/docx
```

The frontend already implements the correct API contract and will work seamlessly with the FastAPI server.
