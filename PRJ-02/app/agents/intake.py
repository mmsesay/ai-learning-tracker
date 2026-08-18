"""Intake agent — first look at the user message before classification.

Step 2 keeps intake **deterministic** (no LLM) so the graph concepts stay
obvious and tests do not require API keys. A later step can swap this for an
LLM that extracts role / missing fields with structured output.
"""

from __future__ import annotations

import re

from app.state import SupportState
from app.utils import last_user_text


def _detect_role(text: str) -> str:
    lower = text.lower()
    if re.search(r"\b(admin|administrator|principal|head\s*teacher)\b", lower):
        return "admin"
    if re.search(r"\b(teacher|staff|educator)\b", lower):
        return "teacher"
    return "unknown"


def run_intake(state: SupportState) -> dict:
    """Normalize intake fields from the latest user message.

    LangGraph: this node only *writes* role (and leaves routing to classify).
    """
    text = last_user_text(state)
    return {
        "user_role": _detect_role(text),
    }
