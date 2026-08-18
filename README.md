# AI Learning Tracker

Public learning repo for **Maej** ([Muhammad Sesay](https://github.com/mmsesay)) — shipping small AI projects while leveling into AI engineering.

Personal study plans and daily logs live in **Google Sheets** (private). This repo is for **code you can clone**.

## Phase 1

| ID | Name | Status | Folder |
|----|------|--------|--------|
| PRJ-01-A | **TAM** — AI Terminal Assistant (tool calling CLI) | Done | [`PRJ-01-A/`](PRJ-01-A/) |
| PRJ-01-B | **DevAssist** — MCP server (stdio + remote Streamable HTTP) | Done | [`PRJ-01-B/`](PRJ-01-B/) |

## PRJ-01-A — TAM

Local terminal agent that uses LLM **tool calling** to explore a workspace:

- list / read / search files  
- write files & run shell (with confirmation)  
- git status  
- OpenRouter free or paid models  

```bash
cd PRJ-01-A
cp .env.example .env   # set OPENROUTER_API_KEY
uv venv && source .venv/bin/activate
uv pip install -e .
tam
```

Details and setup: [`PRJ-01-A/README.md`](PRJ-01-A/README.md)

## PRJ-01-B — DevAssist MCP

**DevAssist** is an MCP server Cursor (or Render) can connect to:

- `list_projects` — projects under `WORKSPACE_ROOT`  
- `search_code` — search a project (skips `.git`, `node_modules`, `.venv`, …)  
- `git_summary` — read-only branch + dirty files  
- **Transports:** local **stdio** or remote **Streamable HTTP** (`POST /mcp`)  

```bash
cd PRJ-01-B
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export WORKSPACE_ROOT="$HOME/Projects"
python server.py   # http://0.0.0.0:3000/mcp
```

Details, Render, Cursor remote URL, and AI SDK example: [`PRJ-01-B/README.md`](PRJ-01-B/README.md)

## Links

- Site: [muhammad.sesay.work](https://muhammad.sesay.work)  
- X: [@NaMiMaej](https://twitter.com/NaMiMaej)  
- OpenRouter: [openrouter.ai](https://openrouter.ai)  
- MCP: [modelcontextprotocol.io](https://modelcontextprotocol.io)
