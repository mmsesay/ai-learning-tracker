"""Read-only Git status helpers for a project under the workspace."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.projects import WorkspaceError, resolve_project

_GIT_TIMEOUT_SEC = 15


def _run_git(project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command in project_root without modifying the repo."""
    return subprocess.run(
        ["git", "-C", str(project_root), *args],
        capture_output=True,
        text=True,
        timeout=_GIT_TIMEOUT_SEC,
        check=False,
    )


def git_summary(project: str) -> str:
    """Summarize Git state for a project (branch + dirty files).

    Runs only read-only git commands (`rev-parse`, `status`). Never stages,
    commits, checkouts, or otherwise mutates the repository.

    Args:
        project: Project name or path under WORKSPACE_ROOT.

    Returns:
        A short human-readable status summary, or an error string.
    """
    try:
        root = resolve_project(project)
    except WorkspaceError as exc:
        return f"Error: {exc}"

    # Confirm this directory is a git work tree before summarizing.
    inside = _run_git(root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        err = (inside.stderr or inside.stdout or "").strip()
        return (
            f"Project: {root}\n"
            f"Not a Git repository.\n"
            f"{err}\n"
        )

    branch_proc = _run_git(root, "rev-parse", "--abbrev-ref", "HEAD")
    branch = branch_proc.stdout.strip() if branch_proc.returncode == 0 else "(unknown)"

    # Porcelain v1: stable machine-readable status (XY path).
    status_proc = _run_git(root, "status", "--porcelain")
    if status_proc.returncode != 0:
        return (
            f"Project: {root}\n"
            f"Branch: {branch}\n"
            f"Error running git status: {(status_proc.stderr or '').strip()}\n"
        )

    lines = [ln for ln in status_proc.stdout.splitlines() if ln.strip()]
    modified: list[str] = []
    untracked: list[str] = []
    other: list[str] = []

    for line in lines:
        # Format: two status chars, space, path (rename has " -> ").
        code = line[:2] if len(line) >= 2 else "??"
        path = line[3:] if len(line) > 3 else line
        if code == "??":
            untracked.append(path)
        elif code.strip() == "":
            other.append(path)
        elif "M" in code or "A" in code or "D" in code or "R" in code or "C" in code:
            modified.append(f"{code} {path}")
        else:
            other.append(f"{code} {path}")

    short = _run_git(root, "status", "-sb")
    short_line = short.stdout.strip().splitlines()[0] if short.stdout.strip() else ""

    out: list[str] = [
        f"Project: {root}",
        f"Branch: {branch}",
        f"Summary: {short_line or '(no short status)'}",
        f"Dirty entries: {len(lines)}",
        "",
    ]

    if not lines:
        out.append("Working tree clean (no modified or untracked files).")
        return "\n".join(out) + "\n"

    if modified:
        out.append("Modified / staged:")
        out.extend(f"  - {item}" for item in modified)
        out.append("")
    if untracked:
        out.append("Untracked:")
        out.extend(f"  - {item}" for item in untracked)
        out.append("")
    if other:
        out.append("Other:")
        out.extend(f"  - {item}" for item in other)
        out.append("")

    return "\n".join(out).rstrip() + "\n"
