"""Lightweight fake OpenAI client for offline workflow runs."""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Iterable, List, Optional


@dataclass
class MockResponseSpec:
    """Instruction describing a mocked Responses API call."""

    kind: str  # "create" or "parse"
    text: Optional[str] = None
    parsed: Optional[Any] = None


class _FakeResponse:
    """Minimal object mimicking the OpenAI Responses return value."""

    def __init__(self, *, text: Optional[str], parsed: Optional[Any]) -> None:
        if parsed is not None and text is None:
            text = json.dumps(parsed, ensure_ascii=False)

        self.output_text = text or ""

        content_item = {"type": "output_text", "text": self.output_text}
        if parsed is not None:
            content_item["parsed"] = parsed

        self.output: List[dict] = [{"content": [content_item]}]

    def model_dump(self) -> dict:  # pragma: no cover - convenience for parity
        return {"output": self.output}


class _FakeResponsesAPI:
    """Sequence-driven replacement for the OpenAI Responses API."""

    def __init__(self, specs: Iterable[MockResponseSpec]) -> None:
        self._queue: Deque[MockResponseSpec] = deque(specs)

    def create(self, **_kwargs: Any) -> _FakeResponse:
        return self._consume("create")

    def parse(self, **_kwargs: Any) -> _FakeResponse:
        return self._consume("parse")

    def _consume(self, expected: str) -> _FakeResponse:
        if not self._queue:
            raise RuntimeError("No mock responses remaining for OpenAI call")

        spec = self._queue.popleft()
        if spec.kind not in {expected, "any"}:
            raise RuntimeError(
                f"Expected a '{expected}' mock response but encountered '{spec.kind}'"
            )

        return _FakeResponse(text=spec.text, parsed=spec.parsed)


class FakeOpenAI:
    """Drop-in replacement for :class:`openai.OpenAI` backed by mock responses."""

    def __init__(self, specs: Iterable[MockResponseSpec]) -> None:
        self.responses = _FakeResponsesAPI(specs)

    @classmethod
    def from_specs(cls, specs: Iterable[MockResponseSpec]) -> "FakeOpenAI":
        return cls(list(specs))
