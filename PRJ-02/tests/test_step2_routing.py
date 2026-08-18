"""Step 2: conditional routing after classification."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from app.graph import build_graph
from app.nodes.classify import classify_issue


def test_classify_grades_is_clear() -> None:
    category, needs, _ = classify_issue("How do I enter grades?")
    assert category == "grades"
    assert needs is False


def test_classify_vague_needs_clarification() -> None:
    category, needs, _ = classify_issue("help")
    assert category == "unknown"
    assert needs is True


def test_graph_routes_clear_question_to_knowledge_path() -> None:
    graph = build_graph()
    result = graph.invoke(
        {"messages": [HumanMessage(content="How do I enter grades?")]}
    )
    assert result["issue_category"] == "grades"
    assert result["clarification_needed"] is False
    assert result.get("retrieved_documents")
    assert "grades" in result["final_answer"].lower()
    assert "enter grades" in result["final_answer"].lower()


def test_graph_routes_vague_question_to_clarification() -> None:
    graph = build_graph()
    result = graph.invoke({"messages": [HumanMessage(content="help")]})
    assert result["clarification_needed"] is True
    assert result.get("clarification_question")
    assert "LEPA" in result["final_answer"]


def test_intake_detects_teacher_role() -> None:
    graph = build_graph()
    result = graph.invoke(
        {
            "messages": [
                HumanMessage(content="I'm a teacher — how do I take attendance?")
            ]
        }
    )
    assert result["user_role"] == "teacher"
    assert result["issue_category"] == "attendance"
    assert result["clarification_needed"] is False
