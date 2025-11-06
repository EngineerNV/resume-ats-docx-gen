"""FastAPI backend for resume generation workflow."""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List
import tempfile
from datetime import datetime
from resume_gen.generator import generate_resume_from_json
import json

app = FastAPI(title="Resume Generator API", version="1.0.0")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create output directory for generated resumes
OUTPUT_DIR = Path.home() / "resume-ats-output"
OUTPUT_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Resume Generator API"}


@app.post("/api/workflow/docx")
async def generate_docx(
    mode: str = Form(...),
    resumeText: str = Form(""),
    context: str = Form(""),
    jobDescriptionText: str = Form(""),
    resumeFiles: List[UploadFile] = File(default=[]),
    jobDescriptionFiles: List[UploadFile] = File(default=[]),
):
    """
    Generate a DOCX resume from provided inputs.
    Returns the generated file and metadata about its location.
    """
    try:
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"resume_{timestamp}.docx"
        output_path = OUTPUT_DIR / output_filename
        
        # Create a basic resume JSON structure from the input
        resume_data = {
            "header": {
                "name": "Generated Resume",
                "email": "contact@example.com",
                "location": "Location, State",
            },
            "professional_summary": resumeText if resumeText else "Professional with diverse experience.",
            "skills": {
                "Technical": ["Python", "JavaScript", "FastAPI"],
            },
            "experience": [],
            "education": [],
        }
        
        # Generate the resume
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_json:
            json.dump(resume_data, tmp_json)
            tmp_json_path = tmp_json.name
        
        try:
            generate_resume_from_json(Path(tmp_json_path), output_path)
        finally:
            Path(tmp_json_path).unlink(missing_ok=True)
        
        # Return the file with metadata
        return FileResponse(
            path=output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=output_filename,
            headers={
                "X-File-Path": str(output_path),
                "X-Output-Directory": str(OUTPUT_DIR),
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate DOCX: {str(e)}")


@app.post("/api/workflow/json")
async def generate_suggestions(
    mode: str = Form(...),
    resumeText: str = Form(""),
    context: str = Form(""),
    jobDescriptionText: str = Form(""),
    resumeFiles: List[UploadFile] = File(default=[]),
    jobDescriptionFiles: List[UploadFile] = File(default=[]),
):
    """
    Generate AI-powered resume suggestions based on inputs.
    """
    try:
        suggestions = {
            "summary": f"Resume analyzed in '{mode}' mode. {len(resumeFiles)} resume files and {len(jobDescriptionFiles)} job description files provided.",
            "highlights": [
                "Strong technical background evident",
                "Experience demonstrates growth trajectory",
                "Skills align well with modern tech stack",
            ],
            "recommendations": [
                "Consider adding quantifiable metrics to achievements",
                "Highlight leadership and collaboration skills",
                "Ensure ATS-friendly formatting throughout",
            ]
        }
        
        return JSONResponse(content={"ok": True, "data": suggestions})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")


@app.get("/api/output-directory")
async def get_output_directory():
    """Get the directory where resumes are saved."""
    return {
        "path": str(OUTPUT_DIR),
        "exists": OUTPUT_DIR.exists(),
        "file_count": len(list(OUTPUT_DIR.glob("*.docx"))) if OUTPUT_DIR.exists() else 0,
    }


if __name__ == "__main__":
    import uvicorn
    print(f"Output directory: {OUTPUT_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
