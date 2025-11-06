"""Workflow that extracts structured resume context from freeform text."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

try:  # pragma: no cover - import guard for offline runs
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover - fallback when SDK unavailable
    from typing import Any as _Any

    OpenAI = _Any  # type: ignore[assignment]

from ..client import create_openai_client
from ..prompts import RESUME_EXTRACTION_INSTRUCTIONS
from .base import AgentDefinition, extract_output_text, user_message


RESUME_EXTRACTION_AGENT = AgentDefinition(
    name="Resume Extraction Agent",
    instructions=RESUME_EXTRACTION_INSTRUCTIONS,
    model="gpt-4.1",
    temperature=1.0,
    top_p=1.0,
    max_output_tokens=30000,
)


@dataclass
class ResumeContextResult:
    """Result returned by :func:`extract_resume_context`."""

    text: str
    parsed: Optional[Any]


def extract_resume_context(
    input_text: str,
    *,
    client: Optional[OpenAI] = None,
) -> ResumeContextResult:
    """Run the resume/context extraction workflow."""

    if not input_text.strip():
        raise ValueError("input_text must not be empty")

    if client is None:
        client = create_openai_client()

    conversation = [user_message(input_text)]
    request = RESUME_EXTRACTION_AGENT.build_request(conversation)
    response = client.responses.create(**request)
    text = extract_output_text(response)

    parsed: Optional[Any]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None

    return ResumeContextResult(text=text, parsed=parsed)

