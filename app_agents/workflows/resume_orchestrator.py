"""
Main orchestrator for resume generation workflow using OpenAI Agents SDK.

This is the single unified entry point for all resume generation workflows.
No compatibility layers, no old patterns - just a clean OpenAI Agents SDK implementation.

Workflow:
1. Prepare input from user data
2. Run OpenAI Agents SDK workflow (resume_json_creator or job_research)
3. Extract optimized JSON
4. Generate intelligent filename
5. Return result ready for DOCX generation
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .resume_json_creator import run_workflow as run_resume_json_workflow, WorkflowInput as ResumeJsonWorkflowInput
from .job_research_agent import run_workflow as run_job_research_workflow, WorkflowInput as JobResearchWorkflowInput
from .resume_context_extractor import run_workflow as run_resume_extraction_workflow, WorkflowInput as ResumeExtractionWorkflowInput


@dataclass
class ResumeWorkflowResult:
    """Result from the resume generation workflow - ready for DOCX generation."""
    
    optimized_resume_json: Dict[str, Any]  # Final optimized resume in standard schema
    filename: str  # Intelligent filename based on candidate name
    mode: str  # "job_tuning" or "resume_improvement"
    job_research_output: Optional[str] = None  # ATS and leadership insights (if job mode)
    reasoning: Optional[str] = None  # Why this optimization was chosen
    

class ResumeOrchestrator:
    """
    Unified orchestrator for OpenAI Agents SDK resume generation.
    
    This is the main entry point - no old patterns, no compatibility wrappers.
    Just clean agent workflow coordination.
    """
    
    def __init__(self):
        """Initialize the orchestrator."""
        pass  # Agents SDK handles client creation internally
    
    async def run(
        self,
        resume_text: str,
        job_description: Optional[str] = None,
        additional_context: Optional[str] = None,
    ) -> ResumeWorkflowResult:
        """
        Run the unified resume generation workflow.
        
        Args:
            resume_text: Raw resume text from user
            job_description: Optional job description for job-tuning mode
            additional_context: Optional additional context about the candidate
            
        Returns:
            ResumeWorkflowResult with optimized JSON ready for DOCX generation
        """
        # Determine mode
        has_job_description = bool(job_description and job_description.strip())
        mode = "job_tuning" if has_job_description else "resume_improvement"
        
        job_research_output = None
        
        # Step 1: Run job research if we have a job description
        if has_job_description:
            job_research_input = self._build_job_research_input(job_description)
            job_research_output = await self._run_job_research(job_research_input)
        
        # Step 2: Run resume optimization workflow
        resume_input = self._build_resume_input(
            resume_text=resume_text,
            job_description=job_description,
            additional_context=additional_context,
            job_research_output=job_research_output,
        )
        
        optimized_resume = await self._run_resume_optimization(resume_input)
        
        # Step 3: Generate intelligent filename
        filename = self._generate_filename(optimized_resume)
        
        # Step 4: Create reasoning
        candidate_name = optimized_resume.get('header', {}).get('name', 'candidate')
        reasoning = f"Generated {mode} resume for {candidate_name}"
        if has_job_description:
            reasoning += " aligned to job requirements"
        
        return ResumeWorkflowResult(
            optimized_resume_json=optimized_resume,
            filename=filename,
            mode=mode,
            job_research_output=job_research_output,
            reasoning=reasoning,
        )
    
    def _build_job_research_input(self, job_description: str) -> str:
        """Build input for job research workflow."""
        return f"JOB DESCRIPTION:\n{job_description}"
    
    def _build_resume_input(
        self,
        resume_text: str,
        job_description: Optional[str],
        additional_context: Optional[str],
        job_research_output: Optional[str],
    ) -> str:
        """Build input for resume optimization workflow."""
        parts = [f"RESUME TEXT:\n{resume_text}"]
        
        if additional_context:
            parts.append(f"ADDITIONAL CONTEXT:\n{additional_context}")
        
        if job_description:
            parts.append(f"JOB DESCRIPTION:\n{job_description}")
        
        if job_research_output:
            parts.append(f"JOB RESEARCH INSIGHTS:\n{job_research_output}")
        
        return "\n\n".join(parts)
    
    async def _run_job_research(self, input_text: str) -> str:
        """Run job research workflow and return clean output."""
        workflow_input = JobResearchWorkflowInput(input_as_text=input_text)
        result = await run_job_research_workflow(workflow_input)

        # The job research workflow returns a string with ATS and leadership insights
        # We just pass it through
        return str(result) if result else ""
    
    async def _run_resume_optimization(self, input_text: str) -> Dict[str, Any]:
        """
        Run resume optimization workflow and get final optimized JSON.
        
        The resume_json_creator workflow runs all agents and returns
        the final optimized JSON from the judge_for_improvement agent.
        """
        # First: try to run the Resume/Context Extractor to produce a structured
        # extract of the resume. If it runs successfully, include its output when
        # calling the resume JSON workflow so downstream agents have structured data.
        try:
            extractor_input = ResumeExtractionWorkflowInput(input_as_text=input_text)
            extracted = await run_resume_extraction_workflow(extractor_input)
        except Exception:
            # If extraction fails for any reason, fall back to raw input_text
            extracted = None

        # Build the input for the resume JSON workflow. Prefer the structured
        # extraction output when available.
        if extracted:
            # If extractor returned a string (JSON-like), include it explicitly.
            # The resume_json_creator workflow expects text input, so pass both
            # the original text and the extracted JSON to give agents the best
            # possible context.
            combined_input = f"EXTRACTED_RESUME_JSON:\n{extracted}\n\nORIGINAL_RESUME_TEXT:\n{input_text}"
        else:
            combined_input = input_text

        workflow_input = ResumeJsonWorkflowInput(input_as_text=combined_input)
        optimized_json = await run_resume_json_workflow(workflow_input)
        return optimized_json

    
    def _generate_filename(self, resume_json: Dict[str, Any]) -> str:
        """
        Generate intelligent filename from resume.
        Format: FirstnameLastname_Resume.docx
        """
        try:
            name = resume_json.get('header', {}).get('name', '')
            if name:
                # Clean: remove special chars, spaces
                clean = ''.join(c for c in name if c.isalnum() or c.isspace())
                clean = clean.replace(' ', '')
                return f"{clean}_Resume.docx"
        except Exception:
            pass
        return "resume.docx"


# Synchronous wrapper
def run_resume_workflow(
    resume_text: str,
    job_description: Optional[str] = None,
    additional_context: Optional[str] = None,
) -> ResumeWorkflowResult:
    """
    Synchronous wrapper for the resume workflow.
    Use this when you can't use async/await.
    """
    orchestrator = ResumeOrchestrator()
    return asyncio.run(
        orchestrator.run(
            resume_text=resume_text,
            job_description=job_description,
            additional_context=additional_context,
        )
    )

