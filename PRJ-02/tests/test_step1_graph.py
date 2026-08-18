"""Smoke tests retained from Step 1 — now assert the Step 2 clear-path behavior."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from app.graph import build_graph


def test_clear_question_reaches_final_answer() -> None:
    graph = build_graph()
    result = graph.invoke(
        {"messages": [HumanMessage(content="How do I enter grades?")]}
    )
    assert "final_answer" in result
    assert result["issue_category"] == "grades"
    assert "grades" in result["final_answer"]
    assert any(isinstance(m, AIMessage) for m in result["messages"])
