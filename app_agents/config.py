"""Configuration helpers for agent workflows."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, ValidationError

try:  # pragma: no cover - optional convenience dependency
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fall back silently when not installed
    load_dotenv = None  # type: ignore[assignment]


def _ensure_dotenv_loaded() -> None:
    """Load .env once at import time if python-dotenv is available."""

    if load_dotenv is None:
        return

    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    # Don't override existing env vars; just populate missing ones.
    load_dotenv(env_path, override=False)


_ensure_dotenv_loaded()

try:  # pragma: no cover - import guard for runtime flexibility
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # pragma: no cover - fallback for environments on Pydantic v1
    from pydantic import BaseSettings  # type: ignore[assignment]

    SettingsConfigDict = None  # type: ignore[assignment]


class AgentSettings(BaseSettings):
    """Runtime configuration for agent workflows."""

    openai_api_key: str = Field(
        alias="OPENAI_API_KEY",
        description="API key used to authenticate with OpenAI services.",
    )
    openai_base_url: Optional[str] = Field(
        default=None,
        alias="OPENAI_BASE_URL",
        description="Optional override for the OpenAI API base URL.",
    )

    if "SettingsConfigDict" in globals() and SettingsConfigDict is not None:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
        )
    else:  # pragma: no cover - compatibility with legacy Pydantic
        class Config:  # type: ignore[too-many-ancestors]
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> AgentSettings:
    """Return cached application settings with a friendly error if missing."""

    try:
        return AgentSettings()
    except ValidationError as exc:  # pragma: no cover - simple pass/fail guard
        missing_key = any("openai_api_key" in "".join(map(str, err["loc"])) for err in exc.errors())
        hint = (
            "Set OPENAI_API_KEY in your environment or .env file before running this "
            "workflow. See README.md for setup instructions."
        )
        message = hint if missing_key else str(exc)
        raise RuntimeError(message) from exc
