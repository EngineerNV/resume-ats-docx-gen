"""Command-line helper to run the resume JSON workflow with sample data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from agents.workflows import ResumeJsonWorkflow, WorkflowMode
from agents.testing.fake_openai import FakeOpenAI
from agents.testing.mock_runs import available_mock_runs, mock_run

SAMPLE_RESUME_TEXT = """
Jane Doe
Email: jane.doe@example.com
Location: San Francisco, CA
LinkedIn: https://linkedin.com/in/janedoe
GitHub: https://github.com/janedoe

SUMMARY
Full-stack software engineer with 6 years of experience building cloud-native services and data-intensive products.

EXPERIENCE
Senior Software Engineer, CloudScale Labs (2021-Present)
- Led development of a multi-region event-driven architecture handling 5B events/day.
- Partnered with SRE team to improve reliability with automated canary analysis and load testing.

Software Engineer, DataWorks (2018-2021)
- Built ETL pipelines in Python and Airflow to power analytics for 50 enterprise customers.
- Collaborated with product to deliver personalization features using GCP data warehouse tooling.

EDUCATION
B.S. Computer Science, University of California, Berkeley (2014-2018)
""".strip()

SAMPLE_JOB_DESCRIPTION = """
Software Engineer, Google Cloud Platform
Join the team building reliable distributed systems that power Google Cloud products. Responsibilities include designing large-scale services, collaborating across disciplines, and ensuring solutions meet security and reliability goals. Strong proficiency in Python or Go, experience with GCP services, Kubernetes, and distributed systems design is required.
""".strip()

SAMPLE_ATS_KEYWORDS = [
    "Python",
    "Google Cloud Platform",
    "Kubernetes",
    "distributed systems",
    "SRE",
]


def _load_text(source: Optional[str], fallback: str) -> str:
    if source is None:
        return fallback
    path = Path(source)
    return path.read_text(encoding="utf-8")


def _load_json(source: Optional[str]) -> Optional[Any]:
    if source is None:
        return None
    path = Path(source)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_ats_keywords(raw: Optional[str]) -> Optional[Sequence[str]]:
    if raw is None:
        return None
    parts = [chunk.strip() for chunk in raw.replace("\n", ",").split(",")]
    keywords = [part for part in parts if part]
    return keywords or None


def run_resume_workflow(
    *,
    mode: WorkflowMode,
    resume_text: str,
    job_description: Optional[str],
    ats_keywords: Optional[Sequence[str]],
    additional_context: Optional[Any],
    client: Optional[Any] = None,
) -> Dict[str, Any]:
    """Execute the workflow and return a serialisable payload."""

    workflow = ResumeJsonWorkflow(client=client)
    result = workflow.run(
        mode=mode,
        resume_text=resume_text,
        job_description=job_description,
        ats_keywords=ats_keywords,
        additional_context=additional_context,
    )

    payload: Dict[str, Any] = {
        "mode": result.mode,
        "should_align_to_job": result.should_align_to_job,
        "resume_context": result.resume_context.parsed,
        "resume_json": result.resume_json.parsed,
        "optimized_resume_json": result.optimized_resume_json.parsed,
        "flow_manager_decision": getattr(result.flow_manager_decision, "parsed", None),
        "job_alignment_guidance": getattr(result.job_alignment_guidance, "parsed", None),
        "resume_improvement_guidance": getattr(result.resume_improvement_guidance, "parsed", None),
        "personal_summary": getattr(result.personal_summary, "parsed", None),
    }

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the resume workflow against sample or user-provided data and print the"
            " optimized resume JSON output."
        )
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "job_tuning", "resume_improvement"],
        default="auto",
        help="Workflow mode to execute (defaults to auto-detection).",
    )
    parser.add_argument(
        "--resume-file",
        help="Path to a text file containing the raw resume input. Uses built-in sample if omitted.",
    )
    parser.add_argument(
        "--job-description-file",
        help=(
            "Path to a text file with the job description. Required when mode is job_tuning"
            " unless ATS keywords are provided. Uses built-in sample if omitted."
        ),
    )
    parser.add_argument(
        "--ats-keywords",
        help="Comma or newline separated ATS keywords. Uses built-in sample when omitted in job_tuning mode.",
    )
    parser.add_argument(
        "--additional-context",
        help="Path to a JSON file containing extra context to forward to the workflow.",
    )
    parser.add_argument(
        "--output",
        help="Optional path to write the aggregated workflow response as JSON.",
    )
    parser.add_argument(
        "--mock-run",
        choices=available_mock_runs(),
        help=(
            "Name of a recorded mock response sequence to replay instead of calling the"
            " OpenAI API."
        ),
    )

    args = parser.parse_args()

    resume_text = _load_text(args.resume_file, SAMPLE_RESUME_TEXT)
    job_description: Optional[str] = None
    if args.job_description_file:
        job_description = _load_text(args.job_description_file, "")

    if args.mode == "job_tuning":
        job_description = job_description or SAMPLE_JOB_DESCRIPTION
        ats_keywords = _parse_ats_keywords(args.ats_keywords) or SAMPLE_ATS_KEYWORDS
    else:
        ats_keywords = _parse_ats_keywords(args.ats_keywords)

    additional_context = _load_json(args.additional_context)

    client = None
    if args.mock_run:
        client = FakeOpenAI.from_specs(mock_run(args.mock_run))

    payload = run_resume_workflow(
        mode=args.mode,  # type: ignore[arg-type]
        resume_text=resume_text,
        job_description=job_description,
        ats_keywords=ats_keywords,
        additional_context=additional_context,
        client=client,
    )

    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
