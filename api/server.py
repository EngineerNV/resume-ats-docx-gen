"""
FastAPI server for resume generation using OpenAI Agents SDK.

Single unified implementation - no old patterns, clean architecture.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
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

# PDF conversion executor (background processing)
pdf_executor = ThreadPoolExecutor(max_workers=2)


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
        
        # Start PDF conversion in background (non-blocking, ~2-5s)
        # User won't wait for this, but it'll be ready when they want to preview/download
        pdf_path = output_path.with_suffix('.pdf')
        asyncio.create_task(convert_docx_to_pdf_async(output_path, pdf_path))
        
        return FileResponse(
            path=str(output_path),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=result.filename,
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": f'attachment; filename="{result.filename}"',
                "X-PDF-Filename": pdf_path.name,  # Tell frontend PDF filename
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


async def convert_docx_to_pdf_async(docx_path: Path, pdf_path: Path):
    """
    Convert DOCX to PDF in background (non-blocking).
    
    Started immediately after DOCX generation.
    Usually completes in 2-5 seconds.
    User doesn't wait - PDF will be ready when they want to preview/download.
    
    Args:
        docx_path: Path to source DOCX file
        pdf_path: Path to output PDF file
    """
    loop = asyncio.get_event_loop()
    
    def _convert():
        try:
            from docx2pdf import convert
            convert(str(docx_path), str(pdf_path))
            print(f"✅ PDF ready: {pdf_path.name}")
        except Exception as e:
            print(f"❌ PDF conversion failed: {e}")
            import traceback
            traceback.print_exc()
    
    await loop.run_in_executor(pdf_executor, _convert)


@app.get("/api/pdf/status/{filename}")
async def check_pdf_status(filename: str):
    """
    Check if PDF is ready (non-blocking check).
    
    Called when user clicks "Preview PDF" or "Download PDF".
    
    Args:
        filename: PDF filename to check (e.g., "JohnDoe_Resume.pdf")
    
    Returns:
        - 200: PDF ready with file info
        - 202: Still converting
        - 404: DOCX/PDF not found
    """
    pdf_path = Path("outbox") / filename
    
    if pdf_path.exists():
        return JSONResponse(
            content={
                "ok": True,
                "ready": True,
                "filename": filename,
                "size": pdf_path.stat().st_size
            },
            status_code=200
        )
    else:
        # Check if DOCX exists (PDF might still be converting)
        docx_filename = filename.replace('.pdf', '.docx')
        docx_path = Path("outbox") / docx_filename
        
        if docx_path.exists():
            return JSONResponse(
                content={
                    "ok": True,
                    "ready": False,
                    "message": "PDF conversion in progress"
                },
                status_code=202
            )
        else:
            return JSONResponse(
                content={
                    "ok": False,
                    "ready": False,
                    "message": "File not found"
                },
                status_code=404
            )


@app.get("/api/pdf/view/{filename}")
async def view_pdf(filename: str):
    """
    Serve PDF for inline viewing (not download).
    
    Used by PDF preview widget in frontend.
    
    Args:
        filename: PDF filename (e.g., "JohnDoe_Resume.pdf")
    
    Returns:
        PDF file with inline Content-Disposition
    """
    pdf_path = Path("outbox") / filename
    
    if pdf_path.exists():
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=filename,
            headers={
                "Cache-Control": "public, max-age=3600",
                # inline = show in browser, not download
                "Content-Disposition": f'inline; filename="{filename}"'
            }
        )
    else:
        return JSONResponse(
            content={"ok": False, "message": "PDF not ready yet"},
            status_code=404
        )


@app.get("/api/download/pdf/{filename}")
async def download_pdf(filename: str):
    """
    Download PDF file (attachment, not inline).
    
    Args:
        filename: PDF filename (e.g., "JohnDoe_Resume.pdf")
    
    Returns:
        PDF file download
    """
    pdf_path = Path("outbox") / filename
    
    if pdf_path.exists():
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=filename,
            headers={
                "Cache-Control": "public, max-age=3600",
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    else:
        return JSONResponse(
            content={"ok": False, "message": "PDF not found"},
            status_code=404
        )


def main():
    """Start the server."""
