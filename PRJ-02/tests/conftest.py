"""Pytest defaults — keep the suite offline unless a test opts into LLM."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _disable_llm_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEPA_USE_LLM", "false")
