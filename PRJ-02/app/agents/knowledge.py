"""Knowledge agent — retrieve docs via the search_knowledge tool."""

from __future__ import annotations

from app.state import SupportState
from app.tools.search_knowledge import search_knowledge_impl
from app.utils import last_user_text


def run_knowledge(state: SupportState) -> dict:
    """Call the knowledge tool and store snippets on state.

    Demonstrates tool use *inside* a graph node. Later you could bind the same
    ``@tool`` to an LLM; for learning we call the implementation directly so
    retrieval stays visible and testable offline.
    """
    query = last_user_text(state)
    category = state.get("issue_category") or "unknown"
    snippets = search_knowledge_impl(query, category=category)
    return {"retrieved_documents": snippets}
