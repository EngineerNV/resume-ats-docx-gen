"""File Naming Agent workflow for coordinating DOCX generation.

This module supersedes the previous mcp_resume_agent for clarity.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:  # pragma: no cover - import guard for offline runs
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover - fallback when SDK unavailable
    from typing import Any as _Any

    OpenAI = _Any  # type: ignore[assignment]

from ..client import create_openai_client
from ..prompts import FILE_NAMING_AGENT_INSTRUCTIONS
import re
from .base import AgentDefinition, extract_output_text, text_item, user_message


def _json_schema(name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "json_schema",
        "name": name,
        "schema": schema,
    }


# Schema for File Naming Agent output (same shape as legacy MCP Resume Agent)
FILE_NAMING_AGENT_SCHEMA = {
    "type": "object",
    "properties": {
        "filename": {"type": "string"},
        "resume_data": {
            "type": "object",
            "description": "Optimized resume JSON payload ready for DOCX generation.",
            "additionalProperties": True,
        },
        "mcp_server_ready": {"type": "boolean"},
        "reasoning": {"type": "string"},
    },
    "required": ["filename", "resume_data", "mcp_server_ready", "reasoning"],
    "additionalProperties": False,
}


# Agent definition for File Naming Agent
FILE_NAMING_AGENT = AgentDefinition(
    name="File Naming Agent",
    instructions=FILE_NAMING_AGENT_INSTRUCTIONS,
    model="gpt-5-mini",
    response_format=None,
)


@dataclass
class FileNamingAgentResult:
    """Result from the File Naming Agent."""

    filename: str
    resume_data: Dict[str, Any]
    mcp_server_ready: bool
    reasoning: str
    text: str
    parsed: Optional[Dict[str, Any]]


def prepare_resume_for_mcp(
    optimized_resume: Dict[str, Any],
    client: Optional[Any] = None,
) -> FileNamingAgentResult:
    """
    Run the File Naming Agent to prepare resume for DOCX generation.

    This agent:
    1. Reviews the optimized resume JSON
    2. Determines an appropriate filename based on the candidate's name
    3. Prepares the data for direct DOCX generation
    """
    if client is None:
        client = create_openai_client()

    input_payload = {
        "optimized_resume": optimized_resume,
    }

    conversation = [
        user_message(json.dumps(input_payload, ensure_ascii=False, indent=2))
    ]

    request = FILE_NAMING_AGENT.build_request(conversation)

    if FILE_NAMING_AGENT.response_format is not None:
        response = client.responses.parse(**request)
    else:
        response = client.responses.create(**request)

    response_dict: Optional[Dict[str, Any]] = None
    if hasattr(response, "model_dump"):
        try:
            response_dict = response.model_dump()  # type: ignore[call-arg]
        except Exception:  # pragma: no cover
            response_dict = None

    parsed: Optional[Dict[str, Any]] = None
    if hasattr(response, "output"):
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
        except Exception:  # pragma: no cover
            parsed = None

    if parsed is None and response_dict is not None:
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

    def _sanitize_filename(s: str) -> str:
        s = s.strip()
        # remove surrounding quotes if present
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            s = s[1:-1]
        # replace spaces and punctuation with underscores, keep alphanumerics and underscores and dots
        s = re.sub(r"[^0-9A-Za-z._]+", "_", s)
        # collapse multiple underscores
        s = re.sub(r"_+", "_", s)
        s = s.strip("_")
        if not s.lower().endswith('.docx'):
            s = s + '.docx'
        return s

    def _filename_from_resume(resume: Dict[str, Any]) -> str:
        header = resume.get("header", {}) if isinstance(resume, dict) else {}
        name = header.get("name") or header.get("full_name") or ""
        if name and isinstance(name, str):
            # build firstname_lastname_resume.docx
            parts = re.findall(r"[A-Za-z0-9]+", name)
            if parts:
                fname = "_".join(parts).lower() + "_resume.docx"
                return _sanitize_filename(fname)
    return "resume.docx"

    filename: str = ""
    resume_data: Dict[str, Any] = optimized_resume
    mcp_server_ready = True
    reasoning = ""
    text = ""

    if parsed is not None:
        # parsed may be a dict-like or a plain string depending on model output
        text = json.dumps(parsed, ensure_ascii=False) if not isinstance(parsed, str) else str(parsed)
        if isinstance(parsed, str):
            filename = _sanitize_filename(parsed)
            reasoning = "Filename returned as plain string by the agent."
        elif isinstance(parsed, dict) and parsed.get("filename"):
            filename = _sanitize_filename(parsed.get("filename"))
            resume_data = parsed.get("resume_data", optimized_resume)
            mcp_server_ready = parsed.get("mcp_server_ready", True)
            reasoning = parsed.get("reasoning", "Filename derived from parsed JSON.")
        else:
            # fallback to try extracting filename from text
            try:
                loaded = json.loads(text)
                if isinstance(loaded, str):
                    filename = _sanitize_filename(loaded)
                    reasoning = "Filename extracted from JSON string payload."
                elif isinstance(loaded, dict) and loaded.get("filename"):
                    filename = _sanitize_filename(loaded.get("filename"))
                    resume_data = loaded.get("resume_data", optimized_resume)
                    mcp_server_ready = loaded.get("mcp_server_ready", True)
                    reasoning = loaded.get("reasoning", "Filename extracted from JSON object payload.")
            except Exception:
                filename = _filename_from_resume(optimized_resume)
                reasoning = "Fallback filename generated from resume header due to unparseable agent output."
    else:
        # No parsed structured output; try to extract text and interpret it
        text = extract_output_text(response_dict if response_dict is not None else response)
        # try JSON first
        try:
            loaded = json.loads(text)
            if isinstance(loaded, str):
                filename = _sanitize_filename(loaded)
                reasoning = "Filename extracted from JSON string payload."
            elif isinstance(loaded, dict) and loaded.get("filename"):
                filename = _sanitize_filename(loaded.get("filename"))
                resume_data = loaded.get("resume_data", optimized_resume)
                mcp_server_ready = loaded.get("mcp_server_ready", True)
                reasoning = loaded.get("reasoning", "Filename extracted from JSON object payload.")
            else:
                # If JSON does not contain filename, try to treat raw text as filename
                filename = _sanitize_filename(text)
                reasoning = "Assumed raw text output is the filename."
        except Exception:
            # not JSON; assume the raw text is the filename or fall back to resume header
            stripped = text.strip()
            if stripped:
                filename = _sanitize_filename(stripped)
                reasoning = "Assumed raw text output is the filename."
            else:
                filename = _filename_from_resume(optimized_resume)
                reasoning = "Fallback filename generated from resume header due to empty agent output."

    return FileNamingAgentResult(
        filename=filename,
        resume_data=resume_data,
        mcp_server_ready=mcp_server_ready,
        reasoning=reasoning,
        text=text,
        parsed=parsed,
    )
