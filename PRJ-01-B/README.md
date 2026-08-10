# PRJ-01-B — Developer Workspace MCP Server

A small, local **Model Context Protocol (MCP)** server that lets Cursor (or any MCP client) list your projects, search code, and read Git status — without leaving a configured workspace directory.

This replaces the earlier weather/API toy example with something you can use while coding.

## What is MCP?

**MCP (Model Context Protocol)** is a standard way for AI apps to call external tools and data sources.

- The **client** (e.g. Cursor) speaks MCP.
- The **server** (this project) exposes tools over a transport — here, **stdio**.
- The model decides when to call a tool; your Python code does the real work and returns text results.

Same idea as tool calling in **PRJ-01-A (TAM)**, but the tools are packaged as an MCP server other apps can plug in.

## What this project demonstrates

- Defining MCP tools with the official Python SDK (`MCPServer`)
- Splitting tool logic into small modules
- Path validation so tools cannot escape `WORKSPACE_ROOT`
- Read-only Git inspection via subprocess
- Simple, beginner-friendly structure (no web framework, no agent loop)

## Architecture

```text
Cursor (MCP client)
        │  stdio
        ▼
   server.py          ← registers tools, runs MCPServer
        │
        ├── tools/projects.py  → list_projects()
        ├── tools/search.py    → search_code(query, project)
        └── tools/git.py       → git_summary(project)
```

| Piece | Role |
|-------|------|
| `server.py` | MCP entrypoint; thin wrappers with docstrings for the client |
| `tools/projects.py` | Workspace root + path safety + project listing |
| `tools/search.py` | Literal text search with ignored directories |
| `tools/git.py` | Branch + dirty files (read-only) |
| `WORKSPACE_ROOT` | Env var: parent folder that contains your projects |

## Available tools

| Tool | Purpose |
|------|---------|
| `list_projects()` | List first-level folders under `WORKSPACE_ROOT` (name + path) |
| `search_code(query, project)` | Search source files; skip `.git`, `node_modules`, `.venv`, etc. |
| `git_summary(project)` | Current branch + modified/untracked files (never mutates) |

## Install

Python 3.10+ recommended.

```bash
cd PRJ-01-B
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
cd PRJ-01-B
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

Quick smoke test (should print projects under your workspace):

```bash
export WORKSPACE_ROOT="$HOME/Projects"   # change to your projects folder
python -c "from tools.projects import list_projects; print(list_projects())"
```

## Configure Cursor

Add a server entry to `~/.cursor/mcp.json` (create the file if needed). Adjust paths for your machine:

```json
{
  "mcpServers": {
    "developer-workspace": {
      "command": "/home/nexlura/Projects/ai-learning-tracker/PRJ-01-B/.venv/bin/python",
      "args": [
        "/home/nexlura/Projects/ai-learning-tracker/PRJ-01-B/server.py"
      ],
      "env": {
        "WORKSPACE_ROOT": "/home/nexlura/Projects"
      }
    }
  }
}
```

Using `uv` instead of a venv path:

```json
{
  "mcpServers": {
    "developer-workspace": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/nexlura/Projects/ai-learning-tracker/PRJ-01-B",
        "run",
        "--with-requirements",
        "requirements.txt",
        "python",
        "server.py"
      ],
      "env": {
        "WORKSPACE_ROOT": "/home/nexlura/Projects"
      }
    }
  }
}
```

Then: **Cursor Settings → Tools & MCP** → reload / enable **developer-workspace**.

## Example prompts (after connecting)

- “List my development projects.”
- “Search `ai-learning-tracker` for `MCPServer`.”
- “What’s the git status of `ai-learning-tracker`?”
- “In `ai-learning-tracker`, find where `list_projects` is defined.”
- “Summarize dirty files in my learning tracker repo.”

## Security considerations

- **Workspace jail:** every project path is resolved and must stay under `WORKSPACE_ROOT`. Absolute paths outside that root are rejected.
- **Read-mostly:** this server lists, searches, and runs read-only `git` commands. It does not write files or mutate git state.
- **Trust boundary:** an MCP client can invoke any exposed tool. Only enable this server for workspaces you are comfortable exposing to the model.
- **Secrets:** do not point `WORKSPACE_ROOT` at folders full of credentials; search can surface `.env.example`-style files and other text. Prefer excluding secret-heavy trees from the workspace root.
- **Local only:** stdio MCP is for your machine; do not expose this process on a network port without a real auth model.

## Layout

```text
PRJ-01-B/
├── server.py           # MCP server entry
├── tools/
│   ├── projects.py     # list_projects + path helpers
│   ├── search.py       # search_code
│   └── git.py          # git_summary
├── requirements.txt
├── README.md
└── .gitignore
```

## How it fits Phase 1

| ID | Focus |
|----|--------|
| **PRJ-01-A** | Tool calling inside your own CLI agent (TAM) |
| **PRJ-01-B** | Same skill idea, exposed as an MCP server for Cursor |

Keep this small on purpose — fundamentals first, not a production code-intel platform.
