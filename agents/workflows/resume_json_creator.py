"""Workflow that orchestrates resume JSON creation using OpenAI agents."""

from __future__ import annotations

import json
from dataclasses import dataclass
import re
from typing import Any, Dict, List, Literal, Optional, Sequence, Union

try:  # pragma: no cover - import guard for offline runs
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover - fallback when SDK unavailable
    from typing import Any as _Any

    OpenAI = _Any  # type: ignore[assignment]

from ..client import create_openai_client
from ..prompts import (
    IMPROVE_CURRENT_RESUME_INSTRUCTIONS,
    JUDGE_FOR_IMPROVEMENT_INSTRUCTIONS,
    PERSONAL_STATEMENT_INSTRUCTIONS,
    RESUME_FLOW_MANAGER_INSTRUCTIONS,
    RESUME_JSON_BUILDER_INSTRUCTIONS,
    TUNE_RESUME_TO_JD_INSTRUCTIONS,
)
from .base import AgentDefinition, extract_output_text, text_item, user_message
from .resume_context_extractor import ResumeContextResult, extract_resume_context


def _json_schema(name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "json_schema",
        "name": name,
        "schema": schema,
    }


_CODE_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def _string_array_schema() -> Dict[str, Any]:
    return {"type": "array", "items": {"type": "string"}}


def _object_schema(properties: Dict[str, Any], required: Sequence[str]) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": False,
    }


def _skill_bucket_adjustments_schema() -> Dict[str, Any]:
    def bucket_schema() -> Dict[str, Any]:
        return _object_schema(
            {
                "add": _string_array_schema(),
                "de_emphasize": _string_array_schema(),
            },
            ["add", "de_emphasize"],
        )

    return _object_schema(
        {
            "Programming Languages": bucket_schema(),
            "Technologies": bucket_schema(),
            "Tools": bucket_schema(),
        },
        ["Programming Languages", "Technologies", "Tools"],
    )


def _section_schema(
    *, include_buckets: bool = False, include_bullet_guidelines: bool = False
) -> Dict[str, Any]:
    properties: Dict[str, Any] = {
        "status": {"type": "string", "enum": ["present", "missing"]},
        "reasoning": {"type": "string"},
        "instructions_for_editor_agent": _string_array_schema(),
    }
    required = ["status", "reasoning", "instructions_for_editor_agent"]

    if include_buckets:
        properties["skill_bucket_adjustments"] = _skill_bucket_adjustments_schema()
        required.append("skill_bucket_adjustments")

    if include_bullet_guidelines:
        properties["bullet_improvement_guidelines"] = _string_array_schema()
        required.append("bullet_improvement_guidelines")

    return _object_schema(properties, required)


TUNE_RESUME_TO_JD_SCHEMA = _object_schema(
    {
        "target_role_priorities": _object_schema(
            {
                "key_competencies": _string_array_schema(),
                "technical_focus": _string_array_schema(),
                "soft_skills_or_domain_focus": _string_array_schema(),
                "critical_ats_keywords": _string_array_schema(),
            },
            [
                "key_competencies",
                "technical_focus",
                "soft_skills_or_domain_focus",
                "critical_ats_keywords",
            ],
        ),
        "coverage_comparison": _object_schema(
            {
                "covered_strong": _string_array_schema(),
                "covered_but_needs_emphasis": _string_array_schema(),
                "missing_or_unclear_pending_verification": _string_array_schema(),
            },
            [
                "covered_strong",
                "covered_but_needs_emphasis",
                "missing_or_unclear_pending_verification",
            ],
        ),
        "section_guidance": _object_schema(
            {
                "header": _section_schema(),
                "skills": _section_schema(include_buckets=True),
                "experience": _section_schema(include_bullet_guidelines=True),
                "education": _section_schema(),
            },
            ["header", "skills", "experience", "education"],
        ),
        "potential_add_pending_verification": _string_array_schema(),
        "orchestrator_priority_actions": _string_array_schema(),
    },
    [
        "target_role_priorities",
        "coverage_comparison",
        "section_guidance",
        "potential_add_pending_verification",
        "orchestrator_priority_actions",
    ],
)


IMPROVE_CURRENT_RESUME_SCHEMA = _object_schema(
    {
        "section_guidance": _object_schema(
            {
                "header": _section_schema(),
                "skills": _section_schema(include_buckets=True),
                "experience": _section_schema(include_bullet_guidelines=True),
                "education": _section_schema(),
            },
            ["header", "skills", "experience", "education"],
        ),
        "potential_add_pending_verification": _string_array_schema(),
        "orchestrator_priority_actions": _string_array_schema(),
    },
    [
        "section_guidance",
        "potential_add_pending_verification",
        "orchestrator_priority_actions",
    ],
)


EDUCATION_ENTRY_SCHEMA = _object_schema(
    {
        "degree": {"type": "string"},
        "institution": {"type": "string"},
        "dates": {"type": "string"},
        "location": {"type": "string"},
        "gpa": {"type": "string"},
    },
    ["degree", "institution", "dates", "location", "gpa"],
)


SKILLS_BUCKET_SCHEMA = _object_schema(
    {
        "Programming Languages": _string_array_schema(),
        "Technologies": _string_array_schema(),
        "Tools": _string_array_schema(),
    },
    ["Programming Languages", "Technologies", "Tools"],
)


RESUME_JSON_BASE_SCHEMA = _object_schema(
    {
        "header": _object_schema(
            {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "location": {"type": "string"},
                "linkedin": {"type": "string"},
                "github": {"type": "string"},
            },
            ["name", "email", "location", "linkedin", "github"],
        ),
        "professional_summary": {"type": "string"},
        "skills": SKILLS_BUCKET_SCHEMA,
        "experience": {"type": "array", "items": {"type": "string"}},
        "education": {
            "type": "array",
            "items": EDUCATION_ENTRY_SCHEMA,
        },
        "awards": {"type": "array", "items": {"type": "string"}},
    },
    [
        "header",
        "professional_summary",
        "skills",
        "experience",
        "education",
        "awards",
    ],
)


RESUME_FLOW_MANAGER = AgentDefinition(
    name="Resume Flow Manager",
    instructions=RESUME_FLOW_MANAGER_INSTRUCTIONS,
    model="gpt-4o",
    response_format=_json_schema(
        "ResumeFlowManager",
        {
            "type": "object",
            "properties": {
                "output": {"type": "boolean"},
            },
            "required": ["output"],
        },
    ),
)


TUNE_RESUME_TO_JD = AgentDefinition(
    name="Tune Resume to JD Agent",
    instructions=TUNE_RESUME_TO_JD_INSTRUCTIONS,
    model="o4-mini",
    reasoning={"effort": "medium", "summary": "detailed"},
    max_output_tokens=6000,
    response_format=_json_schema(
        "TuneResumeToJDGuidance",
        TUNE_RESUME_TO_JD_SCHEMA,
    ),
)


IMPROVE_CURRENT_RESUME = AgentDefinition(
    name="Improve Current Resume Agent",
    instructions=IMPROVE_CURRENT_RESUME_INSTRUCTIONS,
    model="o4-mini",
    reasoning={"effort": "medium", "summary": "auto"},
    max_output_tokens=6000,
    response_format=_json_schema(
        "ImproveCurrentResumeGuidance",
        IMPROVE_CURRENT_RESUME_SCHEMA,
    ),
)


JUDGE_FOR_IMPROVEMENT = AgentDefinition(
    name="Judge for Improvement",
    instructions=JUDGE_FOR_IMPROVEMENT_INSTRUCTIONS,
    model="gpt-4.1",
    temperature=0.6,
    response_format=_json_schema(
        "JudgeForImprovement",
        RESUME_JSON_BASE_SCHEMA,
    ),
)


RESUME_JSON_BUILDER = AgentDefinition(
    name="Resume JSON Builder Agent",
    instructions=RESUME_JSON_BUILDER_INSTRUCTIONS,
    model="gpt-4.1-mini",
    temperature=0.65,
    response_format=_json_schema(
        "ResumeJsonBuilderAgentSchema",
        RESUME_JSON_BASE_SCHEMA,
    ),
)


PERSONAL_STATEMENT_AGENT = AgentDefinition(
    name="Personal Statement Agent",
    instructions=PERSONAL_STATEMENT_INSTRUCTIONS,
    model="gpt-4o",
    temperature=0.7,
    max_output_tokens=9880,
)


WorkflowMode = Literal["auto", "job_tuning", "resume_improvement"]


@dataclass
class AgentRunData:
    """Container for an individual agent invocation output."""

    text: str
    parsed: Optional[Any]


@dataclass
class ResumeJsonWorkflowResult:
    """Aggregated result from running the resume JSON workflow."""

    mode: WorkflowMode
    should_align_to_job: bool
    resume_context: ResumeContextResult
    flow_manager_decision: Optional[AgentRunData]
    job_alignment_guidance: Optional[AgentRunData]
    resume_improvement_guidance: Optional[AgentRunData]
    personal_summary: Optional[AgentRunData]
    resume_json: Optional[AgentRunData]
    optimized_resume_json: Optional[AgentRunData]
    conversation: Sequence[Dict[str, Any]]


class ResumeJsonWorkflow:
    """High level orchestration of resume planning and generation agents."""

    def __init__(self, client: Optional[OpenAI] = None) -> None:
        self.client = client or create_openai_client()

    def run(
        self,
        *,
        resume_text: str,
        mode: WorkflowMode = "auto",
        job_description: Optional[str] = None,
        ats_keywords: Optional[Union[Sequence[str], str]] = None,
        additional_context: Optional[Any] = None,
    ) -> ResumeJsonWorkflowResult:
        """Execute the resume JSON workflow."""

        resume_context = extract_resume_context(resume_text, client=self.client)
        normalized_keywords = self._normalize_ats_keywords(ats_keywords)

        payload: Dict[str, Any] = {
            "mode": mode,
            "resume_text": resume_text,
            "resume_context": resume_context.parsed or resume_context.text,
        }
        if job_description:
            payload["job_description"] = job_description
        if normalized_keywords is not None:
            payload["ats_keywords"] = normalized_keywords
        if additional_context is not None:
            payload["additional_context"] = additional_context

        conversation: List[Dict[str, Any]] = [
            user_message(json.dumps(payload, ensure_ascii=False, indent=2))
        ]

        flow_manager_decision: Optional[AgentRunData]
        should_align_to_job: bool

        if mode == "job_tuning":
            if not job_description and not normalized_keywords:
                raise ValueError(
                    "job_tuning mode requires job_description or ats_keywords"
                )
            flow_manager_decision = None
            should_align_to_job = True
            self._append_assistant_text(conversation, json.dumps({"output": True}))
        elif mode == "resume_improvement":
            flow_manager_decision = None
            should_align_to_job = False
            self._append_assistant_text(conversation, json.dumps({"output": False}))
        else:
            flow_manager_decision = self._call_agent(
                RESUME_FLOW_MANAGER, conversation, expect_json=True
            )
            should_align_to_job = bool(flow_manager_decision.parsed["output"])
            self._append_assistant_text(conversation, flow_manager_decision.text)

        job_alignment_guidance: Optional[AgentRunData] = None
        resume_improvement_guidance: Optional[AgentRunData] = None

        if should_align_to_job:
            job_alignment_guidance = self._call_agent(
                TUNE_RESUME_TO_JD, conversation, expect_json=True
            )
            self._append_assistant_text(conversation, job_alignment_guidance.text)
        else:
            resume_improvement_guidance = self._call_agent(
                IMPROVE_CURRENT_RESUME, conversation, expect_json=True
            )
            self._append_assistant_text(
                conversation, resume_improvement_guidance.text
            )

        personal_summary = self._call_agent(
            PERSONAL_STATEMENT_AGENT, conversation, expect_json=True
        )
        self._append_assistant_text(conversation, personal_summary.text)

        resume_json = self._call_agent(
            RESUME_JSON_BUILDER, conversation, expect_json=True
        )
        self._append_assistant_text(conversation, resume_json.text)

        optimized_resume_json = self._call_agent(
            JUDGE_FOR_IMPROVEMENT, conversation, expect_json=True
        )
        self._append_assistant_text(conversation, optimized_resume_json.text)

        return ResumeJsonWorkflowResult(
            mode=mode,
            should_align_to_job=should_align_to_job,
            resume_context=resume_context,
            flow_manager_decision=flow_manager_decision,
            job_alignment_guidance=job_alignment_guidance,
            resume_improvement_guidance=resume_improvement_guidance,
            personal_summary=personal_summary,
            resume_json=resume_json,
            optimized_resume_json=optimized_resume_json,
            conversation=conversation,
        )

    def _call_agent(
        self,
        agent: AgentDefinition,
        conversation: Sequence[Dict[str, Any]],
        *,
        expect_json: bool = False,
    ) -> AgentRunData:
        request = agent.build_request(conversation)
        if agent.response_format is not None:
            response = self.client.responses.parse(**request)
        else:
            response = self.client.responses.create(**request)

        response_dict: Optional[Dict[str, Any]] = None
        if hasattr(response, "model_dump"):
            try:
                response_dict = response.model_dump()  # type: ignore[call-arg]
            except Exception:  # pragma: no cover - defensive
                response_dict = None

        parsed: Optional[Any] = None
        if expect_json and parsed is None and hasattr(response, "output"):
            try:
                first_block = next(iter(response.output), None)  # type: ignore[attr-defined]
                if first_block is not None:
                    content_items = getattr(first_block, "content", None)
                    if content_items:
                        first_item = content_items[0]
                        if isinstance(first_item, dict):
                            candidate = first_item.get("parsed")
                        else:
                            candidate = getattr(first_item, "parsed", None)
                        if candidate is not None:
                            if hasattr(candidate, "model_dump"):
                                candidate = candidate.model_dump()
                            parsed = candidate
            except Exception:  # pragma: no cover - best-effort fallback
                parsed = None

        if expect_json and parsed is None and response_dict is not None:
            try:
                outputs = response_dict.get("output", [])
                if outputs:
                    content_items = outputs[0].get("content", [])
                    if content_items:
                        first_item_dict = content_items[0]
                        if isinstance(first_item_dict, dict):
                            candidate = first_item_dict.get("parsed")
                            if candidate is not None:
                                parsed = candidate
            except Exception:
                parsed = None

        if parsed is not None:
            text = json.dumps(parsed, ensure_ascii=False)
            return AgentRunData(text=text, parsed=parsed)

        text = extract_output_text(response_dict if response_dict is not None else response)

        if expect_json:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                cleaned_match = _CODE_FENCE_RE.search(text)
                if cleaned_match:
                    cleaned_text = cleaned_match.group(1).strip()
                    try:
                        parsed = json.loads(cleaned_text)
                        text = cleaned_text
                    except json.JSONDecodeError as inner_exc:
                        raise ValueError(
                            f"{agent.name} returned invalid JSON: {text!r}"
                        ) from inner_exc
                else:
                    raise ValueError(
                        f"{agent.name} returned invalid JSON: {text!r}"
                    ) from exc

        return AgentRunData(text=text, parsed=parsed)

    @staticmethod
    def _append_assistant_text(conversation: List[Dict[str, Any]], text: str) -> None:
        conversation.append(
            {"role": "assistant", "content": [text_item(text, item_type="output_text")]}
        )

    @staticmethod
    def _normalize_ats_keywords(
        keywords: Optional[Union[Sequence[str], str]]
    ) -> Optional[List[str]]:
        if keywords is None:
            return None
        if isinstance(keywords, str):
            normalized_source = keywords.replace("\n", ",")
            items = [chunk.strip() for chunk in normalized_source.split(",")]
        else:
            items = [str(item).strip() for item in keywords]
        normalized = [item for item in items if item]
        return normalized or None

