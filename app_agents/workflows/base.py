"""Common utilities shared by agent workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

ContentItem = Dict[str, Any]
Message = Dict[str, Any]


@dataclass
class AgentDefinition:
    """Metadata describing how to invoke a single agent."""

    name: str
    instructions: str
    model: str
    temperature: float = 1.0
    top_p: float = 1.0
    max_output_tokens: int = 2048
    response_format: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    reasoning: Optional[Dict[str, Any]] = None

    def build_request(
        self, conversation: Iterable[Message]
    ) -> Dict[str, Any]:
        """Create the payload sent to the Responses API."""

        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": self.instructions,
                    }
                ],
            },
            *conversation,
        ]

        request: Dict[str, Any] = {
            "model": self.model,
            "input": messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_output_tokens": self.max_output_tokens,
        }

        if self.response_format is not None:
            request["text"] = {"format": self.response_format}
        if self.tools is not None:
            request["tools"] = self.tools
        if self.reasoning is not None:
            request["reasoning"] = self.reasoning

        return request


def text_item(text: str, *, item_type: str = "input_text") -> ContentItem:
    """Return a Responses API content item containing text."""

    return {"type": item_type, "text": text}


def user_message(text: str) -> Message:
    """Create a user message for the Responses API."""

    return {"role": "user", "content": [text_item(text)]}


def extract_output_text(response: Any) -> str:
    """Safely extract concatenated text output from a Responses API response."""

    text = getattr(response, "output_text", None)
    if text:
        return text

    output = None
    if isinstance(response, dict):
        output = response.get("output")
    elif hasattr(response, "output"):
        output = response.output  # type: ignore[attr-defined]

    if output is not None:
        chunks: List[str] = []
        for block in output:
            if isinstance(block, dict):
                content = block.get("content")
            else:
                content = getattr(block, "content", None)
            if not content:
                continue
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get("type")
                    value = item.get("text") or item.get("content")
                else:
                    item_type = getattr(item, "type", None)
                    value = getattr(item, "text", None)
                    if value is None and hasattr(item, "content"):
                        value = getattr(item, "content")
                if item_type in {"output_text", "text"} and isinstance(value, str):
                    chunks.append(value)
        if chunks:
            return "".join(chunks)

    raise RuntimeError("Unable to extract text from agent response")


def parse_json_response(response: Any) -> Any:
    """Parse a JSON payload from a Responses API response."""

    text = extract_output_text(response)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive path
        raise ValueError("Agent response was not valid JSON") from exc
