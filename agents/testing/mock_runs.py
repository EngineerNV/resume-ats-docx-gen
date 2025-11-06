"""Recorded mock responses for offline CLI demonstrations."""

from __future__ import annotations

import json
from typing import Iterable, List

from .fake_openai import MockResponseSpec


def _json(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False)


_RESUME_CONTEXT = {
    "header": {
        "name": "Jordan M. Reynolds",
        "email": "jordan.reynolds@example.com",
        "phone": "(555) 123-8472",
        "location": "Cambridge, MA",
        "linkedin": "linkedin.com/in/jordanreynolds",
        "github": "github.com/jreynolds-dev",
    },
    "professional_summary": (
        "Motivated Software Engineer with experience building scalable backend systems and"
        " user-focused product features while collaborating across teams."
    ),
    "skills": {
        "Languages": ["Python", "Go", "JavaScript", "Java", "C++"],
        "Frameworks/Tools": ["React", "Express", "Flask", "Docker", "Kubernetes", "GraphQL", "gRPC"],
        "Databases": ["PostgreSQL", "Redis", "MongoDB"],
        "Cloud": ["Google Cloud Platform", "AWS (EC2, S3, Lambda)"]
    },
    "experience": [
        {
            "role": "Software Engineering Intern",
            "company": "Google",
            "dates": "Summer 2024",
            "location": "Mountain View, CA",
            "bullets": [
                "Built internal API endpoints in Go for a developer telemetry service, reducing data retrieval latency by about 30%.",
                "Implemented structured logging and instrumentation to improve debugging across microservices.",
                "Collaborated with security and infrastructure teams to ensure compliance with API governance standards.",
            ],
        },
        {
            "role": "Software Engineering Intern",
            "company": "Meta",
            "dates": "Summer 2023",
            "location": "Menlo Park, CA",
            "bullets": [
                "Developed React components for internal data visualization dashboards used by product insights analysts.",
                "Added a caching layer to a Python backend service, improving throughput and reducing server costs.",
                "Participated in code reviews, sprint planning, and feature rollouts.",
            ],
        },
        {
            "role": "Teaching Assistant",
            "company": "Harvard University - CS50",
            "dates": "2022 – 2024",
            "location": "Cambridge, MA",
            "bullets": [
                "Led weekly lab sessions and office hours for more than 200 students learning foundational programming concepts.",
                "Reviewed student submissions and provided debugging guidance.",
                "Contributed to exam question development and course improvements.",
            ],
        },
    ],
    "education": [
        {
            "degree": "B.S. Computer Science",
            "institution": "Harvard University",
            "dates": "May 2025",
            "location": "Cambridge, MA",
            "gpa": "",
        }
    ],
    "projects": [
        {
            "name": "Distributed Key-Value Store (Go)",
            "bullets": [
                "Implemented leader election and replication using the Raft consensus protocol for fault tolerance."
            ],
        },
        {
            "name": "Campus Dining Ratings App (React + Node.js)",
            "bullets": [
                "Designed a full-stack system for student-generated dining hall reviews and recommendations."
            ],
        },
    ],
    "awards": ["HackMIT Finalist (2023)", "TechTogether Boston"],
}


_IMPROVEMENT_GUIDANCE = {
    "section_guidance": {
        "header": {
            "status": "present",
            "reasoning": (
                "Resume context clearly lists name, email, phone, location, and profile links at the top of the document."
            ),
            "instructions_for_editor_agent": [
                "Keep contact information on a single header line for ATS readability.",
                "Ensure phone number formatting is consistent with US standards.",
            ],
        },
        "skills": {
            "status": "present",
            "reasoning": (
                "Skills are organized by category but can better distinguish frameworks from cloud and database tooling."
            ),
            "instructions_for_editor_agent": [
                "Map programming languages, frameworks, and cloud/databases into ATS-friendly buckets.",
                "Highlight Go, Python, and distributed systems tooling to reinforce internship experience.",
            ],
            "skill_bucket_adjustments": {
                "Programming Languages": {
                    "add": ["TypeScript"],
                    "de_emphasize": [],
                },
                "Technologies": {
                    "add": ["GraphQL", "gRPC"],
                    "de_emphasize": [],
                },
                "Tools": {
                    "add": ["Google Cloud Platform", "AWS (EC2, S3, Lambda)"],
                    "de_emphasize": [],
                },
            },
        },
        "experience": {
            "status": "present",
            "reasoning": (
                "Three roles include companies, locations, timeframes, and bullets, though several bullets can emphasize outcomes more explicitly."
            ),
            "instructions_for_editor_agent": [
                "Lead each bullet with measurable outcomes before describing actions.",
                "Clarify collaboration scope (cross-team partnerships, student impact) within bullets.",
            ],
            "bullet_improvement_guidelines": [
                "convert bullets to result → action → context form",
                "add quantification placeholders (e.g., [X%]/[Xms]/[X$])",
                "remove filler verbs such as 'helped', 'worked on'",
            ],
        },
        "education": {
            "status": "present",
            "reasoning": (
                "Education section lists degree, institution, graduation timing, and location; GPA is optional and currently unavailable."
            ),
            "instructions_for_editor_agent": [
                "Add relevant coursework only if needed for space; otherwise keep concise.",
            ],
        },
    },
    "potential_add_pending_verification": [
        "Clarify impact metrics for caching improvements and telemetry latency reductions.",
        "Confirm leadership or mentorship responsibilities within teaching assistant role.",
    ],
    "orchestrator_priority_actions": [
        "Quantify performance gains in each internship bullet.",
        "Group technical skills into Programming Languages, Technologies, and Tools buckets.",
        "Highlight distributed systems and developer productivity themes in the summary.",
    ],
}


_PERSONAL_SUMMARY = {
    "agent_id": "resume_applicant",
    "personal_summary": (
        "I am a software engineer who enjoys building scalable backend services and intuitive developer tooling. "
        "I bring hands-on experience from internships at Google and Meta where I reduced telemetry latency, strengthened observability, "
        "and delivered data visualization features. I thrive in collaborative environments, support large student cohorts as a CS50 teaching assistant, "
        "and am eager to tackle distributed systems challenges that improve product velocity."
    ),
}


_RESUME_JSON = {
    "header": {
        "name": "Jordan M. Reynolds",
        "email": "jordan.reynolds@example.com",
        "location": "Cambridge, MA",
        "linkedin": "linkedin.com/in/jordanreynolds",
        "github": "github.com/jreynolds-dev",
    },
    "professional_summary": (
        "Motivated software engineer with internships at Google and Meta, focused on distributed systems, telemetry, and teaching."
    ),
    "skills": {
        "Programming Languages": ["Python", "Go", "JavaScript", "Java", "C++"],
        "Technologies": ["React", "Node.js", "Express", "Flask", "GraphQL", "gRPC"],
        "Tools": [
            "Docker",
            "Kubernetes",
            "PostgreSQL",
            "Redis",
            "MongoDB",
            "Google Cloud Platform",
            "AWS (EC2, S3, Lambda)",
        ],
    },
    "experience": [
        "Software Engineering Intern, Google (Summer 2024): Built Go APIs for developer telemetry, improved latency ~30%, and expanded structured logging across services.",
        "Software Engineering Intern, Meta (Summer 2023): Delivered React analytics dashboards and introduced a Python caching layer that improved throughput and reduced costs.",
        "Teaching Assistant, Harvard University CS50 (2022–2024): Supported 200+ students via labs, office hours, and exam design.",
    ],
    "education": [
        {
            "degree": "B.S. Computer Science",
            "institution": "Harvard University",
            "dates": "May 2025",
            "location": "Cambridge, MA",
            "gpa": "",
        }
    ],
    "awards": ["HackMIT Finalist (2023)", "TechTogether Boston"],
}


_OPTIMIZED_RESUME_JSON = {
    "header": _RESUME_JSON["header"],
    "professional_summary": (
        "Software engineer with internships at Google and Meta delivering telemetry, caching, and developer enablement features while mentoring CS50 students."
    ),
    "skills": {
        "Programming Languages": ["Python", "Go", "JavaScript", "Java", "C++", "TypeScript"],
        "Technologies": ["React", "Node.js", "Express", "Flask", "GraphQL", "gRPC"],
        "Tools": [
            "Docker",
            "Kubernetes",
            "PostgreSQL",
            "Redis",
            "MongoDB",
            "Google Cloud Platform",
            "AWS (EC2, S3, Lambda)",
        ],
    },
    "experience": _RESUME_JSON["experience"],
    "education": _RESUME_JSON["education"],
    "awards": _RESUME_JSON["awards"],
}


def mock_run(name: str) -> Iterable[MockResponseSpec]:
    if name != "jordan_resume_improvement":
        raise KeyError(f"Unknown mock run: {name}")

    return [
        MockResponseSpec(kind="create", text=_json(_RESUME_CONTEXT)),
        MockResponseSpec(kind="parse", parsed=_IMPROVEMENT_GUIDANCE),
        MockResponseSpec(kind="create", text=_json(_PERSONAL_SUMMARY)),
        MockResponseSpec(kind="parse", parsed=_RESUME_JSON),
        MockResponseSpec(kind="parse", parsed=_OPTIMIZED_RESUME_JSON),
    ]


def available_mock_runs() -> List[str]:
    return ["jordan_resume_improvement"]
