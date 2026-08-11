"""DevAssist MCP server (PRJ-01-B).

Exposes local project discovery, code search, and read-only git status as MCP
tools. Serves either:

- **stdio** — local Cursor / Claude Desktop (`TRANSPORT=stdio`)
- **streamable-http** — remote MCP on ``/mcp`` (default; Render / uvicorn)

Configure ``WORKSPACE_ROOT``, ``PORT``, ``HOST``, and ``API_KEY``.
Tool implementations live in ``tools/`` and are unchanged by the HTTP layer.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Cursor / uvicorn may start this file with a cwd outside PRJ-01-B.
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mcp.server import MCPServer

from tools.git import git_summary as git_summary_impl
from tools.projects import list_projects as list_projects_impl
from tools.search import search_code as search_code_impl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("devassist")

# Server name shown to MCP clients (product name: DevAssist).
mcp = MCPServer("devassist")


@mcp.tool()
async def list_projects() -> str:
    """List development projects under WORKSPACE_ROOT.

    Scans the first level of the configured workspace directory and returns
    each project's name and absolute path. Hidden directories are skipped.

    Returns:
        A readable list of project names and paths.
    """
    return list_projects_impl()


@mcp.tool()
async def search_code(query: str, project: str) -> str:
    """Search source files in a project for a literal text query.

    Ignores common noise directories such as .git, node_modules, .venv,
    __pycache__, and build output folders. Paths are validated so search
    cannot leave WORKSPACE_ROOT.

    Args:
        query: Text to find (case-insensitive substring).
        project: Project directory name or relative path under WORKSPACE_ROOT.

    Returns:
        Matching paths with line numbers and line text, or an error message.
    """
    return search_code_impl(query=query, project=project)


@mcp.tool()
async def git_summary(project: str) -> str:
    """Show a read-only Git summary for a project.

    Reports the current branch, a short status line, and modified/untracked
    files. Never runs mutating git commands.

    Args:
        project: Project directory name or relative path under WORKSPACE_ROOT.

    Returns:
        A short repository status summary, or an error message.
    """
    return git_summary_impl(project=project)


def main() -> None:
    """Start DevAssist using TRANSPORT from the environment."""
    from config import load_settings
    from http_app import build_http_app

    settings = load_settings()
    # Ensure workspace env is visible to tool modules (they read os.environ).
    import os

    if settings.workspace_root:
        os.environ.setdefault("WORKSPACE_ROOT", settings.workspace_root)

    if settings.transport == "stdio":
        logger.info("Starting DevAssist over stdio (local MCP)")
        mcp.run(transport="stdio")
        return

    # Public binds without a key would expose tools to the internet.
    if settings.binds_publicly and not settings.auth_enabled:
        raise SystemExit(
            "Refusing to start Streamable HTTP on a public bind (HOST="
            f"{settings.host}) without API_KEY. Set API_KEY, or use "
            "HOST=127.0.0.1 for local open access."
        )

    # Init bundled demo git repo when present (safe no-op otherwise).
    # Keeps Render Start Command as plain `python server.py`.
    try:
        from scripts.prepare_demo_workspace import main as prepare_demo

        prepare_demo()
    except Exception as exc:  # noqa: BLE001 — demo prep must not block serving
        logger.warning("demo workspace prepare skipped: %s", exc)

    # Streamable HTTP — official MCP remote transport (not legacy SSE).
    # PORT comes from the environment (Render injects $PORT).
    app = build_http_app(mcp, settings)
    import uvicorn

    logger.info(
        "Starting DevAssist Streamable HTTP on http://%s:%s/mcp (auth=%s)",
        settings.host,
        settings.port,
        "on" if settings.auth_enabled else "off",
    )
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
