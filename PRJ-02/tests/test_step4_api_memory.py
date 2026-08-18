"""FastAPI + checkpoint memory tests."""

from __future__ import annotations

from langchain_core.messages import HumanMessage
from fastapi.testclient import TestClient

from app.graph import build_graph
from app.memory.checkpoint import make_memory_checkpointer
from api.main import app


def test_multi_turn_clarification_then_grades(tmp_path) -> None:
    """Same thread_id: vague → clarify, then grades question → docs answer."""
    db = str(tmp_path / "mem.sqlite")
    graph = build_graph(checkpointer=make_memory_checkpointer(db))
    config = {"configurable": {"thread_id": "teacher-1"}}

    first = graph.invoke(
        {"messages": [HumanMessage(content="help")]},
        config=config,
    )
    assert first["clarification_needed"] is True
    assert first.get("clarification_question")

    second = graph.invoke(
        {"messages": [HumanMessage(content="Why aren't grades showing?")]},
        config=config,
    )
    assert second["issue_category"] == "grades"
    assert second["clarification_needed"] is False
    assert second.get("retrieved_documents")
    # Prior human turns still in state (checkpointed memory).
    assert len(second["messages"]) >= 3


def test_chat_endpoint_new_thread() -> None:
    client = TestClient(app)
    res = client.post("/chat", json={"message": "How do I enter grades?"})
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == "grades"
    assert data["memory_updated"] is True
    assert data["thread_id"]
    assert "grade" in data["answer"].lower() or "Grade" in data["answer"]


def test_chat_endpoint_reuses_thread() -> None:
    client = TestClient(app)
    first = client.post("/chat", json={"message": "help"}).json()
    tid = first["thread_id"]
    assert first["clarification_needed"] is True

    second = client.post(
        "/chat",
        json={"message": "I can't log in", "thread_id": tid},
    ).json()
    assert second["thread_id"] == tid
    assert second["category"] == "authentication"
    assert second["clarification_needed"] is False
