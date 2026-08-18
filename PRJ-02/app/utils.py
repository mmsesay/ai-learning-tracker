"""Shared helpers for reading graph state (keep nodes thin)."""

from __future__ import annotations

from langchain_core.messages import BaseMessage, HumanMessage

from app.state import SupportState


def last_user_text(state: SupportState) -> str:
    """Return the most recent human message content, or empty string."""
    messages: list[BaseMessage] = list(state.get("messages") or [])
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return str(msg.content).strip()
    return ""
