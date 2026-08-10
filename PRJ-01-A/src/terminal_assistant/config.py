"""Load settings from environment / .env file.

Defaults target OpenRouter free models so you can learn without OpenAI billing.
The OpenAI Python SDK still works — OpenRouter is OpenAI-compatible: same client,
different base_url + model id.

Switch models anytime by changing OPENAI_MODEL in .env (free or paid).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# OpenRouter free router: picks a free model that supports your request (incl. tools)
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "openrouter/free"


@dataclass(frozen=True)
class Settings:
    """Immutable runtime config passed into the agent."""

    api_key: str
    model: str
    base_url: str | None  # None → official OpenAI; set for OpenRouter / proxies
    workspace: Path  # sandbox root for all file/shell tools
    max_iterations: int = 10  # agent-loop safety cap


def load_settings(workspace: Path | None = None) -> Settings:
    """Load config from env vars.

    Looks for `.env` in the current working directory first, then in PRJ-01-A/,
    so you can launch the CLI from any folder and still find your key.
    """
    cwd = Path.cwd()
    load_dotenv(cwd / ".env")
    # parents[2]: .../src/terminal_assistant/config.py → PRJ-01-A/
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")

    # Prefer OpenRouter key names; fall back to OPENAI_API_KEY (OpenAI-compatible clients)
    api_key = (
        os.getenv("OPENROUTER_API_KEY")
        or os.getenv("OPEN_ROUTER_API_KEY")  # accept common alternate spelling
        or os.getenv("OPENAI_API_KEY")
        or ""
    ).strip()
    if not api_key or api_key in {"sk-...", "your-key-here"}:
        raise SystemExit(
            "Missing API key. Set OPENROUTER_API_KEY in .env "
            "(get one free at https://openrouter.ai/keys)."
        )

    # Detect OpenRouter so defaults point at free models / correct base URL
    using_openrouter = bool(
        os.getenv("OPENROUTER_API_KEY")
        or os.getenv("OPEN_ROUTER_API_KEY")
        or (os.getenv("OPENAI_BASE_URL") or "").find("openrouter.ai") >= 0
        or api_key.startswith("sk-or-")
    )

    if using_openrouter:
        default_model = DEFAULT_OPENROUTER_MODEL
        default_base = DEFAULT_OPENROUTER_BASE_URL
    else:
        default_model = "gpt-4.1-mini"
        default_base = ""

    model = os.getenv("OPENAI_MODEL", default_model).strip()
    base_url = os.getenv("OPENAI_BASE_URL", default_base).strip() or None

    return Settings(
        api_key=api_key,
        model=model,
        base_url=base_url,
        workspace=(workspace or cwd).resolve(),
    )
