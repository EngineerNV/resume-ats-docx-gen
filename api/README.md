# FastAPI Server for Resume Workflow

This FastAPI server provides REST API endpoints that orchestrate the resume generation workflow by:
1. Accepting resume and job description data from the frontend
2. Running the OpenAI agent workflow for resume optimization
3. Using the MCP server to generate DOCX files
4. Returning JSON suggestions or DOCX downloads

## Features

- **JSON Workflow Endpoint** (`/api/workflow/json`): Returns optimized resume JSON suggestions
- **DOCX Generation Endpoint** (`/api/workflow/docx`): Generates and downloads ATS-optimized DOCX resume
- **CORS Support**: Configured for local frontend development
- **Direct Generation**: Uses direct function calls for ~100ms performance improvement
- **Agent Orchestration**: Leverages OpenAI agents for resume optimization
- **Filename Agent**: Intelligent document naming based on candidate information
  

## Installation

The FastAPI server is included when you install the package:

```bash
pip install -e .
```

## Configuration

Create a `.env` file in the project root with your OpenAI API key:

```bash
OPENAI_API_KEY=your-api-key-here
```

Optional configuration:
```bash
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional: custom OpenAI endpoint
```

## Running the Server

### Option 1: Using the CLI command

```bash
resume-api
```

### Option 2: Using uvicorn directly

```bash
uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Using Python module

```bash
python -m api.server
```

The server will start on `http://localhost:8000`

## API Endpoints

### Health Check

```bash
GET /
```

Returns server status.

### Generate JSON Suggestions

```bash
POST /api/workflow/json
```

**Form Data Parameters:**
- `mode` (required): Workflow mode - `"resume"` for improvement, `"job"` for job tuning
- `resumeText` (optional): Raw resume text input
- `context` (optional): Additional context about the candidate
- `jobDescriptionText` (optional): Job description text (required if mode is "job")
- `resumeFiles` (optional): Uploaded resume files
- `jobDescriptionFiles` (optional): Uploaded job description files

**Response:**
```json
{
  "ok": true,
  "data": {
    "mode": "resume_improvement",
    "should_align_to_job": false,
    "resume_json": { ... },
    "optimized_resume_json": { ... },
    "personal_summary": "..."
  }
}
```

### Generate DOCX Resume

```bash
POST /api/workflow/docx
```

**Form Data Parameters:**
Same as `/api/workflow/json` endpoint.

**Response:**
Binary DOCX file download with `Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document`

## Integration with Frontend

The frontend should be configured to point to this API server. Set the following environment variables in the frontend's `.env.local`:

```bash
USE_MOCK=false
PY_WORKFLOW_JSON_URL=http://localhost:8000/api/workflow/json
PY_WORKFLOW_DOCX_URL=http://localhost:8000/api/workflow/docx
```

## Direct Generation Architecture

The FastAPI server uses **direct function calls** (not MCP protocol) for optimal performance and simplicity:

### Generation Flow

1. **Agent Workflow**: OpenAI agents optimize the resume JSON
2. **Filename Agent**: Extracts candidate name and generates intelligent filename
3. **Direct Generation**: Calls `generate_resume_tool()` directly (no MCP protocol)
4. **File Storage**: Saves DOCX to `outbox/` directory
5. **Response**: Returns file to frontend

### Code Example

```python
from agents.workflows import ResumeJsonWorkflow
from agents.workflows.mcp_resume_agent import prepare_resume_for_mcp
from resume_mcp.tools import generate_resume_tool

# 1. Run agent workflow
workflow = ResumeJsonWorkflow()
result = workflow.run(resume_text=text, mode="resume_improvement")

# 2. Generate filename
filename_result = prepare_resume_for_mcp(result.optimized_resume_json.parsed)

# 3. Direct DOCX generation (not via MCP protocol)
generation_result = generate_resume_tool(
    resume_data=filename_result.resume_data,
    filename=filename_result.filename
)

# 4. Return file
return FileResponse(generation_result["path"])
```

### Why Direct Generation?

**Benefits over MCP Protocol**:
- **~100ms faster**: No inter-process communication overhead
- **Simpler**: Fewer moving parts, easier to debug
- **Reliable**: No process spawning issues
- **Maintainable**: Single codebase with direct imports

**When to Use MCP Protocol**:
The standalone MCP server (`resume_mcp/server.py`) is still available for:
- Claude Desktop integration
- VS Code Copilot integration
- Other AI client integrations

But the FastAPI workflow uses direct calls for better performance.

### File Location

Generated resumes are saved to the `outbox/` directory in the project root:
```
resume-ats-docx-gen/
└── outbox/
    ├── jane_smith_resume.docx
    ├── john_doe_resume.docx
    └── ...
```

## Error Handling

The API returns structured error responses:

```json
{
  "ok": false,
  "code": "VALIDATION_ERROR",
  "message": "Error description",
  "fieldErrors": {
    "resumeText": ["Resume text is required"]
  }
}
```

Error codes:
- `VALIDATION_ERROR`: Input validation failed
- `WORKFLOW_ERROR`: Agent workflow execution failed
- `DOCX_GENERATION_ERROR`: DOCX generation failed
- `FILE_NOT_FOUND`: Generated file not found
- `NETWORK_ERROR`: Network/connectivity issue

## Development

For local development with auto-reload:

```bash
uvicorn api.server:app --reload
```

## Testing

You can test the endpoints using curl:

```bash
# Test health check
curl http://localhost:8000/

# Test JSON workflow (resume improvement mode)
curl -X POST http://localhost:8000/api/workflow/json \
  -F 'mode=resume' \
  -F 'resumeText=Your resume text here...'

# Test DOCX generation (job tuning mode)
curl -X POST http://localhost:8000/api/workflow/docx \
  -F 'mode=job' \
  -F 'resumeText=Your resume text here...' \
  -F 'jobDescriptionText=Job description here...' \
  -o resume.docx
```

Or use the interactive API documentation at `http://localhost:8000/docs`
