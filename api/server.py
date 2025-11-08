"""
FastAPI server for resume generation using OpenAI Agents SDK.

Single unified implementation - no old patterns, clean architecture.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import io
import logging

from docx import Document
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
# Note: legacy .doc support removed. We only accept .docx/.txt/.md on the server.
 

logging.basicConfig(level=logging.INFO)

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



@dataclass(frozen=True)
class UploadedFileMeta:
    """Metadata we care about when decoding UploadFile objects."""

    filename: str
    content_type: str


def _looks_like_pdf(meta: UploadedFileMeta) -> bool:
    return meta.filename.endswith('.pdf') or 'pdf' in meta.content_type


def _looks_like_docx(meta: UploadedFileMeta) -> bool:
    return meta.filename.endswith('.docx') or 'wordprocessingml' in meta.content_type


def _extract_pdf_text(content: bytes, meta: UploadedFileMeta) -> Optional[str]:
    """Return text if the payload appears to be a PDF; otherwise None."""
    if not _looks_like_pdf(meta):
        return None

    try:
        import fitz  # PyMuPDF
    except Exception:
        raise HTTPException(400, "PDF extraction requires the 'pymupdf' package (pip install pymupdf)")

    try:
        doc = fitz.open(stream=content, filetype='pdf')
        pages: list[str] = []
        for page in doc:
            text = page.get_text('text')
            if text and text.strip():
                pages.append(text.strip())
        return "\n\n".join(pages).strip()
    except Exception as exc:
        raise HTTPException(400, f"PDF extraction failed: {exc}")


def _extract_docx_text(content: bytes, meta: UploadedFileMeta) -> Optional[str]:
    """Return DOCX text (paragraphs + tables) if file looks like docx."""
    if not _looks_like_docx(meta):
        return None

    try:
        doc = Document(io.BytesIO(content))
    except Exception:
        # Fall back to plain-text decoding if python-docx cannot parse the file.
        return None

    parts: list[str] = []
    for paragraph in doc.paragraphs:
        if paragraph.text and paragraph.text.strip():
            parts.append(paragraph.text.strip())

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text and cell.text.strip():
                    parts.append(cell.text.strip())

    return "\n\n".join(parts).strip()


def _decode_text_bytes(content: bytes, filename: str) -> str:
    """Best-effort decoding for plaintext formats with helpful errors."""
    try:
        return content.decode('utf-8')
    except UnicodeDecodeError:
        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
    raise HTTPException(400, f"Unable to decode file {filename}")


async def read_file_content(file: UploadFile) -> str:
    """Read and decode uploaded file into plain text."""
    content = await file.read()
    metadata = UploadedFileMeta(
        filename=(getattr(file, 'filename', '') or '').lower(),
        content_type=(getattr(file, 'content_type', '') or '').lower(),
    )

    for extractor in (_extract_pdf_text, _extract_docx_text):
        extracted = extractor(content, metadata)
        if extracted:
            return extracted

    return _decode_text_bytes(content, metadata.filename or 'uploaded file')


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
        logging.info(f"Generated DOCX at {output_path} (exists={output_path.exists()})")
        try:
            logging.info(f"DOCX size: {output_path.stat().st_size} bytes")
        except Exception:
            pass
        
        if not output_path.exists():
            return JSONResponse(
                content={
                    "ok": False,
                    "code": "FILE_NOT_FOUND",
                    "message": "DOCX generation failed"
                },
                status_code=500
            )
        
        # Return the generated DOCX directly. We previously converted DOCX -> PDF
        # in the background; to keep behavior simple we no longer generate or
        # advertise PDFs. The frontend will always receive a DOCX download.
        return FileResponse(
            path=str(output_path),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=result.filename,
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": f'attachment; filename="{result.filename}"',
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
