"""MCP Resume Agent workflow for coordinating DOCX generation."""

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
from ..prompts import MCP_RESUME_AGENT_INSTRUCTIONS
from .base import AgentDefinition, extract_output_text, text_item, user_message


def _json_schema(name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "json_schema",
        "name": name,
        "schema": schema,
    }


# Schema for MCP Resume Agent output
MCP_RESUME_AGENT_SCHEMA = {
    "type": "object",
    "properties": {
        "filename": {"type": "string"},
        "resume_data": {"type": "object"},
        "mcp_server_ready": {"type": "boolean"},
        "reasoning": {"type": "string"},
    },
    "required": ["filename", "resume_data", "mcp_server_ready", "reasoning"],
    "additionalProperties": False,
}


# Agent definition for MCP Resume Agent
MCP_RESUME_AGENT = AgentDefinition(
    name="MCP Resume Agent",
    instructions=MCP_RESUME_AGENT_INSTRUCTIONS,
    model="gpt-4o",
    temperature=0.3,
    response_format=_json_schema(
        "MCPResumeAgentOutput",
        MCP_RESUME_AGENT_SCHEMA,
    ),
)


@dataclass
class MCPResumeAgentResult:
    """Result from the MCP Resume Agent."""
    
    filename: str
    resume_data: Dict[str, Any]
    mcp_server_ready: bool
    reasoning: str
    text: str
    parsed: Optional[Dict[str, Any]]


def prepare_resume_for_mcp(
    optimized_resume: Dict[str, Any],
    client: Optional[OpenAI] = None,
) -> MCPResumeAgentResult:
    """
    Run the MCP Resume Agent to prepare resume for DOCX generation.
    
    This agent:
    1. Reviews the optimized resume JSON
    2. Determines an appropriate filename based on the candidate's name
    3. Prepares the data for sending to the MCP server
    
    Args:
        optimized_resume: The complete, optimized resume JSON
        client: Optional OpenAI client (creates one if not provided)
        
    Returns:
        MCPResumeAgentResult with filename, resume data, and metadata
    """
    if client is None:
        client = create_openai_client()
    
    # Prepare input for the agent
    input_payload = {
        "optimized_resume": optimized_resume,
    }
    
    conversation = [
        user_message(json.dumps(input_payload, ensure_ascii=False, indent=2))
    ]
    
    # Build request
    request = MCP_RESUME_AGENT.build_request(conversation)
    
    # Call the agent
    if MCP_RESUME_AGENT.response_format is not None:
        response = client.responses.parse(**request)
    else:
        response = client.responses.create(**request)
    
    # Extract the result
    response_dict: Optional[Dict[str, Any]] = None
    if hasattr(response, "model_dump"):
        try:
            response_dict = response.model_dump()  # type: ignore[call-arg]
        except Exception:  # pragma: no cover - defensive
            response_dict = None
    
    # Try to extract parsed JSON
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
        except Exception:  # pragma: no cover - best-effort fallback
            parsed = None
    
    # Fallback to response_dict
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
    
    # Extract text
    if parsed is not None:
        text = json.dumps(parsed, ensure_ascii=False)
    else:
        text = extract_output_text(response_dict if response_dict is not None else response)
        # Try to parse the text as JSON
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            # If parsing fails, use defaults
            parsed = {
                "filename": "resume.docx",
                "resume_data": optimized_resume,
                "mcp_server_ready": True,
                "reasoning": "Fallback filename due to parsing error",
            }
            text = json.dumps(parsed, ensure_ascii=False)
    
    return MCPResumeAgentResult(
        filename=parsed["filename"],
        resume_data=parsed["resume_data"],
        mcp_server_ready=parsed["mcp_server_ready"],
        reasoning=parsed["reasoning"],
        text=text,
        parsed=parsed,
    )
