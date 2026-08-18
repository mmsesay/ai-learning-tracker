"""Export the compiled LangGraph as Mermaid + ASCII for docs / learning.

Run:
    uv run python -m app.visualize
"""

from __future__ import annotations

from pathlib import Path

from app.graph import build_graph

_DOCS = Path(__file__).resolve().parents[1] / "docs"


def export_graph_docs(docs_dir: Path | None = None) -> tuple[Path, Path]:
    """Write ``graph.mmd`` and ``graph.ascii`` from the live compiled graph.

    LangGraph concept: ``compiled.get_graph()`` exposes the topology so you can
    visualize nodes and conditional edges without drawing them by hand.
    """
    out = docs_dir or _DOCS
    out.mkdir(parents=True, exist_ok=True)

    compiled = build_graph()
    drawable = compiled.get_graph()

    mermaid = drawable.draw_mermaid()
    try:
        ascii_art = drawable.draw_ascii()
    except ImportError:
        # grandalf is optional; keep a readable fallback for docs/CI.
        ascii_art = (
            "START\n"
            "  → intake\n"
            "  → classify\n"
            "       ├─ clarify → ask_clarification → END\n"
            "       └─ continue → knowledge → support → END\n"
            "\n"
            "(Install grandalf for LangGraph ASCII rendering: uv add --dev grandalf)\n"
        )

    mermaid_path = out / "graph.mmd"
    ascii_path = out / "graph.ascii"
    mermaid_path.write_text(
        mermaid + ("\n" if not mermaid.endswith("\n") else ""),
        encoding="utf-8",
    )
    ascii_path.write_text(
        ascii_art + ("\n" if not ascii_art.endswith("\n") else ""),
        encoding="utf-8",
    )
    return mermaid_path, ascii_path


def mermaid_source() -> str:
    """Return Mermaid text for the API / tests."""
    return build_graph().get_graph().draw_mermaid()


if __name__ == "__main__":
    mmd, asc = export_graph_docs()
    print(f"Wrote {mmd}")
    print(f"Wrote {asc}")
    print()
    print(asc)
