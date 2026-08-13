"""Unit tests for search_code match-cap metadata."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.search as search_mod
from tools.search import search_code


def test_search_code_reports_shown_of_total_when_capped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When matches exceed the cap, the header must not imply that is the total."""
    project = tmp_path / "cap-demo"
    project.mkdir()
    (project / "hits.py").write_text(
        "\n".join(f"token_{i} = 'MARKER'" for i in range(10)) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setattr(search_mod, "_MAX_MATCHES", 3)

    out = search_code(query="MARKER", project="cap-demo")

    assert "3 shown of 10" in out
    assert "matches_shown=3" in out
    assert "matches_total=10" in out
    assert "More usages exist beyond this cap" in out
    body_lines = [ln for ln in out.splitlines() if "MARKER" in ln and ":" in ln]
    # Header mentions MARKER in Query line; body hit lines look like hits.py:N: ...
    hit_lines = [ln for ln in body_lines if ln.startswith("hits.py:")]
    assert len(hit_lines) == 3


def test_search_code_shown_equals_total_when_under_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "small-demo"
    project.mkdir()
    (project / "app.py").write_text("hello MARKER world\n", encoding="utf-8")
    monkeypatch.setenv("WORKSPACE_ROOT", str(tmp_path))

    out = search_code(query="MARKER", project="small-demo")

    assert "1 shown of 1" in out
    assert "Truncated" not in out
