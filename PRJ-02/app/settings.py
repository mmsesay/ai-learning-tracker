"""App settings from environment (no secrets in code)."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Runtime config for API + checkpointing."""

    model_config = SettingsConfigDict(
        env_file=str(_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str | None = None
    openrouter_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "openai/gpt-4o-mini"
    lepa_checkpoint_path: str = str(_ROOT / "data" / "checkpoints.sqlite")
    # When false, support agent always uses the template answer (good for CI).
    lepa_use_llm: bool = True


def get_settings() -> Settings:
    return Settings()
