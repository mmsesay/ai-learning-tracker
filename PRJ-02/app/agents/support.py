"""Support agent — turn retrieved docs into the final user-facing answer."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.llm import build_chat_model, llm_configured
from app.state import SupportState
from app.utils import last_user_text

_SYSTEM = """You are the LEPA school-support assistant.
Answer ONLY using the documentation snippets provided.
Be concise, practical, and step-oriented.
If the docs are insufficient, say what is missing — do not invent LEPA features.
"""


def _template_answer(
    *,
    docs: list[str],
    category: str,
    role: str,
    question: str,
) -> str:
    """Deterministic fallback — used in tests and when no LLM key is set."""
    if not docs:
        return (
            "I could not find LEPA documentation for that yet. "
            "Please say which area you need help with "
            "(login, students, attendance, grades, or reports)."
        )
    body = "\n\n".join(docs)
    return (
        f"Here’s what LEPA docs say about your question"
        f"{f' ({category})' if category != 'unknown' else ''}"
        f"{f' as a {role}' if role != 'unknown' else ''}:\n\n"
        f"{body}\n\n"
        f"— Based on your question: {question!r}"
    )


def _llm_answer(*, docs: list[str], category: str, role: str, question: str) -> str:
    model = build_chat_model()
    context = "\n\n---\n\n".join(docs) if docs else "(no documents retrieved)"
    user = (
        f"Category: {category}\n"
        f"User role: {role}\n"
        f"Question: {question}\n\n"
        f"Documentation snippets:\n{context}\n\n"
        "Write the support reply now."
    )
    result = model.invoke(
        [
            SystemMessage(content=_SYSTEM),
            HumanMessage(content=user),
        ]
    )
    return str(result.content).strip()


def run_support(state: SupportState) -> dict:
    """Compose the final answer from ``retrieved_documents``.

    Prefer an LLM rewrite when configured; always fall back to the template
    path so the graph stays usable offline and in CI.
    """
    docs = list(state.get("retrieved_documents") or [])
    category = state.get("issue_category") or "unknown"
    role = state.get("user_role") or "unknown"
    question = last_user_text(state)

    answer = _template_answer(
        docs=docs, category=category, role=role, question=question
    )

    if docs and llm_configured():
        try:
            answer = _llm_answer(
                docs=docs, category=category, role=role, question=question
            )
        except Exception:
            # Keep template answer — never fail the graph because the LLM hiccuped.
            pass

    return {
        "final_answer": answer,
        "messages": [AIMessage(content=answer)],
    }
