"""Utilities for creating OpenAI clients used by agent workflows."""

from __future__ import annotations

from typing import Optional

try:  # pragma: no cover - import guard for offline runs
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover - fallback when SDK unavailable
    class OpenAI:  # type: ignore[too-many-ancestors]
        def __init__(self, *_, **__):
            raise RuntimeError(
                "The OpenAI Python SDK is required for live agent calls. Install the"
                " 'openai' package or run with --mock-run to replay recorded outputs."
            )

from .config import get_settings


def create_openai_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> OpenAI:
    """Create and return a configured :class:`OpenAI` client."""

    settings = get_settings()
    key = api_key or settings.openai_api_key
    if base_url is None:
        base_url = settings.openai_base_url

    return OpenAI(api_key=key, base_url=base_url)
