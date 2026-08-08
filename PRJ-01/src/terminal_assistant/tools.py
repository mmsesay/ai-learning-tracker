"""Tool schemas (for the LLM) and implementations (for your code).

Two halves of tool calling live here:

1. TOOL_SCHEMAS — JSON the model reads to know *what* it can call
2. Python functions + dispatch_tool — what actually runs on your machine

The agent loop (agent.py) connects them: model picks a tool → we run it →
we send the string result back as a role=tool message.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Truncate large outputs so we do not blow the model context window
MAX_READ_CHARS = 40_000
MAX_SEARCH_HITS = 40
MAX_SHELL_CHARS = 20_000
SHELL_TIMEOUT_SEC = 30


def resolve_in_workspace(workspace: Path, relative: str) -> Path:
    """Resolve a path under workspace; reject escapes via .. or absolute paths outside.

    Without this, a malicious/confused tool call like `../../etc/passwd` could
    read files outside the project you launched the assistant in.
    """
    workspace = workspace.resolve()
    candidate = (workspace / relative).resolve()
    try:
        candidate.relative_to(workspace)
    except ValueError as exc:
        raise PermissionError(
            f"Path escapes workspace: {relative!r} (workspace={workspace})"
        ) from exc
    return candidate


# --- Tool implementations -----------------------------------------------


def list_files(workspace: Path, path: str = ".") -> str:
    """List files and directories under path (relative to workspace)."""
    target = resolve_in_workspace(workspace, path)
    if not target.exists():
        return f"Error: path does not exist: {path}"
    if not target.is_dir():
        return f"Error: not a directory: {path}"

    entries: list[str] = []
    # Directories first, then files; case-insensitive names
    for child in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        kind = "dir" if child.is_dir() else "file"
        entries.append(f"{kind}\t{child.name}")
    if not entries:
        return "(empty directory)"
    return "\n".join(entries)


def read_file(workspace: Path, path: str) -> str:
    """Read a text file under the workspace."""
    target = resolve_in_workspace(workspace, path)
    if not target.exists():
        return f"Error: file does not exist: {path}"
    if not target.is_file():
        return f"Error: not a file: {path}"
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"Error reading {path}: {exc}"
    if len(text) > MAX_READ_CHARS:
        return text[:MAX_READ_CHARS] + f"\n\n...[truncated, {len(text)} chars total]"
    return text


def search_text(workspace: Path, query: str, path: str = ".") -> str:
    """Search for query in text files under path (simple substring match).

    This is intentionally naive (not ripgrep) so the learning code stays small.
    """
    if not query:
        return "Error: query must not be empty"
    root = resolve_in_workspace(workspace, path)
    if not root.exists():
        return f"Error: path does not exist: {path}"

    hits: list[str] = []
    # Skip heavy / generated trees — speeds search and avoids noisy matches
    skip_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", ".tox"}

    def walk(directory: Path) -> None:
        nonlocal hits
        try:
            children = list(directory.iterdir())
        except OSError:
            return
        for child in children:
            if len(hits) >= MAX_SEARCH_HITS:
                return
            if child.is_dir():
                if child.name in skip_dirs:
                    continue
                walk(child)
            elif child.is_file():
                try:
                    # Skip likely-binary / huge files quickly
                    if child.stat().st_size > 1_000_000:
                        continue
                    content = child.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for i, line in enumerate(content.splitlines(), start=1):
                    if query.lower() in line.lower():
                        rel = child.relative_to(workspace)
                        hits.append(f"{rel}:{i}: {line.strip()}")
                        if len(hits) >= MAX_SEARCH_HITS:
                            return

    if root.is_file():
        try:
            content = root.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(content.splitlines(), start=1):
                if query.lower() in line.lower():
                    rel = root.relative_to(workspace)
                    hits.append(f"{rel}:{i}: {line.strip()}")
                    if len(hits) >= MAX_SEARCH_HITS:
                        break
        except OSError as exc:
            return f"Error reading {path}: {exc}"
    else:
        walk(root)

    if not hits:
        return f"No matches for {query!r}"
    suffix = "" if len(hits) < MAX_SEARCH_HITS else f"\n...[truncated at {MAX_SEARCH_HITS} hits]"
    return "\n".join(hits) + suffix


def write_file(workspace: Path, path: str, content: str) -> str:
    """Write content to a file under the workspace (creates parent dirs).

    The agent asks for confirmation before this runs (see CONFIRM_TOOLS).
    """
    target = resolve_in_workspace(workspace, path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    except OSError as exc:
        return f"Error writing {path}: {exc}"
    return f"Wrote {len(content)} chars to {path}"


def execute_shell_command(workspace: Path, command: str) -> str:
    """Run a shell command with cwd=workspace. Output is truncated.

    Dangerous by nature — always gated by user confirmation in the agent loop.
    """
    if not command.strip():
        return "Error: command must not be empty"
    try:
        completed = subprocess.run(
            command,
            shell=True,  # needed for pipes/redirects the model may request
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=SHELL_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {SHELL_TIMEOUT_SEC}s"
    except OSError as exc:
        return f"Error running command: {exc}"

    parts = [
        f"exit_code={completed.returncode}",
        "--- stdout ---",
        completed.stdout or "(empty)",
        "--- stderr ---",
        completed.stderr or "(empty)",
    ]
    text = "\n".join(parts)
    if len(text) > MAX_SHELL_CHARS:
        return text[:MAX_SHELL_CHARS] + f"\n...[truncated, {len(text)} chars total]"
    return text


def git_status(workspace: Path) -> str:
    """Return short git status for the workspace."""
    try:
        completed = subprocess.run(
            ["git", "status", "--short"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        return "Error: git is not installed"
    except subprocess.TimeoutExpired:
        return "Error: git status timed out"
    except OSError as exc:
        return f"Error: {exc}"

    if completed.returncode != 0:
        err = (completed.stderr or completed.stdout or "").strip()
        return f"Error (exit {completed.returncode}): {err or 'not a git repository?'}"
    out = completed.stdout.strip()
    return out if out else "(clean working tree)"


# --- OpenAI / OpenRouter tool schemas -----------------------------------
# These are NOT Python. They are JSON Schema descriptions the model reads.
# name + parameters must match what dispatch_tool expects.

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories in a path relative to the workspace root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path. Default: '.'",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a text file relative to the workspace root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative file path to read",
                    },
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_text",
            "description": "Search for a text query in files under a path (case-insensitive).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Substring to search for",
                    },
                    "path": {
                        "type": "string",
                        "description": "Relative path to search under. Default: '.'",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite a text file. Requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative file path to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full file contents to write",
                    },
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_shell_command",
            "description": "Run a shell command in the workspace. Requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute",
                    },
                },
                "required": ["command"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Show git status --short for the workspace.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
]

# Tools that need an interactive [y/N] before running (side effects)
CONFIRM_TOOLS = frozenset({"write_file", "execute_shell_command"})


def dispatch_tool(
    name: str,
    arguments_json: str,
    workspace: Path,
) -> str:
    """Parse tool arguments and run the named Python function.

    Always returns a string — success text or an error message — so the LLM
    can read the outcome in the next agent-loop iteration.
    """
    try:
        args: dict[str, Any] = json.loads(arguments_json) if arguments_json else {}
    except json.JSONDecodeError as exc:
        return f"Error: invalid JSON arguments: {exc}"

    # name (from the model) → actual Python callable
    handlers: dict[str, Callable[..., str]] = {
        "list_files": lambda **kw: list_files(workspace, path=kw.get("path", ".")),
        "read_file": lambda **kw: read_file(workspace, path=kw["path"]),
        "search_text": lambda **kw: search_text(
            workspace, query=kw["query"], path=kw.get("path", ".")
        ),
        "write_file": lambda **kw: write_file(
            workspace, path=kw["path"], content=kw["content"]
        ),
        "execute_shell_command": lambda **kw: execute_shell_command(
            workspace, command=kw["command"]
        ),
        "git_status": lambda **kw: git_status(workspace),
    }

    handler = handlers.get(name)
    if handler is None:
        return f"Error: unknown tool {name!r}"

    try:
        return handler(**args)
    except KeyError as exc:
        return f"Error: missing argument {exc} for {name}"
    except PermissionError as exc:
        return f"Error: {exc}"
    except TypeError as exc:
        return f"Error: bad arguments for {name}: {exc}"
    except Exception as exc:  # noqa: BLE001 — surface any tool failure to the model
        return f"Error running {name}: {exc}"
