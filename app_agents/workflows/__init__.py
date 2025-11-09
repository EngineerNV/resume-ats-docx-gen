"""
OpenAI Agents SDK workflows for resume generation.

Clean unified architecture - single entry point through ResumeOrchestrator.
"""

from .resume_orchestrator import ResumeOrchestrator, ResumeWorkflowResult, run_resume_workflow
# Backwards-compat: export the old compatibility wrapper so older tests and
# scripts that import `ResumeJsonWorkflow` from `app_agents.workflows` keep
# working.
from .workflow_compat import ResumeJsonWorkflow, ResumeJsonWorkflowResult, WorkflowMode

__all__ = [
    "ResumeOrchestrator",
    "ResumeWorkflowResult",
    "run_resume_workflow",
    "ResumeJsonWorkflow",
    "ResumeJsonWorkflowResult",
    "WorkflowMode",
]

