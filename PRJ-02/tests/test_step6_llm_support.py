"""Support agent LLM polish — offline path must still work."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from app.agents import support as support_mod
from app.graph import build_graph


def test_support_uses_template_when_llm_disabled(monkeypatch) -> None:
    monkeypatch.setenv("LEPA_USE_LLM", "false")
    # Clear cached settings if any future caching appears.
    from app import settings as settings_mod

    if hasattr(settings_mod.get_settings, "cache_clear"):
        settings_mod.get_settings.cache_clear()

    graph = build_graph()
    result = graph.invoke(
        {"messages": [HumanMessage(content="Why aren't grades showing?")]}
    )
    assert "Based on your question" in result["final_answer"]
    assert result.get("retrieved_documents")


def test_llm_answer_helper_invoked_when_configured(monkeypatch) -> None:
    monkeypatch.setattr(support_mod, "llm_configured", lambda: True)

    def fake_llm(**kwargs):
        return "Polished: publish your draft grades."

    monkeypatch.setattr(support_mod, "_llm_answer", fake_llm)
    out = support_mod.run_support(
        {
            "messages": [HumanMessage(content="grades missing")],
            "issue_category": "grades",
            "user_role": "teacher",
            "retrieved_documents": ["[grades.md]\nPublish the assessment."],
        }
    )
    assert out["final_answer"].startswith("Polished:")
