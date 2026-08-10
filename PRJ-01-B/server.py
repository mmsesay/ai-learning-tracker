"""DevAssist MCP server (PRJ-01-B).

Exposes local project discovery, code search, and read-only git status as MCP
tools over stdio so clients like Cursor can call them.

Configure the project root with the WORKSPACE_ROOT environment variable.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Cursor may start this file with a cwd outside PRJ-01-B; keep local imports working.
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mcp.server import MCPServer

from tools.git import git_summary as git_summary_impl
from tools.projects import list_projects as list_projects_impl
from tools.search import search_code as search_code_impl

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


if __name__ == "__main__":
    # stdio is what Cursor uses for local MCP servers.
    mcp.run(transport="stdio")
