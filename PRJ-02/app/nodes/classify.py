"""Classify support intent into an issue category + clarification flag.

Educational choice for Step 2: keyword / heuristic classifier.

Why not an LLM yet?
- Conditional routing is the lesson — not model quality.
- Unit tests stay offline and deterministic.
- Swap this module later for structured LLM output without changing the graph.
"""

from __future__ import annotations

import re

from app.state import IssueCategory, SupportState
from app.utils import last_user_text

# (category, keyword patterns) — first match wins (order = priority).
_CATEGORY_RULES: list[tuple[IssueCategory, re.Pattern[str]]] = [
    ("authentication", re.compile(r"\b(log ?in|password|otp|sign ?in|auth|locked out)\b", re.I)),
    ("students", re.compile(r"\b(student|enrol|enroll|register|admission)\b", re.I)),
    ("attendance", re.compile(r"\b(attendance|present|absent|roll call)\b", re.I)),
    ("grades", re.compile(r"\b(grade|grades|mark|marks|score|scores|assessment)\b", re.I)),
    ("reports", re.compile(r"\b(report|reports|export|pdf|printout)\b", re.I)),
]

_VAGUE = re.compile(
    r"^\s*(help|hi|hello|hey|broken|issue|problem|error|not working|doesn't work|does not work)\s*[.!]?\s*$",
    re.I,
)


def classify_issue(text: str) -> tuple[IssueCategory, bool, str]:
    """Return (category, clarification_needed, reason_for_logs).

    Clarification is requested when the message is vague or the category is
    unknown — the model (later) / support agent cannot help without a topic.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return "unknown", True, "empty_message"

    for category, pattern in _CATEGORY_RULES:
        if pattern.search(cleaned):
            return category, False, f"matched_{category}"

    if _VAGUE.match(cleaned) or len(cleaned.split()) <= 3:
        return "unknown", True, "vague_or_short"

    # Specific question but no category keyword — still ask which area of LEPA.
    return "unknown", True, "no_category_keyword"


def classify_node(state: SupportState) -> dict:
    """Node: write ``issue_category`` and ``clarification_needed`` into state."""
    text = last_user_text(state)
    category, needs_clarification, _reason = classify_issue(text)
    return {
        "issue_category": category,
        "clarification_needed": needs_clarification,
    }
