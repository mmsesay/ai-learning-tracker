"""Workspace discovery and path safety for the developer MCP server.

`list_projects` scans a configurable root directory. Other tools import
`get_workspace_root` and `resolve_project` so every path stays inside that root.
"""

from __future__ import annotations

import os
from pathlib import Path

# Markers that suggest a directory is a real software project (not just a folder).
_PROJECT_MARKERS = (
    ".git",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "requirements.txt",
    "Gemfile",
    "pom.xml",
)


class WorkspaceError(ValueError):
    """Raised when the workspace is misconfigured or a path is rejected."""


def get_workspace_root() -> Path:
    """Return the configured workspace root from WORKSPACE_ROOT.

    Defaults to the current working directory if the env var is unset.
    The path is resolved so later containment checks are reliable.
    """
    raw = os.environ.get("WORKSPACE_ROOT", ".").strip() or "."
    root = Path(raw).expanduser().resolve()
    if not root.is_dir():
        raise WorkspaceError(
            f"WORKSPACE_ROOT is not a directory: {root}. "
            "Set WORKSPACE_ROOT to a folder that contains your projects."
        )
    return root


def resolve_project(project: str) -> Path:
    """Resolve a project name or relative path under the workspace root.

    Accepts either a directory name (`ai-learning-tracker`) or a relative
    path (`ai-learning-tracker/PRJ-01-A`). Absolute paths are allowed only
    if they resolve inside the workspace.

    Raises:
        WorkspaceError: if the path is outside the workspace or missing.
    """
    name = (project or "").strip()
    if not name:
        raise WorkspaceError("project is required (name or path under the workspace).")

    root = get_workspace_root()
    candidate = Path(name).expanduser()
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (root / candidate).resolve()

    # Containment check: resolved must be root or a child of root.
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise WorkspaceError(
            f"Refusing path outside WORKSPACE_ROOT ({root}): {project!r}"
        ) from exc

    if not resolved.exists():
        raise WorkspaceError(f"Project not found: {project!r} (looked in {resolved})")
    if not resolved.is_dir():
        raise WorkspaceError(f"Not a directory: {project!r}")

    return resolved


def _looks_like_project(path: Path) -> bool:
    """True if the directory has a common project marker."""
    return any((path / marker).exists() for marker in _PROJECT_MARKERS)


def list_projects() -> str:
    """List development projects under WORKSPACE_ROOT.

    Scans only the first level of the workspace (immediate child directories).
    Hidden folders (names starting with ``.``) are skipped. Each entry shows
    whether common project markers were found.

    Returns:
        A readable multi-line summary of project names and absolute paths.
    """
    try:
        root = get_workspace_root()
    except WorkspaceError as exc:
        return f"Error: {exc}"

    entries: list[Path] = sorted(
        (p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")),
        key=lambda p: p.name.lower(),
    )

    if not entries:
        return f"No projects found under {root}"

    lines = [
        f"Workspace: {root}",
        f"Projects ({len(entries)}):",
        "",
    ]
    for path in entries:
        marker = "project" if _looks_like_project(path) else "folder"
        lines.append(f"- {path.name}")
        lines.append(f"  path: {path}")
        lines.append(f"  kind: {marker}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
