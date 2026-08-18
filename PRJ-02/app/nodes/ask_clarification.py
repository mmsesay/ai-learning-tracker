"""Ask the user for missing details when classification cannot proceed."""

from __future__ import annotations

from langchain_core.messages import AIMessage

from app.state import SupportState


_DEFAULT_QUESTION = (
    "I want to help with LEPA. Which area is this about — "
    "login/authentication, students, attendance, grades, or reports? "
    "Please share one concrete symptom (for example: “I can’t log in” or "
    "“grades are missing for Class 5”)."
)


def ask_clarification(state: SupportState) -> dict:
    """Route target when ``clarification_needed`` is True.

    Sets ``final_answer`` so the API/CLI can return the clarifying question
    immediately. Multi-turn “user replies → classify again” needs checkpointing
    (later step) so the next message shares the same thread id.
    """
    category = state.get("issue_category") or "unknown"
    question = _DEFAULT_QUESTION
    if category != "unknown":
        question = (
            f"This looks related to **{category}**, but I still need more detail. "
            "What exactly happens in LEPA, and what did you expect instead?"
        )

    return {
        "clarification_question": question,
        "final_answer": question,
        "messages": [AIMessage(content=question)],
    }
