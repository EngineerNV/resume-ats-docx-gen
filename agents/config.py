"""Configuration helpers for agent workflows."""

from functools import lru_cache
from typing import Optional

from pydantic import Field

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
    """Return cached application settings."""

    return AgentSettings()
