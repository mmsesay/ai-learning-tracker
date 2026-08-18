"""LLM client helpers (OpenAI-compatible / OpenRouter).

Optional polish layer — the graph works fully offline without a key.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.settings import Settings, get_settings


def llm_configured(settings: Settings | None = None) -> bool:
    """True when an API key is available and LLM polish is not disabled."""
    s = settings or get_settings()
    if not s.lepa_use_llm:
        return False
    return bool(s.openrouter_api_key or s.openai_api_key)


def build_chat_model(settings: Settings | None = None) -> ChatOpenAI:
    """Create a ChatOpenAI client pointing at OpenAI or OpenRouter."""
    s = settings or get_settings()
    if s.openrouter_api_key:
        return ChatOpenAI(
            model=s.openai_model,
            api_key=s.openrouter_api_key,
            base_url=s.openai_base_url or "https://openrouter.ai/api/v1",
            temperature=0.2,
        )
    if s.openai_api_key:
        kwargs: dict = {
            "model": s.openai_model,
            "api_key": s.openai_api_key,
            "temperature": 0.2,
        }
        if s.openai_base_url:
            kwargs["base_url"] = s.openai_base_url
        return ChatOpenAI(**kwargs)
    raise RuntimeError("No OPENROUTER_API_KEY or OPENAI_API_KEY configured")
