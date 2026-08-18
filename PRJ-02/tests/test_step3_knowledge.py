"""Step 3: knowledge base search + support answer path."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from app.graph import build_graph
from app.tools.search_knowledge import search_knowledge_impl


def test_search_knowledge_finds_grades_publish() -> None:
    snippets = search_knowledge_impl("grades not showing", category="grades")
    blob = "\n".join(snippets).lower()
    assert "publish" in blob
    assert "grades.md" in blob


def test_search_knowledge_empty_query() -> None:
    out = search_knowledge_impl("  ", category="grades")
    assert out[0].startswith("Error:")


def test_graph_grades_returns_doc_grounded_answer() -> None:
    graph = build_graph()
    result = graph.invoke(
        {"messages": [HumanMessage(content="Why aren't grades showing?")]}
    )
    assert result["issue_category"] == "grades"
    assert result.get("retrieved_documents")
    assert "Publish" in result["final_answer"] or "publish" in result["final_answer"]


def test_graph_login_path_uses_authentication_docs() -> None:
    graph = build_graph()
    result = graph.invoke(
        {"messages": [HumanMessage(content="I can't log in to LEPA")]}
    )
    assert result["issue_category"] == "authentication"
    assert any("authentication.md" in d for d in result["retrieved_documents"])
    assert "password" in result["final_answer"].lower()


def test_vague_still_asks_clarification() -> None:
    graph = build_graph()
    result = graph.invoke({"messages": [HumanMessage(content="help")]})
    assert result["clarification_needed"] is True
    assert not result.get("retrieved_documents")
