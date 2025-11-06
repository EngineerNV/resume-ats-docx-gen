"""
FastAPI server for orchestrating resume generation workflow.

This server provides REST API endpoints that:
1. Accept resume and job description data from the frontend
2. Orchestrate the OpenAI agent workflow for resume optimization
3. Use the MCP server to generate DOCX files
4. Return JSON suggestions or DOCX downloads to the frontend
"""

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import json
import tempfile
from pathlib import Path

from agents.workflows import ResumeJsonWorkflow
from resume_mcp.tools import generate_resume_tool

app = FastAPI(
    title="Resume ATS DOCX Generator API",
    description="API for generating ATS-optimized resumes",
    version="1.0.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def read_file_content(file: UploadFile) -> str:
    """Read and decode uploaded file content."""
    content = await file.read()
    try:
        return content.decode('utf-8')
    except UnicodeDecodeError:
        # Try common encodings
        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise HTTPException(status_code=400, detail=f"Unable to decode file {file.filename}")


async def combine_text_and_files(text: str, files: List[UploadFile]) -> str:
    """Combine text input with content from uploaded files."""
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
    """Health check endpoint."""
    return {"status": "ok", "message": "Resume ATS DOCX Generator API"}


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
    Process resume workflow and return JSON suggestions.
    
    Args:
        mode: Workflow mode ('resume' for improvement, 'job' for job tuning)
        resumeText: Raw resume text input
        context: Additional context about the candidate
        jobDescriptionText: Job description text
        resumeFiles: Uploaded resume files
        jobDescriptionFiles: Uploaded job description files
    
    Returns:
        JSON response with optimized resume suggestions
    """
    try:
        # Combine text and file inputs
        combined_resume_text = await combine_text_and_files(resumeText, resumeFiles)
        combined_job_description = await combine_text_and_files(jobDescriptionText, jobDescriptionFiles)
        
        # Validate inputs
        if not combined_resume_text or not combined_resume_text.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "code": "VALIDATION_ERROR",
                    "fieldErrors": {
                        "resumeText": ["Resume text is required"]
                    }
                }
            )
        
        # Determine workflow mode
        workflow_mode = "resume_improvement"
        if mode == "job":
            if not combined_job_description or not combined_job_description.strip():
                return JSONResponse(
                    status_code=400,
                    content={
                        "ok": False,
                        "code": "VALIDATION_ERROR",
                        "fieldErrors": {
                            "jobDescriptionText": ["Job description is required in job tuning mode"]
                        }
                    }
                )
            workflow_mode = "job_tuning"
        
        # Prepare additional context
        additional_context = None
        if context and context.strip():
            additional_context = {"user_context": context.strip()}
        
        # Run the agent workflow
        workflow = ResumeJsonWorkflow()
        result = workflow.run(
            mode=workflow_mode,
            resume_text=combined_resume_text,
            job_description=combined_job_description if workflow_mode == "job_tuning" else None,
            additional_context=additional_context,
        )
        
        # Format response to match frontend expectations
        response_data = {
            "mode": result.mode,
            "should_align_to_job": result.should_align_to_job,
            "resume_json": result.resume_json.parsed,
            "optimized_resume_json": result.optimized_resume_json.parsed,
            "personal_summary": result.personal_summary.parsed if result.personal_summary else None,
        }
        
        return JSONResponse(
            status_code=200,
            content={"ok": True, "data": response_data}
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "code": "WORKFLOW_ERROR",
                "message": f"Workflow execution failed: {str(e)}"
            }
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
    Process resume workflow and generate DOCX file.
    
    This endpoint orchestrates the full workflow:
    1. Runs the OpenAI agent workflow to generate optimized resume JSON
    2. Uses the MCP server to convert JSON to DOCX format
    3. Returns the DOCX file for download
    
    Args:
        mode: Workflow mode ('resume' for improvement, 'job' for job tuning)
        resumeText: Raw resume text input
        context: Additional context about the candidate
        jobDescriptionText: Job description text
        resumeFiles: Uploaded resume files
        jobDescriptionFiles: Uploaded job description files
    
    Returns:
        DOCX file download
    """
    try:
        # Combine text and file inputs
        combined_resume_text = await combine_text_and_files(resumeText, resumeFiles)
        combined_job_description = await combine_text_and_files(jobDescriptionText, jobDescriptionFiles)
        
        # Validate inputs
        if not combined_resume_text or not combined_resume_text.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "code": "VALIDATION_ERROR",
                    "fieldErrors": {
                        "resumeText": ["Resume text is required"]
                    }
                }
            )
        
        # Determine workflow mode
        workflow_mode = "resume_improvement"
        if mode == "job":
            if not combined_job_description or not combined_job_description.strip():
                return JSONResponse(
                    status_code=400,
                    content={
                        "ok": False,
                        "code": "VALIDATION_ERROR",
                        "fieldErrors": {
                            "jobDescriptionText": ["Job description is required in job tuning mode"]
                        }
                    }
                )
            workflow_mode = "job_tuning"
        
        # Prepare additional context
        additional_context = None
        if context and context.strip():
            additional_context = {"user_context": context.strip()}
        
        # Run the agent workflow
        workflow = ResumeJsonWorkflow()
        result = workflow.run(
            mode=workflow_mode,
            resume_text=combined_resume_text,
            job_description=combined_job_description if workflow_mode == "job_tuning" else None,
            additional_context=additional_context,
        )
        
        # Get the optimized resume JSON
        optimized_resume = result.optimized_resume_json.parsed
        
        # Use MCP server to generate DOCX
        # The MCP server tool will save to the outbox directory
        filename = "resume.docx"
        mcp_result = generate_resume_tool(
            resume_data=optimized_resume,
            filename=filename
        )
        
        if not mcp_result["success"]:
            return JSONResponse(
                status_code=500,
                content={
                    "ok": False,
                    "code": "DOCX_GENERATION_ERROR",
                    "message": mcp_result["message"],
                    "details": mcp_result.get("details", "")
                }
            )
        
        # Return the generated DOCX file
        docx_path = Path(mcp_result["path"])
        if not docx_path.exists():
            return JSONResponse(
                status_code=500,
                content={
                    "ok": False,
                    "code": "FILE_NOT_FOUND",
                    "message": "Generated DOCX file not found"
                }
            )
        
        return FileResponse(
            path=str(docx_path),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="resume.docx",
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": 'attachment; filename="resume.docx"'
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "code": "WORKFLOW_ERROR",
                "message": f"Workflow execution failed: {str(e)}"
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


def main():
    """Entry point for resume-api command."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

