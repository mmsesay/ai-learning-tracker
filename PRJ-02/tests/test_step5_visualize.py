"""Graph visualization export tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from app.visualize import export_graph_docs, mermaid_source


def test_mermaid_contains_core_nodes() -> None:
    src = mermaid_source()
    for name in ("intake", "classify", "ask_clarification", "knowledge", "support"):
        assert name in src
    assert "clarify" in src
    assert "continue" in src


def test_export_writes_files(tmp_path) -> None:
    mmd, asc = export_graph_docs(tmp_path)
    assert mmd.is_file()
    assert asc.is_file()
    assert "intake" in mmd.read_text(encoding="utf-8")
    assert "classify" in asc.read_text(encoding="utf-8")


def test_graph_endpoint() -> None:
    client = TestClient(app)
    res = client.get("/graph")
    assert res.status_code == 200
    data = res.json()
    assert data["format"] == "mermaid"
    assert "knowledge" in data["source"]
