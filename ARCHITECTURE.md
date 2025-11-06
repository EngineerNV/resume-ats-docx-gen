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
│                          │ Pass JSON to MCP Client               │
│                          │                                       │
│  ┌───────────────────────▼─────────────────────────────────┐   │
│  │              MCP Client (api.mcp_client)                 │   │
│  │                                                           │   │
│  │  - Spawns MCP server subprocess                          │   │
│  │  - Communicates via stdio (MCP protocol)                │   │
│  │  - Calls generate_resume tool on server                 │   │
│  │                                                           │   │
│  └───────────────────────┬─────────────────────────────────┘   │
└──────────────────────────┼───────────────────────────────────────┘
                           │ MCP Protocol (stdio)
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                    MCP Server Process                             │
│                  (resume_mcp.server)                              │
│                                                                   │
│  - Receives tool call via MCP protocol                           │
│  - Validates resume JSON with Pydantic                           │
│  - Generates DOCX using python-docx                              │
│  - Saves to outbox/ directory                                    │
│  - Returns result via MCP protocol                               │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Component Integration

### 1. FastAPI Server → OpenAI Agent Workflow

**File**: `api/server.py`

```python
from agents.workflows import ResumeJsonWorkflow

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

### 2. FastAPI Server → MCP Client → MCP Server

**File**: `api/server.py` and `api/mcp_client.py`

```python
from api.mcp_client import generate_resume_via_mcp

# The MCP client spawns an MCP server subprocess and communicates via MCP protocol
mcp_result = generate_resume_via_mcp(
    resume_data=optimized_resume,
    filename="resume.docx"
)
```

**MCP Client** (`api/mcp_client.py`):
- Spawns MCP server as subprocess using `python -m resume_mcp.server`
- Establishes stdio transport connection
- Sends MCP protocol messages (tool calls)
- Receives responses from MCP server
- Handles errors and connection management

**MCP Server** (`resume_mcp/server.py`):
- Runs as independent process
- Listens on stdio for MCP protocol messages
- Exposes `generate_resume` tool
- Validates resume JSON with Pydantic
- Generates DOCX using python-docx
- Returns results via MCP protocol

**Benefits**:
- Proper client-server architecture
- Protocol-based communication (not direct function calls)
- MCP server can be independently scaled or deployed
- Maintains MCP standards for AI agent integration

### 3. Standalone MCP Server Usage

**File**: `resume_mcp/server.py`

For AI client integration (Claude Desktop, VS Code Copilot):

```bash
python -m resume_mcp.server
```

The standalone MCP server exposes the same tools via the MCP protocol for external AI agents.

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
MCP Tool (generate_resume_tool)
  │
  ├─→ Validate with Pydantic
  ├─→ Generate DOCX with python-docx
  ├─→ Save to outbox/resume.docx
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

- **agents/workflows**: Workflow orchestration
- **resume_mcp/tools**: DOCX generation
- **resume_gen/generator**: Core resume rendering
- **OpenAI SDK**: Agent execution
- **Pydantic**: Data validation

### 3. Error Handling

The integration provides layered error handling:

1. **FastAPI validation**: Input validation before workflow
2. **Agent workflow**: OpenAI API errors and workflow logic
3. **MCP tools**: Resume JSON validation and DOCX generation
4. **Structured responses**: Consistent error format for frontend

## Testing the Integration

### 1. Unit Testing

```bash
# Test MCP integration
python test_api_integration.py
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
