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
- **MCP Integration**: Uses the MCP server tool to generate DOCX files
- **Agent Orchestration**: Leverages OpenAI agents for resume optimization

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

## MCP Server Integration

The FastAPI server integrates with the MCP server by calling the MCP tool functions directly:

1. Using `agents.workflows.ResumeJsonWorkflow` to run the OpenAI agent workflow
2. Calling `resume_mcp.tools.generate_resume_tool` to convert optimized JSON to DOCX
3. The MCP tool saves files to the `outbox/` directory
4. The API returns the generated DOCX file to the client

**Design Note**: The MCP server does not need to be running as a separate process. The FastAPI server calls the MCP tool functions directly as a Python library. This design:
- Simplifies deployment (single process)
- Reduces latency (no network/IPC overhead)
- Improves reliability (no separate process management)
- Maintains the same tool interface for AI agents

The standalone MCP server (`resume-mcp`) is still available for integration with AI clients like Claude Desktop or VS Code Copilot, which connect via the MCP protocol.

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
