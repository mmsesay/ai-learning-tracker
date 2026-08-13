"""Text search across a single project under the workspace root."""

from __future__ import annotations

import os
from pathlib import Path

from tools.projects import WorkspaceError, resolve_project

# Directories we never descend into (noise + huge trees).
_IGNORE_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".tox",
        ".ruff_cache",
        "dist",
        "build",
        ".next",
        ".nuxt",
        "target",
        "coverage",
        ".turbo",
        ".cache",
        "eggs",
        ".eggs",
        ".local-deps",
        "site-packages",
    }
)

# Cap *shown* matches so MCP responses stay readable in a chat context.
# We still count the rest so the model sees "shown of total", not a false ceiling.
_MAX_MATCHES = 40
_MAX_FILE_BYTES = 1_000_000
_TEXT_SUFFIXES = frozenset(
    {
        ".py",
        ".pyi",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".mjs",
        ".cjs",
        ".go",
        ".rs",
        ".java",
        ".kt",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".cs",
        ".rb",
        ".php",
        ".swift",
        ".md",
        ".txt",
        ".toml",
        ".json",
        ".yaml",
        ".yml",
        ".ini",
        ".cfg",
        ".css",
        ".scss",
        ".html",
        ".xml",
        ".sh",
        ".bash",
        ".zsh",
        ".sql",
        ".gitignore",
        ".dockerignore",
    }
)


def _is_searchable_file(path: Path) -> bool:
    """Heuristic: known text suffix, or common extensionless filenames."""
    if path.name in {"Dockerfile", "Makefile", "Rakefile", "Gemfile"}:
        return True
    return path.suffix.lower() in _TEXT_SUFFIXES


def search_code(query: str, project: str) -> str:
    """Search source files inside one project for a literal query string.

    Skips common dependency/build directories. Matching is case-insensitive
    substring search (no regex) to keep the learning server simple.

    Args:
        query: Text to find (non-empty).
        project: Project name or path under WORKSPACE_ROOT.

    Returns:
        Header with matches_shown / matches_total, then matching paths with
        line numbers and line text — or an error string.
    """
    needle = (query or "").strip()
    if not needle:
        return "Error: query must be a non-empty string."

    try:
        root = resolve_project(project)
    except WorkspaceError as exc:
        return f"Error: {exc}"

    needle_lower = needle.lower()
    shown: list[str] = []
    matches_total = 0
    files_scanned = 0

    for dirpath_str, dirnames, filenames in os.walk(root):
        # Mutate dirnames in place so walk does not descend into ignored dirs.
        dirnames[:] = [
            d
            for d in dirnames
            if d not in _IGNORE_DIRS and not d.endswith(".egg-info")
        ]
        dirpath = Path(dirpath_str)

        for filename in filenames:
            path = dirpath / filename
            if not _is_searchable_file(path):
                continue
            try:
                if path.stat().st_size > _MAX_FILE_BYTES:
                    continue
            except OSError:
                continue

            files_scanned += 1
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            for line_no, line in enumerate(text.splitlines(), start=1):
                if needle_lower not in line.lower():
                    continue
                matches_total += 1
                # Keep counting after the cap so totals stay honest for the model.
                if len(shown) < _MAX_MATCHES:
                    rel = path.relative_to(root)
                    shown.append(f"{rel}:{line_no}: {line.strip()}")

    if matches_total == 0:
        return (
            f"Project: {root}\n"
            f"Query: {needle!r}\n"
            f"No matches in {files_scanned} scanned files "
            f"(ignored dirs like .git, node_modules, .venv).\n"
        )

    matches_shown = len(shown)
    header = (
        f"Project: {root}\n"
        f"Query: {needle!r}\n"
        f"Matches: {matches_shown} shown of {matches_total} "
        f"(scanned {files_scanned} files)\n"
    )
    if matches_total > matches_shown:
        header += (
            f"Truncated to {_MAX_MATCHES} matches "
            f"(matches_shown={matches_shown}, matches_total={matches_total}). "
            "More usages exist beyond this cap.\n"
        )
    header += "\n"
    return header + "\n".join(shown) + "\n"
