# Resume Generator Backend API

FastAPI backend server for the resume generation workflow. This server provides REST API endpoints that the frontend can call to generate resumes and get AI-powered suggestions.

## Features

- **DOCX Generation**: Convert resume data to ATS-optimized DOCX format
- **AI Suggestions**: Get AI-powered recommendations for resume improvement
- **File Management**: Track generated files and their locations
- **CORS Support**: Configured for local development with the Next.js frontend

## Installation

The backend dependencies are included in the main project. Install them with:

```bash
# From the project root
pip install -e .
```

Or install backend-specific requirements:

```bash
cd backend
pip install -r requirements.txt
```

## Running the Server

### Development Mode

```bash
# From the project root
python -m backend.main
```

Or with uvicorn directly:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### `GET /`
Health check endpoint

**Response:**
```json
{
  "status": "ok",
  "service": "Resume Generator API"
}
```

### `POST /api/workflow/docx`
Generate a DOCX resume from form data

**Form Data:**
- `mode`: Workflow mode ("resume" or "job_tuning")
- `resumeText`: Plain text resume content
- `context`: Additional context for generation
- `jobDescriptionText`: Job description (for job_tuning mode)
- `resumeFiles`: Uploaded resume files
- `jobDescriptionFiles`: Uploaded job description files

**Response:**
- DOCX file download with headers:
  - `X-File-Path`: Full path to the generated file
  - `X-Output-Directory`: Directory where files are saved

### `POST /api/workflow/json`
Get AI-powered resume suggestions

**Form Data:** Same as `/api/workflow/docx`

**Response:**
```json
{
  "ok": true,
  "data": {
    "summary": "Analysis summary",
    "highlights": ["highlight 1", "highlight 2"],
    "recommendations": ["recommendation 1", "recommendation 2"]
  }
}
```

### `GET /api/output-directory`
Get information about the output directory

**Response:**
```json
{
  "path": "/path/to/output/directory",
  "exists": true,
  "file_count": 5
}
```

## Output Directory

Generated resumes are saved to: `~/resume-ats-output/`

Files are named with timestamps: `resume_YYYYMMDD_HHMMSS.docx`

## Integration with Frontend

Configure the frontend to use the backend by setting environment variables in `frontend/.env.local`:

```bash
USE_MOCK=false
PY_WORKFLOW_DOCX_URL=http://localhost:8000/api/workflow/docx
PY_WORKFLOW_JSON_URL=http://localhost:8000/api/workflow/json
```

## Development

The backend uses:
- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server
- **python-multipart**: For handling file uploads
- **Resume Generator**: Core resume generation logic from `resume_gen`

## Future Enhancements

- [ ] Integration with agent workflows for AI-powered suggestions
- [ ] File upload processing and text extraction
- [ ] Resume parsing from uploaded DOCX/PDF files
- [ ] Database for tracking generated resumes
- [ ] User authentication and sessions
- [ ] PDF export option for preview
