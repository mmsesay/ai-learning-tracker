"""Smoke test for Step 1 graph: START → receive_question → END."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from app.graph import build_graph


def test_step1_receive_question_sets_final_answer() -> None:
    graph = build_graph()
    result = graph.invoke(
        {"messages": [HumanMessage(content="How do I enter grades?")]}
    )
    assert "final_answer" in result
    assert "How do I enter grades?" in result["final_answer"]
    assert result["issue_category"] == "unknown"
    assert any(isinstance(m, AIMessage) for m in result["messages"])
