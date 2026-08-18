"""search_knowledge — simple Markdown file search (no vector DB).

LangGraph / LangChain lesson: a **tool** is a callable capability the agent
(or a node) invokes. This project is about the graph, not RAG quality, so we
use literal case-insensitive matching over ``knowledge/*.md``.
"""

from __future__ import annotations

import re
from pathlib import Path

from langchain_core.tools import tool

# PRJ-02/knowledge — resolved from this file: app/tools/ → ../../knowledge
_KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledge"
_MAX_SNIPPETS = 4
_SNIPPET_CHARS = 500


def _iter_docs(category: str | None = None) -> list[Path]:
    """Prefer the category file when known; otherwise search all .md files."""
    if not _KNOWLEDGE_DIR.is_dir():
        return []
    if category and category != "unknown":
        preferred = _KNOWLEDGE_DIR / f"{category}.md"
        if preferred.is_file():
            return [preferred]
    return sorted(_KNOWLEDGE_DIR.glob("*.md"))


def _score_chunk(chunk: str, terms: list[str]) -> int:
    lower = chunk.lower()
    return sum(1 for t in terms if t in lower)


def search_knowledge_impl(query: str, category: str | None = None) -> list[str]:
    """Return ranked text snippets from the local knowledge base."""
    needle = (query or "").strip()
    if not needle:
        return ["Error: query must be a non-empty string."]

    terms = [t.lower() for t in re.findall(r"[a-zA-Z0-9']+", needle) if len(t) > 2]
    if not terms:
        terms = [needle.lower()]

    scored: list[tuple[int, str]] = []
    for path in _iter_docs(category):
        text = path.read_text(encoding="utf-8")
        # Split on headings / blank lines for coarse chunks.
        parts = re.split(r"\n(?=## )", text)
        for part in parts:
            score = _score_chunk(part, terms)
            if score <= 0 and category and category != "unknown":
                # Still keep intro of the category file so we never return empty
                # when the topic is known but wording differs.
                if part.startswith("# "):
                    score = 1
                else:
                    continue
            elif score <= 0:
                continue
            snippet = part.strip()
            if len(snippet) > _SNIPPET_CHARS:
                snippet = snippet[:_SNIPPET_CHARS].rstrip() + "…"
            scored.append((score, f"[{path.name}]\n{snippet}"))

    scored.sort(key=lambda item: item[0], reverse=True)
    snippets = [s for _, s in scored[:_MAX_SNIPPETS]]
    if not snippets:
        return [
            "No matching documentation found. Ask the user to clarify the LEPA area "
            "(login, students, attendance, grades, reports)."
        ]
    return snippets


@tool
def search_knowledge(query: str, category: str = "unknown") -> str:
    """Search LEPA support Markdown docs for a query.

    Args:
        query: User issue or keywords (e.g. "grades not showing").
        category: Optional issue category from classification.
    """
    snippets = search_knowledge_impl(query, category=category or None)
    return "\n\n---\n\n".join(snippets)
