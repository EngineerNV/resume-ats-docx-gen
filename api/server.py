"""
FastAPI server for resume generation using OpenAI Agents SDK.

Single unified implementation - no old patterns, clean architecture.
"""

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pathlib import Path

from app_agents.workflows import ResumeOrchestrator
from resume_gen.generator import ResumeGenerator

app = FastAPI(
    title="Resume ATS DOCX Generator",
    description="AI-powered ATS-optimized resume generation using OpenAI Agents SDK",
    version="2.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def read_file_content(file: UploadFile) -> str:
    """Read and decode uploaded file."""
    content = await file.read()
    try:
        return content.decode('utf-8')
    except UnicodeDecodeError:
        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise HTTPException(400, f"Unable to decode file {file.filename}")


async def combine_text_and_files(text: str, files: List[UploadFile]) -> str:
    """Combine text input with file contents."""
    parts = []
    if text and text.strip():
        parts.append(text.strip())
    
    for file in files:
        content = await read_file_content(file)
        if content.strip():
            parts.append(content.strip())
    
    return "\n\n".join(parts)


@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "ok",
        "message": "Resume ATS DOCX Generator (OpenAI Agents SDK)",
        "version": "2.0.0"
    }


@app.post("/api/workflow/json")
async def workflow_json(
    mode: str = Form(...),
    resumeText: str = Form(""),
    context: str = Form(""),
    jobDescriptionText: str = Form(""),
    resumeFiles: List[UploadFile] = File(default=[]),
    jobDescriptionFiles: List[UploadFile] = File(default=[]),
):
    """
    Generate optimized resume JSON using OpenAI Agents SDK.
    
    Args:
        mode: 'resume' for improvement, 'job' for job tuning
        resumeText: Resume text
        context: Additional context
        jobDescriptionText: Job description (required for 'job' mode)
        resumeFiles: Resume file uploads
        jobDescriptionFiles: Job description file uploads
    
    Returns:
        JSON with optimized resume data
    """
    try:
        # Combine inputs
        resume_text = await combine_text_and_files(resumeText, resumeFiles)
        job_description = await combine_text_and_files(jobDescriptionText, jobDescriptionFiles)
        
        # Validate
        if not resume_text:
            return JSONResponse(
                content={
                    "ok": False,
                    "code": "VALIDATION_ERROR",
                    "fieldErrors": {"resumeText": ["Resume text is required"]}
                },
                status_code=400
            )
        
        if mode == "job" and not job_description:
            return JSONResponse(
                content={
                    "ok": False,
                    "code": "VALIDATION_ERROR",
                    "fieldErrors": {"jobDescriptionText": ["Job description required in job mode"]}
                },
                status_code=400
            )
        
        # Run workflow
        orchestrator = ResumeOrchestrator()
        result = await orchestrator.run(
            resume_text=resume_text,
            job_description=job_description if mode == "job" else None,
            additional_context=context.strip() if context else None,
        )
        
        return JSONResponse(
            content={
                "ok": True,
                "data": {
                    "mode": result.mode,
                    "filename": result.filename,
                    "optimized_resume_json": result.optimized_resume_json,
                    "job_research_output": result.job_research_output,
                    "reasoning": result.reasoning,
                }
            },
            status_code=200
        )
        
    except Exception as e:
        import traceback
        return JSONResponse(
            content={
                "ok": False,
                "code": "WORKFLOW_ERROR",
                "message": str(e),
                "traceback": traceback.format_exc()
            },
            status_code=500
        )


@app.post("/api/workflow/docx")
async def workflow_docx(
    mode: str = Form(...),
    resumeText: str = Form(""),
    context: str = Form(""),
    jobDescriptionText: str = Form(""),
    resumeFiles: List[UploadFile] = File(default=[]),
    jobDescriptionFiles: List[UploadFile] = File(default=[]),
):
    """
    Generate optimized resume DOCX file using OpenAI Agents SDK.
    
    Complete workflow:
    1. Run OpenAI agent workflow for optimization
    2. Generate intelligent filename
    3. Create DOCX using resume_gen
    4. Return file download
    
    Args:
        mode: 'resume' for improvement, 'job' for job tuning
        resumeText: Resume text
        context: Additional context
        jobDescriptionText: Job description (required for 'job' mode)
        resumeFiles: Resume file uploads
        jobDescriptionFiles: Job description file uploads
    
    Returns:
        DOCX file download
    """
    try:
        # Combine inputs
        resume_text = await combine_text_and_files(resumeText, resumeFiles)
        job_description = await combine_text_and_files(jobDescriptionText, jobDescriptionFiles)
        
        # Validate
        if not resume_text:
            return JSONResponse(
                content={
                    "ok": False,
                    "code": "VALIDATION_ERROR",
                    "fieldErrors": {"resumeText": ["Resume text is required"]}
                },
                status_code=400
            )
        
        if mode == "job" and not job_description:
            return JSONResponse(
                content={
                    "ok": False,
                    "code": "VALIDATION_ERROR",
                    "fieldErrors": {"jobDescriptionText": ["Job description required in job mode"]}
                },
                status_code=400
            )
        
        # Run workflow
        orchestrator = ResumeOrchestrator()
        result = await orchestrator.run(
            resume_text=resume_text,
            job_description=job_description if mode == "job" else None,
            additional_context=context.strip() if context else None,
        )
        
        # Generate DOCX
        output_dir = Path("outbox")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / result.filename
        
        generator = ResumeGenerator(result.optimized_resume_json)
        generator.generate(output_path)
        
        if not output_path.exists():
            return JSONResponse(
                content={
                    "ok": False,
                    "code": "FILE_NOT_FOUND",
                    "message": "DOCX generation failed"
                },
                status_code=500
            )
        
        return FileResponse(
            path=str(output_path),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=result.filename,
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": f'attachment; filename="{result.filename}"'
            }
        )
        
    except Exception as e:
        import traceback
        return JSONResponse(
            content={
                "ok": False,
                "code": "WORKFLOW_ERROR",
                "message": str(e),
                "traceback": traceback.format_exc()
            },
            status_code=500
        )


def main():
    """Start the server."""
